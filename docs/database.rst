.. currentmodule:: roboragi
.. _database:

Database
==========
Roboragi uses caching to make search results faster and more accurate.

Build in database support
--------------------------
Roboragi comes with built in support for SQLite3 and PostgreSQL databases.

To use the built in SQLite3 support, simply use the ``from_sqlite`` method as
such:

.. code-block:: python3

    from roboragi import Roboragi

    async def main():
        mal_config = {
            'user': 'MAL User name',
            'password': 'MAL password'
        }
        anilist_config = {
            'id': 'Anilist client id',
            'secret': 'Anilist client secret'
        }

        db_path = 'path/to/database'

        robo = await Roboragi.from_sqlite(
            mal_config, anilist_config, db_path
        )


To use the built in PostgreSQL support, you will need
`asyncpg <https://github.com/MagicStack/asyncpg>`_ to be installed. Check
:ref:`install` for more information.
Then, use the ``from_postgres`` method as such:

.. code-block:: python3

    from roboragi import Roboragi


    async def main():
        mal_config = {
            'user': 'MAL User name',
            'password': 'MAL password'
        }
        anilist_config = {
            'id': 'Anilist client id',
            'secret': 'Anilist client secret'
        }
        db_config = {
            "host": "localhost",
            "port": "5432",
            "user": "postgres",
            "database": "postgres"
        }

        robo = await Roboragi.from_postgres(
            mal_config, anilist_config, db_config, schema='my_schema'
        )


Extending DatabaseController
----------------------------------------------
You may also write your custom implementation of the database controller if you
wish. To get started, inherit from the ``DataController`` class as such:

.. code-block:: python3

    from roboragi import DataController


    class MyDatabase(DataController):
        def __init__(self, logger):
            super().__init__(logger)

You will need to initialize the super class with a logger object.

Next, you will need to implement ALL of the following methods. The methods
MUST be defined with ``async def``.


.. autoclass:: DataController

    .. automethod:: get_identifier(query, medium)

    .. automethod:: set_identifier(name, medium, site, identifier)

    .. automethod:: get_mal_title(id_, medium)

    .. automethod:: set_mal_title(id_, medium, title)

    .. automethod:: medium_data_by_id(id_, medium, site)

    .. automethod:: set_medium_data(id_, medium, site, data)


