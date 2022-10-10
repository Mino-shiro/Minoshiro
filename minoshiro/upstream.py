"""
Pull synonyms data from upstream.
"""
from sqlite3 import connect
from time import time
from typing import Tuple

from aiohttp_wrapper import SessionManager

from minoshiro.data import data_path

__all__ = ['get_all_synonyms', 'download_anidb']

__db_path = data_path.joinpath('synonyms.db')
__revision_path = data_path.joinpath('revision')
__anidb_time_path = data_path.joinpath('.anidb_time')
__anidb_xml_path = data_path.joinpath('anime-titles.xml')

__SECONDS_IN_A_DAY = 86400


async def get_all_synonyms(session_manager) -> list:
    """
    Get all synonyms from the sqlite db.

    :return: all synonyms from the sqlite db.
    """
    await download_db(session_manager)
    with connect(str(__db_path)) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM main.synonyms')
        rows = cur.fetchall()
    return rows


async def download_anidb(session_manager: SessionManager, timestamp=None, user_agent=None):
    """
    Download the anidb titles data dump

    :param session_manager: the `SessionManager` instance.

    :param timestamp: the last anidb data dump update time stamp if any.

    :param user_agent:
        The user agent that will be used for any requests.  If not provided,
        will use a default provided by the library.

    :return: whether or not the data dump was recent and the timestamp of its last refresh
    """
    recent, refresh_time = check_anidb_download(timestamp)
    if not recent:
        url = 'http://anidb.net/api/anime-titles.xml.gz'
        async with await session_manager.get(
                    url,
                    headers={"User-Agent": user_agent} if user_agent else None
                ) as resp:
            with __anidb_xml_path.open('wb') as f:
                f.write(await resp.read())
    return recent, refresh_time


async def check_revision(session_manager, user_agent=None) -> Tuple[bool, int]:
    """
    Check the revision number from upstream repo.

    :param session_manager: the `SessionManager` instance.

    :param user_agent:
        The user agent that will be used for any requests.  If not provided,
        will use a default provided by the library.

    :return:
        A tuple of whether or not the local revision number matched the
        upstream one and the upstream revision number itself
    """
    url = ('https://raw.githubusercontent.com/Mino-shiro/'
           'minoshiro-database/master/revision')
    async with await session_manager.get(
            url,
            headers={"User-Agent": user_agent} if user_agent else None) as resp:
        revision = int(await resp.text())
    if not __revision_path.is_file():
        return False, revision
    with __revision_path.open() as f:
        local_revision = int(f.read())
    return local_revision == revision, revision


async def download_db(session_manager, user_agent=None):
    """
    Download the synonyms database from upstream if needed.

    :param session_manager: the `SessionManager` instance.

    :param user_agent:
        The user agent that will be used for any requests.  If not provided,
        will use a default provided by the library.
    """
    good, new = await check_revision(session_manager)
    if good and __db_path.is_file():
        return
    url = ('https://github.com/Mino-shiro/minoshiro-database'
           '/raw/master/synonyms.db')
    async with await session_manager.get(
            url,
            headers={"User-Agent": user_agent} if user_agent else None) as resp:
        content = await resp.read()
    with __db_path.open('wb') as db, __revision_path.open('w+') as rev:
        db.write(content)
        rev.write(str(new))


def check_anidb_download(timestamp=None):
    """
    Check if the anidb data dump exists and is new enough to use.
    Side effect: refresh the timestamp for the last update of the anidb data
    dump if it needs one.

    :param timestamp: the last anidb data dump update time stamp if any.

    :return: whether or not the anidb data dump is new enough to use and the
    timestamp of its last refresh
    """
    now = int(time())
    if not __db_path.is_file():
        recent, new = False, now
    else:
        recent, new = check_time(timestamp, now)
    if recent:
        return True, new
    with __anidb_time_path.open('w+') as f:
        f.write(str(now))
    return False, now


def check_time(timestamp=None, now=None):
    """
    Check the last update time for the anidb data dump.  anidb does not want
    people pulling this database more than once a day.

    :param timestamp: the last anidb data dump update time stamp if any.

    :param now: a timestamp to compare with, by default the current time

    :return: whether or not the time delta is less than a day and the timestamp
    """
    now = now if now != None else int(time())
    if timestamp is None:
        if not __anidb_time_path.is_file():
            return False, timestamp
        with __anidb_time_path.open() as f:
            timestamp = int(f.read())
    return now - timestamp < __SECONDS_IN_A_DAY, timestamp
