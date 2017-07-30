"""
Search AniDB for anime.
"""
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote

from pyquery import PyQuery

from session_manager import SessionManager


async def get_anime_url(
        session_manager: SessionManager, query: str) -> Optional[str]:
    """
    Get anime url by search query.
    :param session_manager: the `SessionManager` instance.
    :param query: a search query.
    :return: the anime url if it's found.
    """
    params = {
        'task': 'search',
        'query': quote(query)
    }
    try:
        resp = await session_manager.get(
            'http://anisearch.outrance.pl/', params=params
        )
        async with resp:
            html = await resp.read()
        pq = PyQuery(html)
    except Exception as e:
        session_manager.logger.warn(str(e))
        return

    anime_list = [
        {'titles': titles, 'url': f'http://anidb.net/a{anime.attrib["aid"]}'}
        for titles, anime in
        [(__get_title_info(anime), anime) for anime in pq('animetitles anime')]
        if titles
    ]
    closest = __get_closest(query, anime_list)
    return closest['url'] if closest else None


def __get_title_info(anime) -> List[dict]:
    """
    Generate anime title info by anime.
    :param anime: the anime object from `PyQuery`
    :return: A list of anime title info.
    """
    return [
        {'title': title.text(), 'lang': title.attr['lang']}
        for title in PyQuery(anime).find('title').items()
    ]


def __get_closest(query: str, anime_list: list):
    """
    Get the closest matching `anime` object by search term.
    :param query: the search term.
    :param anime_list: a list of `anime` objects from `PyQuery`
    :return: the closest matching `anime` object by title.
    """
    safe_matches = []
    unsafe_matches = []
    query = query.lower()
    matcher = SequenceMatcher()
    for anime in anime_list:
        for title in anime['titles']:
            matcher.set_seqs(title['title'].lower(), query)
            ratio = matcher.ratio()
            if ratio >= 0.85 and title['lang'].lower() in ('x-jat', 'en'):
                safe_matches.append((anime, ratio))
            elif ratio >= 0.85:
                unsafe_matches.append((anime, ratio))
    if safe_matches:
        safe_matches.sort(key=lambda x: x[1], reverse=True)
        return safe_matches[0][0]
    if unsafe_matches:
        unsafe_matches.sort(key=lambda x: x[1], reverse=True)
        return unsafe_matches[0][0]
