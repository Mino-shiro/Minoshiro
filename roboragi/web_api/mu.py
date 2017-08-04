"""
MU.py
Handles all MangaUpdates information
"""
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote

from pyquery import PyQuery

from roboragi.session_manager import SessionManager


async def get_manga_url(
        session_manager: SessionManager, query: str) -> Optional[str]:
    """
    Get manga url by search query.
    :param session_manager: the `SessionManager` instance.
    :param query: a search query.
    :return: the manga url if it's found.
    """
    params = {
        'search': quote(query)
    }
    try:
        async with await session_manager.get(
                'https://mangaupdates.com/series.html', params=params) as resp:
            html = await resp.text()
            print(html)
    except Exception as e:
        session_manager.logger.warn(str(e))
        return
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
    return __get_closest(query, manga_list)


def get_manga_url_by_id(manga_id) -> str:
    """
    Returns manga url by id.
    :param manga_id: a manga id.
    :return: the manga url.
    """
    return 'https://www.mangaupdates.com/series.html?id=' + str(manga_id)


def __get_closest(query: str, manga_list: List[dict]) -> dict:
    """s
    Get the closest matching light novel by search query.
    :param query: the search term.
    :param manga_list: a list of light novels.
    :return:
        Closest matching manga by search query if found else an empty dict.
    """
    max_ratio, match = 0, None
    matcher = SequenceMatcher(b=query.lower().strip())
    for ln in manga_list:
        title = ln['title'].lower()
        matcher.set_seq1(title)
        ratio = matcher.ratio()
        if ratio > max_ratio and ratio >= 0.85:
            max_ratio = ratio
            match = ln
    return match or {}
