#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from termcolor import colored
import os
import re
import sys

import addict
import clize
import requests
# import timedelta
from bs4 import BeautifulSoup
from sigtools.modifiers import annotate
from sigtools.modifiers import autokwoargs
from sigtools.modifiers import kwoargs

from bookshops.utils.baseScraper import BaseScraper
from bookshops.utils.decorators import catch_errors
from bookshops.utils.scraperUtils import is_isbn
from bookshops.utils.scraperUtils import isbn_cleanup
from bookshops.utils.scraperUtils import priceFromText
from bookshops.utils.scraperUtils import priceStr2Float
from bookshops.utils.scraperUtils import print_card
from bookshops.utils.scraperUtils import Timer

logging.basicConfig(level=logging.ERROR) #to manage with ruche


class Scraper(BaseScraper):

    query = ""


    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "momox"
        #: Base url of the website
        self.SOURCE_URL_BASE = u"https://www.momox-shop.fr"
        #: Url to which we just have to add url parameters to run the search
        self.SOURCE_URL_SEARCH = u"https://www.momox-shop.fr/films-C09/?fcIsSearch=1&searchparam="
        #: advanced url (searcf for isbns)
        self.SOURCE_URL_ADVANCED_SEARCH = u""
        #: the url to search for an isbn: no change.
        self.SOURCE_URL_ISBN_SEARCH = self.SOURCE_URL_SEARCH
        #: Optional suffix to the search url (may help to filter types, i.e. don't show e-books).
        self.URL_END = u""
        self.TYPE_BOOK = u"dvd"
        #: Query parameter to search for the ean/isbn
        self.ISBN_QPARAM = u""
        #: Query param to search for the publisher (editeur)
        self.PUBLISHER_QPARAM = u""
        #: Number of results to display
        self.NBR_RESULTS_QPARAM = u""
        self.NBR_RESULTS = 12

    def __init__(self, *args, **kwargs):
        """
        """
        self.set_constants()
        super(Scraper, self).__init__(*args, **kwargs)

    def _product_list(self):
        try:
            plist = self.soup.find(id='body')
            if not plist:
                logging.warning(u'Warning: product list is null, we (apparently) didn\'t find any result')
                return []
            plist = plist.find_all(class_='mx-product-list-item clearfix')
            return plist
        except Exception as e:
            logging.error("Error while getting product list. Will return []. Error: {}".format(e))
            return []

    def _nbr_results(self):
        try:
            nb = self.soup.find( class_='mx-search-result-message')
            nb = nb.text.strip()
            res = re.search('\d+', nb)
            if not res:
                logging.info('Did not match nb of results')
            else:
                nbr = res.group(0)
                self.nbr_result = int(nbr)
                logging.info(u'Nb of results: {}'.format(nbr))
                return self.nbr_result
        except Exception, e:
            logging.info(u"Could not fetch the nb of results: {}".format(e))

    @catch_errors
    def _details_url(self, product):
        details_url = product.find(class_="mx-product-list-item-title").a.attrs["href"].strip()
        return details_url

    @catch_errors
    def _title(self, product):
        title = product.find(class_='mx-product-list-item-title').text.strip()
        logging.info(u'title: {}'.format(title))
        return title

    @catch_errors
    def _authors(self, product):
        """Return a list of str.
        """
        authors = product.find(class_='mx-product-list-item-manufacturer').text.strip()
        authors = authors.split('\n')
        authors = filter(lambda it: it.strip() not in [u"", "", u"de:", "de:"], authors)
        authors = [it.strip() for it in authors]
        logging.info(u'authors: {}'.format(authors))
        return authors

    @catch_errors
    def _img(self, product):
        img = product.find(class_='mx-product-image').attrs['src']
        return img

    def _price(self, product):
        "The real price, without discounts"
        try:
            price = product.find(class_='mx-strikethrough').text.strip()
            price = priceFromText(price)
            price = priceStr2Float(price)
            return price
        except Exception, e:
            logging.info('Erreur getting price {}'.format(e))

    @catch_errors
    def _isbn(self, product):
        pass

    @catch_errors
    def _details(self, product):
        """
        Information on a product's page.
        Exple: https://www.momox-shop.fr/lea-fehner-les-ogres-fr-import-dvd-M0B01FV3FM3K.html

        - product: parsed html (soup).
        """
        title = product.find(id="test_product_name").text.strip()
        img = product.find(id="product_img").attrs['src']
        # TODO: authors
        return {
            'isbn': self.isbn,
            'title': title,
            'img': img,
            'details_url': self.url_product_page,
        }

    def search(self, *args, **kwargs):
        """
        Searches DVDs. Returns a tuple: list of DVDs (dicts), stacktraces.
        """
        bk_list = []
        stacktraces = []

        if self.ISBN_SEARCH_REDIRECTED_TO_PRODUCT_PAGE:
            card = self._details(self.soup)
            return [card], stacktraces

        product_list = self._product_list()
        nbr_results = self._nbr_results()
        for product in product_list:
            authors = self._authors(product)
            b = addict.Dict()
            b.search_terms = self.query
            b.data_source = self.SOURCE_NAME
            b.search_url = self.url
            b.details_url = self._details_url(product)
            b.title = self._title(product)
            b.authors = authors
            b.authors_repr = ", ".join(authors)
            b.price = self._price(product)
            b.card_type = self.TYPE_BOOK
            b.img = self._img(product)

            bk_list.append(b.to_dict())

        return bk_list, stacktraces


@annotate(words=clize.Parameter.REQUIRED, review='r')
@autokwoargs()
def main(review=False, *words):
    """
    review: search for reviews on lmda.net, and print a short summary.

    words: keywords to search (or isbn/ean)
    """
    if not words:
        print "Please give keywords as arguments"
        return
    scrap = Scraper(*words)
    bklist, errors = scrap.search()
    print " Nb results: {}".format(len(bklist))

    map(print_card, bklist)

def run():
    exit(clize.run(main))

if __name__ == '__main__':
    clize.run(main)
