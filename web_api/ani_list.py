from itertools import chain
from typing import Optional

from session_manager import HTTPStatusError, SessionManager

__escape_table = {
    '&': ' ',
    "\'": "\\'",
    '\"': '\\"',
    '/': ' ',
    '-': ' '
    # '!': '\!'
}


def escape(text: str) -> str:
    """
    Escape text for ani list use.
    :param text: the text to be escaped.
    :return: the escaped text.
    """
    return ''.join(__escape_table.get(c, c) for c in text)


def get_synonyms(request: dict):
    """
    Get all synonyms from a request.
    :param request: the request data.
    :return: all synonyms form the request.
    """
    iterator = chain(
        (request.get('title_english'), request.get('title_romaji')),
        request.get('synonyms', ())
    )
    return [s for s in iterator if s]


class AniList:
    """
    Since we need a new access token from Anilist every hour, a class is more
    appropriate to handle ani list searches.
    """

    def __init__(self, session_manager: SessionManager, client_id: str,
                 client_secret: str):
        """
        Init the class.
        :param client_id: the Anilist client id.
        :param client_secret: the Anilist client secret.
        """
        self.access_token = None
        self.client_id = client_id
        self.client_secret = client_secret
        self.session_manager = session_manager
        self.base_url = 'https://anilist.co/api'

    async def get_token(self) -> Optional[str]:
        """
        Get an access token from Anilist.
        :return: the access token if success.
        """
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        try:
            resp = await self.session_manager.post(
                f'{self.base_url}/auth/access_token',
                params=params
            )
        except HTTPStatusError as e:
            self.session_manager.logger.warn(str(e))
            return
        async with resp:
            js = await resp.json()
            return js.get('access_token')
