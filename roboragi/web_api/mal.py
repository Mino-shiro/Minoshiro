"""
Search MAL for anime/manga/lightnovels.
"""

import xml.etree.cElementTree as ET
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote

from roboragi.session_manager import SessionManager


async def get_entry_details(
        session_manager: SessionManager,
        header_info: dict,
        medium: str,
        query: str,
        thing_id: str=None) -> Optional[dict]:
    """
    Get the details of an thing by search query.
    :param query: the search term.
    :param thing_id: thing id.
    :return: dict with thing info.
    """
    if medium == 'ln' or medium == 'manga':
        url = f'https://myanimelist.net/api/manga/search.xml?q={quote(query)}'
    else:
        url = f'https://myanimelist.net/api/anime/search.xml?q={quote(query)}'
    try:
        async with await session_manager.get(
                url, headers=header_info) as resp:
            html = await resp.text()
    except Exception as e:
        session_manager.logger.warn(str(e))
        return
    thing_list = []
    for thing in ET.fromstring(html).findall('./entry'):
        synonyms = None
        if thing.find('synonyms').text is not None:
            synonyms = thing.find('synonyms').text.split(";")
        if medium == 'anime':
            data = {
                'id': thing.find('id').text,
                'title': thing.find('title').text,
                'english': thing.find('english').text,
                'synonyms': synonyms,
                'episodes': thing.find('episodes').text,
                'type': thing.find('type').text,
                'status': thing.find('status').text,
                'start_date': thing.find('start_date').text,
                'end_date': thing.find('end_date').text,
                'synopsis': thing.find('synopsis').text,
                'image': thing.find('image').text
            }
        else:
            data = {
                'id': thing.find('id').text,
                'title': thing.find('title').text,
                'english': thing.find('english').text,
                'synonyms': synonyms,
                'chapters': thing.find('chapters').text,
                'volumes': thing.find('volumes').text,
                'type': thing.find('type').text,
                'status': thing.find('status').text,
                'start_date': thing.find('start_date').text,
                'end_date': thing.find('end_date').text,
                'synopsis': thing.find('synopsis').text,
                'image': thing.find('image').text
            }
        thing_list.append(data)

    if thing_id:
        return __get_thing_by_id(thing_id, thing_list)
    else:
        return __get_closest(query.strip(), thing_list)


def __get_closest(query: str, thing_list: List[dict]) -> dict:
    """
    Get the closest matching anime by search query.
    :param query: the search term.
    :param thing_list: a list of animes.
    :return: Closest matching anime by search query if found
                else an empty dict.
    """
    max_ratio, match = 0, None
    matcher = SequenceMatcher(b=query.lower().strip())
    for thing in thing_list:
        ratio = __match_max(thing, matcher)
        if ratio > max_ratio and ratio >= 0.90:
            max_ratio = ratio
            match = thing
    return match or {}


def __match_max(thing: dict, matcher: SequenceMatcher) -> float:
    """
    Get the max matched ratio for a given thing.
    :param thing: the thing.
    :param matcher: the `SequenceMatcher` with the search query as seq2.
    :return: the max matched ratio.
    """
    max_ratio = 0
    matcher.set_seq1(thing['title'].lower())
    ratio = matcher.ratio()
    if ratio > max_ratio:
        max_ratio = ratio
    if thing['synonyms']:
        for synonym in thing['synonyms']:
            matcher.set_seq1(synonym.lower())
            ratio = matcher.ratio()
            if ratio > max_ratio:
                max_ratio = ratio
    return max_ratio


def __get_thing_by_id(thing_id: str, thing_list: List[dict]) -> dict:
    """
    Get the max matched ratio for a given thing.
    :param thing_id: the id that we are looking for.
    :param thing_list: the `SequenceMatcher` with the search query as seq2.
    :return: the max matched ratio.
    """
    try:
        for thing in thing_list:
            if int(thing['id']) == int(thing_id):
                return thing

        return {}
    except Exception:
        return {}
