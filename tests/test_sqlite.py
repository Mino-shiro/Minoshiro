from random import choice, randint
from time import time

import pytest

from minoshiro.data_controller import SqliteController
from minoshiro.data_controller.enums import Medium
from tests import clear_sqlite, test_data_path
from tests.utils import *

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def sqlite_controller():
    path = str(test_data_path.joinpath('test_db'))
    res = await SqliteController.get_instance(path)
    yield res
    clear_sqlite(path)


async def test_identifier(sqlite_controller: SqliteController):
    """
    Test getting and setting identifier in the lookup table.
    """
    entries = random_lookup_entries()
    for name, value in entries.items():
        for medium, site_vals in value.items():
            for site, id_ in site_vals.items():
                await sqlite_controller.set_identifier(name, medium, site, id_)
            res = await sqlite_controller.get_identifier(name, medium)
            assert res == value.get(medium)


async def test_mal_title(sqlite_controller: SqliteController):
    """
    Test getting and setting mal titles.
    """
    ids = set(random_str() for _ in range(randint(10, 20)))
    for id_ in ids:
        mediums = random_mediums()
        for med in mediums:
            title = random_str()
            await sqlite_controller.set_mal_title(id_, med, title)
            assert await sqlite_controller.get_mal_title(id_, med) == title
            new = f'{title} asopdhsahdas'
            await sqlite_controller.set_mal_title(id_, med, new)
            assert await sqlite_controller.get_mal_title(id_, med) == new


async def test_data(sqlite_controller: SqliteController):
    """
    Test getting and setting medium data. We will only run this test on the
    `anime` table since all tables have the same structures.
    """
    ids = set(random_str() for _ in range(randint(5, 15)))
    names = [f'name {i} {random_str()}' for i in ids]

    sql = """
    UPDATE anime
    SET cachetime=$1
    WHERE id=$2 AND site=$3
    """

    for id_, name in zip(ids, names):
        tmp = {}
        sites = random_sites()
        for site in sites:
            data = random_dict()
            tmp[site] = data
            await sqlite_controller.set_identifier(name, Medium.ANIME, site,
                                                   id_)
            await sqlite_controller.set_medium_data(id_, Medium.ANIME, site,
                                                    data)
        assert await sqlite_controller.get_medium_data(name,
                                                       Medium.ANIME) == tmp

        updated_site = choice(sites)
        await sqlite_controller.execute(
            sql, (int(time()) - 88888, id_, updated_site.value)
        )
        new_data = await sqlite_controller.get_medium_data(name, Medium.ANIME)
        assert not new_data or updated_site not in new_data
