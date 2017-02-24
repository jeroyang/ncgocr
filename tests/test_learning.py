#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

"""
test_learning
----------------------------------

Tests for `learning` module.
"""

import unittest

from mcgocr import learning

class TestFeatureExtract(unittest.TestCase):
    def setUp(self):
        self.extractor = learning.Extractor()
    

        
