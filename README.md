
# Web scraping to get book informations

This library is to get book informations. We can search with **keywords**,
with the **isbn**, with an **advanced search**, and do **pagination**.

We get the data from existing websites. We scrape:

- for French books, http://www.librairie-de-paris.fr (at first Decitre, but it's less complete)
- for Spain: http://www.casadellibro.com
- for Germany: *the site went down !* This is the danger of webscraping.

we get: the title and authors, the price, the publisher(s), the cover, etc

<img src="cli-search.png"</img>

## Import data from an ods or csv file

If your file has an 'isbn' and a 'quantity' column, it's easy, we will
find all the book information.

If it has the title and the publisher, it's doable but error prone. We
can still do it, but you shall do an inventory of your stock
afterwards.

See the ``odsimport`` module. It gives back a json. It's your
responsibility to add what you want in your database (this is done in
Abelujo).

Usable, but work in progress.

### Accepted format and columns

We can read ods and csv files.

- a file with an "isbn" and "quantity" column,
- a file with columns "title", "publisher", "isbn" (optionnal in this
  case), "shelf", "distributor", "quantity". There is **no** "price"
  column. "authors" is optionnal (it can help to fetch the correct
  book).

If the file has no headers, use the "odsettings.py" configuration file
(in particular, to set the csv delimiter, either "," or ";").


## Why not Amazon ?

Amazon kills the book industry and its employees.  But moreover, with
can link to a good and independent bookshop from within the
application, and… we learn a lot in doing this !

## Why not Google books ?

It has very few data.

## Why not the BNF (Bibliothèque Nationale de France) ?

Because, for bookshops, we need recent books (the BNF takes a few
months), up to date information. There isn't a lot of tools either.


# Install

This lib isn't on pypi yet.

It is usable, but not mature.

It's used as a git submodule at Abelujo https://gitlab.com/vindarel/abelujo

# Use

So, for now you need to clone this repo.

To try it out, go to a scraper directory:

    cd frFR/librairiedeparis/
    python librairiedeparisScraper.py 9782918059363

and you get the above screenshot.

## Advanced search

Work in progress.

You can search ``ed:agone`` to search for a specific publisher.

## Pagination

We do pagination.


# Develop and test

See http://dev.abelujo.cc/webscraping.html

Development mode:

    pip install -e .

Now you can edit the project and run the development version like the
lib is meant to be run, i.e. with the `entry_points`: `livres`,
`libros`, etc. 

doc: https://python-packaging-user-guide.readthedocs.org/en/latest/distributing/#working-in-development-mode


# Bugs and shortcomings

This is webscraping, so it doesn't go without pitfalls:

- the site can go down. It happened already.
- the site can change, it which case we would have to change our
  sraper too. This can be catched early with automated and frequent
  tests (work ongoing).

# Licence

LGPLv3
