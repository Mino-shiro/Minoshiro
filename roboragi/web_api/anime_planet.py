"""
Retrieve anime info from AnimePlanet.
"""
from collections import deque
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote

from pyquery import PyQuery

from roboragi.session_manager import SessionManager


def sanitize_search_text(text: str) -> str:
    """
    Sanitize text for Anime-Planet use.
    :param text: the text to be escaped.
    :return: the escaped text.
    """
    return text.replace('(TV)', 'TV')


async def get_anime_url(
        session_manager: SessionManager, query: str) -> Optional[str]:
    """
    Get anime url by search query.
    :param session_manager: the `SessionManager` instance.
    :param query: a search query.
    :return: the anime url if it's found.
    """
    query = sanitize_search_text(query)
    params = {
        'name': quote(query)
    }
    async with await session_manager.get(
            "http://www.anime-planet.com/anime/all?",
            params=params) as resp:
        html = await resp.text()
    ap = PyQuery(html)

    if ap.find('.cardDeck.pure-g.cd-narrow[data-type="anime"]'):
        anime_list = []
        for entry in ap.find('.card.pure-1-6'):
            anime = {
                'title': PyQuery(entry).find('h4').text(),
                'url': f'''http://www.anime-planet.com{PyQuery(entry).find("a").attr("href")}'''
            }
            anime_list.append(anime)
        return __get_closest(query, anime_list).get('url')
    else:
        return ap.find("meta[property='og:url']").attr('content')


async def get_manga_url(
        session_manager: SessionManager,
        query: str,
        author_name: str=None) -> Optional[str]:
    """
    Get manga url by search query.
    :param session_manager: the `SessionManager` instance.
    :param query: a search query.
    :return: the anime url if it's found.
    """
    params = {
            'name': quote(query)
        }
    if author_name:
        params['author'] = quote(author_name)
        async with await session_manager.get(
                "http://www.anime-planet.com/manga/all?",
                params=params) as resp:
            html = await resp.text()
        if "No results found" in html:
            rearranged_author_names = deque(
                author_name.split(' '))
            rearranged_author_names.rotate(-1)
            rearranged_name = ' '.join(rearranged_author_names)
            params['author'] = quote(rearranged_name)
            async with await session_manager.get(
                    "http://www.anime-planet.com/manga/all?",
                    params=params) as resp:
                html = await resp.text()
    else:
        async with await session_manager.get(
                "http://www.anime-planet.com/manga/all?",
                params=params) as resp:
            html = await resp.text()
    ap = PyQuery(html)


    if ap.find('.cardDeck.pure-g.cd-narrow[data-type="manga"]'):
        manga_list = []
        for entry in ap.find('.card.pure-1-6'):
            anime = {
                'title': PyQuery(entry).find('h4').text(),
                'url': f'''http://www.anime-planet.com{PyQuery(entry).find("a").attr("href")}'''
            }
            manga_list.append(anime)

            if author_name:
                author_name = author_name.lower().split(' ')
                for manga in manga_list:
                    manga['title'] = manga['title'].lower()
                    for name in author_name:
                        manga['title'] = manga['title'].replace(name, '')
                    manga['title'] = manga['title'].replace('(', '')
                    manga['title'] = manga['title'].replace(')', '').strip()

        return __get_closest(query, manga_list).get('url')
    else:
        return ap.find("meta[property='og:url']").attr('content')
    pass


def get_anime_url_by_id(anime_id: str) -> str:
    """
    Returns anime url by id.
    :param anime_id: an anime id.
    :return: the anime url.
    """
    return 'http://www.anime-planet.com/anime/' + str(anime_id)


def get_manga_url_by_id(manga_id: str) -> str:
    """
    Returns manga url by id.
    :param manga_id: a manga id.
    :return: the manga url.
    """
    return 'http://www.anime-planet.com/manga/' + str(manga_id)


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
        matcher.set_seq1(anime['title'].lower())
        ratio = matcher.ratio()
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
    print(anime)
    for title in anime['titles']:
        matcher.set_seq1(title['title'].lower())
        ratio = matcher.ratio()
        if ratio > max_ratio:
            max_ratio = ratio
    return max_ratio
