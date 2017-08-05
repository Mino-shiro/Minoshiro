from asyncio import get_event_loop
from base64 import b64encode
from time import time
from typing import Any, Dict

from aiohttp import ClientSession

from roboragi.data import data_path
from roboragi.data_controller import DataController, PostgresController
from roboragi.data_controller.enums import Medium, Site
from roboragi.session_manager import SessionManager
from roboragi.utils.helpers import get_synonyms
from roboragi.web_api import ani_db, ani_list, anime_planet, lndb, mal, mu, nu
from .logger import get_default_logger
from .utils.pre_cache import cache_top_40, cache_top_pages


class Roboragi:
    def __init__(self, session_manager: SessionManager,
                 db_controller: DataController, mal_config: dict,
                 anilist_config: dict, *, logger=None, loop=None):
        """
        It is suggested to use one of the class methods to create the instance
        if you wish to use one of the data controllers provided by the library.

        Make sure you run the `pre_cache` method if you initializeed the class
        directly from the `__init__` method.

        :param session_manager:
            The `SessionManager` instance.
            See class `roboragi.session_manager.SessionManager` for details.

        :param db_controller:
            Any sub class of `roboragi.data_controller.abc.DataController`
            will work here.

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

        :param logger:
            The logger object. If it's not provided, will use the
            defualt logger provided by the library.

        :param loop:
            An asyncio event loop. If not provided will use the default
            event loop.
        """
        mal_user, mal_pass = mal_config.get('user'), mal_config.get('password')
        assert mal_user and mal_pass, ('Please provide MAL user'
                                       'name and password.')

        anilist_id = anilist_config.get('id')
        anilist_pass = anilist_config.get('secret')
        assert anilist_id and anilist_pass, ('Please provide Anilist client'
                                             'id and client secret.')

        self.session_manager = session_manager
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

        self.loop = loop or get_event_loop()
        self.logger = logger or get_default_logger()

        self.__anidb_list = None
        self.__anidb_time = None

    @classmethod
    async def from_postgres(cls, db_config: dict, mal_config: dict,
                            anilist_config: dict, *,
                            cache_pages: int = 0, logger=None, loop=None):
        """
        Get an instance of `Roboragi` with class `PostgresController` as the
        database controller.

        :param db_config:
            A dict of database config for the connection.

            It should contain the keys in  keyword arguments for the :func:
            `asyncpg.connection.connect` function.

            It may contain an extra key "schema" for the name of the databse
            schema.
            If this key is not present, the schema defaults to "roboragi"

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
                "id" for client id and "secret" for client secret.

        :param cache_pages:
            The number of pages of anime and manga from Anilist to cache
            before the instance is created. Each page contains 40 entries max.

        :param logger:
            The logger object. If it's not provided, will use the
            defualt logger provided by the library.

        :param loop:
            An asyncio event loop. If not provided will use the default
            event loop.

        :return: Instance of `Roboragi` with class `PostgresController` as the
                 database controller.
        """
        assert cache_pages >= 0, 'Param `cache_pages` must not be negative.'
        db_config = dict(db_config)
        logger = logger or get_default_logger()
        schema = db_config.pop('schema', 'roboragi')
        db_controller = await PostgresController.get_instance(
            logger, db_config, schema=schema
        )

        session_manager = SessionManager(ClientSession(), logger)
        instance = cls(session_manager, db_controller, mal_config,
                       anilist_config, logger=logger, loop=loop)
        await instance.pre_cache(cache_pages)
        return instance

    async def pre_cache(self, cache_pages: int):
        """
        Pre cache the data base with some anime and managa data.

        :param cache_pages: the number of pages to cache.
        """
        self.logger.info('Populating lookup...')
        await self.db_controller.pre_cache()
        self.logger.info('Lookup populated.')

        self.logger.info('Populating data...')
        for med in (Medium.ANIME, Medium.MANGA):
            await cache_top_40(
                med, self.session_manager, self.db_controller,
                self.anilist, self.mal_headers
            )
            if cache_pages:
                await cache_top_pages(
                    med, self.session_manager, self.db_controller,
                    self.anilist, self.mal_headers, cache_pages
                )
        self.logger.info('Data populated.')

    async def find_anime(self, query: str) -> dict:
        """
        Searches all of the databases and returns the info.

        :param query: the search term.

        :return: dict with anime info.
        """
        return await self.__get_results(query, Medium.ANIME)

    async def find_manga(self, query: str) -> dict:
        """
        Searches all of the databases and returns the info
        :param query: the search term.
        :return: dict with manga info.
        """
        return await self.__get_results(query, Medium.MANGA)

    async def find_novel(self, query: str) -> dict:
        """
        Searches all of the databases and returns the info
        :param query: the search term.
        :return: dict with novel info.
        """
        return await self.__get_results(query, Medium.LN)

    async def __fetch_anidb(self):
        """
        Fetch data dump from anidb if one of the following is True:
            The data dump file is not found.
            The data dump file is more than a day old.
        """
        now = int(time())
        if self.__anidb_list and now - self.__anidb_time < 86400:
            return

        time_path = data_path.joinpath('.anidb_time')
        dump_path = data_path.joinpath('anime-titles.xml')

        if time_path.is_file():
            with time_path.open() as tf:
                self.__anidb_time = int(tf.read())
        else:
            with time_path.open('w+') as tfw:
                tfw.write(str(now))
            self.__anidb_time = now
        if (not data_path.is_file()) or ((now - self.__anidb_time) >= 86400):
            async with await self.session_manager.get(
                    'http://anidb.net/api/anime-titles.xml.gz'
            ) as resp:
                with dump_path.open('wb') as f:
                    f.write(await resp.read())
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

        :return: the anilist data if found.
        """
        if medium not in (Medium.ANIME, Medium.MANGA, Medium.LN):
            return
        cached_anilist = cached_data.get(Site.ANILIST)
        if cached_anilist:
            return cached_anilist

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
            self.logger.warning(str(e))
            resp = None

        try:
            return resp
        finally:
            if resp:
                id_ = str(resp['id'])
                for syn in get_synonyms(resp, Site.ANILIST):
                    await self.db_controller.set_identifier(
                        syn, medium, Site.ANILIST, id_
                    )
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

        :return: the MAL data if found.
        """
        if medium not in (Medium.ANIME, Medium.MANGA, Medium.LN):
            return
        cached_mal = cached_data.get(Site.MAL)
        if cached_mal:
            return cached_mal
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
            self.logger.warning(str(e))
            resp = None

        try:
            return resp
        finally:
            if resp:
                id_ = str(resp['id'])
                await self.db_controller.set_mal_title(
                    id_, medium, resp['title']
                )
                for syn in get_synonyms(resp, Site.MAL):
                    await self.db_controller.set_identifier(
                        syn, medium, Site.MAL, id_
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

        :return: The url if found.
        """
        if medium != Medium.ANIME:
            return
        cached_id = cached_ids.get(Site.ANIDB) if cached_ids else None
        base_url = 'https://anidb.net/perl-bin/animedb.pl?show=anime&aid='
        if cached_id:
            return f'{base_url}/{cached_id}'
        await self.__fetch_anidb()
        res = await self.loop.run_in_executor(
            None, ani_db.get_anime, query, self.__anidb_list
        )

        if res:
            id_ = res['id']
            try:
                return f'{base_url}/{id_}'
            finally:
                for title in res['titles']:
                    await self.db_controller.set_identifier(
                        title, Medium.ANIME, Site.ANIDB, id_
                    )

    async def __find_ani_planet(self, medium: Medium, query: str):
        """
        Find a anime or manga url from ani planet.

        :param medium: the medium type.

        :param query: the search query.

        :return: the ani planet url if found.
        """
        try:
            if medium == Medium.ANIME:
                return await anime_planet.get_anime_url(
                    self.session_manager, query
                )

            if medium == Medium.MANGA:
                return await anime_planet.get_manga_url(
                    self.session_manager, query
                )
        except Exception as e:
            self.logger.warning(str(e))

    async def __find_kitsu(self, medium: Medium, query: str):
        pass

    async def __find_manga_updates(self, medium, query):
        """
        Find a manga updates url.

        :param medium: the medium type.

        :param query: the search query.

        :return: the url if found.
        """
        if medium == Medium.MANGA:
            try:
                return await mu.get_manga_url(
                    self.session_manager, query
                )
            except Exception as e:
                self.logger.warning(str(e))

    async def __find_lndb(self, medium, query):
        """
        Find an lndb url.

        :param medium: the medium type.

        :param query: the search query.

        :return: the lndb url if found.
        """
        if medium == Medium.LN:
            try:
                return await lndb.get_light_novel_url(
                    self.session_manager, query
                )
            except Exception as e:
                self.logger.warning(str(e))

    async def __find_novel_updates(self, medium, query):
        """
        Find a Novel Updates url.

        :param medium: the medium type.

        :param query: the search query.

        :return: the url if found.
        """
        if medium == Medium.LN:
            try:
                return await nu.get_light_novel_url(
                    self.session_manager, query
                )
            except Exception as e:
                self.logger.warning(str(e))

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

    async def __get_results(self, query, medium: Medium) -> Dict[Site, Any]:
        """
        Get results from all sites.

        :param query: the search query.

        :param medium: the medium type.

        :return: Search results from all sites if found.
        """
        res = {}
        cached_data, cached_id = await self.__get_cached(query, medium)

        res[Site.ANILIST] = await self.__find_anilist(
            cached_data, cached_id, medium, query
        )

        res[Site.MAL] = await self.__find_mal(
            cached_data, cached_id, medium, query
        )

        res[Site.ANIDB] = await self.__find_anidb(cached_id, medium, query)

        res[Site.ANIMEPLANET] = await self.__find_ani_planet(medium, query)

        res[Site.KITSU] = None

        res[Site.MANGAUPDATES] = await self.__find_manga_updates(medium, query)

        res[Site.LNDB] = await self.__find_lndb(medium, query)

        res[Site.NOVELUPDATES] = await self.__find_novel_updates(medium, query)

        res[Site.VNDB] = None

        return {k: v for k, v in res.items() if v}
