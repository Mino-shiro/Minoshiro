from typing import Dict, Optional

from data_controller.enums import Medium, Site
from utils.helpers import await_func


class DataController:
    """
    An ABC for all classes that deals with database read write.
    """
    __slots__ = ('logger',)

    def __init__(self, logger):
        """
        :param logger: the logger object to do logging with.
        """
        self.logger = logger

    def get_identifier(self, query: str,
                       medium: Medium) -> Optional[Dict[Site, str]]:
        """
        Get the identifier of a given search query.

        :param query: the search query.

        :param medium: the medium type.

        :return: A dict of all identifiers for this search query for all sites,
                 None if nothing is found.
        """
        raise NotImplementedError

    def set_identifier(self, name: str, medium: Medium,
                       site: Site, identifier: str):
        """
        Set the identifier for a given name.

        :param name: the name.

        :param medium: the medium type.

        :param site: the site.

        :param identifier: the identifier.
        """
        raise NotImplementedError

    def get_mal_title(self, id_: str, medium: Medium) -> Optional[str]:
        """
        Get a MAL title by its id.
        :param id_: th MAL id.
        :param medium: the medium type.
        :return: The MAL title if it's found.
        """
        raise NotImplementedError

    def set_mal_title(self, id_: str, medium: Medium, title: str):
        """
        Set the MAL title for a given id.
        :param id_: the MAL id.

        :param medium: The medium type.

        :param title: The MAL title for the given id.
        """
        raise NotImplementedError

    def medium_data_by_id(self, id_: str, medium: Medium,
                          site: Site) -> Optional[dict]:
        """
        Get data by id.
        :param id_: the id.
        :param medium: the medium type.
        :param site: the site.
        :return: the data for that id if found.
        """
        raise NotImplementedError

    def set_medium_data(self, id_: str, medium: Medium, site: Site, data: dict):
        """
        Set the data for a given id.

        :param id_: the id.
        
        :param medium: the medium type.

        :param site: the site.

        :param data: the data for the id.
        """
        raise NotImplementedError

    async def get_medium_data(self, query: str,
                              medium: Medium, loop=None) -> Optional[dict]:
        """
        Get the cached data for the given search query.

        :param query: the search query.

        :param medium: the medium type.

        :param loop: the asyncio event loop, optional. If None is provided,
        will use the default event loop.

        :return: the cached data, for all sites that has the data.
        """
        id_dict = await await_func(
            self.get_identifier, loop, query, medium
        )
        if not id_dict:
            return
        return {site: data for site, data in {
            site: await await_func(
                self.medium_data_by_id, loop, id_, medium, site
            )
            for site, id_ in id_dict.items()}.items() if data}
