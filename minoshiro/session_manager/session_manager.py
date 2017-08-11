from http import HTTPStatus
from json import loads

from aiohttp import ClientResponse, ClientSession


class HTTPStatusError(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

    def __str__(self):
        return f'HTTPStatusError:\nCode: {self.code}\nMessage: {self.msg}'

    def __repr__(self):
        return f'HTTPStatusError({self.code}, {self.msg})'


class SessionManager:
    """
    An aiohttp client session manager.
    """
    __slots__ = ('_session', 'logger', 'codes')

    def __init__(self, logger):
        """
        Initialize the instance of this class.
        """
        self._session = None
        self.logger = logger
        self.codes = {l.value: l.description for l in list(HTTPStatus)}

    def __del__(self):
        """
        Class destructor, close the client session.
        """
        self._session.close()

    async def __session(self):
        if not self._session:
            self._session = ClientSession()
        return self._session

    def return_response(self, res, code):
        """
        Return an Aiohttp or Request response object.

        :param res: the response.

        :param code: the response code.

        :return: the response object.

        :raises: HTTPStatusError if status code isn't 200
        """
        if 200 <= code < 300:
            return res
        raise HTTPStatusError(code, self.codes.get(code, None))

    async def __json_async(self, url, params, **kwargs):
        """
        Return the json content from an HTTP request using Aiohttp.

        :param url: the url.

        :param params: the request params.

        :return: the json content in a python dict.

        :raises HTTPStatusError: if the status code isn't in the 200s
        """
        try:
            res = await self.get(url, params=params, **kwargs)
        except HTTPStatusError as e:
            raise e
        async with res:
            content = await res.read()
            return loads(content) if content else None

    async def get_json(self, url: str, params: dict = None, **kwargs):
        """
        Get the json content from an HTTP request.

        :param url: the url.

        :param params: the request params.

        :return: the json content in a dict if success, else the error message.

        :raises HTTPStatusError: if the status code isn't in the 200s
        """
        return await self.__json_async(url, params, **kwargs)

    async def get(
            self, url, *, allow_redirects=True, **kwargs) -> ClientResponse:
        """
        Make HTTP GET request

        :param url: Request URL, str or URL

        :param allow_redirects:
            If set to False, do not follow redirects. True by default.

        :param kwargs:
            In order to modify inner request parameters, provide kwargs.

        :return: a client response object.

        :raises: HTTPStatusError if status code isn't between 200-299
        """
        session = await self.__session()
        r = await session.get(
            url, allow_redirects=allow_redirects, **kwargs)
        return self.return_response(r, r.status)

    async def post(self, url, *, data=None, **kwargs) -> ClientResponse:
        """
        Make HTTP POST request.

        :param url: Request URL, str or URL

        :param data:
            Dictionary, bytes, or file-like object to send in the
            body of the request (optional)

        :param kwargs:
            In order to modify inner request parameters, provide kwargs.

        :return: a client response object.

        :raises: HTTPStatusError if status code isn't between 200-299
        """
        session = await self.__session()
        resp = await session.post(url, data=data, **kwargs)
        return self.return_response(resp, resp.status)
