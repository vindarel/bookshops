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

"""Live tests, end to end tests for casadellibro: check that we still
scrape stuff on the existing website.

"""
import os
import unittest

from bookshops.utils.testScraperBase import testScraperBase

from casadellibroScraper import Scraper
from casadellibroScraper import postSearch


class LiveTest(testScraperBase):

    def __init__(self, *args, **kwargs):
        kwargs['scraper'] = Scraper
        kwargs['postSearch'] = postSearch
        super(LiveTest, self).__init__(*args, **kwargs)
        self.scraper = Scraper
        cur_file = os.path.abspath(__file__)
        dirname = os.path.dirname(cur_file)
        self.tfile = os.path.join(dirname, "test_scraper.yaml")


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(LiveTest)
    # Warning, we manually added the tests.
    suite.addTest(LiveTest('testSearch'))
    suite.addTest(LiveTest('testPostSearch'))
    res = unittest.TextTestRunner().run(suite)
    if res.wasSuccessful():
        exit(0)
    else:
        exit(1)
