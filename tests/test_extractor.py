#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

"""
test_extractor
----------------------------------

Tests for `extractor` module.
"""

import unittest

from mcgocr import extractor as ex

class TestFunctions(unittest.TestCase):
    
    def test_fit_border(self):
        text = 'very tedious'
        span = (5, 8)
        result = ex._fit_border(text, span)
        self.assertEqual(result, False)
        
        text = 'this ted bear'
        span = (5, 8)
        result = ex._fit_border(text, span)
        self.assertEqual(result, True)
        
class TestIndex(unittest.TestCase):
    
    def setUp(self):
        self.index0 = ex.Index()
        self.index0.update({'a': {1, 2}, 'b': {3, 4}})
        self.index1 = ex.Index()
        self.index1.update({'a': {2, 9}, 'c': {5, 6}})
    
    def test_add(self):
        result = self.index0 + self.index1
        wanted = ex.Index()
        wanted.update({'a': {1, 2, 9}, 'b': {3, 4}, 'c':{5, 6}})
        self.assertEqual(result, wanted)
        
    def test_missing(self):
        self.index0.use_default = True
        self.assertEqual(self.index0['k'], set())
        self.assertIn('k', self.index0)
        
        self.index0.use_default = False
        self.assertEqual(self.index0['m'], set())
        self.assertNotIn('m', self.index0)


