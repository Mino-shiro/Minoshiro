"""
NovelUpdates.py
Handles all NovelUpdates information
"""
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote
from pyquery import PyQuery
from session_manager import SessionManager


async def get_light_novel_url(
        session_manager: SessionManager, query: str) -> Optional[str]:
    """
    Get ln url by search query.
    :param session_manager: the `SessionManager` instance.
    :param query: a search query.
    :return: the ln url if it's found.
    """
    params = {
        's': quote(query)
    }
    try:
        async with await session_manager.get(
                'http://www.novelupdates.com/?', params=params) as resp:
            html = await resp.text()
    except Exception as e:
        session_manager.logger.warn(str(e))
        return
    nu = PyQuery(html)
    ln_list = []

    for thing in nu.find('.w-blog-entry'):
        if PyQuery(thing).find('.w-blog-entry-title').text():
            data = {
                'title': PyQuery(thing).find('.w-blog-entry-title').text(),
                'url': PyQuery(thing).find('.w-blog-entry-link').attr('href')
            }
            ln_list.append(data)
    return __get_closest(query, ln_list).get('url')


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
