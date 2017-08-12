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


async def download_anidb(session_manager: SessionManager, timestamp=None):
    """

    :param session_manager:
    :param timestamp:
    :return:
    """
    good, new_time = check_anidb_download(timestamp)
    if not good:
        url = 'http://anidb.net/api/anime-titles.xml.gz'
        async with await session_manager.get(url) as resp:
            with __anidb_xml_path.open('wb') as f:
                f.write(await resp.read())
    return good, new_time


async def check_revision(session_manager) -> Tuple[bool, int]:
    """
    Check the revision number from upstream repo.

    :param session_manager: the `SessionManager` instance.

    :return:
        A tuple of (The revision number matched, the upstream revision number)
    """
    url = ('https://raw.githubusercontent.com/Mino-shiro/'
           'minoshiro-database/master/revision')
    async with await session_manager.get(url) as resp:
        revision = int(await resp.text())
    if not __revision_path.is_file():
        return False, revision
    with __revision_path.open() as f:
        local_revision = int(f.read())
    return local_revision == revision, revision


async def download_db(session_manager):
    """
    Download the database from upstream if needed.

    :param session_manager: the `SessionManager` instance.
    """
    good, new = await check_revision(session_manager)
    if good and __db_path.is_file():
        return
    url = ('https://github.com/Mino-shiro/minoshiro-database'
           '/raw/master/synonyms.db')
    async with await session_manager.get(url) as resp:
        content = await resp.read()
    with __db_path.open('wb') as db, __revision_path.open('w+') as rev:
        db.write(content)
        rev.write(str(new))


def check_anidb_download(timestamp=None):
    """

    :param timestamp:

    :return:
    """
    now = int(time())
    if not __db_path.is_file():
        res, new = False, now
    else:
        res, new = check_time(timestamp)
    if res:
        return True, new
    with __anidb_time_path.open('w+') as f:
        f.write(str(now))
    return False, now


def check_time(timestamp=None):
    """
    Check the time for anidb data dump.

    :param timestamp: the current time stamp if any.

    :return:
    """
    now = int(time())
    if timestamp is None:
        if not __anidb_time_path.is_file():
            return False, timestamp
        with __anidb_time_path.open() as f:
            timestamp = int(f.read())
    return now - timestamp < 86400, timestamp
