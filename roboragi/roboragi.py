from ast import literal_eval
from asyncio import get_event_loop
from base64 import b64encode
from itertools import chain
from pathlib import Path
from time import time
from typing import Dict, Iterable, Union

from roboragi.data import data_path
from roboragi.data_controller import DataController, PostgresController, \
    SqliteController
from roboragi.data_controller.data_utils import get_all_synonyms
from roboragi.data_controller.enums import Medium, Site
from roboragi.session_manager import SessionManager
from roboragi.utils.helpers import get_synonyms
from roboragi.utils.pre_cache import cache_top_pages
from roboragi.web_api import ani_db, ani_list, anime_planet, kitsu, lndb, mal, \
    mu, nu
from .logger import get_default_logger


class Roboragi:
    def __init__(self, db_controller: DataController, mal_config: dict,
                 anilist_config: dict, *, logger=None, loop=None):
        """
        Represents the search instance.

        It is suggested to use one of the class methods to create the instance
        if you wish to use one of the data controllers provided by the library.

        Make sure you run the ``pre_cache`` method if you initialized the class
        directly from the ``__init__`` method.

        :param db_controller:
            Any sub class of ``roboragi.data_controller.abc.DataController``
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

        :param anilist_config:
            A dict for Anilist authorization.
            It must contain the keys:
                ``id``: Your Anilist client id
                ``secret``: Your Anilist client secret.

        :param logger:
            The logger object. If it's not provided, will use the
            defualt logger provided by the library.

        :param loop:
            An asyncio event loop. If not provided will use the default
            event loop.
        """
        self.session_manager = SessionManager(logger)
        mal_user, mal_pass = mal_config.get('user'), mal_config.get('password')
        assert mal_user and mal_pass, ('Please provide MAL user'
                                       'name and password.')

        anilist_id = anilist_config.get('id')
        anilist_pass = anilist_config.get('secret')
        assert anilist_id and anilist_pass, ('Please provide Anilist client'
                                             'id and client secret.')

        self.db_controller = db_controller

        mal_agent = mal_config.get(
            'description', 'A Python library for anime search.'
        )
        mal_auth = b64encode(f'{mal_user}:{mal_pass}'.encode()).decode()

        self.mal_headers = {
            'Authorization': f'Basic {mal_auth}',
            'User-Agent': mal_agent
        }

        self.anilist = ani_list.AniList(
            self.session_manager, anilist_id, anilist_pass
        )

        self.kitsu = kitsu.Kitsu(
            self.session_manager, '', ''
        )

        self.loop = loop or get_event_loop()
        self.logger = logger or get_default_logger()

        synonyms = get_all_synonyms()
        self.anime_synonyms = {}
        self.manga_synonyms = {}
        self.novel_synonyms = {}
        for name, type_, db_links in synonyms:
            if type_.lower() == 'anime':
                self.anime_synonyms[name.lower()] = db_links
            elif type_.lower() == 'manga':
                self.manga_synonyms[name.lower()] = db_links
            elif type_.lower() == 'ln':
                self.novel_synonyms[name.lower()] = db_links

        self.__anidb_list = None
        self.__anidb_time = None

    @classmethod
    async def from_postgres(cls, mal_config: dict, anilist_config: dict,
                            db_config: dict = None, pool=None, *,
                            schema='roboragi', cache_pages: int = 0,
                            cache_mal_entries: int = 0, logger=None, loop=None):
        """
        Get an instance of `Roboragi` with class `PostgresController` as the
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

        :param anilist_config:
            A dict for Anilist authorization. It must contain the keys:
                id: Your Anilist client id
                secret: Your Anilist client secret.

        :param db_config:
            A dict of database config for the connection.

            It should contain the keys in  keyword arguments for the :func:
            `asyncpg.connection.connect` function.

        :param pool: an existing connection pool.

        One of ``db_config`` or ``pool`` must not be None.

        :param schema: the schema name used. Defaults to `roboragi`

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
            Instance of `Roboragi` with class `PostgresController`
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
        instance = cls(db_controller, mal_config, anilist_config,
                       logger=logger, loop=loop)
        await instance.pre_cache(cache_pages, cache_mal_entries)
        return instance

    @classmethod
    async def from_sqlite(cls, mal_config: dict, anilist_config: dict,
                          path: Union[str, Path], *,
                          cache_pages: int = 0, cache_mal_entries: int = 0,
                          logger=None, loop=None):
        """
        Get an instance of `Roboragi` with class `SqliteController` as the
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

        :param anilist_config:
            A dict for Anilist authorization. It must contain the keys:
                id: Your Anilist client id
                secret: Your Anilist client secret.

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
            Instance of `Roboragi` with class `PostgresController`
            as the database controller.
        """
        logger = logger or get_default_logger()
        db_controller = await SqliteController.get_instance(path, logger, loop)
        instance = cls(db_controller, mal_config, anilist_config,
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
        await self.db_controller.pre_cache()
        self.logger.info('Lookup populated.')

        self.logger.info('Populating data...')

        for med in (Medium.ANIME, Medium.MANGA):
            if cache_pages:
                await cache_top_pages(
                    med, self.session_manager, self.db_controller,
                    self.anilist, self.mal_headers, cache_pages,
                    cache_mal_entries
                )

        self.logger.info('Data populated.')
        self.logger.info('Fetching anidb datadump...')
        await self.__fetch_anidb()
        self.logger.info('Anidb datadump fetched.')

    async def yield_data(self, query: str, medium: Medium,
                         sites: Iterable[Site] = None):
        """
        Yield the data for the search query from all sites.

        :param query: the search query.

        :param medium: the medium type.

        :param sites:
            an iterable of sites desired. If None is provided, will
            search all sites by default.

        :return:
            an asynchronous generator that yields the site and data
            in a tuple for all sites requested.
        """
        cached_id = {}
        if medium == Medium.ANIME:
            synonym_data = self.anime_synonyms.get(query.lower())
        elif medium == Medium.MANGA:
            synonym_data = self.manga_synonyms.get(query.lower())
        elif medium == Medium.LN:
            synonym_data = self.novel_synonyms.get(query.lower())
        sites = sites if sites else list(Site)
        cached_data, cached_id = await self.__get_cached(query, medium)
        to_be_cached = {}
        names = []
        for site in sites:
            if synonym_data:
                cached_id = {site: str(
                    self.__get_synonym_data(synonym_data, site))}
            res, id_ = await self.__get_result(
                cached_data, cached_id, query, names, site, medium
            )
            if res:
                yield site, res
                for title in get_synonyms(res, site):
                    names.append(title)
            if id_:
                to_be_cached[site] = id_
        await self.__cache(to_be_cached, names, medium)

    async def get_data(self, query: str, medium: Medium,
                       sites: Iterable[Site] = None) -> Dict[Site, dict]:
        """
        Get the data for the search query in a dict.

        :param query: the search query.

        :param medium: the medium type.

        :param sites:
            an iterable of sites desired. If None is provided, will
            search all sites by default.

        :return: Data for all sites in a dict {Site: data}
        """
        return {site: val async for site, val in self.yield_data(
            query, medium, sites
        )}

    def __get_synonym_data(
            self, synonym_data: dict, site: Site) -> dict:
        synonym_data = literal_eval(synonym_data)
        keys = synonym_data.keys()
        syn_ids = {}
        if site == Site.MAL and 'mal' in keys:
            syn_ids = str(synonym_data['mal'][1])
        elif site == Site.ANILIST and 'ani' in keys:
            syn_ids = synonym_data['ani']
        elif site == Site.ANIMEPLANET and 'ap' in keys:
            syn_ids = synonym_data['ap']
        elif site == Site.ANIDB and 'adb' in keys:
            syn_ids = synonym_data['adb']
        elif site == Site.KITSU and 'kit' in keys:
            syn_ids = synonym_data['kit']
        elif site == Site.MANGAUPDATES and 'mu' in keys:
            syn_ids = synonym_data['mu']
        elif site == Site.LNDB and 'lndb' in keys:
            syn_ids = synonym_data['lndb']
        elif site == Site.NOVELUPDATES and 'nu' in keys:
            syn_ids = synonym_data['nu']
        elif site == Site.VNDB and 'vndb' in keys:
            pass
        return syn_ids

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
            if not name:
                continue
            await self.db_controller.set_identifier(
                name, medium, site, id_
            )

    async def __fetch_anidb(self):
        """
        Fetch data dump from anidb if one of the following is True:
            The data dump file is not found.
            The data dump file is more than a day old.
        """
        now = int(time())

        def __write_time(p):
            with p.open('w+') as tfw:
                tfw.write(str(now))
            self.__anidb_time = now

        if self.__anidb_list and now - self.__anidb_time < 86400:
            return

        time_path = data_path.joinpath('.anidb_time')
        dump_path = data_path.joinpath('anime-titles.xml')

        if time_path.is_file():
            with time_path.open() as tf:
                self.__anidb_time = int(tf.read())
        else:
            __write_time(time_path)

        if not dump_path.is_file() or now - self.__anidb_time >= 86400:
            async with await self.session_manager.get(
                    'http://anidb.net/api/anime-titles.xml.gz'
            ) as resp:
                with dump_path.open('wb') as f:
                    f.write(await resp.read())
                __write_time(time_path)

        with dump_path.open() as xml_file:
            xml = xml_file.read()

        self.__anidb_list = ani_db.process_xml(xml)

    async def __find_anilist(self, cached_data, cached_ids, medium, query):
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

        :return: the anilist data and id in a tuple if found.
        """
        if medium not in (Medium.ANIME, Medium.MANGA, Medium.LN):
            return None, None
        cached_anilist = cached_data.get(Site.ANILIST)
        if cached_anilist:
            return cached_anilist, str(cached_anilist['id'])

        anilist_id = cached_ids.get(Site.ANILIST) if cached_ids else None

        try:
            if anilist_id:
                resp = await self.anilist.get_entry_by_id(
                    self.session_manager, medium, anilist_id
                )
            else:
                resp = await self.anilist.get_entry_details(
                    self.session_manager, medium, query
                )
        except Exception as e:
            self.logger.warning(f'Error raised by Anilist: {e}')
            resp = None

        id_ = str(resp['id']) if resp else None
        try:
            return resp, id_
        finally:
            if resp and id_:
                await self.db_controller.set_medium_data(
                    id_, medium, Site.ANILIST, resp
                )

    async def __find_mal(self, cached_data, cached_ids, medium, query):
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
        try:
            resp = await mal.get_entry_details(
                self.session_manager, self.mal_headers, medium, query, mal_id
            )
        except Exception as e:
            self.logger.warning(f'Error raised by MAL: {e}')
            resp = None

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

    async def __find_ani_planet(
            self, cached_ids, medium: Medium, query: str, names: list):
        """
        Find a anime or manga url from ani planet.

        :param medium: the medium type.

        :param query: the search query.

        :return: the ani planet data and id in a tuple  if found.
        """
        ap_id = cached_ids.get(Site.ANIMEPLANET) if cached_ids else None
        try:
            if medium == Medium.ANIME:
                if ap_id:
                    return {'url': anime_planet.get_anime_url_by_id(
                        cached_ids.get(Site.ANIMEPLANET))}, None
                else:
                    return {'url': await anime_planet.get_anime_url(
                        self.session_manager, query, names
                    )}, None

            if medium == Medium.MANGA:
                if ap_id:
                    return {'url': anime_planet.get_manga_url_by_id(
                        cached_ids.get(Site.ANIMEPLANET))}, None
                else:
                    return {'url': await anime_planet.get_manga_url(
                        self.session_manager, query, names
                    )}, None
        except Exception as e:
            self.logger.warning(f'Error raised by Ani-planet: {e}')
        return None, None

    async def __find_kitsu(self, cached_data, cached_ids, medium, query):
        """
        Find a anime or manga url from ani planet.

        :param medium: the medium type.

        :param query: the search query.

        :return: the ani planet data and id in a tuple  if found.
        """
        if medium not in (Medium.ANIME, Medium.MANGA, Medium.LN):
            return None, None
        kitsu_id = cached_ids.get(Site.KITSU) if cached_ids else None
        try:
            if kitsu_id:
                resp = await self.kitsu.get_entry_by_id(
                    medium, kitsu_id
                )
            else:
                resp = await self.kitsu.search_entries(
                    medium, query
                )
        except Exception as e:
            self.logger.warning(f'Error raised by Kitsu: {e}')
            resp = None
        id_ = str(resp['id']) if resp else None
        try:
            return resp, id_
        finally:
            if resp and id_:
                pass

    async def __find_manga_updates(self, cached_ids, medium, query, names):
        """
        Find a manga updates url.

        :param medium: the medium type.

        :param query: the search query.

        :return: the data and id in a tuple if found.
        """
        mu_id = cached_ids.get(Site.MANGAUPDATES) if cached_ids else None
        if medium == Medium.MANGA:
            try:
                if mu_id:
                    return {'url': mu.get_manga_url_by_id(
                        mu_id
                    )}, None
                else:
                    return {'url': await mu.get_manga_url(
                        self.session_manager, query, names
                    )}, None
            except Exception as e:
                self.logger.warning(f'Error raised by Manga Updates: {e}')
        return None, None

    async def __find_lndb(self, cached_ids, medium, query, names):
        """
        Find an lndb url.

        :param medium: the medium type.

        :param query: the search query.

        :return: the lndb data and id in a tuple if found.
        """
        lndb_id = cached_ids.get(Site.LNDB) if cached_ids else None
        if medium == Medium.LN:
            try:
                if lndb_id:
                    return {'url': lndb.get_light_novel_by_id(
                        lndb_id
                    )}, None
                else:
                    return {'url': await lndb.get_light_novel_url(
                        self.session_manager, query, names
                    )}, None
            except Exception as e:
                self.logger.warning(f'Error raised by LNDB: {e}')
        return None, None

    async def __find_novel_updates(self, cached_ids, medium, query, names):
        """
        Find a Novel Updates url.

        :param medium: the medium type.

        :param query: the search query.

        :return: the data and id in a tuple if found.
        """
        nu_id = cached_ids.get(Site.NOVELUPDATES) if cached_ids else None
        if medium == Medium.LN:
            try:
                if nu_id:
                    return {'url': nu.get_light_novel_by_id(
                        nu_id
                    )}, None
                return {'url': await nu.get_light_novel_url(
                    self.session_manager, query, names
                )}, None
            except Exception as e:
                self.logger.warning(f'Error raised by Novel Updates: {e}')
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
                           site: Site, medium: Medium) -> tuple:
        """
        Get results from a site.

        :param cached_data: the cached data.

        :param cached_id: the cached id.

        :param site: the site.

        :param query: the search query.

        :param medium: the medium type.

        :return: Search results data and id in a tuple for that site.
        """
        if site == Site.ANILIST:
            return await self.__find_anilist(
                cached_data, cached_id, medium, query
            )

        if site == Site.KITSU:
            return await self.__find_kitsu(
                cached_data, cached_id, medium, query
            )

        if site == site.MAL:
            return await self.__find_mal(cached_data, cached_id, medium, query)

        if site == Site.ANIDB:
            return await self.__find_anidb(cached_id, medium, query)

        if site == Site.ANIMEPLANET:
            return await self.__find_ani_planet(
                cached_id, medium, query, names
            )

        if site == Site.MANGAUPDATES:
            return await self.__find_manga_updates(
                cached_id, medium, query, names
            )

        if site == Site.LNDB:
            return await self.__find_lndb(cached_id, medium, query, names)

        if site == Site.NOVELUPDATES:
            return await self.__find_novel_updates(
                cached_id, medium, query, names
            )

        if site == Site.VNDB:
            return None, None
