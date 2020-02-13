#!/usr/bin/env python
from __future__ import print_function
from dilicomScraper import Scraper

if __name__ == '__main__':
    """
    Run:

    python test_end2end.py
    """
    isbn = '9782732486819'
    scrap = Scraper(isbn)
    bklist, errors = scrap.search()
    assert bklist
    bk = bklist[0]
    assert bk.get('price') == 16.50
    assert bk.get('authors_repr') == 'JONAS/RIHN'
    assert bk.get('data_source') == 'dilicom'
    assert bk.get('date_publication')
    assert bk.get('details_url') == u'https://dilicom-prod.centprod.com/catalogue/detail_article_consultation.html?ean=9782732486819&emet='
    assert bk.get('fmt') == None
    assert bk.get('height') == 320
    assert bk.get('img') == None
    assert bk.get('isbn') == '9782732486819'
    assert bk.get('price') == 16.5
    assert bk.get('publishers') == ['Martiniere j']
    assert bk.get('pubs_repr') == 'Martiniere j'
    assert bk.get('search_terms') == ''
    assert bk.get('summary') == None
    assert bk.get('thickness') == 15
    assert bk.get('title') == 'Habiter le monde'
    assert bk.get('weight') == 692
    assert bk.get('width') == 250
    print('dilicom isbn search OK')
    exit(0)
