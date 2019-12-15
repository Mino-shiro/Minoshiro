from difflib import SequenceMatcher
from typing import List, Optional

from aiohttp_wrapper import SessionManager

from minoshiro.enums import Medium
from minoshiro.helpers import filter_anime_manga

__escape_table = {
    '&': ' ',
    "\'": "\\'",
    '\"': '\\"',
    '/': ' ',
    '-': ' '
    # '!': '\!'
}

__base_url = 'https://graphql.anilist.co'


def escape(text: str) -> str:
    """
    Escape text for ani list use.

    :param text: the text to be escaped.

    :return: the escaped text.
    """
    return ''.join(__escape_table.get(c, c) for c in text)


def get_closest(query: str, thing_list: List[dict]) -> dict:
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
        ratio = match_max(thing, matcher)
        if ratio > max_ratio and ratio >= 0.90:
            max_ratio = ratio
            match = thing
    return match or {}


def match_max(thing: dict, matcher: SequenceMatcher) -> float:
    """
    Get the max matched ratio for a given thing.

    :param thing: the thing.

    :param matcher: the `SequenceMatcher` with the search query as seq2.

    :return: the max matched ratio.
    """
    thing_name_list = []
    max_ratio = 0
    if 'title' in thing and thing['title'] is not None:
        for title in thing['title']:
            if thing['title'][title]:
                thing_name_list.append(thing['title'][title].lower())

    if 'synonyms' in thing:
        for synonym in thing['synonyms']:
            thing_name_list.append(synonym.lower())

    for name in thing_name_list:
        matcher.set_seq1(name.lower())
        ratio = matcher.ratio()
        if 'one shot' in thing['type'].lower():
            ratio -= .05
        if ratio > max_ratio:
            max_ratio = ratio
    return max_ratio


async def get_entry_by_id(session_manager: SessionManager,
                          medium: Medium, entry_id: str,
                          timeout=3) -> dict:
    """
    Get the full details of an thing by id

    :param session_manager: session manager object

    :param medium: medium to search for

    :param entry_id: thing id.

    :param timeout:
        The timeout in seconds for each HTTP request. Defualt is 3.

    :return: dict with thing info.
    """
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = {
        'query': (__get_query_string(medium, entry_id)).replace('\n', '')
    }
    async with await session_manager.post(
            __base_url, headers=headers, json=data, timeout=timeout) as resp:
        js = await resp.json()

    return js['data']['Media']


async def get_entry_details(session_manager: SessionManager,
                            medium: Medium, query: str,
                            timeout=3) -> Optional[dict]:
    """
    Get the details of an thing by search query.

    :param session_manager: session manager object

    :param medium: medium to search for 'anime', 'manga', 'novel'

    :param query: the search term.

    :param timeout:
        The timeout in seconds for each HTTP request. Defualt is 3.

    :return: dict with thing info.
    """
    if medium not in (Medium.ANIME, Medium.MANGA, Medium.LN):
        raise ValueError('Only Anime, Manga and LN are supported.')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = {
        'query': f'{__get_query_string(medium, query, True)} }}'
    }
    async with await session_manager.post(
            __base_url, headers=headers, json=data, timeout=timeout) as resp:
        thing = await resp.json()
    closest_entry = get_closest(query, thing['data']['Page']['media'])
    return closest_entry


async def get_page_by_popularity(session_manager, medium: Medium,
                                 page: int, timeout=10) -> Optional[dict]:
    """
    Gets the 40 entries in the medium from specified page.

    :param session_manager: the session manager.

    :param medium: medium 'manga' or 'anime'.

    :param page: page we want info from

    :param timeout:
        The timeout in seconds for each HTTP request. Defualt is 10.

    :return: dict of page
    """
    med_str = filter_anime_manga(medium)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = {
        'query': (f'''
            query {{
                Page (page: {page}, perPage: 40) {{
                    media (type: {med_str.upper()} sort: POPULARITY_DESC ) {{
                        title {{
                        romaji
                        english
                        native
                        userPreferred
                        }}
                    synonyms
                    id
                    url: siteUrl
                    type
                    format
                    }}
                }}
                }}''').replace('\n', '')
    }
    async with await session_manager.post(
            __base_url, headers=headers, json=data, timeout=timeout) as resp:
        thing = await resp.json()
    return thing['data']['Page']['media']


def __get_query_string(medium, query, search=False) -> str:
    med_str = 'ANIME' if medium == Medium.ANIME else 'MANGA'
    if search:
        full_str = f'''Page (page: 1, perPage: 40) {{
                media (search: "{query}" type: {med_str})'''
        if medium == Medium.LN:
            full_str = f'''Page (page: 1, perPage: 40) {{
                media (search: "{query}" type: {med_str} format: NOVEL)'''
    else:
        full_str = f'Media (id: {query}, type: {med_str})'
    query = f'''
    query {{
        {full_str} {{
            id
            idMal
            title {{
            romaji
            english
            native
            }}
            url: siteUrl
            startDate {{
            year
            month
            day
            }}
            endDate {{
            year
            month
            day
            }}
            coverImage {{
            large
            medium
            }}
            bannerImage
            format
            type
            status
            episodes
            chapters
            volumes
            season
            description
            averageScore
            meanScore
            genres
            synonyms
            nextAiringEpisode {{
            airingAt
            timeUntilAiring
            episode
            }}
        }}
    }}'''
    return query
