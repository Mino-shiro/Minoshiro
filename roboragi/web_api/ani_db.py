"""
Search AniDB for anime.
"""
from difflib import SequenceMatcher
from typing import Dict, Optional

from xmltodict import parse


def process_xml(xml_string: str) -> Dict[str, dict]:
    """
    Process the xml string from the anidb data dump.

    :param xml_string: the xml string.
    
    :return: A list of dict with keys "id" and "titles".
    """
    parsed = parse(xml_string)
    lst = parsed['animetitles']['anime']
    res = {}
    for anime in (__format_anime(entry) for entry in lst):
        for name in anime['titles']:
            res[name.lower()] = anime
    return res


def get_anime(query: str, anime_list: dict) -> Optional[dict]:
    """
    Get an anime url from a list of animes.

    :param query: the search query.

    :param anime_list: the list of animes.

    :return: the anime id if found, else None.
    """
    anime = anime_list.get(query.lower())
    if anime:
        return anime
    max_ratio, match = 0, None
    matcher = SequenceMatcher(b=query.lower())
    for name, anime in anime_list.items():
        matcher.set_seq1(name.lower())
        ratio = matcher.ratio()
        if ratio > 0.99:
            return anime
        if ratio > max_ratio and ratio >= 0.85:
            max_ratio = ratio
            match = anime
    if match:
        return match


def __format_anime(anime_dict: dict) -> Optional[dict]:
    """
    Format an anime entry from the parsed xml string to a dict.

    :param anime_dict: the input anime dict.

    :return: a dict {"id": the anime id, "titles": the list of titles}
    """
    id_ = anime_dict.get('@aid')
    titles = anime_dict.get('title')
    if not titles or not id_:
        return
    try:
        title_text = [t.get('#text') for t in titles]
    except AttributeError:
        _title = titles.get('#text')
        if not _title:
            return
        title_text = [_title]
    if not title_text:
        return
    return {'id': id_, 'titles': title_text}
