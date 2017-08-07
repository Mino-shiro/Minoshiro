.. _quickstart:

Quickstart
==========
This page gives a brief introduction to the library.
It assumes you have the library installed,
if you don’t check the :ref:`install` portion.

The code block below showcases the basic usage using the built in support for
PostgreSQL and Sqlite3.

.. code-block:: python3

    from pathlib import Path

    from roboragi import Medium, Roboragi, Site

    mal_config = {
        'user': 'MAL User name',
        'password': 'MAL password'
    }
    anilist_config = {
        'id': 'Anilist client id',
        'secret': 'Anilist client secret'
    }


    async def postgres():
        postgres_config = {
            "host": "localhost",
            "port": "5432",
            "user": "postgres",
            "database": "postgres"
        }

        # You can choose how many pages from Anilist
        # and how many entries from MAL
        # to cache at the instance creation.
        robo = await Roboragi.from_postgres(
            mal_config, anilist_config, postgres_config,
            cache_pages=1, cache_mal_entries=30
        )

        # get_data eagerly evaluates all the data
        # and return them in a dict
        saekano = await robo.get_data(
            'Saenai Heroine no Sodatekata', Medium.ANIME
        )
        for site, data in saekano.items():
            print(site, data)

        # yield_data lazily evaluates the data
        # and you can iterate over them as such
        async for site, data in robo.yield_data('New Game!',
                                                Medium.MANGA):
            print(site, data)


    async def sqlite():
        # from_sqlite method accepts a string or a Pathlib Path object.
        sqlite_path = 'path/to/sqlite/database'
        another_path = Path('another/sqlite/path')

        robo = await Roboragi.from_sqlite(
            sqlite_path, mal_config, anilist_config
        )

        # We only want the results from those 2 sites.
        sites = (Site.LNDB, Site.MAL)
        async for site, data in robo.get_data(
            'overlord', Medium.LN, sites):
            print(site, data)

        another_robo = await Roboragi.from_sqlite(
            another_path, mal_config, anilist_config
        )
        print(await another_robo.get_data(
            'Love Live Sunshine!', Medium.ANIME
        ))
