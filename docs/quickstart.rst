.. _quickstart:

Quickstart
==========
This page gives a brief introduction to the library.
It assumes you have the library installed,
if you don’t check the :ref:`install` portion.

The code block below showcases the basic usage using the built in support for
PostgreSQL and SQLite3.

.. code-block:: python3

    from pathlib import Path

    from minoshiro import Medium, Minoshiro, Site

    mal_config = {
        'user': 'MAL User name',
        'password': 'MAL password'
    }


    async def postgres():
        postgres_config = {
            "host": "localhost",
            "port": "5432",
            "user": "postgres",
            "database": "postgres"
        }

        robo = await Minoshiro.from_postgres(
            mal_config, postgres_config,
            cache_pages=1, cache_mal_entries=30
        )

        # get_data eagerly evaluates all the data and return them in a dict
        saekano = await robo.get_data(
            'Saenai Heroine no Sodatekata', Medium.ANIME
        )
        for site, data in saekano.items():
            print(site, data)

        # yield_data lazily evaluates the data and you can iterate over them
        async for site, data in robo.yield_data('New Game!', Medium.MANGA):
            print(site, data)


    async def sqlite():
        # from_sqlite method accepts both a string or a Pathlib Path object.
        sqlite_path = 'path/to/sqlite/database'
        another_path = Path('another/sqlite/path')

        robo = await Minoshiro.from_sqlite(
            mal_config, sqlite_path
        )

        # We only want the results from those 2 sites.
        sites = (Site.LNDB, Site.MAL)
        async for site, data in robo.get_data('overlord', Medium.LN, sites):
            print(site, data)

        another_robo = await Minoshiro.from_sqlite(
            mal_config, another_path
        )
        # Specify the seconds for HTTP request timeout.
        print(
            await another_robo.get_data(
                'Love Live Sunshine!', Medium.ANIME, timeout=10
            )
        )
