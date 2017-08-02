"""
Database utility functions.
"""

from json import loads
from typing import Optional

from asyncpg import Record
from asyncpg.pool import Pool

from .data_utils import get_all_synonyms


def parse_record(record: Record) -> Optional[tuple]:
    """
    Parse a asyncpg Record object to a tuple of values
    :param record: the asyncpg Record object
    :return: the tuple of values if it's not None, else None
    """
    try:
        return tuple(record.values())
    except AttributeError:
        return None


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
      medium SMALLINT,
      site SMALLINT,
      identifier VARCHAR NOT NULL,
      PRIMARY KEY (syname, medium, site)
    );""".format(schema)

    mal = """
    CREATE TABLE IF NOT EXISTS {}.mal (
      id VARCHAR,
      medium SMALLINT,
      title VARCHAR NOT NULL,
      PRIMARY KEY (id, medium)
    );
    """.format(schema)

    tables = """
    CREATE TABLE IF NOT EXISTS {} (
      id VARCHAR,
      site SMALLINT,
      dict VARCHAR,
      cachetime TIMESTAMP,
      PRIMARY KEY (id, site)
    )
    """
    await pool.execute(lookup)
    await pool.execute(mal)
    for name in ('anime', 'manga', 'ln', 'vn'):
        await pool.execute(tables.format(f'{schema}.{name}'))


async def populate_lookup(pool: Pool, schema: str):
    """
    Populate the lookup table with synonyms.
    :param pool: the connection pool.
    :param schema: the schema name.
    """
    rows = get_all_synonyms()
    convert_type = {
        'Anime': 1,
        'Manga': 2,
        'LN': 3
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
        await __populate_one(schema, pool, name, medium, 1, mal_id)
        await __populate_one(schema, pool, name, medium, 2, anilist)
        await __populate_one(schema, pool, name, medium, 3, ap)
        await __populate_one(schema, pool, name, medium, 4, anidb)


async def __populate_one(schema, pool, name, medium, site, id_):
    sql = """
    INSERT INTO {} VALUES ($1, $2, $3, $4)
    ON CONFLICT (syname, medium, site)
    DO NOTHING 
    """.format(f'{schema}.lookup')
    if str(id_):
        await pool.execute(sql, name, medium, site, str(id_))
