"""
Search AniDB for anime.
"""
from difflib import SequenceMatcher
from typing import List, Optional

from xmltodict import parse

from roboragi.data import data_path
from roboragi.session_manager import SessionManager


def write_timestamp(time_stamp: int):
    with data_path.joinpath('.anidb_time').open('w+') as time_file:
        time_file.write(str(time_stamp))


async def get_data_dump(session_manager: SessionManager) -> str:
    """
    Get the data dump from anidb and write it to file.
    :param session_manager: the `SessionManager` instance.
    """
    url = 'http://anidb.net/api/anime-titles.xml.gz'
    async with await session_manager.get(url) as resp:
        return await resp.read()


def process_xml(xml_string: str) -> List[dict]:
    """
    Process the xml string from the anidb data dump.
    :param xml_string: the xml string.
    :return: A list of dict with keys "id" and "titles".
    """
    parsed = parse(xml_string)
    lst = parsed['animetitles']['anime']
    return [
        anime for anime in
        (__format_anime(entry) for entry in lst)
        if anime
    ]


def get_anime_url(query: str, anime_list: List[dict]) -> Optional[str]:
    """
    Get an anime url from a list of animes.
    :param query: the search query.
    :param anime_list: the list of animes.
    :return: the anime url if found, else None.
    """
    max_ratio, match = 0, None
    matcher = SequenceMatcher(b=query.lower())
    for anime in anime_list:
        ratio = __match_max(anime, matcher)
        if ratio > max_ratio and ratio >= 0.85:
            max_ratio = ratio
            match = anime
    if match:
        return (f'https://anidb.net/perl-bin/'
                f'animedb.pl?show=anime&aid={match["id"]}')


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


def __match_max(anime: dict, matcher: SequenceMatcher) -> float:
    """
    Get the max matched ratio for a given anime.

    :param anime: the anime.

    :param matcher: the `SequenceMatcher` with the search query as seq2.

    :return: the max matched ratio.
    """
    max_ratio = 0
    for title in anime['titles']:
        matcher.set_seq1(title.lower())
        ratio = matcher.ratio()
        if ratio > max_ratio:
            max_ratio = ratio
    return max_ratio
