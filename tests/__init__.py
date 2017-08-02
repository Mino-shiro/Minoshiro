from json import load
from pathlib import Path

from asyncpg import create_pool

__all__ = ['test_data_path', 'get_pool', 'SCHEMA']

test_data_path = Path(Path(__file__).parent.joinpath('test_data'))
SCHEMA = 'robotesting'

with test_data_path.joinpath('postgres.json').open() as js:
    __conn_data = load(js)


async def get_pool():
    """
    Get a connection pool for testing.
    Clear all data in the DB before returing the pool.

    :return: the connection pool.
    """
    pool = await create_pool(**__conn_data)
    await __clear(pool)
    return pool


async def __clear(pool):
    """
    Clear all tables in the testing schema.
    :param pool: the connection pool.
    """
    tables = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema=$1
    AND table_type='BASE TABLE'
    """
    table_names = [
        tuple(v.values())[0] for v in
        [r for r in await pool.fetch(tables, SCHEMA)]
    ]
    for table in table_names:
        await pool.execute(f'TRUNCATE {SCHEMA}.{table}')
