#!/usr/bin/env python
# -*- coding: utf-8 -*-




import logging
from termcolor import colored

import addict
import clize
import requests
from bs4 import BeautifulSoup
from sigtools.modifiers import annotate
from sigtools.modifiers import autokwoargs

from bookshops.utils import simplecache

from bookshops.utils.baseScraper import BaseScraper
from bookshops.utils.decorators import catch_errors
from bookshops.utils.scraperUtils import is_isbn
from bookshops.utils.scraperUtils import priceFromText
from bookshops.utils.scraperUtils import priceStr2Float
from bookshops.utils.scraperUtils import price_fmt
from bookshops.utils.scraperUtils import print_card
from bookshops.utils.scraperUtils import rmPunctuation
from bookshops.utils.scraperUtils import Timer


logging.basicConfig(level=logging.ERROR)

# logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.ERROR)
log = logging.getLogger(__name__)


class Scraper(BaseScraper):

    query = ""

    def set_constants(self):
        #: Name of the website
        self.SOURCE_NAME = "librairiedeparis"
        #: Base url of the website
        self.SOURCE_URL_BASE = "http://www.librairie-de-paris.fr"
        #: Url to which we just have to add url parameters to run the search
        self.SOURCE_URL_SEARCH = "http://www.librairie-de-paris.fr/listeliv.php?RECHERCHE=simple&LIVREANCIEN=2&MOTS="
        #: advanced url (searcf for isbns)
        self.SOURCE_URL_ADVANCED_SEARCH = "http://www.librairie-de-paris.fr/listeliv.php?RECHERCHE=appro&LIVREANCIEN=2&MOTS="
        #: the url to search for an isbn.
        self.SOURCE_URL_ISBN_SEARCH = self.SOURCE_URL_SEARCH
        #: Optional suffix to the search url (may help to filter types, i.e. don't show e-books).
        self.URL_END = "&x=0&y=0"  # search books
        self.TYPE_BOOK = "book"
        #: Query parameter to search for the ean/isbn
        self.ISBN_QPARAM = ""
        #: Query param to search for the publisher (editeur)
        self.PUBLISHER_QPARAM = "EDITEUR"
        #: Number of results to display
        self.NBR_RESULTS_QPARAM = "NOMBRE"
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
        if self.page == 1 or self.page == "1" or self.page == "1":
            return ""

        page_qparam = ""
        if type(self.page) in [type("u"), type("str")]:
            self.page = int(self.page)
        if self.NBR_RESULTS and self.NBR_RESULTS_QPARAM:
            page_qparam = "&{}={}&{}={}".format(self.NBR_RESULTS_QPARAM,
                                                 self.NBR_RESULTS,
                                                 "DEBUT",
                                                 self.NBR_RESULTS * (self.page - 1))

        return page_qparam

    def _product_list(self):
        try:
            plist = self.soup.find(class_='resultsList')
            if not plist:
                logging.warning('Warning: product list is null, we (apparently) didn\'t find any result')
                return []
            plist = plist.find_all('li', recursive=False)  # only direct <li> children.
            # logging.debug("found plist: {}".format(len(plist)))
            return plist
        except Exception as e:
            logging.error("Error while getting product list. Will return []. Error: {}".format(e))
            return []

    def _nbr_results(self):
        pass
        try:
            nbr_resultl_list = self.soup.find_all('div', class_='result_position')
            nbr_result = nbr_resultl_list[0].text.strip()
            res = nbr_result.split('sur')[-1]
            if not res:
                print('Error matching nbr_result')
            else:
                nbr = int(res.strip())
                self.NBR_RESULTS = nbr
                logging.info('Nb of results: {}'.format(nbr))
                return nbr
        except Exception as e:
            logging.info("Could not fetch the nb of results: {}".format(e))

    @catch_errors
    def _details_url(self, product):
        details_url = product.find(class_="livre_titre").a.attrs["href"].strip()
        details_url = self.SOURCE_URL_BASE + details_url
        return details_url

    @catch_errors
    def _title(self, product):
        title = product.find(class_='livre_titre').text.strip()
        logging.info('title: {}'.format(title))
        return title.capitalize()

    @catch_errors
    def _authors(self, product):
        """Return a list of str.
        """
        authors = product.find(class_='livre_auteur').text  # xxx many authors ? see list_authors
        authors = authors.split('\n')
        # TODO: multiple authors
        authors = [it for it in authors if it != ""]
        authors = [it.strip().capitalize() for it in authors]
        logging.info('authors: ' + ', '.join(a for a in authors))
        return authors

    @catch_errors
    def _img(self, product):
        img = product.find(class_='zone_image').a.img['data-original']
        return img

    @catch_errors
    def _publisher(self, product):
        """
        Return a list of publishers (strings).
        """
        try:
            pub = product.find(class_="editeur").text.split('-')[0].strip()
            # TODO: multiple publishers ?
            return [pub]
        except Exception as e:
            logging.error("Error scraping the publisher(s): {}".format(e))
        return []

    def _price(self, product):
        "The real price (as float), without discounts"
        try:
            price = product.find(class_='item_prix').text.strip()
            price = priceFromText(price)
            price = priceStr2Float(price)
            return price
        except Exception as e:
            print(('Erreur getting price {}'.format(e)))

    @catch_errors
    def _isbn(self, product):
        """
        Return: str
        """
        res = product.find(class_="editeur-collection-parution").text.split('\n')
        isbn = res[-2].strip()
        if not is_isbn(isbn):
            res = [it for it in res if is_isbn(it)]
            isbn = res[0]
        return isbn

    @catch_errors
    def _description(self, product):
        """To get with postSearch.
        """
        pass

    @catch_errors
    def _details(self, product):
        # looks deprecated.
        try:
            logging.warning("not up to date. Looks like unused anyway.")
            details_soup = product.getDetailsSoup()
            tech = details_soup.find(class_='technic')
            li = tech.find_all('li')

            details = {}
            for k in li:
                key = k.contents[0].strip().lower()
                if key == 'ean :':
                    details['isbn'] = k.em.text.strip()
                    logging.info('isbn: ' + details['isbn'])
                elif key == 'editeur :':
                    details['editor'] = k.em.text.strip()
                    logging.info('editor: ' + details['editor'])
                elif key == 'isbn :':
                    details['isbn'] = k.em.text.strip()
                    logging.info('isbn: ' + details['isbn'])

            if not details:
                logging.warning("Warning: we didn't get any details (isbn,…) about the book")
            return details

        except Exception as e:
            print(('Error on getting book details', e))

    @catch_errors
    def _date_publication(self, product):
        date_publication = product.find(class_="MiseEnLigne")
        if date_publication:
            # not available sometimes.
            date_publication = date_publication.text.strip()
        return date_publication

    @catch_errors
    def _availability(self, product):
        """Return: string.
        """
        availability = product.find(class_='item_stock')
        if availability:
            availability = availability.text.strip()
        return availability

    @catch_errors
    def _format(self, product):
        """
        Possible formats :pocket, big.

        - return: str or None
        """
        FMT_POCKET = "Format poche"
        FMT_LARGE = "Grand format"
        fmt = product.find(class_='item_format')
        fmt = fmt.text.strip()
        res = None
        if FMT_LARGE.upper() in fmt.upper():
            res = FMT_LARGE
        elif FMT_POCKET.upper() in fmt.upper():
            res = FMT_POCKET

        return res

    def search(self, *args, **kwargs):
        """Searches books. Returns a list of books.

        From keywords, fires a query and parses the list of
        results to retrieve the information of each book.

        args: liste de mots, rajoutés dans le champ ?q=
        """
        if self.cached_results is not None:
            log.debug("search: hit cache.")
            # print("-- cache hit for ".format(self.ARGS))
            assert isinstance(self.cached_results, list)
            return self.cached_results, []

        bk_list = []
        stacktraces = []

        product_list = self._product_list()
        # nbr_results = self._nbr_results()
        for product in product_list:
            authors = self._authors(product)
            publishers = self._publisher(product)
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
            b.price_fmt = price_fmt(b.price, self.currency)
            b.currency = self.currency
            b.publishers = publishers
            b.pubs_repr = ", ".join(publishers)
            b.card_type = self.TYPE_BOOK
            b.img = self._img(product)
            b.summary = self._description(product)
            b.isbn = self._isbn(product)
            b.availability = self._availability(product)

            bk_list.append(b.to_dict())

        simplecache.cache_results(self.SOURCE_NAME, self.ARGS, bk_list)
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


