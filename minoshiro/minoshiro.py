from asyncio import get_event_loop
from base64 import b64encode
from itertools import chain
from pathlib import Path
from traceback import format_exc
from typing import Dict, Iterable, Union

from aiohttp_wrapper import SessionManager

from .data import data_path
from .data_controller import (DataController, PostgresController,
                              SqliteController)
from .enums import Medium, Site
from .helpers import get_synonyms
from .logger import get_default_logger
from .pre_cache import cache_top_pages
from .upstream import download_anidb
from .web_api import ani_db, ani_list, anime_planet, kitsu, lndb, mal, mu, nu


class Minoshiro:
    def __init__(self, db_controller: DataController, mal_config: dict,
                 *, logger=None, loop=None):
        """
        Represents the search instance.

        It is suggested to use one of the class methods to create the instance
        if you wish to use one of the data controllers provided by the library.

        Make sure you run the ``pre_cache`` method if you initialized the class
        directly from the ``__init__`` method.

        :param db_controller:
            Any sub class of ``minoshiro.data_controller.abc.DataController``
            will work here.

        :param mal_config:
            A dict for MAL authorization.
            It must contain the keys:
                ``user``: Your MAL username
                ``password``: Your MAL password

            It may also contain a key "description" for the description you
            wish to use in the auth header.

            If this key is not present, the description defaults to:
            ``A Python library for anime search.``

        :param logger:
            The logger object. If it's not provided, will use the
            defualt logger provided by the library.

        :param loop:
            An asyncio event loop. If not provided will use the default
            event loop.
        """
        self.session_manager = SessionManager()
        mal_user, mal_pass = mal_config.get('user'), mal_config.get('password')
        assert mal_user and mal_pass, ('Please provide MAL user'
                                       'name and password.')

        self.db_controller = db_controller

        mal_agent = mal_config.get(
            'description', 'A Python library for anime search.'
        )
        mal_auth = b64encode(f'{mal_user}:{mal_pass}'.encode()).decode()

        self.mal_headers = {
            'Authorization': f'Basic {mal_auth}',
            'User-Agent': mal_agent
        }

        self.kitsu = kitsu.Kitsu(
            self.session_manager, '', ''
        )

        self.loop = loop or get_event_loop()
        self.logger = logger or get_default_logger()

        self.__anidb_list = None
        self.__anidb_time = None

    @classmethod
    async def from_postgres(cls, mal_config: dict, db_config: dict = None,
                            pool=None, *, schema='minoshiro',
                            cache_pages: int = 0, cache_mal_entries: int = 0,
                            logger=None, loop=None):
        """
        Get an instance of `minoshiro` with class `PostgresController` as the
        database controller.

        :param mal_config:
            A dict for MAL authorization.
            It must contain the keys:
                user: Your MAL username
                password: Your MAL password

            It may also contain a key "description" for the description you
            wish to use in the auth header.

            If this key is not present, the description defaults to:
                "A Python library for anime search."

        :param db_config:
            A dict of database config for the connection.

            It should contain the keys in  keyword arguments for the :func:
            `asyncpg.connection.connect` function.

        :param pool: an existing connection pool.

        One of ``db_config`` or ``pool`` must not be None.

        :param schema: the schema name used. Defaults to `minoshiro`

        :param cache_pages:
            The number of pages of anime and manga from Anilist to cache
            before the instance is created. Each page contains 40 entries max.

        :param cache_mal_entries:
            The number of MAL entries you wish to cache.

        :param logger:
            The logger object. If it's not provided, will use the
            defualt logger provided by the library.

        :param loop:
            An asyncio event loop. If not provided will use the default
            event loop.

        :return:
            Instance of `minoshiro` with class `PostgresController`
            as the database controller.
        """
        assert db_config or pool, (
            'Please either provide a connection pool or '
            'a dict of connection data for creating a new '
            'connection pool.'
        )
        logger = logger or get_default_logger()
        db_controller = await PostgresController.get_instance(
            logger, db_config, pool, schema=schema
        )
        instance = cls(db_controller, mal_config, logger=logger, loop=loop)
        await instance.pre_cache(cache_pages, cache_mal_entries)
        return instance

    @classmethod
    async def from_sqlite(cls, mal_config: dict,
                          path: Union[str, Path], *,
                          cache_pages: int = 0, cache_mal_entries: int = 0,
                          logger=None, loop=None):
        """
        Get an instance of `minoshiro` with class `SqliteController` as the
        database controller.

        :param mal_config:
            A dict for MAL authorization.
            It must contain the keys:
                user: Your MAL username
                password: Your MAL password

            It may also contain a key "description" for the description you
            wish to use in the auth header.

            If this key is not present, the description defaults to:
                "A Python library for anime search."

        :param path:
            The path to the SQLite3 database, can either be a string or a
            Pathlib Path object.

        :param cache_pages:
            The number of pages of anime and manga from Anilist to cache
            before the instance is created. Each page contains 40 entries max.

        :param cache_mal_entries:
            The number of MAL entries you wish to cache.

        :param logger:
            The logger object. If it's not provided, will use the
            defualt logger provided by the library.

        :param loop:
            An asyncio event loop. If not provided will use the default
            event loop.

        :return:
            Instance of `minoshiro` with class `PostgresController`
            as the database controller.
        """
        logger = logger or get_default_logger()
        db_controller = await SqliteController.get_instance(path, logger, loop)
        instance = cls(db_controller, mal_config,
                       logger=logger, loop=loop)
        await instance.pre_cache(cache_pages, cache_mal_entries)
        return instance

    async def pre_cache(self, cache_pages: int, cache_mal_entries: int):
        """
        Pre cache the database with anime and managa data.

        :param cache_pages:
            Number of Anilist pages to cache. There are 40 entries per page.

        :param cache_mal_entries: Number of MAL entries you wish to cache.
        """
        assert cache_pages >= 0, 'Param `cache_pages` must not be negative.'
        assert cache_mal_entries >= 0, ('Param `cache_mal_entries`'
                                        'must not be negative.')
        if cache_mal_entries:
            assert cache_pages > 0, ('You must have at least 1'
                                     'cached page to cache MAL entries.')
        self.logger.info('Populating lookup...')
        await self.db_controller.pre_cache(self.session_manager)
        self.logger.info('Lookup populated.')

        self.logger.info('Populating data...')

        for med in (Medium.ANIME, Medium.MANGA):
            if cache_pages:
                await cache_top_pages(
                    med, self.session_manager, self.db_controller,
                    self.mal_headers, cache_pages, cache_mal_entries,
                    self.logger
                )

        self.logger.info('Data populated.')
        await self.__fetch_anidb()

    async def yield_data(self, query: str, medium: Medium,
                         sites: Iterable[Site] = None, *, timeout=3):
        """
        Yield the data for the search query from all sites.

        :param query: the search query.

        :param medium: the medium type.

        :param sites:
            an iterable of sites desired. If None is provided, will
            search all sites by default.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return:
            an asynchronous generator that yields the site and data
            in a tuple for all sites requested.
        """
        sites = sites if sites else list(Site)
        cached_data, cached_id = await self.__get_cached(query, medium)
        to_be_cached = {}
        names = []
        for site in sites:
            res, id_ = await self.__get_result(
                cached_data, cached_id, query, names, site, medium, timeout
            )
            if res:
                yield site, res
                for title in get_synonyms(res, site):
                    names.append(title)
            if id_:
                to_be_cached[site] = id_
        await self.__cache(to_be_cached, names, medium)

    async def get_data(self, query: str, medium: Medium,
                       sites: Iterable[Site] = None, *,
                       timeout=3) -> Dict[Site, dict]:
        """
        Get the data for the search query in a dict.

        :param query: the search query.

        :param medium: the medium type.

        :param sites:
            an iterable of sites desired. If None is provided, will
            search all sites by default.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: Data for all sites in a dict {Site: data}
        """
        return {site: val async for site, val in self.yield_data(
            query, medium, sites, timeout=timeout
        )}

    async def __cache(self, to_be_cached, names, medium):
        """
        Cache search results into the db.

        :param to_be_cached: items to be cached.

        :param names: all names for the item.

        :param medium: the medium type.
        """
        itere = set(chain(*names))
        for site, id_ in to_be_cached.items():
            await self.__cache_one(site, id_, medium, itere)

    async def __cache_one(self, site, id_, medium, iterator):
        """
        Cache one id.

        :param site: the site.

        :param id_: the id.

        :param medium: the medium type.

        :param iterator: an iterator for all names.
        """
        for name in iterator:
            if name:
                await self.db_controller.set_identifier(
                    name, medium, site, id_
                )

    async def __fetch_anidb(self):
        """
        Fetch data dump from anidb if one of the following is True:
            The data dump file is not found.
            The data dump file is more than a day old.
        """
        dump_path = data_path.joinpath('anime-titles.xml')
        self.logger.info('Checking anidb conditions...')
        good, new_time = await download_anidb(
            self.session_manager, self.__anidb_time
        )
        if good:
            self.logger.info(
                'Anidb condition is good, no new data downloaded.'
            )
        else:
            self.logger.info(
                'Anidb condition is outdated, new data downloaded.'
            )

        if not good or not self.__anidb_list:
            self.logger.info('Reading anidb data from disk...')
            with dump_path.open() as xml_file:
                xml = xml_file.read()
            self.__anidb_list = ani_db.process_xml(xml)
            self.logger.info('Anidb data read from disk.')
        self.__anidb_time = new_time

    async def __find_anilist(self, cached_data, cached_ids,
                             medium, query, timeout):
        """
        Find Anilist data.

        Return the cached data if it exists.

        If there are no cached data, attempt make an api call to Anilist and
        find the data. Return and cache the api call result if it's found,
        else return None.

        :param cached_data: a dict of cached data.

        :param cached_ids: a dict of cached ids.

        :param medium: the medium type.

        :param query: the search query.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: the anilist data and id in a tuple if found.
        """
        if medium not in (Medium.ANIME, Medium.MANGA, Medium.LN):
            return None, None
        cached_anilist = cached_data.get(Site.ANILIST)
        if cached_anilist:
            return cached_anilist, str(cached_anilist['id'])

        anilist_id = cached_ids.get(Site.ANILIST) if cached_ids else None

        if anilist_id:
            resp = await ani_list.get_entry_by_id(
                self.session_manager, medium, anilist_id, timeout
            )
        else:
            resp = await ani_list.get_entry_details(
                self.session_manager, medium, query, timeout
            )

        id_ = str(resp['id']) if resp else None
        try:
            return resp, id_
        finally:
            if resp and id_:
                await self.db_controller.set_medium_data(
                    id_, medium, Site.ANILIST, resp
                )

    async def __find_mal(self, cached_data, cached_ids,
                         medium, query, timeout):
        """
        Find MAL data.

        Return the cached data if it exists.

        If there are no cached data, attempt make an api call to MAL and
        find the data. Return and cache the api call result if it's found,
        else return None.

        :param cached_data: a dict of cached data.

        :param cached_ids: a dict of cached ids.

        :param medium: the medium type.

        :param query: the search query.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: the MAL data and id in a tuple  if found.
        """
        if medium not in (Medium.ANIME, Medium.MANGA, Medium.LN):
            return None, None
        cached_mal = cached_data.get(Site.MAL)
        if cached_mal:
            return cached_mal, str(cached_mal['id'])
        mal_id = cached_ids.get(Site.MAL) if cached_ids else None
        if mal_id:
            cached_title = await self.db_controller.get_mal_title(
                mal_id, medium)
            if cached_title:
                query = cached_title

        resp = await mal.get_entry_details(
            self.session_manager, self.mal_headers, medium, query, mal_id,
            timeout
        )

        id_ = str(resp['id']) if resp else None
        try:
            return resp, id_
        finally:
            if resp and id_:
                await self.db_controller.set_mal_title(
                    id_, medium, resp['title']
                )
                await self.db_controller.set_medium_data(
                    id_, medium, Site.MAL, resp
                )

    async def __find_anidb(self, cached_ids, medium, query):
        """
        Find Anidb url.

        Return the cached url if it's found.

        If no cached url is found, try search through the datadump,
        return and cache the url if it's found.

        :param cached_ids: a dict of cached ids.

        :param query: the search query.

        :return: The data and id in a tuple if found.
        """
        if medium != Medium.ANIME:
            return None, None
        cached_id = cached_ids.get(Site.ANIDB) if cached_ids else None
        base_url = 'https://anidb.net/perl-bin/animedb.pl?show=anime&aid='
        if cached_id:
            return {'url': f'{base_url}{cached_id}'}, cached_id
        await self.__fetch_anidb()
        res = await self.loop.run_in_executor(
            None, ani_db.get_anime, query, self.__anidb_list
        )
        if not res:
            return None, None
        id_ = res['id']
        res['url'] = f'{base_url}{id_}'
        return res, id_

    async def __find_ani_planet(self, cached_ids, medium: Medium,
                                query: str, names: list, timeout):
        """
        Find a anime or manga url from ani planet.

        :param medium: the medium type.

        :param query: the search query.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: the ani planet data and id in a tuple  if found.
        """
        ap_id = cached_ids.get(Site.ANIMEPLANET) if cached_ids else None

        if medium == Medium.ANIME:
            if ap_id:
                return {'url': anime_planet.get_anime_url_by_id(
                    cached_ids.get(Site.ANIMEPLANET))}, None
            else:
                return {'url': await anime_planet.get_anime_url(
                    self.session_manager, query, names, timeout=timeout
                )}, None

        if medium == Medium.MANGA:
            if ap_id:
                return {'url': anime_planet.get_manga_url_by_id(
                    cached_ids.get(Site.ANIMEPLANET))}, None
            else:
                return {'url': await anime_planet.get_manga_url(
                    self.session_manager, query, names, timeout=timeout
                )}, None

        return None, None

    async def __find_kitsu(self, cached_ids, medium, query, timeout):
        """
        Find a anime or manga url from ani planet.

        :param medium: the medium type.

        :param query: the search query.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: the ani planet data and id in a tuple  if found.
        """
        if medium not in (Medium.ANIME, Medium.MANGA, Medium.LN):
            return None, None
        kitsu_id = cached_ids.get(Site.KITSU) if cached_ids else None
        if kitsu_id:
            resp = await self.kitsu.get_entry_by_id(
                medium, kitsu_id, timeout
            )
        else:
            resp = await self.kitsu.search_entries(
                medium, query, timeout
            )
        id_ = str(resp['id']) if resp else None
        return resp, id_

    async def __find_manga_updates(self, cached_ids, medium,
                                   query, names, timeout):
        """
        Find a manga updates url.

        :param medium: the medium type.

        :param query: the search query.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: the data and id in a tuple if found.
        """
        mu_id = cached_ids.get(Site.MANGAUPDATES) if cached_ids else None
        if medium == Medium.MANGA:
            if mu_id:
                return {'url': mu.get_manga_url_by_id(
                    mu_id
                )}, None
            else:
                return {'url': await mu.get_manga_url(
                    self.session_manager, query, names, timeout
                )}, None

        return None, None

    async def __find_lndb(self, cached_ids, medium, query, names, timeout):
        """
        Find an lndb url.

        :param medium: the medium type.

        :param query: the search query.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: the lndb data and id in a tuple if found.
        """
        lndb_id = cached_ids.get(Site.LNDB) if cached_ids else None
        if medium == Medium.LN:
            if lndb_id:
                return {'url': lndb.get_light_novel_by_id(
                    lndb_id
                )}, None
            else:
                return {'url': await lndb.get_light_novel_url(
                    self.session_manager, query, names, timeout)}, None
        return None, None

    async def __find_novel_updates(self, cached_ids, medium,
                                   query, names, timeout):
        """
        Find a Novel Updates url.

        :param medium: the medium type.

        :param query: the search query.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: the data and id in a tuple if found.
        """
        nu_id = cached_ids.get(Site.NOVELUPDATES) if cached_ids else None
        if medium == Medium.LN:
            if nu_id:
                return {'url': nu.get_light_novel_by_id(
                    nu_id
                )}, None
            return {'url': await nu.get_light_novel_url(
                self.session_manager, query, names, timeout
            )}, None

        return None, None

    async def __find_vndb(self, medium, query):
        pass

    async def __get_cached(self, query: str, medium: Medium) -> tuple:
        """
        Get cached data from the database.

        :param query: the search query.

        :param medium: the medium type.

        :return: a tuple of (cached data, cached ids)
        """
        identifiers = await self.db_controller.get_identifier(query, medium)
        if not identifiers:
            return {}, None
        entry_resp = {}
        for site, id_ in identifiers.items():
            medium_data = await self.db_controller.medium_data_by_id(
                id_, medium, site)
            if medium_data:
                entry_resp[site] = medium_data

        return entry_resp, identifiers

    async def __get_result(self, cached_data, cached_id, query, names,
                           site: Site, medium: Medium, timeout) -> tuple:
        """
        Get results from a site.

        :param cached_data: the cached data.

        :param cached_id: the cached id.

        :param site: the site.

        :param query: the search query.

        :param medium: the medium type.

        :param timeout:
            The timeout in seconds for each HTTP request. Defualt is 3.

        :return: Search results data and id in a tuple for that site.
        """
        try:
            if site == Site.ANILIST:
                return await self.__find_anilist(
                    cached_data, cached_id, medium, query, timeout
                )

            if site == Site.KITSU:
                return await self.__find_kitsu(
                    cached_id, medium, query, timeout
                )

            if site == site.MAL:
                return await self.__find_mal(
                    cached_data, cached_id, medium, query, timeout
                )

            if site == Site.ANIDB:
                return await self.__find_anidb(cached_id, medium, query)

            if site == Site.ANIMEPLANET:
                return await self.__find_ani_planet(
                    cached_id, medium, query, names, timeout
                )

            if site == Site.MANGAUPDATES:
                return await self.__find_manga_updates(
                    cached_id, medium, query, names, timeout
                )

            if site == Site.LNDB:
                return await self.__find_lndb(
                    cached_id, medium, query, names, timeout
                )

            if site == Site.NOVELUPDATES:
                return await self.__find_novel_updates(
                    cached_id, medium, query, names, timeout
                )

            if site == Site.VNDB:
                return None, None
        except Exception as e:
            self.logger.warning(
                f'Error raised when retriving data from {site}: {e}\n'
                f'{format_exc()}'
            )
            return None, None
