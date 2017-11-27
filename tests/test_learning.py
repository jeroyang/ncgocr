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

from ncgocr import learning
from ncgocr.extractor import Entity, Pattern, Evidence, Grounds
from ncgocr.concept import Statement, GoData
from txttk.corpus import Sentence, Candidate

class TestFeatureExtract(unittest.TestCase):
    def setUp(self):
        sentence = Sentence('testing patterning boost', 0, 'doc00')
        t0 = Entity('test', 'GO:testing')
        t1 = Pattern('pattern', 'annotator')
        t2 = Entity('boosttest', 'boost')
        e0 = Evidence(t0, 'testing', 0, 7)
        e1 = Evidence(t1, 'patterning', 8, 18)
        e2 = Evidence(t2, 'boost', 19, 24)
        s0 = Statement('GO:testing%000', [e0, e1])
        s1 = Statement('GO:testing%boosttest', [e0, e2])
        c0 = Candidate(s0, [e0, e1], sentence)
        c1 = Candidate(s0, [e0], sentence)
        c2 = Candidate(s1, [e2], sentence)

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
        self.c2 = c2

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
                              ('TEXT=testing patterning', True),
                              ('TEXT[:3]=tes', True),
                              ('TEXT[-3:]=ing', True),
                              ('BOOST', 0)])
        self.assertEqual(result, wanted)

        result = learning.evidence_measurements(self.c2)
        wanted = OrderedDict([('LENGTH', 5),
                              ('TEXT=boost', True),
                              ('TEXT[:3]=boo', True),
                              ('TEXT[-3:]=ost', True),
                              ('BOOST', 1)])
        self.assertEqual(result, wanted)


    def test_bias_measurements(self):

        result = learning.bias_measurements(self.c0)
        wanted = OrderedDict([('SATURATION', 1.0)])
        self.assertEqual(result, wanted)

        result = learning.bias_measurements(self.c1)
        wanted = OrderedDict([('OMIT=pattern', True),
                              ('SATURATION', 0.5)])
        self.assertEqual(result, wanted)
