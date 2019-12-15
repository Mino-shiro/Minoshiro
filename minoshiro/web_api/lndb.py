"""
Search LNDB for anime.
"""
from difflib import SequenceMatcher
from typing import List, Optional

from aiohttp_wrapper import SessionManager
from pyquery import PyQuery


async def get_light_novel_url(
        session_manager: SessionManager,
        query, names, timeout=3) -> Optional[dict]:
    """
    Get ln url by search query.

    :param session_manager: the `SessionManager` instance.

    :param query: a search query.

    :param names: a list of known names

    :param timeout:
        The timeout in seconds for each HTTP request. Defualt is 3.

    :return: the ln url if it's found.
    """
    query = query.replace(' ', '+')
    params = f'text={query}'

    async with await session_manager.get(
            'http://lndb.info/search?',
            params=params, timeout=timeout) as resp:
        if 'light_novel' in str(resp.url):
            s = (str(resp.url)).rsplit('/', 1)
            title = s[-1].replace('_', ' ')
            return {'title': title, 'url': str(resp.url)}
        html = await resp.text()
    lndb = PyQuery(html)

    ln_list = []
    for thing in lndb.find('#bodylightnovelscontentid table tr'):
        if PyQuery(thing).find('a').text():
            data = {
                'title': PyQuery(thing).find('a').text(),
                'url': PyQuery(thing).find('a').attr('href')
            }
            ln_list.append(data)
    return __get_closest(query, ln_list, names)


def get_light_novel_by_id(ln_id) -> str:
    """
    Returns a light novel url by id.

    :param ln_id: a ln id.

    :return: the ln url
    """
    return f'http://lndb.info/light_novel/{ln_id!s}'


def __get_closest(query: str, ln_list: List[dict], names) -> dict:
    """
    Get the closest matching light novel by search query.

    :param query: the search term.

    :param ln_list: a list of light novels.

    :param names: a list of known names

    :return:
        Closest matching novel by search query if found else an empty dict.
    """
    synonyms_list = names
    synonyms_list.insert(0, query)
    match = None
    for name in synonyms_list:
        max_ratio = 0
        matcher = SequenceMatcher(b=name.lower())
        for ln in ln_list:
            matcher.set_seq1(ln['title'].lower())
            ratio = matcher.ratio()
            if ratio > max_ratio and ratio >= 0.85:
                max_ratio = ratio
                match = ln
        if match:
            break
    return match or {}
