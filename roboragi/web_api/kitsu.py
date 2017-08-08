"""
Handles all Kitsu api calls
"""
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote

from roboragi.data_controller.enums import Medium
from roboragi.session_manager import SessionManager


def parse_resp(entry, medium):
    anime_list = []

    medium_str = 'anime' if medium == Medium.ANIME else 'manga'
    attributes = entry.get('attributes', {})
    titles = attributes.get('titles', {})
    slug = attributes.get('slug')

    anime_list.append(
        {
            'id': entry.get('id'),
            'url': (
                f'https://kitsu.io/{medium_str}/{slug}' if slug else None
            ),
            'title_romaji': titles.get('en_jp'),
            'title_english': titles.get('en'),
            'title_japanese': titles.get('ja_jp'),
            'synonyms': set(attributes.get('abbreviatedTitles', [])),
            'description': attributes.get('synopsis')
        }
    )

    if medium == Medium.ANIME:
        anime_list[-1]['episode_count'] = (
            int(attributes.get('episodeCount', 0))
        )
        anime_list[-1]['nsfw'] = attributes.get('nsfw')

        anime_list[-1]['type'] = attributes.get('showType')

    elif medium in [Medium.MANGA, Medium.LN]:
        anime_list[-1]['volume_count'] = (
            int(attributes.get('volumeCount', 0))
        )
        anime_list[-1]['chapter_count'] = (
            int(entry['attributes']['chapterCount'])
            if entry['attributes']['chapterCount'] else None
        )
        anime_list[-1]['type'] = entry['attributes']['mangaType']


    return_list = []
    for entry in anime_list:
        if medium == Medium.MANGA:
            if entry['type'].lower() != 'novel':
                return_list.append(entry)
        if medium == Medium.LN:
            if entry['type'].lower() == 'novel':
                return_list.append(entry)
        else:
            return_list.append(entry)
    return anime_list


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
        if ratio == 1.0:
            return thing
        if ratio > max_ratio and ratio >= 0.90:
            max_ratio = ratio
            match = thing
    return match


def match_max(thing: dict, matcher: SequenceMatcher) -> float:
    """
    Get the max matched ratio for a given thing.

    :param thing: the thing.

    :param matcher: the `SequenceMatcher` with the search query as seq2.

    :return: the max matched ratio.
    """
    attributes = thing['attributes']
    thing_name_list = []
    max_ratio = 0
    if 'canonicalTitle' in attributes:
        thing_name_list.append(attributes['canonicalTitle'].lower())

    if 'titles' in attributes and attributes['titles'] is not None:
        for title in attributes['titles']:
            thing_name_list.append(attributes['titles'][title].lower())

    if attributes.get('abbreviatedTitles'):
        for title in attributes['abbreviatedTitles']:
            thing_name_list.append(title.lower())
    for name in thing_name_list:
        matcher.set_seq1(name.lower())
        ratio = matcher.ratio()
        if 'one shot' in thing['type'].lower():
            ratio = ratio - .05
        if ratio > max_ratio:
            max_ratio = ratio
    return max_ratio


class Kitsu:
    def __init__(self, session_manager: SessionManager, client_id: str,
                 client_secret: str):
        """
        Init the class.
        :param client_id: the Anilist client id.
        :param client_secret: the Anilist client secret.
        """
        self.access_token = None
        # temporary, as application registration isn't implemented yet
        self.client_id = ('dd031b32d2f56c990b1425efe6c42ad847'
                          'e7fe3ab46bf1299f05ecd856bdb7dd')
        self.client_secret = ('54d7307928f63414defd96399fc31ba84'
                              '7961ceaecef3a5fd93144e960c0e151')
        self.session_manager = session_manager
        self.base_url = 'https://kitsu.io/api/edge/'

    async def search_entries(self, medium: Medium,
                             query: str) -> Optional[dict]:
        """
        Get the details of an thing by search query.

        :param medium: medium to search for 'anime', 'manga', 'novel'

        :param query: the search term.

        :return: dict with thing info.
        """
        medium_str = 'anime' if medium == Medium.ANIME else 'manga'
        url = f'{self.base_url}/{medium_str}?filter[text]={quote(query)}'
        headers = {
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/vnd.api+json'
        }

        js = await self.session_manager.get_json(
            url, headers=headers, content_type='application/vnd.api+json'
        )
        if js:
            closest_entry = get_closest(query, js['data'])
            if closest_entry:
                results = parse_resp(closest_entry, medium)
                return results[0]

    async def get_entry_by_id(self, medium: Medium, id_: str) -> Optional[dict]:
        """
        Get the details of a thing by id.

        :param medium: medium to search for 'anime', 'manga', 'novel'

        :param id_: the id.

        :return: dict with thing info.
        """
        medium_str = 'anime' if medium == Medium.ANIME else 'manga'
        url = f'{self.base_url}/{medium_str}?filter[slug]={id_}'
        headers = {
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/vnd.api+json'
        }

        js = await self.session_manager.get_json(
            url, headers=headers, content_type='application/vnd.api+json'
        )

        first = js['data']
        results = parse_resp(first.pop(), medium)
        return results[0]
