Development notes for the datasource scrapers
=============================================


This must be an independent module.

How do the scrapers work ?
--------------------------

How do they work ? What data do they return ?

See the documentation in `chapitreScraper.py`.

`discogs` will use the official client.

How to write another scraper ?
------------------------------

See `chapitreScraper.py` doc, but wait a bit.

Logging
-------

use::

    import logging
    logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
    log = logging.getLogger(__name__)

every log will be print to the console::

  log.debug("debug!")


Next: configure a more complete logging strategy.
