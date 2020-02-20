#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 - 2019 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

import re
import string
import time

import addict
from termcolor import colored
import string as string_mod

CODES_DISPO = {
    6: u"Arrêt de commercialisation",
    1: u"Disponible",  # ?
    0: u"disponibilité inconnue",
}


class Timer(object):
    """
    Context manager. If not muted, prints its mesure on stdout.

    Usage:

    with Timer("short description"[, silent=True]):
        pass

    - silent: False: prints its mesure (default). True, do nothing.

    """
    def __init__(self, name="", silent=False):
        if not name:
            name = "Timer"
        self.name = name
        self.silent = silent

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, exc_type, exc_val, traceback):
        self.end = time.time()
        if not self.silent:
            print "{} lasted: {} sec".format(self.name, self.end - self.start)


def priceFromText(text):
    """Extract the price from text with regexp.
    """
    match = re.search('\d+[,\.]?\d*', text)
    price = match.group()
    return price


def priceStr2Float(str):
    """Gets a str, performs basic formatting and returns a Float.

    Formatting: replaces commas with dots.

    arg: string
    returns: Float
    """
    return float(str.replace(",", "."))


def isbn_cleanup(isbn):
    """Clean the string and return only digits. (actually, remove all
    punctuation, most of all the dash).

    Because a bar code scanner only prints digits, that's the format
    we want in the database.

    - isbn: a str / unicode
    - return: a string, with only [0-9] digits.

    TODO: replace with isbnlib.canonical

    """
    # note: we duplicated this function in models.utils
    res = isbn
    if isbn:
        # note: punctuation is just punctuation, not all fancy characters like « or @
        punctuation = set(string.punctuation)
        res = "".join([it for it in isbn if it not in punctuation])

    return res


def is_isbn(it):
    """Return True is the given string is an ean or an isbn, i.e:

    - is of type str (or unicode). The string must contain only
      alpha-numerical characters.
    - length of 13 or 10

    XXX: look in isbnlib
    """
    # note: method duplicated from models.utils
    ISBN_ALLOWED_LENGTHS = [13, 10]
    res = False
    pattern = re.compile("[0-9]+")
    if (isinstance(it, unicode) or isinstance(it, str)) and \
       len(it) in ISBN_ALLOWED_LENGTHS and \
       pattern.match(it):
        res = True

    return res


def rmPunctuation(it):
    """
    Remove all punctuation from the string.

    return: str
    """
    # https://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
    # ret = it.translate(None, string.punctuation) # faster, not with unicode
    if not it:
        return it
    exclude = set(string_mod.punctuation)
    st = ''.join(ch for ch in it if ch not in exclude)
    return st


def print_card(card, details=False):
    """Pretty output for the console.
    """
    card = addict.Dict(card)
    COL_WIDTH = 30
    TRUNCATE = 19
    currency = card.get('currency', '€')

    print colored(" " + card.title, "blue")
    # Great formatting guide: https://pyformat.info/ :)
    print "   {:{}.{}} {:>{}.{}} {:4}   {}".\
        format(", ".join(card.authors or []), COL_WIDTH, TRUNCATE,
               ", ".join(card.publishers or []), COL_WIDTH, TRUNCATE,
               price_fmt(card.price, currency),
               card.isbn if card.isbn else "")
    if details:
        print u"   Date publication: {}".format(card.date_publication)
        if card.get('availability'):
            print u"   {}".format(CODES_DISPO.get(card.availability))


def price_fmt(price, currency):
    """
    Return: a string, with the price formatted correctly with its currency symbol.

    Exemple: 10 € or CHF 10
    """
    if price is None or isinstance(price, str) or not currency:
        return price
    if currency.lower() == 'chf':
        return 'CHF {:.2f}'.format(price)
    else:
        return '{:.2f} €'.format(price)
