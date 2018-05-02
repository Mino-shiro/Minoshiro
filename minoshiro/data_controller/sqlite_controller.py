from asyncio import get_event_loop
from json import dumps, loads
from pathlib import Path
from sqlite3 import connect
from time import time
from typing import Dict, Optional, Union

from minoshiro.enums import Medium, Site
from minoshiro.logger import get_default_logger
from minoshiro.upstream import get_all_synonyms
from .abc import DataController
from .constants import convert_medium, tables
from .sqlite_utils import make_tables


class SqliteController(DataController):
    """
    A SQLite3 data controller.
    """
    __slots__ = ('path', '_loop')

    def __init__(self, path: Union[str, Path], logger, loop=None):
        """
        Init method. Create the instance with the `get_instance` method to make
        sure you have all the tables needed.

        :param path:
            Path to the database,
            can be a string or a Pathlib Path object.

        :param logger: The logger object used for logging.

        :param loop:
            The asyncio event loop.
            If None is provided will use the default event loop.
        """
        self.path = str(path)
        self._loop = loop
        super().__init__(logger)

    @classmethod
    async def get_instance(cls, path: Union[str, Path], logger=None,
                           loop=None):
        """
        Get a new instance of `SqliteController`

        This method will create the appropriate tables needed.

       :param path:
            Path to the database,
            can be a string or a Pathlib Path object.

        :param logger: The logger object used for logging.

        :param loop:
            The asyncio event loop.
            If None is provided will use the default event loop.

        :return: A new instance of `SqliteController`
        """
        logger = logger or get_default_logger()
        logger.info('Creating tables...')
        await make_tables(path, loop or get_event_loop())
        logger.info('Tables created.')
        return cls(path, logger, loop)

    async def get_identifier(self, query: str,
                             medium: Medium) -> Optional[Dict[Site, str]]:
        """
        Get the identifier of a given search query.

        :param query: the search query.

        :param medium: the medium type.

        :return:
            A dict of all identifiers for this search query for all sites,
            None if nothing is found.
        """
        sql = """
        SELECT site, identifier FROM lookup
        WHERE LOWER(syname)=LOWER(?) AND medium=?
        """
        rows = await self.fetchall(sql, (query, medium.value))
        if not rows:
            return
        return {Site(site): id_ for site, id_ in rows if id_}

    async def set_identifier(self, name: str, medium: Medium,
                             site: Site, identifier: str):
        """
        Set the identifier for a given name.

        :param name: the name.

        :param medium: the medium type.

        :param site: the site.

        :param identifier: the identifier.
        """
        sql = 'REPLACE INTO lookup VALUES (?,?,?,?)'
        await self.execute(sql, (name, medium.value, site.value, identifier))

    async def get_mal_title(self, id_: str, medium: Medium) -> Optional[str]:
        """
        Get a MAL title by its id.

        :param id_: th MAL id.

        :param medium: the medium type.

        :return: The MAL title if it's found.
        """
        sql = 'SELECT title FROM mal WHERE id=? AND medium=?'
        row = await self.fetchone(sql, (id_, medium.value))
        if not row:
            return
        return row[0]

    async def set_mal_title(self, id_: str, medium: Medium, title: str):
        """
        Set the MAL title for a given id.

        :param id_: the MAL id.

        :param medium: The medium type.

        :param title: The MAL title for the given id.
        """
        sql = 'REPLACE INTO mal VALUES (?, ?, ?)'
        await self.execute(sql, (id_, medium.value, title))

    async def medium_data_by_id(self, id_: str, medium: Medium,
                                site: Site) -> Optional[dict]:
        """
        Get data by id.

        Note that if the data cache is more than 1 day old this will delete
        the row in the DB and return None.

        :param id_: the id.

        :param medium: the medium type.

        :param site: the site.

        :return: the data for that id if found.
        """
        sql = (f'SELECT dict, cachetime FROM {tables[medium]} '
               f'WHERE id=? AND site=?')
        row = await self.fetchone(sql, (id_, site.value))
        if not row:
            return
        data, cachetime = row
        now = int(time())
        if now - cachetime > 86400:
            await self.delete_medium_data(id_, medium, site)
            return
        return loads(data) if data else None

    async def set_medium_data(self, id_: str, medium: Medium,
                              site: Site, data: dict):
        """
        Set the data for a given id.

        :param id_: the id.

        :param medium: the medium type.

        :param site: the site.

        :param data: the data for the id.
        """
        sql = f'REPLACE INTO {tables[medium]} VALUES (?, ?, ?, ?)'
        await self.execute(sql, (id_, site.value, dumps(data), int(time())))

    async def delete_medium_data(self, id_: str, medium: Medium, site: Site):
        """
        Delete a row in medium data table.

        :param id_: the id.

        :param medium: the medium type.

        :param site: the site.
        """
        sql = f'DELETE FROM {tables[medium]} WHERE id=? AND site=?'
        try:
            await self.execute(sql, (id_, site.value))
        except Exception as e:
            self.logger.warning(str(e))

    async def pre_cache(self, session_manager):
        """
        Populate the lookup with synonyms.

        :param session_manager: The Aiohttp SessionManager.
        """
        rows = await get_all_synonyms(session_manager)
        with connect(self.path) as conn:
            for name, type_, db_links in rows:
                dict_ = loads(db_links)
                mal_name, mal_id = dict_.get('mal', ('', ''))
                anilist = dict_.get('ani')
                ap = dict_.get('ap')
                anidb = dict_.get('adb')
                medium = convert_medium[type_]
                if mal_name and mal_id:
                    _cache_mal(conn, str(mal_id), medium, str(mal_name))
                _precache(conn, name, medium, Site.MAL, mal_id)
                _precache(conn, name, medium, Site.ANILIST, anilist)
                _precache(conn, name, medium, Site.ANIMEPLANET, ap)
                _precache(conn, name, medium, Site.ANIDB, anidb)
            conn.commit()

    @property
    def loop(self):
        """
        :return: `self._loop` or a default event loop.
        """
        return self._loop or get_event_loop()

    def __execute(self, sql: str, params=None):
        """
        Execute and commit and SQL query.

        :param sql: the SQL query.

        :param params: the SQL parameters.
        """
        with connect(self.path) as conn:
            conn.execute(sql, params)
            conn.commit()

    async def execute(self, sql: str, params=None):
        """
        Run `self.__execute` using an asyncio event loop.

        :param sql: the SQL query.

        :param params: the SQL parameters.
        """
        await self.loop.run_in_executor(
            None, self.__execute, sql, params
        )

    def __fetch(self, all_: bool, sql: str, params=None):
        """
        Fetch results from a SQL query.

        :param all_: True to fetch all rows, False to fetch one row.

        :param sql: the SQL query.

        :param params: the SQL parameters.

        :return: The results fetched from the SQL query.
        """
        with connect(self.path) as conn:
            cur = conn.execute(sql, params)
            if all_:
                return cur.fetchall()
            else:
                return cur.fetchone()

    async def fetchall(self, sql: str, params=None):
        """
        Run `self.__fetch` using an asyncio event loop.

        :param sql: the SQL query.

        :param params: the SQL parameters.

        :return: All rows fetched from the SQL query.
        """
        return await self.loop.run_in_executor(
            None, self.__fetch, True, sql, params
        )

    async def fetchone(self, sql: str, params=None):
        """
        Run `self.__fetch` using an asyncio event loop.

        :param sql: the SQL query.

        :param params: the SQL parameters.

        :return: One row fetched from the SQL query.
        """
        return await self.loop.run_in_executor(
            None, self.__fetch, False, sql, params
        )


def _precache(conn, name, medium, site, id_):
    """
    Cache id.
    """
    if name and (id_ or isinstance(id_, int)):
        sql = 'REPLACE INTO lookup VALUES (?,?,?,?)'
        conn.execute(
            sql, (str(name), medium.value, site.value, str(id_))
        )


def _cache_mal(conn, id_: str, medium: Medium, title: str):
    """
    Cache mal title.
    """
    sql = 'REPLACE INTO mal VALUES (?, ?, ?)'
    conn.execute(sql, (id_, medium.value, title))
