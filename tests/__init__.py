from json import load
from pathlib import Path

__all__ = ['test_data_path', 'postgres_data']

test_data_path = Path(Path(__file__).parent.joinpath('test_data'))

with test_data_path.joinpath('postgres.json').open() as js:
    postgres_data = load(js)
