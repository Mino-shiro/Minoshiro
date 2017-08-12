"""
Pull synonyms data from upstream.
"""
from sqlite3 import connect

from minoshiro.data import data_path

__db_path = data_path.joinpath('synonyms.db')
__revision_path = data_path.joinpath('revision')


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


async def check_revision(session_manager) -> tuple:
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
