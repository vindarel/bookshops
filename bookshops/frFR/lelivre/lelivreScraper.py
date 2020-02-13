#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

import addict
import clize
import requests
from bs4 import BeautifulSoup
from sigtools.modifiers import annotate
from sigtools.modifiers import autokwoargs
from sigtools.modifiers import kwoargs

from bookshops.utils.decorators import catch_errors
from bookshops.utils.scraperUtils import is_isbn
from bookshops.utils.scraperUtils import priceFromText
from bookshops.utils.scraperUtils import priceStr2Float
from bookshops.utils.scraperUtils import print_card

logging.basicConfig(level=logging.ERROR)

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.ERROR)
log = logging.getLogger(__name__)


def find_dd(terms, descriptions, term):
    """
    Find Éditeur, EAN, Parution etc in a dd table.

    The dd table can contain 3 to 5 descriptions, we can't rely on the
    descriptions' position.

    - descriptions (list)
    - term (str): part of a term (from the dd table).

    terms:
    [<dt>\xc9diteur</dt>, <dt>Collection</dt>, <dt>Format</dt>, <dt>Parution</dt>, <dt>EAN</dt>]

    descriptions:
    [<dd><a href="/Editeur-arche_editeur-c105882-True">Arche \xe9diteur</a></dd>, <dd><a href="/Collection-sc%C3%A8ne%20ouverte-True">Sc\xe8ne ouverte</a></dd>, <dd>Livre Broch\xe9</dd>, <dd>09 - 2019</dd>, <dd>9782851819673</dd>]

    Return the matching description.
    """
    for i, cur_term in enumerate(terms):
        if term.lower() in cur_term.text.lower():
            desc = descriptions[i]
            if desc.find('a'):
                # for Éditeur, Collection.
                return desc.a.text
            return desc.text

