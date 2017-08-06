.. _install:

Install
==========
To install the base version, simply install from PyPi: ::

  pip install roboragi

This library also comes with a PostgreSQL data controller, to use this you will
need a PostgreSQL version 9.6 or above instance hosted.

To install with the built in PostgreSQL support, use: ::

  pip install roboragi[postgres]

or simply install `asyncpg <https://github.com/MagicStack/asyncpg>`_
version 0.12.0 or later from PyPi

To achieve maximum speed with this library,
`uvloop <https://github.com/MagicStack/uvloop>`_ is highly recommended.
