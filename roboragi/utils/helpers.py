from roboragi.data_controller.enums import Medium


def filter_anime_manga(medium: Medium) -> str:
    if medium == Medium.ANIME:
        return 'anime'
    elif medium == Medium.MANGA:
        return 'manga'
    else:
        raise ValueError('Only anime and managa are supported.')
