from base64 import b64encode
from time import time
from typing import Optional

from aiohttp import ClientSession

from roboragi.data import data_path
from roboragi.data_controller import DataController, PostgresController
from roboragi.data_controller.enums import Medium, Site
from roboragi.session_manager import SessionManager
from roboragi.web_api import ani_db, ani_list, anime_planet, lndb, mal, mu, nu
from .logger import get_default_logger
from .utils.pre_cache import cache_top_40, cache_top_pages


class Roboragi:
    def __init__(self, session_manager: SessionManager,
                 db_controller: DataController, mal_config: dict,
                 anilist_config: dict, logger=None):
        """

        :param session_manager:
        :param db_controller:
        :param mal_config:
        :param anilist_config:
        :param logger:
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
        mal_auth = b64encode(f'{mal_user}:{mal_pass}')

        self.mal_headers = {
            'Authorization': f'Basic {mal_auth}',
            'User-Agent': mal_agent
        }

        self.anilist = ani_list.AniList(
            self.session_manager, anilist_id, anilist_pass
        )

        self.logger = logger or get_default_logger()

        self.__anidb_list = None
        self.__anidb_time = None

    async def fetch_anidb(self):
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

        if now - self.__anidb_time < 86400 and dump_path.is_file():
            with dump_path.open() as xml_file:
                xml = xml_file.read()
        else:
            url = 'http://anidb.net/api/anime-titles.xml.gz'
            async with await self.session_manager.get(url) as resp:
                xml = await resp.read()
            with dump_path.open('w+') as write_xml:
                write_xml.write(xml)
        self.__anidb_list = ani_db.process_xml(xml)

    @classmethod
    async def from_postgres(cls, db_config: dict, mal_config: dict,
                            anilist_config: dict, logger=None,
                            cache_pages: int = 0):
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
            It must contain the keys "user" and "password"

            It may also contain a key "description" for the description you
            wish to use in the auth header.

            If this key is not present, the description defaults to:
                "A Python library for anime search."

        :param anilist_config:
            A dict for Anilist authorization. It must contain the keys:
                "id" for client id and "secret" for client secret.

        :param logger:
            The logger object. If it's not provided, will use the
            defualt logger provided by the library.

        :param cache_pages:
            The number of pages of anime and manga from Anilist to cache
            before the instance is created. Each page contains 40 entries max.

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
        instance = cls(session_manager, db_controller,
                       mal_config, anilist_config, logger)
        await instance.__pre_cache(cache_pages)
        return instance

    async def __pre_cache(self, cache_pages: int):
        """
        Pre cache the data base with some anime and managa data.

        :param cache_pages: the number of pages to cache.
        """
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

    async def __cache_entry(self, entry_resp: dict, medium: Medium):
        """
        Adds entry to cache

        :param entry_resp: dict of all entries to be added

        :param medium: Medium type of entries
        """
        for entry in entry_resp:
            pass

    async def find_anime(self, anime_title) -> dict:
        """
        Searches all of the databases and returns the info
        :param query: the search term.
        :return: dict with anime info.
        """
        await self.fetch_anidb()
        try:
            cached_anime = await self.get_cached(anime_title, Medium.ANIME)
            if cached_anime is not None:
                return cached_anime
            entry_resp = {}
            entry_resp['anilist'] = await self.anilist_client.get_entry_details(
                self.session,
                Medium.ANIME,
                anime_title) if self.anilist_client else None
            entry_resp['mal'] = await mal.get_entry_details(
                self.session,
                self.mal_headers,
                Medium.ANIME,
                anime_title) if self.mal_headers else None
            entry_resp['anidb'] = await ani_db.get_anime_url(
                self.session, anime_title)
            entry_resp['animeplanet'] = await anime_planet.get_anime_url(
                self.session, anime_title)
            self.__cache_entry(entry_resp, Medium.ANIME)
            return entry_resp
        except Exception as e:
            self.logger.error(str(e))
            raise e

    async def find_manga(self, manga_title) -> dict:
        """
        Searches all of the databases and returns the info
        :param query: the search term.
        :return: dict with manga info.
        """
        try:
            cached_manga = await self.get_cached(manga_title, Medium.MANGA)
            if cached_manga is not None:
                return cached_manga
            entry_resp = {}
            entry_resp['anilist'] = await self.anilist_client.get_entry_details(
                self.session,
                Medium.MANGA,
                manga_title) if self.anilist_client else None
            entry_resp['mal'] = await mal.get_entry_details(
                self.session,
                self.mal_headers,
                Medium.MANGA,
                manga_title) if self.mal_headers else None
            entry_resp['animeplanet'] = await anime_planet.get_manga_url(
                self.session,
                manga_title)
            entry_resp['mangaupdates'] = await mu.get_manga_url(
                self.session,
                manga_title)
            self.__cache_entry(entry_resp, Medium.MANGA)
            return entry_resp
        except Exception as e:
            self.logger.error(str(e))
            raise e

    async def find_novel(self, novel_title) -> dict:
        """
        Searches all of the databases and returns the info
        :param query: the search term.
        :return: dict with novel info.
        """
        try:
            cached_novel = await self.get_cached(novel_title, Medium.LN)
            if cached_novel is not None:
                return cached_novel
            entry_resp = {}
            entry_resp['anilist'] = await self.anilist_client.get_entry_details(
                self.session,
                Medium.LN,
                novel_title) if self.anilist_client else None
            entry_resp['mal'] = await mal.get_entry_details(
                self.session,
                self.mal_headers,
                Medium.LN,
                novel_title) if self.mal_headers else None
            entry_resp['lndb'] = lndb.get_light_novel_url(
                self.session,
                novel_title)
            entry_resp['novelupdates'] = await nu.get_light_novel_url(
                self.session,
                novel_title)
            self.__cache_entry(entry_resp, Medium.LN)
            return entry_resp
        except Exception as e:
            self.logger.error(str(e))
            raise e

    async def get_cached(self, title: str, medium: Medium) -> Optional[dict]:
        entry_resp = {}
        identifiers = await self.db_controller.get_identifier(title, medium)
        if identifiers is not None:
            for site in identifiers.keys():
                medium_data = await self.db_controller.medium_data_by_id(
                    identifiers[site.name], Medium, site)
                if medium_data is not None:
                    entry_resp[site.name] = medium_data
                else:
                    if site == Site.MAL:
                        title = self.db_controller.get_mal_title(
                            identifiers['mal'], medium)
                        entry_resp[site.name] = await mal.get_entry_details(
                            self.session,
                            self.mal_headers,
                            medium,
                            title,
                            identifiers[site]
                        )
                    elif site == Site.ANILIST:
                        entry_resp[
                            site.name] = await self.anilist_client.get_entry_by_id(
                            self.session,
                            medium,
                            identifiers[site]
                        )
                    else:
                        entry_resp[site.name] = identifiers[site]
            return entry_resp
        else:
            return None
