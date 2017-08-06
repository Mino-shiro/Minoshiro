from enum import EnumMeta

from roboragi import DataController, Medium, PostgresController, Roboragi, Site


def test_imports():
    assert isinstance(Roboragi, type)
    assert isinstance(DataController, type)
    assert isinstance(PostgresController, type)
    assert PostgresController in DataController.__subclasses__()
    assert isinstance(Site, EnumMeta)
    assert isinstance(Medium, EnumMeta)
