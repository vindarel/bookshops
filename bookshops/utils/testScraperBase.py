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

import unittest
import yaml


def filterAttribute(attr, dataresult, fdata):
    """Find a dict from fdata list whose key 'attr' is equal to dataresult's key.

    - fdata: list
    - dataresult: list
    - attr: str

    return: a list
    """
    return [it for it in fdata if it.get(attr) == dataresult.get(attr)]


class testScraperBase(unittest.TestCase):
    """Test the results of search() and postSearch() from a list of
    expected results stored in a yaml file.
    """

    def __init__(self, *args, **kwargs):
        self.scraper = kwargs.pop('scraper')
        self.postSearch = kwargs.pop('postSearch')
        # Full path to the yaml defining tests. Must be overwritten.
        self.tfile = "test_scraper.yaml"
        super(testScraperBase, self).__init__(*args, **kwargs)

    def setUp(self):
        with open(self.tfile, "rb") as f:
            # note: pyyaml doesn't load strings as unicode
            # u"". There's a hack out there, but unittest is clever
            # enough.
            self.datatest = yaml.safe_load(f.read())

    def tearDown(self):
        pass

    def testSearch(self):
        for bktest in self.datatest:
            if bktest.get("search"):
                # Get real results (from cache)
                scrap = self.scraper(*bktest["search"]["search_keywords"].split())
                bklist, errors = scrap.search()
                # We found some results:
                self.assertTrue(bklist)
                # Get the real results that matches the one we described in the yaml.
                dataresults = bktest["search"]["results"]
                filtered_res = filterAttribute("title", dataresults, bklist)
                filtered_res = filterAttribute("ean", dataresults, filtered_res)
                if 'price' in dataresults:
                    filtered_res = filterAttribute("price", dataresults, filtered_res)

                # Test the attributes.
                self.assertTrue(filtered_res)
                for attr in ["title",
                             "ean",  # may be None
                             "price",
                             "publishers",
                             "authors",
                             "img",
                             "date_publication",
                             "details_url"]:
                    # Better: use nose's test generators to test all attributes at once.
                    if attr in dataresults:
                        print(("Checking {}.".format(attr)))
                        self.assertEqual(filtered_res[0].get(attr), dataresults.get(attr))
                    else:
                        print(("Not checking {}".format(attr)))

    def testPostSearch(self):
        for bktest in self.datatest:
            if bktest.get("postSearch"):
                postresult = self.postSearch(bktest.get("postSearch"))
                for attr in bktest["postSearch"]["results"]:
                    self.assertEqual(postresult[attr],
                                     bktest["postSearch"]["results"][attr])
