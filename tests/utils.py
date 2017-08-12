from itertools import product
from random import choice, randint, sample
from string import printable
from typing import Dict, List

from minoshiro.enums import Medium, Site

__all__ = ['random_sites', 'random_mediums', 'random_str',
           'random_dict', 'random_lookup_entries']


def __random_enum_members(enum) -> list:
    """
    Get a list of unique random members from an enum.
    :param enum: the enum.
    :return: a list of unique random members from an enum
    """
    return sample(list(enum), randint(1, len(enum)))


def random_sites() -> List[Site]:
    """
    Get a list of unique random sites.
    :return: a list of random sites.
    """
    return __random_enum_members(Site)


def random_mediums() -> List[Medium]:
    """
    Get a list of unique random mediums.
    :return: a list of random mediums.
    """
    return __random_enum_members(Medium)


def random_str() -> str:
    """
    Generate a random string.
    :return: the random string.
    """
    length = randint(1, 15)
    return f'test_{"".join(choice(printable) for _ in range(length))}'


def random_dict(depth=0):
    """
    Generate a random dict.
    :return: the random dict.
    """
    rand_lst = lambda: [random_str() for _ in range(randint(5, 10))]
    if depth >= 2:
        return choice([random_str(), rand_lst()])
    res = {}
    for key in set(rand_lst()):
        type_ = choice([0, 1, 2])
        if type_ == 0:
            res[key] = random_str()
        elif type_ == 1:
            res[key] = [random_dict(depth + 1) for _ in range(randint(5, 10))]
        else:
            res[key] = random_dict(depth + 1)
    return res


def random_lookup_entries() -> Dict[str, Dict[Medium, Dict[Site, str]]]:
    """
    Return a dict of random look up entries.
    :return: A dict of {lookup name: {(site, medium): id}}
    """
    mediums = random_mediums()
    sites = random_sites()
    names = set(random_str() for _ in range(randint(5, 15)))
    res = {}
    for name in names:
        res[name] = {}
        for site, medium in product(sites, mediums):
            if medium not in res[name]:
                res[name][medium] = {}
            res[name][medium][site] = random_str()
    return res
