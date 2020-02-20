#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

from bs4 import BeautifulSoup
import datetime
import logging
import logging.config
import os
import requests

import addict
import clize
import toolz

from sigtools.modifiers import annotate
from sigtools.modifiers import autokwoargs

from bookshops.utils.decorators import catch_errors
from bookshops.utils.scraperUtils import is_isbn
from bookshops.utils.scraperUtils import print_card
from bookshops.utils.scraperUtils import price_fmt

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s',
                    level=logging.ERROR)
log = logging.getLogger(__name__)


class Scraper():
    """
    Dilicom SOAP service.

    This is not a scraper, but we keep the class name for automatic inclusion
    into Abelujo.
    """
    currency = '€'
    query = ""
    isbns = []
    words = []

    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "dilicom"

        # self.WSDL = "http://websfel.centprod.com/v2/DemandeFicheProduit?wsdl"
        self.POST_URL = 'http://websfel.centprod.com/v2/DemandeFicheProduit'
        self.DILICOM_USER = os.getenv('DILICOM_USER')
        self.DILICOM_PASSWORD = os.getenv('DILICOM_PASSWORD')
        self.SOURCE_URL_FICHE_PRODUIT = u"https://dilicom-prod.centprod.com/catalogue/detail_article_consultation.html?ean={}"

    def __init__(self, *args, **kwargs):
        self.set_constants()
        self.USER_AGENT = "Abelujo"
        self.HEADERS = {'SOAPAction': '""', 'Content-Type': 'text/xml; charset=utf-8'}
        # Get the search terms that are isbn
        if args:
            self.isbns = filter(is_isbn, args)

        # Get the search keywords without isbns
        # unsupported by Dilicom.
        # self.words = list(set(args) - set(self.isbns))

    @catch_errors
    def _details_url(self, product):
        return self.SOURCE_URL_FICHE_PRODUIT.format(product.find('ean13').text)

    @catch_errors
    def _title(self, product):
        title = product.find('libetd') or ""
        if title:
            title = title.text
        return title.title()

    @catch_errors
    def _authors(self, product):
        """Return a list of str.
        """
        auteur = product.find('auteur') or ""
        if auteur:
            auteur = auteur.text.title()
        # TODO: multiple authors
        return [auteur]

    @catch_errors
    def _img(self, product):
        # Not available in FEL à la demande.
        return None

    @catch_errors
    def _publishers(self, product):
        """
        Return a list of publishers (strings).
        """
        it = product.find('edit') or ''
        if it:
            it = it.text.title()
        return [it]

    def _price(self, product):
        "The real price, without discounts"
        price = product.find('prix') or 0
        if price:
            price = price.text  # "00013000"
            price = float(price)
            # TODO:
            # - code dispo
            price = price / 1000.0
        return price

    @catch_errors
    def _isbn(self, product):
        """
        Return: str
        """
        ean = product.find('ean13').text
        return ean

    @catch_errors
    def _description(self, product):
        # Not available.
        pass

    @catch_errors
    def _dimensions(self, product):
        """
        Épaisseur, hauteur, largeur, poids.
        Return: tuple of ints.
        """
        res = []
        # All xml nodes are present, but they can be without content.
        for name in ['epaiss', 'haut', 'larg', 'poids']:
            prop = product.find(name) or 0
            if prop and prop.text:
                prop = int(prop.text)
            res.append(prop)

        return tuple(res)

    @catch_errors
    def _date_publication(self, product):
        """
        Return a datetime.date object.
        In the scrapers we returned a string, parsed later in Abelujo.
        """
        date_publication = product.find('dtparu') or ""
        if date_publication:
            date_publication = date_publication.text
            date_publication = datetime.datetime.strptime(date_publication, '%Y%m%d')
        return date_publication

    @catch_errors
    def _availability(self, product):
        """
        Return: int.
        cf codes in scraperUtils.
        We don't store this in Abelujo, as it is supposed to change anytime.
        """
        availability = int(product.find('codedispo').text or '0')
        return availability

    @catch_errors
    def _format(self, product):
        """
        Possible formats :pocket, big.

        - return: str
        """
        # TODO:
        pass

    def bulk_search(self, isbns):
        """
        Search for many isbns, 100 max.
        Do 1 post request.
        Return:
        - tuple list of books (dicts), stacktraces
        """
        bk_list = []
        stacktraces = []
        envelope_skeleton = """<?xml version='1.0' encoding='utf-8'?>
<soap-env:Envelope xmlns:soap-env="http://schemas.xmlsoap.org/soap/envelope/"><soap-env:Body><ns0:demandeFicheProduit xmlns:ns0="http://fel.ws.accelya.com/"><demandeur>{USER}</demandeur><motDePasse>{PASSWORD}</motDePasse>{EANS}<multiple>false</multiple></ns0:demandeFicheProduit></soap-env:Body></soap-env:Envelope>"""
        ean_skeleton = """<ean13s>{EAN}</ean13s>"""

        envelope = envelope_skeleton.replace('{USER}', self.DILICOM_USER)\
                                    .replace('{PASSWORD}', self.DILICOM_PASSWORD)

        EANS = ''
        for isbn in isbns:
            skel = ean_skeleton.replace('{EAN}', isbn)
            EANS = EANS + skel

        envelope = envelope.replace('{EANS}', EANS)

        session = requests.Session()
        req = session.post(self.POST_URL, data=envelope, headers=self.HEADERS)
        if not req.status_code == 200:
            log.error("POST request to Dilicom responded with a non-success status code: {}".format(req.status_code))

        soup = BeautifulSoup(req.text, 'lxml')
        product_list = soup.find_all('elemreponse')  # tags are lowercase.
        code_execution = soup.find('demandeficheproduitrs').find('codeexecution').text
        if code_execution != "OK":
            logging.warning('The SOAP request {} on Dilicom was not OK: {}'.format(self.query, code_execution))

        for product in product_list:
            code = product.find('codeexecution').text
            if code != 'OK':
                log.error(u"Code execution not OK for Dilicom result: {}".format(product))
                continue

            # Strangely, 'diagnostic' is not found with new query method.
            # if product['diagnostic'] == 'UNKNOWN_EAN':
            # log.warn(u"unknown ean: {}".format(product['ean13']))
            # continue

            b = addict.Dict()
            authors = self._authors(product)
            publishers = self._publishers(product)
            b.authors = authors
            b.search_terms = self.query
            b.data_source = self.SOURCE_NAME
            b.date_publication = self._date_publication(product)
            b.details_url = self._details_url(product)
            b.fmt = self._format(product)
            b.title = self._title(product)
            b.authors_repr = ", ".join(authors)
            b.price = self._price(product)
            b.price_fmt = price_fmt(b.price, self.currency)
            b.currency = self.currency
            b.publishers = publishers
            b.pubs_repr = ", ".join(publishers)
            # b.card_type = self.TYPE_BOOK
            b.img = self._img(product)
            b.summary = self._description(product)
            b.isbn = self._isbn(product)
            b.availability = self._availability(product)
            b.thickness, b.height, b.width, b.weight = self._dimensions(product)

            bk_list.append(b.to_dict())

        return bk_list, stacktraces

    def search(self, *args, **kwargs):
        """
        Searches ISBNs, possibly hundreds at once, by batch of 100.
        Returns a tuple: list of books, stacktraces.
        """

        if not self.DILICOM_USER or not self.DILICOM_PASSWORD:
            log.warn(u"Dilicom: no DILICOM_USER or DILICOM_PASSWORD found. Aborting the search.")
            return [], [u"No user and password found for Dilicom connection."]

        # Le FEL à la demande ne permet pas de recherche libre!
        if not self.isbns:
            log.warn(u"Dilicom's FEL à la demande only wants ISBNs, and none was given. Return.")
            return [], [u"Please only search ISBNs on Dilicom."]

        if len(self.isbns) > 100:
            log.debug(u"Searching for more than 100 ISBNs.")

        isbn_groups = toolz.partition_all(100, self.isbns)

        all_results = []
        all_stacktraces = []
        for isbns in isbn_groups:
            res, stacktraces = self.bulk_search(isbns)
            all_results += res
            all_stacktraces += stacktraces

        return all_results, all_stacktraces


@annotate(words=clize.Parameter.REQUIRED)
@autokwoargs()
def main(*words):
    """
    Search for ISBNs. Dilicom's FEL à la demande doesn't accept free search.
    """
    if not words:
        print("Please give ISBNs as arguments")
        return

    isbns = filter(is_isbn, words)
    if not isbns:
        print("Dilicom n'accepte pas la recherche libre par mots-clefs. Veuillez chercher par ISBN(s).")
        exit(0)
    scrap = Scraper(*isbns)
    bklist, errors = scrap.search()

    [print_card(it, details=True) for it in bklist]


def run():
    exit(clize.run(main))


if __name__ == '__main__':
    clize.run(main)
