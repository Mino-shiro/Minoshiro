"""
Retrieve anime info from AnimePlanet.
"""
from collections import deque
from difflib import SequenceMatcher
from itertools import chain
from typing import List, Optional
from urllib.parse import quote

from pyquery import PyQuery


def sanitize_search_text(text: str) -> str:
    """
    Sanitize text for Anime-Planet use.
    :param text: the text to be escaped.
    :return: the escaped text.
    """
    return text.replace('(TV)', 'TV')


async def get_anime_url(session_manager, query, names: list,
                        timeout=3) -> Optional[str]:
    """
    Get anime url by search query.

    :param session_manager: the `SessionManager` instance.

    :param query: a search query.

    :param names: a list of synonyms

    :param timeout:
        The timeout in seconds for each HTTP request. Defualt is 3.

    :return: the anime url if it's found.
    """
    query = sanitize_search_text(query)
    params = {'name': quote(query)}
    async with await session_manager.get(
            "http://www.anime-planet.com/anime/all?",
            params=params, timeout=timeout) as resp:
        html = await resp.text()
    ap = PyQuery(html)
    if ap.find('.cardDeck.pure-g.cd-narrow[data-type="anime"]'):
        anime_list = []
        for entry in ap.find('.card.pure-1-6'):
            anime_list.append({
                'title': PyQuery(entry).find('h4').text(),
                'url': (f'http://www.anime-planet.com'
                        f'{PyQuery(entry).find("a").attr("href")}')
            })
        return __get_closest(query, anime_list, names).get('url')
    return ap.find("meta[property='og:url']").attr('content')


async def get_manga_url(session_manager, query,
                        names: list, author_name=None,
                        timeout=3) -> Optional[str]:
    """
    Get manga url by search query.

    :param session_manager: the `SessionManager` instance.

    :param query: a search query.

    :param names: a list of known names

    :param author_name: name for the manga author name

    :param timeout:
        The timeout in seconds for each HTTP request. Defualt is 3.

    :return: the anime url if it's found.
    """
    params = {'name': quote(query)}
    if author_name:
        params['author'] = quote(author_name)
        async with await session_manager.get(
                "http://www.anime-planet.com/manga/all?",
                params=params, timeout=timeout) as resp:
            html = await resp.text()
        if "No results found" in html:
            rearranged_author_names = deque(
                author_name.split(' '))
            rearranged_author_names.rotate(-1)
            rearranged_name = ' '.join(rearranged_author_names)
            params['author'] = quote(rearranged_name)
            async with await session_manager.get(
                    "http://www.anime-planet.com/manga/all?",
                    params=params, timeout=timeout) as resp:
                html = await resp.text()
    else:
        async with await session_manager.get(
                "http://www.anime-planet.com/manga/all?",
                params=params, timeout=timeout) as resp:
            html = await resp.text()
    ap = PyQuery(html)

    if ap.find('.cardDeck.pure-g.cd-narrow[data-type="manga"]'):
        manga_list = []
        for entry in ap.find('.card.pure-1-6'):
            anime = {
                'title': PyQuery(entry).find('h4').text(),
                'url': (f'http://www.anime-planet.com'
                        f'{PyQuery(entry).find("a").attr("href")}')
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

        return __get_closest(query, manga_list, names).get('url')
    else:
        return ap.find("meta[property='og:url']").attr('content')


def get_anime_url_by_id(anime_id) -> str:
    """
    Returns anime url by id.

    :param anime_id: an anime id.

    :return: the anime url.
    """
    return 'http://www.anime-planet.com/anime/' + str(anime_id)


def get_manga_url_by_id(manga_id) -> str:
    """
    Returns manga url by id.

    :param manga_id: a manga id.

    :return: the manga url.
    """
    return 'http://www.anime-planet.com/manga/' + str(manga_id)


def __get_closest(query: str, anime_list: List[dict], names) -> dict:
    """
    Get the closest matching anime by search query.

    :param query: the search term.

    :param anime_list: a list of anime.

    :param names: a list of known names

    :return:
        Closest matching anime by search query if found else an empty dict.
    """
    for name in chain((query,), names):
        matcher = SequenceMatcher(b=name.lower())
        for anime in anime_list:
            matcher.set_seq1(anime['title'].lower())
            ratio = matcher.ratio()
            if ratio >= 0.85:
                return anime
    return {}
