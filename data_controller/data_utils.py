from itertools import product

from asyncpg.pool import Pool


async def make_tables(pool: Pool, schema: str):
    """
    Make tables used for caching if they don't exist.
    :param pool: the connection pool.
    :param schema: the schema name.
    """
    sites = ('mal', 'anilist')
    mediums = ('anime', 'manga', 'novel')
    tables = [f'{schema}.{"".join(i)}' for i in product(sites, mediums)]
    await pool.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
    for t in tables:
        sql = """
            CREATE TABLE IF NOT EXISTS {} (
                id VARCHAR PRIMARY KEY,
                NAME VARCHAR,
                synonyms VARCHAR[],
                accesstimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dict JSONB
            )""".format(t)
        await pool.execute(sql)
