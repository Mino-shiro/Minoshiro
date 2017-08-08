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

.. _Extending DatabaseController:

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

.. code-block:: python3

    @abstractmethod
    async def get_identifier(self, query: str,
                             medium: Medium) -> Optional[Dict[Site, str]]:
        """
        Get the identifier of a given search query.

        :param query: the search query.
        :type query: str

        :param medium: the medium type.
        :type medium: Medium

        :return:
            A dict of all identifiers for this search query for all sites,
            None if nothing is found.
        :rtype: Optional[Dict[Site, str]]
        """
        raise NotImplementedError

    @abstractmethod
    async def set_identifier(self, name: str, medium: Medium,
                             site: Site, identifier: str):
        """
        Set the identifier for a given name.

        :param name: the name.
        :type name: str

        :param medium: the medium type.
        :type medium: Medium

        :param site: the site.
        :type site: Site

        :param identifier: the identifier.
        :type identifier: str
        """
        raise NotImplementedError

    @abstractmethod
    async def get_mal_title(self, id_: str, medium: Medium) -> Optional[str]:
        """
        Get a MAL title by its id.

        :param id_: th MAL id.
        :type id_: str

        :param medium: the medium type.
        :type medium: Medium

        :return: The MAL title if it's found.
        :rtype: Optional[str]
        """
        raise NotImplementedError

    @abstractmethod
    async def set_mal_title(self, id_: str, medium: Medium, title: str):
        """
        Set the MAL title for a given id.

        :param id_: the MAL id.
        :type id_: str

        :param medium: The medium type.
        :type medium: Medium

        :param title: The MAL title for the given id.
        :type title: str
        """
        raise NotImplementedError

    @abstractmethod
    async def medium_data_by_id(self, id_: str, medium: Medium,
                                site: Site) -> Optional[dict]:
        """
        Get data by id.

        :param id_: the id.
        :type id_: str

        :param medium: the medium type.
        :type medium: Medium

        :param site: the site.
        :type site: Site

        :return: the data for that id if found.
        :rtype: Optional[dict]
        """
        raise NotImplementedError

    @abstractmethod
    async def set_medium_data(self, id_: str, medium: Medium,
                              site: Site, data: dict):
        """
        Set the data for a given id.

        :param id_: the id.
        :type id_: str

        :param medium: the medium type.
        :type medium: Medium

        :param site: the site.
        :type site: Site

        :param data: the data for the id.
        :type data: dict
        """
        raise NotImplementedError