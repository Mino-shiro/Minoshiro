from enum import EnumMeta

from roboragi import DataController, Medium, PostgresController, Roboragi, Site, \
    SqliteController


def test_imports():
    assert isinstance(Roboragi, type)
    assert isinstance(DataController, type)
    assert isinstance(PostgresController, type)
    assert isinstance(SqliteController, type)
    assert PostgresController in DataController.__subclasses__()
    assert SqliteController in DataController.__subclasses__()
    assert isinstance(Site, EnumMeta)
    assert isinstance(Medium, EnumMeta)
