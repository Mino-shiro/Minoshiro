"""
Database utility functions.
"""

from typing import Optional

from asyncpg import Record
from asyncpg.pool import Pool


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
