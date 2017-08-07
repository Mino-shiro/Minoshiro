.. _api:

API
==========
The following section outlines the API of Roboragi.

Roboragi
--------------------
.. py:class:: Roboragi(session_manager, db_controller, mal_config, anilist_config, \*, logger=None, loop=None)

    Represents the search instance.

    It is suggested to use one of the class methods to create the instance
    if you wish to use one of the data controllers provided by the library.

    Make sure you run the ``pre_cache`` method if you initialized the class
    directly from the ``__init__`` method.

    **Parameters**

    * session_manager(SessionManager) -  The ``SessionManager`` instance.
      See class ``roboragi.session_manager.SessionManager`` for details.

    * db_controller(DataController) -  Any sub class of
      ``roboragi.data_controller.abc.DataController`` will work here.

    * mal_config(dict) - A dict for MAL authorization.
        It must contain the keys:
            ``user``: Your MAL username

            ``password``: Your MAL password

        It may also contain a key ``description`` for the description you
        wish to use in the auth header.

        If this key is not present, the description defaults to:
        ``A Python library for anime search.``

    * anilist_config(dict) -  A dict for Anilist authorization.
        It must contain the keys:
            ``id``: Your Anilist client id

            ``secret``: Your Anilist client secret.

    * logger(Optional[Logger]) -  The logger object. If it's not provided, will use the
      defualt logger provided by the library.

    * loop(Optional[`Event loop <https://docs.python.org/3/library/asyncio-eventloops.html>`_]) -
      An asyncio event loop. If not provided will use the default event loop.

.. py:classmethod:: from_postgres(mal_config, anilist_config, db_config = None, pool=None, \*, schema='roboragi', cache_pages=0, cache_mal_entries=0, logger=None, loop=None)

    Get an instance of :py:class:`Roboragi`  with class :py:class:`PostgresController` as the database controller.

    **Parameters**

    * mal_config(dict) - A dict for MAL authorization.
        It must contain the keys:
            ``user``: Your MAL username

            ``password``: Your MAL password

        It may also contain a key ``description`` for the description you
        wish to use in the auth header.

        If this key is not present, the description defaults to:
        ``A Python library for anime search.``

    * anilist_config(dict) -  A dict for Anilist authorization.
        It must contain the keys:
            ``id``: Your Anilist client id

            ``secret``: Your Anilist client secret.


    * db_config(dict) - A dict of database config for the connection.
        It should contain the keys in keyword arguments for the ``asyncpg.connection.connect`` function.

        An example config might look like this:

        .. code-block:: python3

            db_config = {
                "host": "localhost",
                "port": "5432",
                "user": "postgres",
                "database": "postgres"
            }

    * pool(`Pool <https://magicstack.github.io/asyncpg/current/api/index.html?#asyncpg.pool.Pool>`_)
      - an existing ``asyncpg`` connection pool.

      One of ``db_config`` or ``pool`` must not be None.

    * schema(Optional[str]) - the name for the schema used. Defaults to ``roboragi``

    * cache_pages(Optional[int]) -  The number of pages of anime and manga from Anilist to cache
      before the instance is created. Each page contains 40 entries max.

    * cache_mal_entries(Optional[int]) - The number of MAL entries you wish to cache.
      ``cache_pages`` must be greater than 0 to cache MAL entries.

    * logger(Optional[Logger]) -  The logger object. If it's not provided, will use the
      defualt logger provided by the library.

    * loop(Optional[`Event loop <https://docs.python.org/3/library/asyncio-eventloops.html>`_]) -
      An asyncio event loop. If not provided will use the default event loop.