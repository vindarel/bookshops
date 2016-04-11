
# Datasources: Web scraping to get book informations

This library is to get book informations. We can search with **keywords**,
with the **isbn**, with an **advanced search**, and do **pagination**.

We get the data from existing websites. We scrape:

- for French books, http://www.librairie-de-paris.fr (at first Decitre, but it's less complete)
- for Spain: http://www.casadellibro.com
- for Germany: *the site went down !* This is the danger of webscraping.

we get: the title and authors, the price, the publisher(s), the cover, etc

## Why not Amazon ?

Amazon kills the book industry and its employees.  But moreover, with
can link to a good and independent bookshop from within the
application, and… we learn a lot in doing this !

## Why not Google books ?

It has very few data.

## Why not the BNF (Bibliothèque Nationale de France) ?

Because, for bookshops, we need the price and recent books.


# Install

This lib isn't on pypi yet.

It is usable, but not mature.

It's used as a git submodule at Abelujo https://gitlab.com/vindarel/abelujo

# Use

So, for now you need to clone this repo.

To try it out, go to a scraper directory:

    cd frFR/librairiedeparis/
    python librairiedeparisScraper.py 9782918059363

and you get

```
Nb results: 1
{'authors': [u'Collectif'],
 'card_type': u'book',
 'data_source': 'librairiedeparis',
 'details_url': u'http://www.librairie-de-paris.fr/9782805920677-critiquer-foucault-collectif/',
 'img': 'http://images.titelive.com/677/9782805920677_1_m.jpg',
 'isbn': u'9782805920677',
 'price': 20.0,
 'publishers': [u'Aden Belgique'],
 'search_terms': '9782805920677',
 'search_url': u'http://www.librairie-de-paris.fr/listeliv.php?RECHERCHE=simple&LIVREANCIEN=2&MOTS=9782805920677&x=0&y=0',
 'summary': None,
 'title': u'Critiquer Foucault'}
```

## Advanced search

Work in progress.

You can search ``ed:agone`` to search for a specific publisher.

## Pagination

We do pagination.


# Develop and test

See http://dev.abelujo.cc/webscraping.html

# Bugs and shortcomings

This is webscraping, so it doesn't go without pitfalls:

- the site can go down. It happened already.
- the site can change, it which case we would have to change our
  sraper too. This can be catched early with automated and frequent
  tests (work ongoing).
