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
from mock import MagicMock
from collections import OrderedDict

from mcgocr import learning
from mcgocr.extractor import Entity, Pattern, Evidence, Grounds
from mcgocr.concept import Statement, GoData
from experiment.corpus import Candidate

class TestFeatureExtract(unittest.TestCase):
    def setUp(self):
        t0 = Entity('test', 'GO:testing')
        t1 = Pattern('pattern', 'annotator')
        e0 = Evidence(t0, 'testing', 0, 7)
        e1 = Evidence(t1, 'patterning', 8, 17)
        s0 = Statement('GO:testing%000', [e0, e1])
        c0 = Candidate(s0, [e0])
        concept = MagicMock()
        concept.namespace = 'mocked'
        self.godata = {'GO:testing': concept}
        
        self.t0 = t0
        self.t1 = t1
        self.e0 = e0
        self.e1 = e1
        self.c0 = c0
    
    def test_concept_measurements(self):
        result = learning.concept_measurements(self.c0,
                                self.godata)
        wanted = OrderedDict([('GOID', 'GO:testing'),
                              ('STATID', 'GO:testing%000'),
                              ('NAMESPACE', 'mocked')])
        self.assertEqual(result, wanted)
    

        
