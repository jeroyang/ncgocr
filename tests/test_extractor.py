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

from ncgocr import extractor as ex

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


class TextFunctions2(unittest.TestCase):
    def test_nearest_evidences(self):
        positional_index = {'a': {(1, 1), (3, 3)},
                            'b': {(2, 2), (5, 5)},
                            'c': {(4, 4)}}
        wanted_terms = ['a', 'b']
        current_position = 3
        result = ex.nearest_evidences(current_position, wanted_terms, positional_index)
        wanted = [2, 3]
        self.assertEqual(result, wanted)
