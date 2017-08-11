from sqlite3 import connect


async def make_tables(path, loop):
    """
    Make tables for caching if they don't exist.

    :param path: Path to the database.

    :param loop: the asyncio event loop.
    """
    await loop.run_in_executor(None, __make_tables, path)


def __make_tables(path):
    """
    Make tables for caching if they don't exist.

    :param path: Path to the database.
    """
    with connect(str(path)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS lookup(
              syname VARCHAR,
              medium INT,
              site INT,
              identifier VARCHAR NOT NULL,
              PRIMARY KEY (syname, medium, site)
            )"""
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS mal(
              id VARCHAR,
              medium INT,
              title VARCHAR NOT NULL,
              PRIMARY KEY (id, medium)
            )
            """
        )

        tables = """
        CREATE TABLE IF NOT EXISTS {} (
          id VARCHAR,
          site INT,
          dict VARCHAR,
          cachetime INT,
          PRIMARY KEY (id, site)
        )
        """

        for name in ('anime', 'manga', 'ln', 'vn'):
            connection.execute(tables.format(name))
        connection.commit()
