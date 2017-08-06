"""
NovelUpdates.py
Handles all NovelUpdates information
"""
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote

from pyquery import PyQuery

from roboragi.session_manager import SessionManager


async def get_light_novel_url(
        session_manager: SessionManager,
        query: str,
        names: list) -> Optional[dict]:
    """
    Get ln url by search query.

    :param session_manager: the `SessionManager` instance.

    :param query: a search query.

    :param names: a list of known names

    :return: the ln url if it's found.
    """
    params = {
        's': quote(query)
    }

    async with await session_manager.get(
            'http://www.novelupdates.com/?', params=params) as resp:
        html = await resp.text()

    nu = PyQuery(html)
    ln_list = []

    for thing in nu.find('.w-blog-entry'):
        if PyQuery(thing).find('.w-blog-entry-title').text():
            data = {
                'title': PyQuery(thing).find('.w-blog-entry-title').text(),
                'url': PyQuery(thing).find('.w-blog-entry-link').attr('href')
            }
            ln_list.append(data)
    return __get_closest(query, ln_list, names)


def get_light_novel_by_id(ln_id: str) -> str:
    """
    Returns ln url by id.

    :param ln_id: a ln id.

    :return: the ln url.
    """
    return 'http://novelupdates.com/series/' + str(ln_id)


def __get_closest(query: str, ln_list: List[dict], names) -> dict:
    """
    Get the closest matching light novel by search query.

    :param query: the search term.

    :param ln_list: a list of light novels.

    :param names: a list of known names

    :return:
        Closest matching novel by search query if found else an empty dict.
    """
    synonyms_list = list(names[0])
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
