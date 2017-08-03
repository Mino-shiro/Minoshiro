"""
Populate the database with some data
before the main search class is initialized.
"""
from typing import AsyncGenerator

from roboragi.data_controller import DataController
from roboragi.data_controller.enums import Medium, Site
from roboragi.session_manager import SessionManager
from roboragi.web_api import AniList
from roboragi.web_api.mal import get_entry_details

__all__ = ['cache_top_40']


async def cache_top_40(medium: Medium, session_manager: SessionManager,
                       db: DataController, anilist: AniList, mal_headers: dict):
    """
    Cache the top 40 entries for all genres from Anilist, and try to cache
    each entry for a MAL entry as well.

    :param medium: The medium type.

    :param session_manager: the `SessionManager` instance.

    :param db: the `DataController` instance.

    :param anilist: the `AniList` instance.

    :param mal_headers: dict of mal auth headers.

    """
    async for entry in __top_40_anilist(medium, session_manager, anilist):
        anilist_id = entry['id']
        await db.set_medium_data(str(anilist_id), medium, Site.ANILIST, entry)

        romanji_name = entry.get('title_romaji')
        english_name = entry.get('title_english')
        anime_name = romanji_name or english_name
        if not anime_name:
            continue
        await __cache_anilist_id(romanji_name, medium, anilist_id, db)
        await __cache_anilist_id(english_name, medium, anilist_id, db)
        await __cache_mal_entry(
            db, anime_name, medium, mal_headers, session_manager
        )


async def __top_40_anilist(medium: Medium, session_manager: SessionManager,
                           anilist: AniList) -> AsyncGenerator[dict]:
    """
    Yields top 40 anime/manga for each genre in Anilist.

    :param medium: The medium type, only Anime and Manga are supported.

    :param session_manager: the `SessionManager` instance.

    :param anilist: the `Anilist` instance.

    :return: an asynchronous generators that yields top 40 anime/manga
    for each genre in Anilist.
    """
    genres = await anilist.get_genres(session_manager, medium)
    if not genres:
        return
    for entry in genres:
        genre = entry.get('genre')
        if not genre:
            continue
        res = await anilist.get_top_40_by_genre(
            session_manager, medium, genre
        )
        if res:
            for data in res:
                if data.get('id') is not None:
                    yield data


async def __cache_anilist_id(name, medium, id_, db):
    """
    Cache an anilist id to the db.
    :param name: the name of the id.
    :param medium: the medium type.
    :param id_: the id.
    :param db: the `DataController` instance.
    """
    if name:
        await db.set_identifier(name, medium, Site.ANILIST, id_)


async def __cache_mal_entry(db, name, medium, mal_headers, session_manager):
    """
    Search MAL from a name, cache the
    :param db: the `DataController` instance.
    :param name: the name of the anime/manga.
    :param medium: the medium type.
    :param mal_headers: the mal auth headers.
    :param session_manager: the `SessionManager` instance.
    """
    id_dict = await db.get_identifier(name, medium) or {}
    mal_id = id_dict.get(Site.MAL)

    mal_entry = await get_entry_details(
        session_manager, mal_headers, medium, name, mal_id
    )
    if not mal_entry:
        return

    id_ = mal_entry.get('id')

    if not id_:
        return
    id_ = str(id_)
    title = mal_entry.get('title')
    if title:
        await db.set_mal_title(id_, medium, title)
    await db.set_medium_data(id_, medium, Site.MAL, mal_entry)
