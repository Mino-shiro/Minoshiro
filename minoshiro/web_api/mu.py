"""
MU.py
Handles all MangaUpdates information
"""
from difflib import SequenceMatcher
from typing import List
from urllib.parse import quote

from pyquery import PyQuery


async def get_manga_url(session_manager, query, names: list, timeout=3) -> dict:
    """
    Get manga url by search query.

    :param session_manager: the `SessionManager` instance.

    :param query: a search query.

    :param names: a list of known names

    :return: the manga url if it's found.
    """
    params = {
        'search': quote(query)
    }

    async with await session_manager.get(
            'https://mangaupdates.com/series.html', params=params, timeout=timeout) as resp:
        html = await resp.text()

    mu = PyQuery(html)
    manga_list = []
    for thing in mu.find('.series_rows_table tr'):
        if PyQuery(thing).find('.col1').text():
            data = {
                'title': PyQuery(thing).find('.col1').text(),
                'url': PyQuery(thing).find('.col1 a').attr('href'),
                'genres': PyQuery(thing).find('.col2').text(),
                'year': PyQuery(thing).find('.col3').text(),
                'rating': PyQuery(thing).find('.col4').text()
            }
            manga_list.append(data)
    return __get_closest(query, manga_list, names)


def get_manga_url_by_id(manga_id) -> str:
    """
    Returns manga url by id.

    :param manga_id: a manga id.

    :return: the manga url.
    """
    return 'https://www.mangaupdates.com/series.html?id=' + str(manga_id)


def __get_closest(query: str, manga_list: List[dict], names) -> dict:
    """
    Get the closest matching manga by search query.

    :param query: the search term.

    :param manga_list: a list of mangas.

    :param names: a list of known names

    :return:
        Closest matching manga by search query if found else an empty dict.
    """
    synonyms_list = names
    synonyms_list.insert(0, query)
    match = None
    for name in synonyms_list:
        max_ratio = 0
        matcher = SequenceMatcher(b=name.lower())
        for manga in manga_list:
            matcher.set_seq1(manga['title'].lower())
            ratio = matcher.ratio()
            if ratio > max_ratio and ratio >= 0.85:
                max_ratio = ratio
                match = manga
        if match:
            break
    return match or {}
