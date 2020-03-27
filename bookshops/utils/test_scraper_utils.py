#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run:
make unit
aka
cd bookshops/utils && pytest
"""

from .scraperUtils import price_fmt

def test_price_fmt():
    assert '10.00 €' == price_fmt(10, None)
    assert '10.00 €' == price_fmt(10.0, None)
    assert 'CHF 10.00' == price_fmt(10, 'CHF')
    assert 'CHF 10' == price_fmt("10", 'chf')
    assert '10 €' == price_fmt("10", None)
    assert '10 €' == price_fmt("10", '€')
    assert '10 €' == price_fmt("10", '€')