# class Scraper(BaseScraper):
class Scraper():

    query = ""
    currency = "CHF"

    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "lelivre.ch"
        #: Base url of the website
        self.SOURCE_URL_BASE = u"https://www.lelivre.ch"
        #: GET or POST to run the search? GET by default.
        self.METHOD = 'POST'
        #: POST paramaters:
        self.PARAMS = {'inputSearch': ''}

        #: Url to search.
        self.SOURCE_URL_SEARCH = u"https://www.lelivre.ch/Results"
        #: advanced url
        self.SOURCE_URL_ADVANCED_SEARCH = u""
        #: the url to search for an isbn.
        self.SOURCE_URL_ISBN_SEARCH = self.SOURCE_URL_SEARCH
        #: Optional suffix to the search url (may help to filter types, i.e. don't show e-books).
        self.URL_END = u""
        self.TYPE_BOOK = u"book"
        #: Query parameter to search for the ean/isbn
        self.ISBN_QPARAM = u""
        #: Query param to search for the publisher (editeur)
        self.PUBLISHER_QPARAM = u"EDITEUR"
        #: Number of results to display
        self.NBR_RESULTS_QPARAM = u""
        self.NBR_RESULTS = 12

        self.USER_AGENT = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0"
        self.HEADERS = {'user-agent': self.USER_AGENT}

    def __init__(self, *args, **kwargs):
        """
        """
        self.args = args
        self.set_constants()
        self.PARAMS['inputSearch'] = args

        self.req = None
        self.url = self.SOURCE_URL_SEARCH
        self.soup = None
        isbns = []
        if args:
            isbns = filter(is_isbn, args)
        if len(isbns) > 1:
            logging.info(u"Searching many isbns at once is not supported with this datasource so far.")
            return
        if isbns:
            self.PARAMS['inputSearch'] = isbns[0]
        else:
            self.PARAMS['inputSearch'] = " ".join(args)

        self.req = requests.post(self.url, params=self.PARAMS, headers=self.HEADERS)
        if self.req.status_code != 200:
            logging.warning(u"Our search status code is not 'success'.")
        self.soup = BeautifulSoup(self.req.text, 'lxml')

    def _product_list(self):
        """
        returns: a list of BeautifulSoup results that contain each the information
        about a single book.
        """
        try:
            plist = self.soup.find(class_='result-table')
            if not plist:
                logging.warning(u'Warning: product list is null, we (apparently) didn\'t find any result')
                return []
            if not plist:
                logging.info(u"No product list for search {} on {}.".format(self.args, self.DATA_SOURCE_NAME))
            plist = plist.find_all(class_='result-item')
            return plist
        except Exception as e:
            logging.error("Error while getting product list. Will return []. Error: {}".format(e))
            return []

    def _nbr_results(self):
        """
        Official number of results of the datasource.
        """
        pass

    @catch_errors
    def _details_url(self, product):
        details_url = product.find(class_='result-details').h2.a['href'].strip()
        details_url = self.SOURCE_URL_BASE + details_url
        return details_url

    @catch_errors
    def _title(self, product):
        try:
            title = product.find(class_='result-details').find('h2').text.strip()
            return title.capitalize()
        except Exception as e:
            logging.error(u"Could not find title when searching for {}: {}".format(self.args, e))
            return ""

    @catch_errors
    def _authors(self, product):
        """Return a list of str.
        """
        try:
            authors = product.find(class_='result-author').text
            authors = authors.split('\n')
            authors = filter(lambda it: it not in ["", '', u""], authors)
            authors = [it.strip().capitalize() for it in authors]
            return authors
        except Exception as e:
            logging.error(u"Error getting authors for {}: {}".format(self.args, e))

    @catch_errors
    def _img(self, product):
        img = product.find(class_='result-cover').img['src']
        return img

    def _publishers(self, product):
        """
        Return a list of publishers (strings).
        """
        try:
            terms = product.find_all('dt')
            descriptions = product.find_all('dd')
            assert len(terms) == len(descriptions)
            res = find_dd(terms, descriptions, 'diteur')  # leave out É or é.
            return [res]
        except Exception as e:
            logging.error(u"Error getting publisher(s) of {}: {}".format(self.args, e))
            return []

    def _price(self, product):
        "The public price."
        try:
            price = product.find(class_='result-price').text.strip()
            price = priceFromText(price)
            price = priceStr2Float(price)
            return price
        except Exception, e:
            print 'Erreur getting price {}'.format(e)

    @catch_errors
    def _isbn(self, product):
        """
        Return: str
        """
        terms = product.find_all('dt')
        descriptions = product.find_all('dd')
        assert len(terms) == len(descriptions)
        isbn = find_dd(terms, descriptions, 'ean')
        return isbn

    @catch_errors
    def _description(self, product):
        """
        To get with postSearch.
        """
        pass

    @catch_errors
    def _date_publication(self, product):
        """
        return: a str that is correctly parsed by dateparser.parse (year and month ok,
        it gets the current day)

        Exemple: '09 - 2019' -> 2019-09-13 if today is the 13th of the month.
        It's OK for Abelujo Card.from_dict.

        Note that we can also return a datetime object.
        """
        terms = product.find_all('dt')
        descriptions = product.find_all('dd')
        assert len(terms) == len(descriptions)
        res = find_dd(terms, descriptions, 'parution')
        return res

    @catch_errors
    def _format(self, product):
        """
        - return: str or None
        """
        terms = product.find_all('dt')
        descriptions = product.find_all('dd')
        assert len(terms) == len(descriptions)
        res = find_dd(terms, descriptions, 'format')
        return res

    def search(self, *args, **kwargs):
        """Searches books. Returns a list of books.

        From keywords, fires a query and parses the list of
        results to retrieve the information of each book.

        args: liste de mots, rajoutés dans le champ ?q=
        """
        bk_list = []
        stacktraces = []

        product_list = self._product_list()
        # nbr_results = self._nbr_results()
        for product in product_list:
            authors = self._authors(product)
            publishers = self._publishers(product)
            b = addict.Dict()
            b.search_terms = self.query
            b.data_source = self.SOURCE_NAME
            b.search_url = self.url
            b.date_publication = self._date_publication(product)
            b.details_url = self._details_url(product)
            b.fmt = self._format(product)
            b.title = self._title(product)
            b.authors = authors
            b.authors_repr = ", ".join(authors)
            b.price = self._price(product)
            b.publishers = publishers
            b.pubs_repr = ", ".join(publishers)
            b.card_type = self.TYPE_BOOK
            b.img = self._img(product)
            b.summary = self._description(product)
            b.isbn = self._isbn(product)
            # b.availability

            b.currency = self.currency

            bk_list.append(b.to_dict())

        return bk_list, stacktraces

def postSearch(card, isbn=None):
    """Get a card (dictionnary) with 'details_url'.

    Gets additional data:
    - description

    Check the isbn is valid. If not, return None. But that shouldn't happen !

    We can give the isbn as a keyword-argument (it can happen when we
    import data from a file). In that case, don't look for the isbn.

    Return a new card (dict) complemented with the new attributes.

    """
    return card


@annotate(words=clize.Parameter.REQUIRED, review='r')
@autokwoargs()
def main(review=False, *words):
    """
    words: keywords to search, or one ISBN.
    """
    if not words:
        print "Please give keywords as arguments"
        return
    scrap = Scraper(*words)
    bklist, errors = scrap.search()
    print " Nb results: {}".format(len(bklist))
    bklist = [postSearch(it) for it in bklist]
    [print_card(it, details=True) for it in bklist]


def run():
    exit(clize.run(main))


if __name__ == '__main__':
    clize.run(main)
