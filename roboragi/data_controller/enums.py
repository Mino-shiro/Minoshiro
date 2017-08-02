from enum import Enum

__all__ = ['Site', 'Medium']


class Site(Enum):
    MAL = 1
    ANILIST = 2
    ANIMEPLANET = 3
    ANIDB = 4
    KITSU = 5
    MANGAUPDATES = 6
    LNDB = 7
    NOVELUPDATES = 8
    VNDB = 9


class Medium(Enum):
    ANIME = 1
    MANGA = 2
    LN = 3
    VN = 4