def _scrape_review(link):
    """
    - link: url to get a review from.

    Return: a dict (or None).
    """
    from goose import Goose
    goo = Goose()
    SHORT_SUMMARY_LENGTH = 400
    LONG_SUMMARY_LENGTH = 2000
    article = goo.extract(url=link)

    if not article.cleaned_text:
        return None

    res = {
        'title': article.title,
        'meta_description': article.meta_description,
        'url': link,
        'short_summary': article.cleaned_text[:SHORT_SUMMARY_LENGTH],
        'long_summary': article.cleaned_text[:LONG_SUMMARY_LENGTH] + "...",
    }
    return res


def reviews(card):
    """Get some reviews on good websites.

    We search on:
    - lmda.net,
    - franceculture.fr

    search engine: framabee.org (longish).

    - card: a card dict with at least title, authors, distributor.

    Return: a list of reviews (dict) with: title, url, short summary, long summary.
    """
    # silent=False
    silent = True
    # Search on lmda.net magazine.
    url = "https://framabee.org/?q=site%3Almda.net+site%3Afranceculture.org {{ search }} &categories=general"
    # on one website only with framabee :/
    # url = "https://framabee.org/?q=site%3Afranceculture.org {{ search }} &categories=general"
    # on all internet:
    # url = "https://framabee.org/?q={{ search }}&categories=general"
    if not card.get('authors') or not card.get('title'):
        return None

    urltosearch = url.replace('{{ search }}', '{}'.format(rmPunctuation(card['title'])))
    logging.info("request of reviews for {}...".format(urltosearch))
    with Timer("request on framabee", silent=silent):   # False: print output.
        req = requests.get(urltosearch)
    if not req.status_code == 200:
        logging.info("status code for request on {}: {}".format(card['title'], req.status_code))
        return None

    soup = BeautifulSoup(req.content, 'lxml')
    try:
        links = soup.find_all(class_='result')
    except Exception as e:
        print(("Error finding results in html: {}".format(e)))
        return None

    if not links:
        return None

    # Links to lmda.net.
    try:
        links = [it.h4.a.attrs['href'] for it in links]
    except Exception as e:
        print(("Error extracting href from soup: {}".format(e)))
        return None

    # only a few reviews. All won't be relevant.
    links = links[:5]

    # Extract the reviews, in parallel.
    revs = []
    try:
        import multiprocessing
        pool = multiprocessing.Pool(8)
        revs = pool.map(_scrape_review, links)
        revs = [it for it in revs if it is not None]

        # don't keep zombi processes; the context manager didn't seem to work.
        pool.terminate()
        pool.join()
    except Exception as e:
        print(("Error getting reviews: {}".format(e)))

    return revs


@annotate(words=clize.Parameter.REQUIRED, review='r')
@autokwoargs()
def main(review=False, *words):
    """
    review: search for reviews on lmda.net, and print a short summary.

    words: keywords to search (or isbn/ean)
    """
    if not words:
        print("Please give keywords as arguments")
        return
    scrap = Scraper(*words)
    bklist, errors = scrap.search()
    print((" Nb results: {}/{}".format(len(bklist), scrap.NBR_RESULTS)))
    bklist = [postSearch(it) for it in bklist]

    # Get reviews:
    if review:
        rev = _scrape_review('http://www.lmda.net/din/tit_lmda.php?Id=17702')
        revs = reviews(bklist[0])
        print(("We got {} reviews:".format(len(revs))))
        for rev in revs:
            print((rev['short_summary']))
            print((colored(rev['url'], 'grey')))

    list(map(print_card, bklist))


def run():
    exit(clize.run(main))


if __name__ == '__main__':
    clize.run(main)
