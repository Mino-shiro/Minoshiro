"""
Database utility functions.
"""
from sqlite3 import connect

from data import data_path


def get_all_synonyms() -> list:
    """
    Get all synonyms from the sqlite db.
    :return: all synonyms from the sqlite db.
    """
    with connect(str(data_path.joinpath('synonyms.db'))) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM main.synonyms')
        rows = cur.fetchall()
    return rows
