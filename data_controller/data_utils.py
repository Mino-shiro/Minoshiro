"""
Database utility functions.
"""

from json import loads
from sqlite3 import connect

from asyncpg.pool import Pool

from data import data_path


async def make_tables(pool: Pool, schema: str):
    """
    Make tables used for caching if they don't exist.
    :param pool: the connection pool.
    :param schema: the schema name.
    """
    await pool.execute('CREATE SCHEMA IF NOT EXISTS {};'.format(schema))

    lookup = """
    CREATE TABLE IF NOT EXISTS {}.lookup (
      syname VARCHAR,
      medium VARCHAR,
      site VARCHAR,
      identifier VARCHAR NOT NULL,
      PRIMARY KEY (syname, medium, site)
    );""".format(schema)

    mal = """
    CREATE TABLE IF NOT EXISTS {}.mal (
      id VARCHAR,
      medium VARCHAR,
      title VARCHAR NOT NULL,
      PRIMARY KEY (id, medium)
    );
    """.format(schema)

    tables = """
    CREATE TABLE IF NOT EXISTS {} (
      id VARCHAR,
      site VARCHAR,
      dict VARCHAR,
      cachetime TIMESTAMP,
      PRIMARY KEY (id, site)
    )
    """
    await pool.execute(lookup)
    await pool.execute(mal)
    for name in ('anime', 'manga', 'novel'):
        await pool.execute(tables.format(f'{schema}.{name}'))


def get_all_synonyms() -> list:
    """
    Get all synonyms from the sqlite db.
    :return: all synonyms from the sqlite db.
    """
    with connect(str(data_path.joinpath('synonyms.db'))) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM main.synonyms')
        rows = cur.fetchall()
    return rows


async def populate_lookup(pool: Pool, schema: str):
    """
    Populate the lookup table with synonyms.
    :param pool: the connection pool.
    :param schema: the schema name.
    """
    rows = get_all_synonyms()
    convert_type = {
        'Anime': 'anime',
        'Manga': 'manga',
        'LN': 'novel'
    }
    mal_sql = """
    INSERT INTO {} VALUES ($1, $2, $3)
    ON CONFLICT (id, medium)
    DO NOTHING
    """.format(f'{schema}.mal')

    for name, type_, db_links in rows:
        dict_ = loads(db_links)
        mal_name, mal_id = dict_.get('mal', ('', ''))
        anilist = dict_.get('ani')
        ap = dict_.get('ap')
        anidb = dict_.get('adb')
        medium = convert_type[type_]
        if mal_name and mal_id:
            await pool.execute(mal_sql, str(mal_id), medium, mal_name)
        await __populate_one(schema, pool, name, medium, 'mal', mal_id)
        await __populate_one(schema, pool, name, medium, 'anilist', anilist)
        await __populate_one(schema, pool, name, medium, 'ap', ap)
        await __populate_one(schema, pool, name, medium, 'anidb', anidb)


async def __populate_one(schema, pool, name, medium, site, id_):
    sql = """
    INSERT INTO {} VALUES ($1, $2, $3, $4)
    ON CONFLICT (syname, medium, site)
    DO NOTHING 
    """.format(f'{schema}.lookup')
    if str(id_):
        await pool.execute(sql, name, medium, site, str(id_))
