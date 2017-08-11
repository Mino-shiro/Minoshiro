from minoshiro.data_controller.enums import Medium, Site


def filter_anime_manga(medium: Medium) -> str:
    if medium == Medium.ANIME:
        return 'anime'
    elif medium == Medium.MANGA:
        return 'manga'
    else:
        raise ValueError('Only anime and managa are supported.')


def get_synonyms(entry: dict, site: Site):
    """
    Yield all synonyms from an entry.

    :param entry: the request data.

    :param site: The site for the entry.

    :return: A generator that yields all synonyms from a entry.
    """
    if not entry:
        return
    if site == Site.ANILIST:
        keys = ('title_english', 'title_romaji')
        lst_key = 'synonyms'
    elif site == Site.MAL:
        keys = ('title', 'english')
        lst_key = 'synonyms'
    elif site == Site.ANIDB:
        keys = ()
        lst_key = 'titles'
        pass
    else:
        return

    for key in keys:
        val = entry.get(key)
        if val:
            yield val.rstrip()

    lst = entry.get(lst_key, ())
    if lst and not isinstance(lst, str):
        for syn in lst:
            yield syn.strip()
