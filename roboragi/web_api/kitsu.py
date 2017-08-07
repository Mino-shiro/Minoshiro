"""
Handles all Kitsu api calls
"""
from difflib import SequenceMatcher
from typing import List, Optional
from urllib.parse import quote
from roboragi.data_controller.enums import Medium
from roboragi.session_manager import HTTPStatusError, SessionManager


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
        self.client_id = 'dd031b32d2f56c990b1425efe6c42ad847e7fe3ab46bf1299f05ecd856bdb7dd'
        self.client_secret = '54d7307928f63414defd96399fc31ba847961ceaecef3a5fd93144e960c0e151'
        self.session_manager = session_manager
        self.base_url = 'https://kitsu.io/api/edge/'

    async def search_entries(
            self, medium: Medium, query: str) -> Optional[dict]:
        """
        Get the details of an thing by search query.

        :param session_manager: session manager object

        :param medium: medium to search for 'anime', 'manga', 'novel'

        :param query: the search term.

        :return: dict with thing info.
        """
        results = None
        medium_str = 'anime' if medium == Medium.ANIME else 'manga'
        url = f'{self.base_url}/{medium_str}?filter[text]={quote(query)}'
        headers = {
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/vnd.api+json'
        }

        try:
            async with await self.session_manager.get(
                    url, headers=headers) as resp:
                js = await resp.json(content_type='application/vnd.api+json')
        except HTTPStatusError as e:
            self.session_manager.logger.warn(str(e))
            return
        if js:
            closest_entry = self.__get_closest(query, js['data'])
            results = self.__parse_resp(closest_entry, medium)
            return results[0]
        else:
            return

    async def get_entry_by_id(
            self, medium: Medium, _id: str) -> Optional[dict]:
        """
        Get the details of a thing by id.

        :param session_manager: session manager object

        :param medium: medium to search for 'anime', 'manga', 'novel'

        :param query: the search term.

        :return: dict with thing info.
        """
        results = None
        medium_str = 'anime' if medium == Medium.ANIME else 'manga'
        url = f'{self.base_url}/{medium_str}?filter[slug]={_id}'
        headers = {
            'Accept': 'application/vnd.api+json',
            'Content-Type': 'application/vnd.api+json'
        }

        try:
            async with await self.session_manager.get(
                    url, headers=headers) as resp:
                js = await resp.json(content_type='application/vnd.api+json')
        except HTTPStatusError as e:
            self.session_manager.logger.warn(str(e))
            return
        first = js['data']
        results = self.__parse_resp(first.pop(), medium)
        return results[0]

    def __parse_resp(self, entry, medium):
        anime_list = []
        medium_str = 'anime' if medium == Medium.ANIME else 'manga'
        try:
            anime_list.append(dict(
                id=entry['id'],
                url=f'https://kitsu.io/{medium_str}/{entry["attributes"]["slug"]}',
                title_romaji=entry['attributes']['titles']['en_jp']
                    if 'en_jp' in entry['attributes']['titles'] else None,
                title_english=entry['attributes']['titles']['en']
                    if 'en' in entry['attributes']['titles'] else None,
                title_japanese=entry['attributes']['titles']['ja_jp']
                    if 'ja_jp' in entry['attributes']['titles'] else None,
                synonyms=set(entry['attributes']['abbreviatedTitles'])
                    if entry['attributes']['abbreviatedTitles'] else set(),
                description=entry['attributes']['synopsis']))

            if medium == Medium.ANIME:
                anime_list[-1]['episode_count'] = \
                    int(entry['attributes']['episodeCount'])\
                    if int(entry['attributes']['episodeCount']) > 0 else None
                anime_list[-1]['nsfw'] = entry['attributes']['nsfw']
                anime_list[-1]['type'] = entry['attributes']['showType']

            elif medium in [Medium.MANGA, Medium.LN]:
                anime_list[-1]['volume_count'] = \
                    int(entry['attributes']['volumeCount'])\
                    if entry['attributes']['volumeCount'] else None
                anime_list[-1]['chapter_count'] = \
                    int(entry['attributes']['chapterCount']) \
                    if entry['attributes']['chapterCount'] else None
                anime_list[-1]['type'] = entry['attributes']['mangaType']
        except AttributeError:
            pass

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

    def __get_closest(self, query: str, thing_list: List[dict]) -> dict:
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
            ratio = self.__match_max(thing, matcher)
            if ratio > max_ratio and ratio >= 0.90:
                max_ratio = ratio
                match = thing
        return match or {}

    def __match_max(self, thing: dict, matcher: SequenceMatcher) -> float:
        """
        Get the max matched ratio for a given thing.

        :param thing: the thing.

        :param matcher: the `SequenceMatcher` with the search query as seq2.
        
        :return: the max matched ratio.
        """
        thing_name_list = []
        max_ratio = 0
        if 'canonicalTitle' in thing['attributes']:
            thing_name_list.append(thing['attributes']['canonicalTitle'].lower())

        if 'abbreviatedTitles' in thing['attributes']:
            for title in thing['attributes']['abbreviatedTitles']:
                thing_name_list.append(title.lower())
        for name in thing_name_list:
            matcher.set_seq1(name.lower())
            ratio = matcher.ratio()
            if ('one shot' in thing['type'].lower()):
                ratio = ratio - .05
            if ratio > max_ratio:
                max_ratio = ratio
        return max_ratio
