from asyncpg import InterfaceError, create_pool
from asyncpg.pool import Pool

from data_controller.data_utils import make_tables, populate_lookup


class DataController:
    """
    To be able to integrate with an existing database, all tables for roboragi
    will be put under the `roboragi` schema unless a different schema name is
    passed to the __init__ method.

    This will only implement data caching, since keeping track of stats is not
    in the scope of this project.

    The site names used are:
    `anidb`, `mal`, 'ap', 'anilist'

    The medium names are:
    `anime`, `manga`, `novel`
    """

    def __init__(self, pool: Pool, logger, schema: str = 'roboragi'):
        """
        Init
        :param pool: the `asyncpg` connection pool.
        :param logger: logger object used for logging.
        :param schema:
        """
        self.pool = pool
        self.schema = schema
        self.logger = logger

    @classmethod
    async def get_instance(cls, logger, connection_data: dict = None,
                           pool: Pool = None, schema: str = 'roboragi'):
        """
        Get a new instance of `DataController`
        :param logger: the logger object.

        :param connection_data: data used in making a new connection pool.
        :param pool: an existing connection pool.

        One of `connection_data` or `pool` must not be None.

        :param schema: the schema name used. Defaults to `roboragi`

        :return: a new instance of `DataController`
        """
        assert connection_data or pool, (
            'Please either provide a connection pool or '
            'a dict of connection data for creating a new '
            'connection pool.'
        )
        if not pool:
            host = connection_data['host']
            port = connection_data['port']
            user = connection_data['user']
            database = connection_data['database']
            password = connection_data['password']
            try:
                pool = await create_pool(
                    host=host, port=port, user=user,
                    database=database, password=password

                )
            except InterfaceError as e:
                logger.error(str(e))
                raise e
        await make_tables(pool, schema)
        await populate_lookup(pool, schema)
        return cls(pool, logger, schema)
