#!/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2014 - 2020 The Abelujo Developers
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

import logging

import clize
import lxml.html
import requests
from sigtools.modifiers import annotate
from sigtools.modifiers import kwoargs

from bookshops.utils.scraperUtils import print_card
from bookshops.utils.scraperUtils import Timer

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

DATA_SOURCE_NAME = "Discogs.com"
DEFAULT_IMG_SIZE = "150"  # "90" or "150"
TYPE_CD = "cd"
TYPE_VINYL = "vinyl"


class Scraper(object):
    """Scrap the discogs search results.

    DISCLAIMER: the official python client has been broken since more than a
    year. We should use it when available.

    In the heart of this scraping are a couple of xpath expressions, in
    the search method.

    """

    def __init__(self, *args, **kwargs):
        """
        """
        self.discogs_url = "http://discogs.com"
        self.search_prefix = "/search/?q="
        self.search_suffix = "&type=all"
        self.url = ""

        self.headers = {"User-Agent": "Abelujo (temp) scraper"}

        if args:
            query = "+".join(arg for arg in args)
            self.url = self.discogs_url + self.search_prefix + query + self.search_suffix
            log.debug("we'll search: %s" % self.url)

    def search(self):
        to_ret = []
        title, cover, details_url = "", "", ""
        req = requests.get(self.url, headers=self.headers)
        tree = lxml.html.fromstring(req.content)
        # Get the 50 (first page) references
        cards = tree.xpath("//*[contains(@class, 'card_large')]")

        for el in cards:
            try:
                title = el.xpath("h4//text()")[0]
                authors = el.xpath("h5//a/text()")
                cover = el.xpath("*//img/@src")[0]
                details_url = el.xpath("h4//a/@href")[0]
            except Exception as e:
                log.error(e)

            to_ret.append({"title": title,
                           "authors": authors,
                           "details_url": self.discogs_url + details_url,
                           "img": cover,
                           "card_type": TYPE_CD,
                           "data_source": "discogs",  # same name as in abelujo views.
                           })

        return to_ret, []  # stacktraces


@annotate(words=clize.Parameter.REQUIRED)
@kwoargs()
def main(*words):
    """
    words: keywords to search (or isbn/ean)
    """
    if not words:
        print "Please give keywords as arguments"
        return
    with Timer("call to scraper", silent=True):
        scrap = Scraper(*words)
        bklist, errors = scrap.search()
        print " Nb results: {}".format(len(bklist))
        map(print_card, bklist)


def run():
    exit(clize.run(main))


if __name__ == '__main__':
    clize.run(main)
