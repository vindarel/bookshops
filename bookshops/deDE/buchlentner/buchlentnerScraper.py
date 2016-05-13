#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import re
import sys

import addict
import clize
import requests
import requests_cache
from bs4 import BeautifulSoup
from sigtools.modifiers import annotate
from sigtools.modifiers import kwoargs

from bookshops.utils.baseScraper import Scraper as baseScraper
from bookshops.utils.decorators import catch_errors
from bookshops.utils.scraperUtils import is_isbn
from bookshops.utils.scraperUtils import isbn_cleanup
from bookshops.utils.scraperUtils import priceFromText
from bookshops.utils.scraperUtils import priceStr2Float
from bookshops.utils.scraperUtils import print_card

logging.basicConfig(level=logging.ERROR) #to manage with ruche
requests_cache.install_cache()


# logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.ERROR)
log = logging.getLogger(__name__)

class Scraper(baseScraper):
    """We can search for CDs, DVD and other stuff on buchlentner.

    Suchtipps:
    - foo OR bar
    - AND
    - NOT
    - foo-bar: findet Ergebnisse, die den Begriff
      "Geschichten-Erzähler" in allen Schreibweisen enthalten, sowohl
      als einzelnes Wort, als Phrase oder mit Bindestrich

    """

    query = ""


    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "buchlentner"
        #: Base url of the website
        self.SOURCE_URL_BASE = u"http://www.buchlentner.de"
        #: Url to which we just have to add url parameters to run the search
        self.SOURCE_URL_SEARCH = u"http://www.buchlentner.de/webapp/wcs/stores/servlet/SearchCmd?storeId=21711&catalogId=4099276460822233275&langId=-3&pageSize=10&beginIndex=0&sType=SimpleSearch&resultCatEntryType=2&showResultsPage=true&pageView=image&pageType=PK&mediaTypes=Book:Bücher&searchBtn=SUCHEN&searchTerm="
        #: advanced url (search for isbns)
        self.SOURCE_URL_ADVANCED_SEARCH = u"http://www.buchlentner.de/webapp/wcs/stores/servlet/KNVAdvancedSearchResult?storeId=21711&catalogId=4099276460822233275&langId=-3&fromAdvanceSearch=AdvanceSearch&pageType=HU&language_selected=&language=&stock=&iehack=☠&offer=&avail=&media=Books&author1=&author=&actor1=&actor=&topic=&publisher1=&publisher=&movie_category=All+Categories&movie_category=All+Categories&articleno=&lang=deutsch&lang=&lang1=deutsch&lang1=deutsch&movie_subtitle=&covertype=all&covertype=all&range_price=from-to&range_price=from-to&price_from=&price_to=&range_age=from-to&range_age=from-to&age_from=&age_to=&range_age1=from-to&range_age1=from-to&age1_from=&age1_to=&range_age2=from-to&age2_from=&age2_to=&range_issuedate=from-to&range_issuedate=from-to&issuedate_from=&issuedate_to=&issue1=&issue=&nott=&title="
        #: the url to search for an isbn.
        self.SOURCE_URL_ISBN_SEARCH = u"http://www.buchlentner.de/webapp/wcs/stores/servlet/KNVAdvancedSearchResult?storeId=21711&catalogId=4099276460822233275&langId=-3&fromAdvanceSearch=AdvanceSearch&pageType=HU&language_selected=&language=&stock=&iehack=☠&offer=&avail=&media=All+Media&title=&author1=&author=&actor1=&actor=&topic=&publisher1=&publisher=&movie_category=All+Categories&movie_category=All+Categories&lang=&lang=&lang1=deutsch&lang1=deutsch&movie_subtitle=&covertype=all&covertype=all&range_price=from-to&range_price=from-to&price_from=&price_to=&range_age=from-to&range_age=from-to&age_from=&age_to=&range_age1=from-to&range_age1=from-to&age1_from=&age1_to=&range_age2=from-to&age2_from=&age2_to=&range_issuedate=from-to&range_issuedate=from-to&issuedate_from=&issuedate_to=&issue1=&issue=&nott=&articleno="
        #: Optional suffix to the search url (may help to filter types, i.e. don't show e-books).
        self.URL_END = u"" # search books
        self.TYPE_BOOK = u"book"
        #: Query parameter to search for the ean/isbn
        self.ISBN_QPARAM = u""
        #: Query param to search for the publisher (editeur)
        self.PUBLISHER_QPARAM = u""
        #: Number of results to display
        self.NBR_RESULTS_QPARAM = u"NOMBRE"
        self.NBR_RESULTS = 12

    def __init__(self, *args, **kwargs):
        """
        """
        self.set_constants()
        super(Scraper, self).__init__(*args, **kwargs)

    def pagination(self):
        """Format the url part to grab the right page.

        Return: a str, the necessary url part to add at the end.
        """
        if self.page == 1 or self.page == u"1" or self.page == "1":
            return ""

        page_qparam = u""
        if type(self.page) in [type(u"u"), type("str")]:
            self.page = int(self.page)
        if self.NBR_RESULTS and self.NBR_RESULTS_QPARAM:
            page_qparam = u"&{}={}&{}={}".format(self.NBR_RESULTS_QPARAM,
                                                 self.NBR_RESULTS,
                                                 "DEBUT",
                                                 self.NBR_RESULTS * (self.page - 1))

        return page_qparam

    def _product_list(self):
        # The table doesn't have its css classes 'even' and 'odd' yet.
        try:
            plist = self.soup.find(class_='searchResultsList')
            if not plist:
                logging.warning(u'Warning: product list is null, we (apparently) didn\'t find any result')
                return []
            plist = plist.find_all('li')
            return plist
        except Exception as e:
            logging.error("Error while getting product list. Will return []. Error: {}".format(e))
            return []

    def _nbr_results(self):
        pass
        try:
            nbr_result = self.soup.find('div', class_='searchResultsOptions').h3
            nbr_result = priceFromText(nbr_result.text)
            if not nbr_result:
                return None
        except Exception, e:
            print "\nError fetching the nb of results:", e

    @catch_errors
    def _details_url(self, product):
        details_url = product.find(class_="prodTitle").h3.a.attrs["href"].strip()
        details_url = self.SOURCE_URL_BASE + details_url
        return details_url

    @catch_errors
    def _title(self, product):
        title = product.find(class_='prodTitle').h3.a.text.strip()
        logging.info(u'title: {}'.format(title))
        return title

    @catch_errors
    def _authors(self, product):
        """Return a list of str.
        """
        authors = product.find(class_='prodSubTitle').h3.a.text.strip()
        authors = authors.split('\n')
        authors = filter(lambda it: it != u"", authors)
        authors = [it.strip() for it in authors]
        logging.info(u'authors: '+ ', '.join(a for a in authors))
        return authors

    @catch_errors
    def _img(self, product):
        img = product.find(class_='icoBook').img['src']
        img = "http:" + img
        return img

    @catch_errors
    def _publisher(self, product):
        pub = product.find(class_="year").text.split('-')[1].strip()
        return pub

    def _price(self, product):
        "The real price, without discounts"
        try:
            price = product.find(class_='bookPrise').text.strip()
            price = priceFromText(price)
            price = priceStr2Float(price)
            return price
        except Exception, e:
            print 'Erreur getting price {}'.format(e)

    @catch_errors
    def _isbn(self, product):
        """With buchlentner, we get the isbn on the product page. We need a
        second request.

        Return: str

        """
        return ""

    @catch_errors
    def _description(self, product):
        """To get with postSearch.
        """
        return ""


    def search(self, *args, **kwargs):
        """Searches books. Returns a list of books.

        From keywords, fires a query on the website and parses the list of
        results to retrieve the information of each book.

        args: list of words

        """
        bk_list = []
        stacktraces = []

        product_list = self._product_list()
        nbr_results = self._nbr_results()
        for product in product_list:
            b = addict.Dict()
            b.search_terms = self.query
            b.data_source = self.SOURCE_NAME
            b.search_url = self.url

            b.details_url = self._details_url(product)
            b.title = self._title(product)
            b.authors = self._authors(product)
            b.price = self._price(product)
            b.publishers = [self._publisher(product)]
            b.card_type = self.TYPE_BOOK
            b.img = self._img(product)
            # b.summary = self._description(product)
            # b.isbn = self._isbn(product)

            bk_list.append(b.to_dict())

        return bk_list, stacktraces

