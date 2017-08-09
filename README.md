# Roboragi [![Build Status](https://travis-ci.org/MaT1g3R/Roboragi.svg?branch=master)](https://travis-ci.org/MaT1g3R/Roboragi) [![Documentation Status](https://readthedocs.org/projects/roboragi/badge/?version=latest)](http://roboragi.readthedocs.io/en/latest/?badge=latest)

Inspired by the original [Reddit bot](https://github.com/Nihilate/Roboragi), Roboragi is an async Python library that brings various web APIs for anime, manga, and light novel into one place.

## Features
* Simple and modern Pythonic API using `async/await` syntax
* Fetches search results from up to 9 different websites
* Cached search results for faster access
* Integrates with existing databases

## Requirements
Requires [Python3.6](https://www.python.org/downloads/) or above. Python3.5 and below is not supported.

## Install
To install the base version, simply install from PyPi:
```
pip install roboragi
```

This library also comes with a PostgreSQL support, to use this feature you will need a PostgreSQL version 9.6 or above instance hosted.

To install with the built in PostgreSQL support, use:
```
pip install roboragi[postgres]
```

This installs [asyncpg](https://github.com/MagicStack/asyncpg) alongside of the base requirements.

## Documentation
Documentation can be found at https://roboragi.readthedocs.io/en/latest/

You can also find some quick examples in this [file](https://github.com/MaT1g3R/Roboragi/blob/master/example.py).

## License
Roboragi is released under the MIT license. See the license [file](https://github.com/MaT1g3R/Roboragi/blob/master/LICENSE) for more details.
