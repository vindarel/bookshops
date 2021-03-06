#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 - 2020 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

"""
Base scraper to build new ones.
"""

import logging
import requests
from bs4 import BeautifulSoup

from bookshops.utils.scraperUtils import is_isbn
from bookshops.utils.scraperUtils import price_fmt
from bookshops.utils.decorators import catch_errors
from bookshops.utils import simplecache

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)


"""Some fields are not available directly in the search results page
but in the book's details page, which needs another GET
request. We don't request it for every book, this would be too
long. We will fetch those complementary informations when the user
recquires it (when it clicks to add a book or to get more
informations about one). We call the postSearch method, defined
above, which gets those complementary fields, if any.

Advanced search
---------------

Still experimental.

To search for all publications by a publisher, type "ed:name".

To do:
- different keywords/language,
- see the keyword with a regexp (ed[a-z]*:)
- search for keywords also,
- and pagination, because we want to parse through everything

Shall we use xpath ?
--------------------

You can use xpath expressions to get information.
Xpath expressions are terse, they allow to further factorize code.
"""


class BaseScraper(object):
    """Base class to build scrapers. Mostly used for the __init__ and
    postSearch methods. A subclass will redefine the methods used to
    really extract the data.

    Must have:

    - an init to construct the url

    - a search() method to fire the query, which must return a tuple
      (list of search results/stacktraces). A search result is a dict.

    """

    currency = '€'
    query = ""
    METHOD = 'GET'

    def set_constants(self):
        """Call before __init__.
        """
        self.SOURCE_NAME = "name"
        #: Base url of the website
        self.SOURCE_URL_BASE = "http//url-base"
        #: GET or POST?
        #: Url to which we just have to add url parameters to run the search
        self.SOURCE_URL_SEARCH = "url-search"
        #: Advanced search url
        self.SOURCE_URL_ADVANCED_SEARCH = ""
        #: The url to search for an isbn (can be the advanced or the simple one).
        self.SOURCE_URL_ISBN_SEARCH = self.SOURCE_URL_SEARCH
        self.ERR_OUTOFSTOCK = "product out of stock"
        self.TYPE_BOOK = "book"
        self.TYPE_DVD = "dvd"
        # there is no comic type.
        self.TYPE_DEFAULT = self.TYPE_BOOK

        #: Query parameter to search for the ean/isbn (if needed, maybe it uses the regular search pattern).
        #: for example, "dctr_ean", without & nor =
        self.ISBN_QPARAM = ""
        #: Query parameter to filter on the publisher
        self.PUBLISHER_QPARAM = ""
        #: Number of results to display
        self.NBR_RESULTS_QPARAM = ""
        self.NBR_RESULTS = 24  # 12 by default

    def __init__(self, *args, **kwargs):
        """Constructs the query url with the given parameters, retrieves the
        page and parses it through BeautifulSoup. Then we can call
        search() to get a list of results, or specific methods (_isbn,
        _authors, _title, …).

        parameters: either a list of words (fires a global search) or
        keywords arguments (key/values pairs, values being lists).

        Keys can be: label (for title), author_names,publisher, isbn etc.
        """

        self.ARGS = args  # remember for simplecache, access in search() method.
        self.cached_results = simplecache.get_cache(self.SOURCE_NAME, args)
        if self.cached_results is not None:
            log.debug("Hit cache.")
            return

        self.USER_AGENT = "Abelujo"
        self.HEADERS = {'user-agent': self.USER_AGENT}

        #: When we search for an isbn, it's possible the website lend
        # us not to the default search results page, but redirect us to
        # the product page instead. In that case the search() method,
        # with default CSS selectors, won't work. We must scrap the
        # product page for everything. We could not accept the
        # redirection, but with it we go faster to a much more useful
        # product page.
        self.ISBN_SEARCH_REDIRECTED_TO_PRODUCT_PAGE = False

        self.page = 1
        isbns = []
        if not args and not kwargs:
            print('Error: give args to the query')

        # headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.65 Safari/537.36',

        # Get the search terms that are isbn
        # (we only search for one atm)
        if args:
            isbns = list(filter(is_isbn, args))

        # Get the search keywords without isbns
        words = list(set(args) - set(isbns))

        # Pagination
        if 'PAGE' in kwargs:
            self.page = kwargs.pop('PAGE')
            if not self.page:
                self.page = 1

        if kwargs:
            if 'isbn' in kwargs:
                kwargs[self.ISBN_QPARAM] = kwargs['isbn']
                kwargs.pop('isbn')

            # Build url with the remaining query parameters.
            self.url = self.SOURCE_URL_SEARCH  # ready to add query+args+parameters
            q = ""
            for k, v in list(kwargs.items()):
                urlend = "+".join(val for val in v)
                q += "&%s=%s" % (k, urlend)

            self.url += q
            self.url += self.URL_END + self.pagination()

        else:

            # If a isbn is given, search for it
            if isbns:
                # Some sites use query parameters to set the isbn,
                # others treat it like a normal one (casa del libro).
                if self.ISBN_QPARAM not in ["", ""]:
                    self.query = "&{}={}".format(self.ISBN_QPARAM, isbns[0])
                else:
                    # XXX: we could search for many isbns at once.
                    self.query = isbns[0]
                    self.isbn = self.query

                self.url = self.SOURCE_URL_ISBN_SEARCH + self.query
                self.url += self.URL_END  # no pagination when isbn

            # otherwise search the keywords.
            else:
                # Check an advanced search of the form "editeur:name"
                if "ed:" in words[0]:
                    ed = words[0].split(':')[1]
                    self.query = "&{}={}".format(self.PUBLISHER_QPARAM, ed)
                    self.url = self.SOURCE_URL_ADVANCED_SEARCH + self.query

                else:
                    self.query = "+".join(words)
                    self.url = self.SOURCE_URL_SEARCH + self.query

                self.url += self.URL_END + self.pagination()

        log.debug('search url: %s' % self.url)
        self.req = requests.get(self.url, headers=self.HEADERS)
        if self.req.history and self.req.history[0].status_code == 302:
            log.info("First request: we got redirected")
            self.ISBN_SEARCH_REDIRECTED_TO_PRODUCT_PAGE = True
            self.url_product_page = self.req.url

        self.soup = BeautifulSoup(self.req.content, "lxml")

    def pagination(self):
        """Format the url part to grab the right page.

        Return: a str, the necessary url part to add at the end.
        """
        page_qparam = ""
        return page_qparam

    def _product_list(self):
        """The css class that every block of book has in common.

        returns: a list of type soup that contain each the information
        about a single book.
        """
        items = self.soup.find_all(class_="categorySummary")
        return items

    @catch_errors
    def _title(self, product):
        pass

    @catch_errors
    def _details_url(self, product):
        pass

    @catch_errors
    def _date_publication(self, product):
        """Date of publication. Not a Date object, just a string.
        """
        pass

    @catch_errors
    def _price(self, product):
        """return a float."""
        return None

    @catch_errors
    def _authors(self, product):
        """return a list of strings."""
        authors = []
        return authors

    @catch_errors
    def _description(self, product):
        """No description in the result page.
        There is a summup in the details page. See postSearch.
        """
        pass

    @catch_errors
    def _img(self, product):
        """return the full url to the cover."""
        pass

    @catch_errors
    def _publisher(self, product):
        """return a list of strings."""
        publisher = ""
        return [publisher]

    @catch_errors
    def _date(self, product):
        """return a string."""
        pass

    @catch_errors
    def _isbn(self, product):
        pass

    @catch_errors
    def _availability(product):
        """Availability.
        Return: a string.
        """
        pass

    def search(self, *args, **kwargs):
        """Searches books.

        Returns: a couple list of books / stacktraces.
        """
        if self.cached_results is not None:
            log.debug("search: hit cache.")
            return self.cached_results

        bk_list = []
        stacktraces = []
        product_list = self._product_list()
        status = self.req.status_code
        if (status / 100) in [4, 5]:  # get 400 and 500 errors
            stacktraces.append("The remote source has a problem, we can not connect to it.")

        for product in product_list:
            authors = self._authors(product)
            authors_repr = ""
            if isinstance(authors_repr, list):
                authors_repr = [", ".join(authors_repr)]
            else:
                authors_repr = authors
            publishers = self._publisher(product) or []
            b = {}
            b["data_source"] = self.SOURCE_NAME
            b["isbn"] = self._isbn(product)  # missing
            b["title"] = self._title(product)
            b["details_url"] = self._details_url(product)
            b["date_publication"] = self._date_publication(product)
            b["search_url"] = self.url
            b["search_terms"] = self.query
            b["authors"] = authors
            b["authors_repr"] = authors_repr
            b["price"] = self._price(product)
            b["price_fmt"] = price_fmt(b.price, self.currency)
            b["currency"] = self.currency

            b["description"] = self._description(product)
            b["img"] = self._img(product)
            b["publishers"] = publishers
            b["pubs_repr"] = ", ".join(publishers)
            b["date"] = self._date(product)
            b["availability"] = self._availability(product)
            b["card_type"] = self.TYPE_BOOK
            bk_list.append(b)

        simplecache.cache_results(self.SOURCE_NAME, self.ARGS, bk_list)

        return (bk_list, stacktraces)


def postSearch(card):
    """Complementary informations to fetch on a details' page.

    The card must have an isbn in the end.

    Return: the card dict, with isbn
    """
    return card


def reviews(card_dict):
    """Get reviews of that card on good websites.

    Return: a list of reviews (dict) with: title, url, short and long summary.
    """
    pass