def _isbn(details_url):
    """Get the card isbn

    - details_url: valid url leading to the card's product page

    return: a tuple valid and clean-up isbn (str), the soup
    """
    import isbnlib
    isbn = None
    try:
        log.info("Looking for isbn of {}...".format(details_url))
        req = requests.get(details_url)
        soup = BeautifulSoup(req.content, "lxml")
        isbn = soup.find(class_="col49 floatRight")
        isbn = isbnlib.get_isbnlike(isbn.text)
        isbn = filter(lambda it: it.startswith('978'), isbn)
        if isbn:
            isbn = isbnlib.canonical(isbn[0])
            log.info("Found isbn of url {}: {}".format(details_url, isbn))

    except Exception as e:
        log.error("Error while getting the isbn from url '{}': {}".format(details_url, e))
        return isbn

    return isbn, soup

def _description(details_url, soup=None):
    """TODO:
    """
    if soup:
        desc = soup.find(class_="paging_container3")

        return desc

def postSearch(card, isbn=None, description=None):
    """Get a card (dictionnary) with 'details_url'.

    Gets additional data:
    - isbn
    - description

    Check the isbn is valid. If not, return None. But that shouldn't happen !

    We can give the isbn as a keyword-argument (it can happen when we
    import data from a file). In that case, don't look for the isbn.

    Return a new card (dict) complete with the new attributes.

    """
    card = addict.Dict(card) # easier dot manipulation
    soup = None

    if not isbn:
        card.isbn, soup = _isbn(card.details_url)

    # if not description:
        # card.description = _description(card.details_url, soup=soup)

    card = card.to_dict()
    return card

@annotate(isbn="i", timing="t", words=clize.Parameter.REQUIRED)
@kwoargs("isbn", "timing")
def main(isbn=False, timing=False, *words):
    """
    words: keywords to search (or isbn/ean)
    """
    if not words:
        print "Please give keywords as arguments"
        return
    import time
    start = time.time()
    scrap = Scraper(*words)
    bklist, errors = scrap.search()

    # Getting all the isbn will take longer, even with multiprocessing.
    if isbn:
        import multiprocessing
        pool = multiprocessing.Pool(8)
        # bklist = [postSearch(it) for it in bklist]
        bklist = pool.map(postSearch, bklist)

    end = time.time()
    print " Nb results: {}".format(len(bklist))
    if timing:
        print "Took {} s".format(end - start)
    map(print_card, bklist)

def run():
    exit(clize.run(main))

if __name__ == '__main__':
    clize.run(main)
