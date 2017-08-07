.. _logging:

Logging
==========
Roboragi logs errors and debug information via the
`logging <https://docs.python.org/3/library/logging.html>`_ Python module. The
library comes with a basic logger that prints to ``STDERR``. It is strongly
recommended you log to a log file in addition to printing to ``STDERR``.

Configuration of the logger can be as simple as:

.. code-block:: python3

    from logging import FileHandler, Formatter

    from roboragi import get_default_logger

    logger = get_default_logger()
    file_handler = FileHandler(filename='my_log_file.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
    )
    logger.addHandler(file_handler)

More advance setups are possible with the
`logging <https://docs.python.org/3/library/logging.html>`_ module. You can
configure the logger to your liking as such:

.. code-block:: python3

    from logging import getLogger

    import roboragi

    my_logger = getLogger('roboragi')

    ...

And finally, if you already have a logger set up in your application, you can
simply use the existing logger instead of the one provided by the library.