"""
Search LNDB for anime.
"""
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote

from pyquery import PyQuery

from roboragi.session_manager import SessionManager


async def get_light_novel_url(
        session_manager: SessionManager, query: str) -> Optional[str]:
    """
    Get ln url by search query.
    :param session_manager: the `SessionManager` instance.
    :param query: a search query.
    :return: the ln url if it's found.
    """
    query = query.replace(' ', '+')
    params = {
        'text': quote(query)
    }
    try:
        async with await session_manager.get(
                'http://lndb.info/search?',
                params=params) as resp:
            html = await resp.text()
            if 'light_novel' in html.url:
                return html.url

        lndb = PyQuery(html)
    except Exception as e:
            session_manager.logger.warn(str(e))
            return
    ln_list = []
    for thing in lndb.find('#bodylightnovelscontentid table tr'):
        if PyQuery(thing).find('a').text():
            data = {
                'title': PyQuery(thing).find('a').text(),
                'url': PyQuery(thing).find('a').attr('href')
            }
            ln_list.append(data)

    return __get_closest(query, ln_list).get('url')


def get_light_novel_by_id(ln_id: str) -> str:
    """
    Returns ln url by id.
    :param ln_id: a ln id.
    :return: the ln url.
    """
    return 'http://lndb.info/light_novel/' + str(ln_id)


def __get_closest(query: str, ln_list: List[dict]) -> dict:
    """
    Get the closest matching light novel by search query.
    :param query: the search term.
    :param anime_list: a list of light novels.

    :return:
        Closest matching anime by search query if found else an empty dict.
    """
    max_ratio, match = 0, None
    matcher = SequenceMatcher(b=query.lower())
    for ln in ln_list:
        ratio = matcher.set_seq1(ln['title'].lower())
        if ratio > max_ratio and ratio >= 0.85:
            max_ratio = ratio
            match = ln
    return match or {}
