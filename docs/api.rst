.. _api:

API
==========
The following section outlines the API of Roboragi.

Default Logger
---------------
.. py:function:: get_default_logger()

    Return a basic default :py:class:`logging.Logger`

    **Returns**

    A basic logger with a :py:class:`logging.StreamHandler` attatched and with
    level ``INFO``

Roboragi
--------------------
.. py:class:: Roboragi(db_controller, mal_config, \*, logger=None, loop=None)

    Represents the search instance.

    It is suggested to use one of the class methods to create the instance
    if you wish to use one of the data controllers provided by the library.

    Make sure you run the :py:meth:`pre_cache` method if you initialized the
    class directly from the ``__init__`` method.

    **Parameters**

    * db_controller(:py:class:`DataController`) -
      Any sub class of :py:class:`DataController` will work here.

    * mal_config(:py:class:`dict`) - A dict for MAL authorization.
        It must contain the keys:
            ``user``: Your MAL username

            ``password``: Your MAL password

        It may also contain a key ``description`` for the description you
        wish to use in the auth header.

        If this key is not present, the description defaults to:
        ``A Python library for anime search.``

    * logger(Optional[:py:class:`logging.Logger`]) -  The logger object.
      If it's not provided, will use the defualt logger provided by the library.

    * loop(Optional[`Event loop <https://docs.python.org/
      3/library/asyncio-eventloops.html>`_]) -
      An asyncio event loop. If not provided will use the default event loop.

    .. py:classmethod:: from_postgres(mal_config, db_config = None, pool=None, \*, schema='roboragi', cache_pages=0, cache_mal_entries=0, logger=None, loop=None)

        This method is a *coroutine*

        Get an instance of :py:class:`Roboragi`  with
        :py:class:`PostgresController` as the database controller.

        **Parameters**

        * mal_config(:py:class:`dict`) - A dict for MAL authorization.
            It must contain the keys:
                ``user``: Your MAL username

                ``password``: Your MAL password

            It may also contain a key ``description`` for the description you
            wish to use in the auth header.

            If this key is not present, the description defaults to:
            ``A Python library for anime search.``

        * db_config(:py:class:`dict`) -
          A dict of database config for the connection.
          It should contain the keys in keyword arguments for the
          ``asyncpg.connection.connect`` function.

          An example config might look like this:

            .. code-block:: python3

                db_config = {
                    "host": 'localhost',
                    "port": '5432',
                    "user": 'postgres',
                    "database": 'postgres'
                }

        * pool(`Pool <https://magicstack.github.io/asyncpg/
          current/api/index.html?#asyncpg.pool.Pool>`_) - an
          existing ``asyncpg`` connection pool.

          One of ``db_config`` or ``pool`` must not be None.

        * schema(Optional[:py:class:`str`]) - the name for the schema used.
          Defaults to ``roboragi``

        * cache_pages(Optional[:py:class:`int`]) -
          The number of pages of anime and
          manga from Anilist to cache before the instance is created.
          Each page contains 40 entries max.

        * cache_mal_entries(Optional[:py:class:`int`]) -
          The number of MAL entries you wish to cache.
          ``cache_pages`` must be greater than 0 to cache MAL entries.

        * logger(Optional[:py:class:`logging.Logger`]) -  The logger object.
          If it's not provided, will use the defualt logger
          provided by the library.

        * loop(Optional[`Event loop <https://docs.python.org/3/
          library/asyncio-eventloops.html>`_]) - An asyncio event loop.
          If not provided will use the default event loop.

        **Returns**

        Instance of :py:class:`Roboragi` with
        :py:class:`PostgresController` as the database controller.

    .. py:classmethod:: from_sqlite(mal_config, path, \*, cache_pages=0, cache_mal_entries=0, logger=None, loop=None)

        This method is a *coroutine*

        Get an instance of :py:class:`Roboragi` with
        :py:class:`SqliteController` as the database controller.

        **Parameters**

        * mal_config(:py:class:`dict`) - A dict for MAL authorization.
            It must contain the keys:
                ``user``: Your MAL username

                ``password``: Your MAL password

            It may also contain a key ``description`` for the description you
            wish to use in the auth header.

            If this key is not present, the description defaults to:
            ``A Python library for anime search.``

        * path(Union[:py:class:`str`, :py:class:`pathlib.Path`]) -
          The path to the SQLite3 database,
          can either be a string or a Pathlib Path object.

        * cache_pages(Optional[:py:class:`int`]) -  The number of pages of
          anime and manga from Anilist to cache before the instance is created.
          Each page contains 40 entries max.

        * cache_mal_entries(Optional[:py:class:`int`]) -
          The number of MAL entries
          you wish to cache. ``cache_pages`` must be greater than
          0 to cache MAL entries.

        * logger(Optional[:py:class:`logging.Logger`]) -
          The logger object. If it's not provided,
          will use the defualt logger provided by the library.

        * loop(Optional[`Event loop <https://docs.python.org/3/
          library/asyncio-eventloops.html>`_]) -
          An asyncio event loop. If not provided
          will use the default event loop.

        **Returns**

        Instance of :py:class:`Roboragi` with
        :py:class:`PostgresController` as the database controller.

    .. py:method:: pre_cache(cache_pages, cache_mal_entries)

        This method is a *coroutine*

        Pre cache the database with anime and managa data.

        This method is called by :py:meth:`from_postgres`
        and :py:meth:`from_sqlite`, so you do not need to call this method if
        you created ths class instance with those two methods.

        **Parameters**

        * cache_pages(:py:class:`int`) - Number of Anilist pages to cache.
          There are 40 entries per page.

        * cache_mal_entries(:py:class:`int`) -
          Number of MAL entries you wish to cache.

    .. py:method:: yield_data(query, medium, sites)

        This method is a *coroutine*

        Yield the data for the search query from all sites.

        Sites with no data found will be skipped.

        **Parameters**

        * query(:py:class:`str`) - the search query

        * medium(:py:class:`Medium`) - the medium type

        * sites(Optional[Iterable[:py:class:`Site`]]) -
          an iterable of sites desired. If None is provided,
          will search all sites by default

        **Returns**

        An asynchronous generator that yields the site and data
        in a tuple for all sites requested.

    .. py:method:: get_data(query, medium, sites)

        This method is a *coroutine*

        Get the data for the search query in a dict.

        Sites with no data found will not be in the return value.

        **Parameters**

        * query(:py:class:`str`) - the search query

        * medium(:py:class:`Medium`) - the medium type

        * sites(Optional[Iterable[:py:class:`Site`]]) -
          an iterable of sites desired. If None is provided,
          will search all sites by default

        **Returns**

        Data for all sites in a dict ``{Site: data}``

        **Note**

        When retrieving data from the result of this method, use the
        :py:meth:`dict.get` method instead of square brackets.

        Example:

        .. code-block:: python3

            results = await search_instance.get_data(
                'Non Non Biyori', Medium.ANIME
            )

            # Good
            anilist = results.get(Site.ANILIST)

            # Bad, might raise KeyError
            anilist = results[Site.ANILIST]

