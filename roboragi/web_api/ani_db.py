"""
Search AniDB for anime.
"""
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote

from pyquery import PyQuery

from roboragi.session_manager import SessionManager


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
        async with await session_manager.get(
                'http://anisearch.outrance.pl/', params=params) as resp:
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
    return __get_closest(query, anime_list).get('url')


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


def __get_closest(query: str, anime_list: List[dict]) -> dict:
    """
    Get the closest matching anime by search query.
    :param query: the search term.
    :param anime_list: a list of animes.

    :return:
        Closest matching anime by search query if found else an empty dict.
    """
    max_ratio, match = 0, None
    matcher = SequenceMatcher(b=query.lower())
    for anime in anime_list:
        ratio = __match_max(anime, matcher)
        if ratio > max_ratio and ratio >= 0.85:
            max_ratio = ratio
            match = anime
    return match or {}


def __match_max(anime: dict, matcher: SequenceMatcher) -> float:
    """
    Get the max matched ratio for a given anime.

    :param anime: the anime.

    :param matcher: the `SequenceMatcher` with the search query as seq2.

    :return: the max matched ratio.
    """
    max_ratio = 0
    for title in anime['titles']:
        matcher.set_seq1(title['title'].lower())
        ratio = matcher.ratio()
        if ratio > max_ratio:
            max_ratio = ratio
    return max_ratio
