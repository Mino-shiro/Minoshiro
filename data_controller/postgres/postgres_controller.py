import re

from asyncpg import InterfaceError, create_pool
from asyncpg.pool import Pool

from data_controller import DataController
from .postgres_utils import make_tables, populate_lookup


class PostgresController(DataController):
    """
    To be able to integrate with an existing database, all tables for roboragi
    will be put under the `roboragi` schema unless a different schema name is
    passed to the __init__ method.

    This will only implement data caching, since keeping track of stats is not
    in the scope of this project.
    """

    def __init__(self, pool: Pool, logger, schema: str = 'roboragi'):
        """
        Init
        :param pool: the `asyncpg` connection pool.
        :param logger: logger object used for logging.
        :param schema: the schema name, default is `roboragi`
        """
        self.pool = pool
        self.schema = schema
        self.logger = logger

    @classmethod
    async def get_instance(cls, logger, connect_kwargs: dict = None,
                           pool: Pool = None, schema: str = 'roboragi'):
        """
        Get a new instance of `PostgresController`
        :param logger: the logger object.

        :param connect_kwargs:
        Keyword arguments for the :func:`asyncpg.connection.connect` function.

        :param pool: an existing connection pool.

        One of `pool` or `connect_kwargs` must not be None.

        :param schema: the schema name used. Defaults to `roboragi`

        :return: a new instance of `PostgresController`
        """
        assert connect_kwargs or pool, (
            'Please either provide a connection pool or '
            'a dict of connection data for creating a new '
            'connection pool.'
        )
        if not re.fullmatch('[a-zA-Z]+', schema):
            raise ValueError('Please only use upper and lower case'
                             'letters in the schema name.')
        if not pool:
            try:
                pool = await create_pool(**connect_kwargs)
                logger.info('Connection pool made.')
            except InterfaceError as e:
                logger.error(str(e))
                raise e
        logger.info('Creating tables...')
        await make_tables(pool, schema)
        logger.info('Tables created.')
        logger.info('Populating database...')
        await populate_lookup(pool, schema)
        logger.info('Database populated.')
        return cls(pool, logger, schema)
