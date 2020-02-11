#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import logging
import logging.config
import os

import addict
import clize
import zeep

from sigtools.modifiers import annotate
from sigtools.modifiers import autokwoargs

from bookshops.utils.decorators import catch_errors
from bookshops.utils.scraperUtils import is_isbn
from bookshops.utils.scraperUtils import print_card

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.ERROR)

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'zeep.transports': {
            # 'level': 'DEBUG',
            'level': 'WARN',
            'propagate': True,
            'handlers': ['console'],
        },
    }
})

log = logging.getLogger(__name__)

class Scraper():
    """
    Dilicom SOAP service.

    This is not a scraper, but we keep the class name for automatic inclusion into Abelujo.
    """

    query = ""
    isbns = []
    words = []

    strict = True  # zeep option. Without strict, it fails parsing the response.

    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "dilicom"

        self.WSDL = "http://websfel.centprod.com/v2/DemandeFicheProduit?wsdl"
        self.DILICOM_USER = os.getenv('DILICOM_USER')
        self.DILICOM_PASSWORD = os.getenv('DILICOM_PASSWORD')
        #: The url parameter that appears on Dilicom website, without
        #: which we can't see the product.
        #: Example: https://dilicom-prod.centprod.com/catalogue/detail_article_consultation.html?ean=9782840550877&emet=3010xxxx00100
        self.DILICOM_EMET = os.getenv('DILICOM_EMET') or ""
        self.SOURCE_URL_FICHE_PRODUIT = u"https://dilicom-prod.centprod.com/catalogue/detail_article_consultation.html?ean={}&emet={}"

    def __init__(self, *args, **kwargs):
        self.set_constants()
        self.USER_AGENT = "Abelujo"
        self.HEADERS = {'user-agent': self.USER_AGENT}
        # Get the search terms that are isbn
        # xxx: search for many at once.
        if args:
            self.isbns = filter(is_isbn, args)

        # Get the search keywords without isbns
        self.words = list(set(args) - set(self.isbns))

    @catch_errors
    def _details_url(self, product):
        return self.SOURCE_URL_FICHE_PRODUIT.format(product['ean13'], self.DILICOM_EMET)

    @catch_errors
    def _title(self, product):
        title = product['elemGeneraux'] or ""
        if title:
            title = title['libstd']
        return title.capitalize()

    @catch_errors
    def _authors(self, product):
        """Return a list of str.
        """
        auteur = product['elemGeneraux'] or ""
        if auteur:
            auteur = auteur['auteur']
        # TODO: multiple authors
        # XXX: they are all uppercase.
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
        it = product['elemGeneraux'] or ""
        if it:
            it = it['edit'] or ""
        it = it.capitalize()
        return [it]

    def _price(self, product):
        "The real price, without discounts"
        price = product['elemTarif']['prix']  # "00013000"
        price = int(price)
        # TODO:
        # - code dispo
        return price / 1000

    @catch_errors
    def _isbn(self, product):
        """
        Return: str
        """
        ean = product['ean13']
        return ean

    @catch_errors
    def _description(self, product):
        """To get with postSearch.
        """
        # not available.
        pass

    @catch_errors
    def _dimensions(self, product):
        """Épaisseur, hauteur, largeur, poids."""
        elt = product['dimensions']
        if elt and len(elt) > 3:
            return (int(elt['epaiss'] or 0),  # data not always available
                    int(elt['haut'] or 0),
                    int(elt['larg'] or 0),
                    int(elt['poids'] or 0))
        return None, None, None, None

    @catch_errors
    def _date_publication(self, product):
        """
        Return a datetime.date object.
        In the scrapers we returned a string, parsed later in Abelujo.
        """
        date_publication = product['elemGeneraux'] or ""
        if date_publication:
            date_publication = date_publication['dtparu']
            date_publication = datetime.datetime.strptime(date_publication, '%Y%m%d')
        return date_publication

    @catch_errors
    def _availability(self, product):
        """
        Return: int.
        cf codes in scraperUtils.
        We don't store this in Abelujo, as it is supposed to change anytime.
        """
        availability = int(product['elemTarif']['codedispo'] or '0')
        return availability

    @catch_errors
    def _format(self, product):
        """
        Possible formats :pocket, big.

        - return: str or None
        """
        # TODO:
        pass

    def search(self, *args, **kwargs):
        """Searches books. Returns a list of books.

        From keywords, fires a query on decitre and parses the list of
        results to retrieve the information of each book.

        args: liste de mots, rajoutés dans le champ ?q=

        """
        bk_list = []
        stacktraces = []
        if not self.DILICOM_USER or not self.DILICOM_PASSWORD:
            log.warn(u"Dilicom: no DILICOM_USER or DILICOM_PASSWORD found. Aborting the search.")
            return [], [u"No user and password found for Dilicom connection."]

        client = zeep.Client(self.WSDL)
        # Le FEL ne permet pas de recherche libre?!
        if not self.isbns:
            log.warn(u"Dilicom's FEL à la demande only wants ISBNs, and none was given. Return.")
            return [], [u"Please search ISBNs on Dilicom."]
        if len(self.isbns) > 1:
            log.warn("Searching many ISBNs on Dilicom: TODO.")
        with client.settings(strict=False):
            resp = client.service.demandeFicheProduit(
                demandeur=self.DILICOM_USER, motDePasse=self.DILICOM_PASSWORD,
                ean13s=self.isbns[0],
                multiple=False)

        code_execution = resp['codeExecution']
        if code_execution != "OK":
            logging.warning('Searching {} on Dilicom was not OK: {}'.format(self.query, code_execution))
        product_list = resp['elemReponse']

        for product in product_list:
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


@annotate(words=clize.Parameter.REQUIRED)
@autokwoargs()
def main(*words):
    """
    isbns: isbns to search. Dilicom's FEL à la demande doesn't accept free search.
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
