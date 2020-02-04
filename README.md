# Bibliographic search of BOOKS, CDs and DVDs

This library was initially to search for bibliographic data of books,
and it was expanded for **DVDs** and **CDs**. We can search with
**keywords**, with the **isbn** (so than we can use barcode scanners),
with some advanced search, and we have pagination.

We get the data from existing websites. We scrape:

- for French books:
  - [Dilicom](https://dilicom-prod.centprod.com/)'s profesional provider,
  - http://www.librairie-de-paris.fr See [its doc](doc/frenchscraper.md) ![](http://gitlab.com/vindarel/bookshops/badges/master/build.svg?job=french_scraper)
- for Spain: http://www.casadellibro.com ![](http://gitlab.com/vindarel/bookshops/badges/master/build.svg?job=spanish_scraper)
- for Germany: http://www.buchlentner.de ![](http://gitlab.com/vindarel/bookshops/badges/master/build.svg?job=german_scraper)
- for DVDs: https://www.momox-shop.fr
- and for CDs: https://www.discogs.com (may need more testing)

We retrieve: the title and authors, the price, the isbn, the publisher(s), the cover,...

This library forms the heart of
[Abelujo](https://gitlab.com/vindarel/abelujo/), a free software for
bookshops.

![](cli-search.png)

# Install

Install from pypi:

    pip install bookshops

# Use

## Command line

You can try this lib on the command line with the following commands:
- `livres`: french books
- `dilicom`: Dilicom search (only searches ISBNs, no free search)
- `libros`: spanish books
- `bucher`: german books
- `discogs`: CDs
- `movies`: DVDs
- come and ask for more :)

For example:

    livres antigone

or

    livres 9782918059363

and you get the above screenshot.

**Options**: (this may vary according to the scrapers, check them with `-h`)
- `-i` or `--isbn` to ensure to get all the isbn. The command line
  tool won't get them by default if they need to be fetched with
  another http request for each book. That depends on the websites.

## Settings

The Dilicom interface requires you to set two environment variables:

    export DILICOM_USER="300xxx"
    export DILICOM_PASSWORD="xyz"

## As a library

But most of all, from within your program:

    from bookshops.frFR.librairiedeparis.librairiedeparisScraper import Scraper as frenchScraper

    scraper = frenchScraper("search keywords")
    cards = scraper.search()
    # we get a list of dictionnaries with the title, the authors, etc.


## Advanced search

Work in progress.

You can search ``ed:agone`` to search for a specific publisher.

## Pagination

We do pagination:

    scraper = frenchScraper("search keywords", page=2)


# Why not… ?

## Why not Amazon ?

Amazon kills the book industry and its employees.  But moreover, we
can add value to our results. We can link to a good and independent
bookshop from within our application, we could command books from it,
we could say if it has exemplaries in stock or not, etc.

Technically speaking, the Amazon API web service can be too limiting
and not appropriate. One must register to Amazon Product Advertising
and to AWS, making it more difficult for deployment or independant
users, and it changes way more often than our resailers' websites.

## Why not Google books ?

It has very few data.

## Why not the BNF (Bibliothèque Nationale de France) ?

Because, for bookshops, we need recent books (they enter the BNF
database after a few months), and the price.


# Develop and test

See http://dev.abelujo.cc/webscraping.html

Development mode:

    pip install -e .

Now you can edit the project and run the development version like the
lib is meant to be run, i.e. with the `entry_points`: `livres`,
`libros`, etc.

doc: https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#working-in-development-mode


# Bugs and shortcomings

Note: the Dilicom interface is not concerned by these limitations.

This is webscraping, so it doesn't go without pitfalls:

- the site can go down. It happened already.
- the site can change, it which case we would have to change our
  sraper too. To catch this early we run automatic tests every
  week. The actual website didn't change in 3 years.


# Changelog

## 0.4

- added Dilicom interface. It only provides search of ISBN(s), it doesn't provide free and advanced search.

## 0.3.1

- added search of DVDs
- updated french scrapers (first time needed in four years).

## 0.2.2

- remove deprecated import from ods/csv feature. Might do a simpler one in the future.

## 0.2.1

- german scraper: search by isbn

## 0.2.0

- German scraper
- multiprocessing for the german scraper (from 15 to 9s) (see [issue #1](https://gitlab.com/vindarel/bookshops/issues/1))
- `--isbn` option for it

## 0.1.x

- french, spanish scrapers
- command line tool

# Licence

LGPLv3
