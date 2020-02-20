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

"""
Simple caching mechanism.
Without dependencies.

Not saved to disk, cleared each day.
"""
from __future__ import print_function

import datetime
import logging

logging.basicConfig(format='%(levelname)s [%(name)s]:%(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

CACHED_CONTENT = {
    'source_name': {
        'args': {
            'datetime': 'datetime object',
            'day': 'day (int)',
            'results': ['bklist'],
        }
    },
}


def _stringify_args(args):
    return "{}".format(args)


def get_cache(source_name, args):
    stringified_args = _stringify_args(args)
    now = datetime.datetime.now()
    try:
        CACHED_CONTENT.setdefault(source_name, {})
        res = CACHED_CONTENT[source_name].setdefault(stringified_args, {})
        if res:
            if res.get('day') <= now.day:
                log.debug("Hit cache.")
                # print("-- cache hit for {}".format(args))
                return res.get('results')
            else:
                try:
                    del res
                    del CACHED_CONTENT[source_name][stringified_args]
                    return
                except Exception as e:
                    log.error(u"Could not delete the cache: {}".format(e))
    except Exception as e:
        log.error("Could not save cache: {}".format(e))
        return


def cache_results(source_name, args, results):
    try:
        stringified_args = _stringify_args(args)
        now = datetime.datetime.now()
        global CACHED_CONTENT
        CACHED_CONTENT.setdefault(source_name, {})
        CACHED_CONTENT[source_name].setdefault(stringified_args, {})
        CACHED_CONTENT[source_name][stringified_args] = {
            'day': now.day,
            'datetime': now,
            'results': results,
        }
        log.debug("Saved cache.")
        return True
    except Exception as e:
        log.error(u"Failed to cache results for {} with args {}: {}".
                  format(source_name, args, e))