Enums
---------
Roboragi uses two enums to represent medium type and website.

.. py:class:: Site

    .. py:attribute:: MAL = 1
    .. py:attribute:: ANILIST = 2
    .. py:attribute:: ANIMEPLANET = 3
    .. py:attribute:: ANIDB = 4
    .. py:attribute:: KITSU = 5
    .. py:attribute:: MANGAUPDATES = 6
    .. py:attribute:: LNDB = 7
    .. py:attribute:: NOVELUPDATES = 8
    .. py:attribute:: VNDB = 9


.. py:class:: Medium

    .. py:attribute:: ANIME = 1
    .. py:attribute:: MANGA = 2
    .. py:attribute:: LN = 3
    .. py:attribute:: VN = 4

Database Controllers
--------------------------
.. py:class:: DataController(logger)

    An ABC (abstract base class) that deals with database caching.

    See :ref:`Extending DatabaseController` for details.

.. py:class:: PostgresController(pool, logger, schema='roboragi')

    To be able to integrate with an existing database, all tables for roboragi
    will be put under the ``roboragi`` schema unless a different schema name is
    passed to the __init__ method.

    Create the instance with the :py:meth:`get_instance` method to make
    sure you have all the tables needed.

    .. py:classmethod:: get_instance(logger, connect_kwargs=None, pool=None, schema='roboragi')

        This method is a *coroutine*

        Get a new instance of :py:class:`PostgresController`

        This method will create the appropriate tables needed.

        **Parameters**

        * logger(Optional[:py:class:`logging.Logger`]) -
          The logger object. If it's not provided,
          will use the defualt logger provided by the library.

        * connect_kwargs(:py:class:`dict`) -
          A dict of database config for the connection.
          It should contain the keys in keyword arguments for the
          ``asyncpg.connection.connect`` function.

          An example config might look like this:

            .. code-block:: python3

                db_config = {
                    "host": 'localhost',
                    "port": '5432',
                    "user": 'postgres',
                    "database": 'postgres'
                }

        * pool(`Pool <https://magicstack.github.io/asyncpg/
          current/api/index.html?#asyncpg.pool.Pool>`_) - an
          existing ``asyncpg`` connection pool.

          One of ``db_config`` or ``pool`` must not be None.

        * schema(:py:class:`str`) - the name for the schema used.
          Defaults to ``roboragi``

        **Returns**

        a new instance of :py:class:`PostgresController`

.. py:class:: SqliteController(path, logger, loop=None)

    A SQLite3 data controller.

    Create the instance with the :py:meth:`get_instance` method to make
    sure you have all the tables needed.

    .. py:classmethod:: get_instance(path, logger=None, loop=None)

        This method is a *coroutine*

        Get a new instance of :py:class:`SqliteController`

        This method will create the appropriate tables needed.

        **Parameters**

        * path(Union[:py:class:`str`, :py:class:`pathlib.Path`]) -
          The path to the SQLite3 database,
          can either be a string or a Pathlib Path object.

        * logger(Optional[:py:class:`logging.Logger`]) -
          The logger object. If it's not provided,
          will use the defualt logger provided by the library.

        * loop(Optional[`Event loop <https://docs.python.org/3/
          library/asyncio-eventloops.html>`_]) -
          An asyncio event loop. If not provided
          will use the default event loop.

        **Returns**

        A new instance of :py:class:`SqliteController`
