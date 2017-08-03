from asyncpg import create_pool
from aiohttp import ClientSession
from typing import Optional

from roboragi import get_default_logger
from roboragi.data_controller import PostgresController
from roboragi.data_controller.enums import Medium, Site
from roboragi.web_api import ani_db, ani_list, anime_planet, lndb, mal, mu

from roboragi.web_api import nu


class SearchInstance:

    def __init__(self, config: dict):
        """
        Initialize the class
        """
        self.session = ClientSession()
        self.logger = get_default_logger()
        if config['anilist_client_id']:
            self.ani_client_id = config['anilist_client_id']
            self.ani_client_secret = config['anilist_client_secret']
        if config['mal_user_agent']:
            self.mal_user_agent = config['mal_user_agent']
            self.mal_authorization = config['mal_auth']
        if config['database_name']:
            self.database_name = config['database_name']
            self.database_user = config['database_user']
            self.database_password = config['database_password']
            self.database_host = config['database_host']
        self.mal_headers = None
        self.anilist_client = None
        self.db_pool = None
        self.db_controller = None

    @classmethod
    async def create(cls, config: dict):
        """
        Searches all of the databases and returns the info
        :param config: dict with initialization info
        :return: SearchInstance object
        """
        self = SearchInstance(config)
        try:
            if self.database_name:
                self.db_pool = await create_pool(
                    database=self.database_name,
                    host=self.database_host,
                    user=self.database_user,
                    password=self.database_password
                )
                self.db_controller = await PostgresController.get_instance(
                    self.logger,
                    pool=self.db_pool
                )
        except Exception as e:
            self.logger.error(str(e))
            raise e
        try:
            if self.ani_client_id:
                self.anilist_client = ani_list.AniList(
                    self.session,
                    self.ani_client_id,
                    self.ani_client_secret
                )
            if self.mal_user_agent:
                self.mal_headers = {
                    'Authorization': self.mal_authorization,
                    'User-Agent': self.mal_user_agent
                }
        except Exception as e:
            self.logger.error(str(e))
            raise e
        return self

    async def find_anime(self, anime_title) -> dict:
        """
        Searches all of the databases and returns the info
        :param query: the search term.
        :return: dict with anime info.
        """
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
            return entry_resp
        except Exception as e:
            self.logger.error(str(e))
            raise e

    async def get_cached(self, title: str, medium: Medium) -> Optional[dict]:
        entry_resp = {}
        identifiers = await self.db_controller.get_identifier(title, medium)
        if identifiers is not None:
            for site in identifiers.keys():
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
                    entry_resp[site.name] = await self.anilist_client.get_entry_by_id(
                        self.session,
                        medium,
                        identifiers[site]
                    )
                else:
                    entry_resp[site.name] = identifiers[site]
            return entry_resp
        else:
            return None
