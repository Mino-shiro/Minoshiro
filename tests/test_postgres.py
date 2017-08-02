from datetime import datetime
from random import choice, randint
from time import time

import pytest

from roboragi import get_default_logger
from roboragi.data_controller import PostgresController
from roboragi.data_controller.enums import Medium
from tests import SCHEMA, get_pool
from tests.utils import random_dict, random_lookup_entries, random_mediums, \
    random_sites, random_str

pytestmark = pytest.mark.asyncio


@pytest.fixture()
async def postgres():
    pool = await get_pool()
    post = await PostgresController.get_instance(
        get_default_logger(), pool=pool, schema=SCHEMA
    )
    yield post
    await pool.close()


async def test_identifier(postgres: PostgresController):
    """
    Test getting and setting identifier in the lookup table.
    """
    entries = random_lookup_entries()
    for name, value in entries.items():
        for medium, site_vals in value.items():
            for site, id_ in site_vals.items():
                await postgres.set_identifier(name, medium, site, id_)
            res = await postgres.get_identifier(name, medium)
            assert res == value.get(medium)


async def test_mal_title(postgres: PostgresController):
    """
    Test getting and setting mal titles.
    """
    ids = set(random_str() for _ in range(randint(10, 20)))
    for id_ in ids:
        mediums = random_mediums()
        for med in mediums:
            title = random_str()
            await postgres.set_mal_title(id_, med, title)
            assert await postgres.get_mal_title(id_, med) == title
            new = f'{title} asopdhsahdas'
            await postgres.set_mal_title(id_, med, new)
            assert await postgres.get_mal_title(id_, med) == new


async def test_data(postgres: PostgresController):
    """
    Test getting and setting medium data. We will only run this test on the
    `anime` table since all tables have the same structures.
    """
    ids = set(random_str() for _ in range(randint(5, 15)))
    names = [f'name {i} {random_str()}' for i in ids]
    for id_, name in zip(ids, names):
        tmp = {}
        sites = random_sites()
        for site in sites:
            data = random_dict()
            tmp[site] = data
            await postgres.set_identifier(name, Medium.ANIME, site, id_)
            await postgres.set_medium_data(id_, Medium.ANIME, site, data)
        assert await postgres.get_medium_data(name, Medium.ANIME) == tmp
        sql = """
        UPDATE robotesting.anime
        SET cachetime=$1
        WHERE id=$2 AND site=$3
        """

        updated_site = choice(sites)
        await postgres.pool.execute(
            sql, datetime.fromtimestamp(time() - 88888),
            id_, updated_site.value
        )
        new_data = await postgres.get_medium_data(name, Medium.ANIME)
        assert not new_data or updated_site not in new_data
