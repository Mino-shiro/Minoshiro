"""
Populate the database with some data
before the main search class is initialized.
"""

from aiohttp_wrapper import SessionManager

from .data_controller import DataController
from .enums import Medium, Site
from .helpers import get_synonyms
from .web_api.ani_list import get_page_by_popularity
from .web_api.mal import get_entry_details

__all__ = ['cache_top_pages']


async def cache_top_pages(medium: Medium, session_manager: SessionManager,
                          db: DataController, mal_headers: dict,
                          page_count: int, cache_mal_entries: int):
    """
    Cache the top n pages of anime/manga from Anilist, and try to cache each
    entry for MAL as well.

    :param medium: The medium type.

    :param session_manager: the `SessionManager` instance.

    :param db: the `DataController` instance.

    :param anilist: the `AniList` instance.

    :param mal_headers: dict of mal auth headers.

    :param page_count: the number of desired pages.

    :param cache_mal_entries: The number of MAL entries to cache.
    """
    assert page_count > 0, 'Please enter a page count greater than 0.'
    await __cache(
        __n_popular_anilist(page_count, medium, session_manager),
        db, medium, mal_headers, session_manager, cache_mal_entries
    )


async def __cache(async_iter, db, medium, mal_headers, session_manager,
                  cache_mal_entries):
    """
    Cache entries from an `AsyncGenerator`

    :param async_iter: the `AsyncGenerator`

    :param db: the `DataController` instance.

    :param medium: The medium type.

    :param mal_headers: dict of mal auth headers.

    :param session_manager: the `SessionManager` instance.

    :param cache_mal_entries: The number of MAL entries to cache.
    """
    i = 0
    async for entry in async_iter:
        anilist_id = str(entry['id'])
        await db.set_medium_data(anilist_id, medium, Site.ANILIST, entry)

        romanji_name = entry.get('title_romaji')
        english_name = entry.get('title_english')
        anime_name = romanji_name or english_name
        if not anime_name:
            continue
        for syn in get_synonyms(entry, Site.ANILIST):
            await db.set_identifier(syn, medium, Site.ANILIST, anilist_id)
        if i < cache_mal_entries:
            await __cache_mal_entry(
                db, anime_name, medium, mal_headers, session_manager
            )
            i += 1


async def __n_popular_anilist(
        page_count: int, medium: Medium, session_manager: SessionManager):
    """
    Yields top n pages of anime/manga by popularity from Anilist.

    :param page_count: the desired number of pages.

    :param medium: the medium type.

    :param session_manager: the `SessionManager` instance.

    :param anilist: the `Anilist` instance.

    :return: an asynchronous generator that
             yields top n pages of anime/manga for Anilist.
    """
    for i in range(page_count):
        try:
            page_entries = await get_page_by_popularity(
                session_manager, medium, i + 1
            )
            error = False
        except Exception as e:
            session_manager.logger.warning(f'Error raised by Anilist: {e}')
            page_entries = None
            error = True
        if not page_entries and error:
            continue
        elif not page_entries:
            break
        for entry in page_entries:
            id_ = entry.get('id')
            if id_ or isinstance(id_, int):
                yield entry


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
    try:
        mal_entry = await get_entry_details(
            session_manager, mal_headers, medium, name, mal_id
        )
    except Exception as e:
        session_manager.logger.debug(f'Error raised by MAL: {e} '
                                     f'on item {name}')
        mal_entry = None
    if not mal_entry:
        return

    id_ = mal_entry.get('id')

    if not id_:
        return
    id_ = str(id_)
    title = mal_entry.get('title')
    for syn in get_synonyms(mal_entry, Site.MAL):
        await db.set_identifier(syn, medium, Site.MAL, id_)
    if title:
        await db.set_mal_title(id_, medium, title)
    await db.set_medium_data(id_, medium, Site.MAL, mal_entry)
