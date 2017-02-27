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
from experiment.corpus import Sentence, Candidate

class TestFeatureExtract(unittest.TestCase):
    def setUp(self):
        sentence = Sentence('testing patterning good', 0, 'doc00')
        t0 = Entity('test', 'GO:testing')
        t1 = Pattern('pattern', 'annotator')
        e0 = Evidence(t0, 'testing', 0, 7)
        e1 = Evidence(t1, 'patterning', 8, 18)
        s0 = Statement('GO:testing%000', [e0, e1])
        c0 = Candidate(s0, [e0, e1], sentence)
        c1 = Candidate(s0, [e0], sentence)
        
        concept = MagicMock()
        concept.namespace = 'mocked'
        
        self.godata = {'GO:testing': concept}
        self.sentence = sentence
        self.t0 = t0
        self.t1 = t1
        self.e0 = e0
        self.e1 = e1
        self.c0 = c0
        self.c1 = c1
    
    def test_concept_measurements(self):
        result = learning.concept_measurements(self.c0,
                                self.godata)
        wanted = OrderedDict([('GOID', 'GO:testing'),
                              ('STATID', 'GO:testing%000'),
                              ('NAMESPACE', 'mocked')])
        self.assertEqual(result, wanted)
    
    def test_evidence_measurements(self):
        result = learning.evidence_measurements(self.c0)
        wanted = OrderedDict([('LENGTH', 18), 
                              ('TEXT', 'testing patterning'),
                              ('TEXT[:3]', 'tes'),
                              ('TEXT[-3:]', 'ing')])
        self.assertEqual(result, wanted)

    def test_bias_measurements(self):
        
        result = learning.bias_measurements(self.c0)
        wanted = OrderedDict([('OMIT', []),
                              ('SATURATION', 1.0)])
        self.assertEqual(result, wanted)
        
        result = learning.bias_measurements(self.c1)
        wanted = OrderedDict([('OMIT', ['pattern']),
                              ('SATURATION', 0.5)])
        self.assertEqual(result, wanted)
        