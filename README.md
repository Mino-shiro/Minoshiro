# Minoshiro [![Build Status](https://travis-ci.org/Mino-shiro/Minoshiro.svg?branch=master)](https://travis-ci.org/Mino-shiro/Minoshiro) [![Documentation Status](https://readthedocs.org/projects/minoshiro/badge/?version=latest)](http://minoshiro.readthedocs.io/en/latest/?badge=latest)

Inspired by the Roboragi [Reddit bot](https://github.com/Nihilate/Roboragi), Minoshiro is an async Python library that brings various web APIs for anime, manga, and light novel into one place.

## Features
* Simple and modern Pythonic API using `async/await syntax
* Fetches search results from up to 9 different websites
* Cached search results for faster access
* Integrates with existing databases

## Requirements
Requires [Python3.6](https://www.python.org/downloads/) or above. Python3.5 and below is not supported.

## Install
To install the base version, simply install from PyPi:
```
pip install minoshiro
```

This library also comes with a PostgreSQL support, to use this feature you will need a PostgreSQL version 9.6 or above instance hosted.

To install with the built in PostgreSQL support, use:
```
pip install minoshiro[postgres]
```

This installs [asyncpg](https://github.com/MagicStack/asyncpg) alongside of the base requirements.

## Documentation
Documentation can be found at https://minoshiro.readthedocs.io/en/latest/

You can also find some quick examples in this [file](https://github.com/Mino-shiro/Minoshiro/blob/master/example.py).

## License
Roboragi is released under the MIT license. See the license [file](https://github.com/Mino-shiro/Minoshiro/blob/master/LICENSE) for more details.
