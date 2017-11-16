#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

"""
test_concept
----------------------------------

Tests for `concept` module.
"""

import unittest

from ncgocr import concept as c
from ncgocr import gopattern

PATTERN_PATH = 'tests/pattern_definition.txt'

class TestIndex(unittest.TestCase):

    def setUp(self):
        self.index0 = c.Index()
        self.index0.update({'a': {1, 2}, 'b': {3, 4}})
        self.index1 = c.Index()
        self.index1.update({'a': {2, 9}, 'c': {5, 6}})

    def test_add(self):
        result = self.index0 + self.index1
        wanted = c.Index()
        wanted.update({'a': {1, 2, 9}, 'b': {3, 4}, 'c':{5, 6}})
        self.assertEqual(result, wanted)

    def test_missing(self):
        self.index0.use_default = True
        self.assertEqual(self.index0['k'], set())
        self.assertIn('k', self.index0)

        self.index0.use_default = False
        self.assertEqual(self.index0['m'], set())
        self.assertNotIn('m', self.index0)

class TestSplitFunctions(unittest.TestCase):
    def setUp(self):
        label = 'upregulation of gene slicing via miRNA'
        self.label = label
        self.main_trunk = c.Trunk('upregulation of gene slicing', 'main', 0, len('upregulation of gene slicing'))
        self.constraint_trunk = c.Trunk('miRNA', 'constraint', label.index('miRNA'), len(label))

    def test_clean(self):
        fragment = 'to Hello Kitty'
        wanted = 'Hello Kitty'
        result = c._clean(fragment)
        self.assertEqual(result, wanted)

        fragment = 'Mickey in'
        wanted = 'Mickey'
        result = c._clean(fragment)
        self.assertEqual(result, wanted)

    def test_split_trunk(self):
        label = self.label
        main_trunk = self.main_trunk
        constraint_trunk = self.constraint_trunk
        wanted = [main_trunk, constraint_trunk]
        result = c.split_trunk(label)
        self.assertEqual(result, wanted)

    def test_split_pattern(self):
        regex_in = gopattern.PatternManager.from_definition(PATTERN_PATH).regex_in()
        trunk = self.main_trunk
        p0 = (c.Pattern, 'positregulate', 'upregulation', 0, len('upregulation'))
        e0 = (c.Entity, 'gene slicing', 'gene slicing', self.label.index('gene slicing'), len(trunk.text))
        wanted = [p0, e0]
        result = c.split_pattern(trunk, regex_in)
        self.assertEqual(result, wanted)

        trunk = self.constraint_trunk
        c0 = (c.Constraint, 'miRNA', 'miRNA', self.label.index('miRNA'), len(self.label))
        wanted = [c0]
        result = c.split_pattern(trunk, regex_in)
        self.assertEqual(result, wanted)

    def test_evidence_split(self):
        regex_in = gopattern.PatternManager.from_definition(PATTERN_PATH).regex_in()
        goid = 'GO:testing'
        label = 'upregulation of gene slicing via miRNA'
        trunk = self.main_trunk
        t1 = c.Pattern('positregulate', 'annotator')
        e1 = c.Evidence(t1, 'upregulation', 0, len('upregulation'))
        t2 = c.Entity('gene slicing', 'GO:testing')
        e2 = c.Evidence(t2, 'gene slicing', self.label.index('gene slicing'), len(trunk.text))
        t3 = c.Constraint('miRNA', 'GO:testing')
        e3 = c.Evidence(t3, 'miRNA', self.label.index('miRNA'), len(self.label))
        result = c.evidence_split(goid, label, regex_in)
        wanted = [e1, e2, e3]
        self.assertEqual(result, wanted)

class TestEvidence(unittest.TestCase):

    def setUp(self):
        term0 = c.Term('lemma', 'GO:testing')
        term1 = c.Term('text', 'GO:testing')
        self.evidence0 = c.Evidence(term0, 'lemma', 12, 17)
        self.evidence1 = c.Evidence(term1, 'text', 18, 22)

    def test_sub(self):
        e0 = self.evidence0
        e1 = self.evidence1
        result = e1-e0
        self.assertEqual(result, 1)

        result = e0-e1
        self.assertEqual(result, -10)

class TestStatement(unittest.TestCase):

    def setUp(self):
        self.t0 = c.Term('lemma', 'GO:testing')
        self.t1 = c.Term('text', 'GO:testing')
        self.t2 = c.Pattern('regulation', 'annotator')
        self.e0 = c.Evidence(self.t0, 'lemma', 12, 17)
        self.e1 = c.Evidence(self.t1, 'text', 18, 22)
        self.e2 = c.Evidence(self.t2, 'increase', 23, 31)
        self.s0 = c.Statement('s0', [self.e0, self.e2])
        self.s1 = c.Statement('s1', [self.e1, self.e2])

    def test_eq(self):
        self.assertEqual(self.s0, self.s1)

    def test_hash(self):
        h0 = hash(self.s0)
        h1 = hash(self.s1)
        self.assertNotEqual(h0, h1)

    def test_terms(self):
        result = self.s0.terms()
        wanted = [self.t0, self.t2]
        self.assertEqual(result, wanted)

    def test_eq_terms(self):
        result = self.s0.eq_terms(self.s1)
        wanted = [(self.t1, self.t0)]
        self.assertEqual(result, wanted)

class TestCluster(unittest.TestCase):
    def setUp(self):
        self.t0 = c.Entity('number', 'GO:testing')
        self.t1 = c.Entity('amount', 'GO:testing')
        self.t2 = c.Entity('size', 'GO:testing')
        self.t3 = c.Entity('count', 'GO:testing')
        self.c0 = c.Cluster(self.t0, {self.t0, self.t1})
        self.c1 = c.Cluster(self.t2, {self.t2, self.t3})

    def test_fragments(self):
        result = self.c0.fragments()
        wanted = {'number', 'amount'}
        self.assertEqual(result, wanted)

    def test_add(self):
        cluster = self.c0
        cluster.add(self.t2)
        result = cluster.terms
        wanted = {self.t0, self.t1, self.t2}
        self.assertEqual(result, wanted)

    def test_merge(self):
        c0, c1 = self.c0, self.c1
        c0.merge(c1)
        wanted = c.Cluster(self.t0, {self.t0, self.t1, self.t2, self.t3})
        self.assertEqual(c0, wanted)

class TestClusterBook(unittest.TestCase):
    def setUp(self):
        self.t0 = c.Entity('number', 'GO:testing')
        self.t1 = c.Entity('amount', 'GO:testing')
        self.c0 = c.Cluster(self.t0, {self.t0, self.t1})

        self.t2 = c.Entity('size', 'GO:testing')
        self.t3 = c.Entity('count', 'GO:testing')
        self.c1 = c.Cluster(self.t2, {self.t2, self.t3})

        self.t4 = c.Entity('teacher', 'GO:testing')
        self.t5 = c.Entity('tutor', 'GO:testing')
        self.c2 = c.Cluster(self.t4, {self.t4, self.t5})

        self.cb = c.ClusterBook()

    def test_preferred_term(self):
        cb = self.cb
        cb.add(self.c0)
        cb.merge(self.c0, self.c1)
        result = cb.preferred_term(self.t3)
        wanted = self.t0
        self.assertEqual(result, wanted)

    def test_add(self):
        cb = self.cb
        cb.add(self.c0)
        cb.add(self.c1)
        self.assertEqual(cb.clusters, {self.c0, self.c1})
        self.assertIs(cb.index[self.t1], self.c0)

    def test_merge(self):
        cb = self.cb
        cb.add(self.c0)
        cb.merge(self.c0, self.c1)
        merged_cluster = cb.index[self.t1]
        self.assertEqual(merged_cluster.terms, {self.t0, self.t1, self.t2, self.t3})

    def test_merge_term(self):
        cb = self.cb
        cb.add(self.c0)
        cb.merge_term(self.t1, self.t3)
        merged_cluster = cb.index[self.t1]
        self.assertEqual(merged_cluster.terms, {self.t0, self.t1, self.t3})

    def test_add_terms(self):
        cb = self.cb
        cb.add(self.c0)
        cb.add(self.c1)
        cb.add(self.c2)
        cb.merge(self.c0, self.c1)
        cb.add_terms([self.t4, self.t5])
        self.assertIn(self.t4, cb.index)
        self.assertIn(self.t5, cb.index)

    def test_simplity(self):
        self.t0 = c.Entity('vitamin C', 'GO:000')
        self.t1 = c.Entity('ascorbic acid', 'GO:000')
        self.t2 = c.Entity('ascorbate', 'GO:000')
        self.c0 = c.Cluster(self.t0, {self.t0, self.t1, self.t2})

        self.t3 = c.Entity('vitamin C', 'GO:111')
        self.t4 = c.Entity('L-ascorbic acid', 'GO:111')
        self.t5 = c.Entity('L-ascorbate', 'GO:111')
        self.c1 = c.Cluster(self.t3, {self.t3, self.t4, self.t5})

        self.t6 = c.Entity('vitamin B12', 'GO:222')
        self.t7 = c.Entity('cobalamin', 'GO:222')
        self.c2 = c.Cluster(self.t6, {self.t6, self.t7})

        cb = self.cb
        cb.add(self.c0)
        cb.add(self.c1)
        cb.add(self.c2)
        result = cb.simplify(0.2)
        self.assertNotEqual(cb.preferred_term(self.t1),
                            cb.preferred_term(self.t3))
        self.assertNotEqual(cb.preferred_term(self.t1),
                            cb.preferred_term(self.t6))
        self.assertEqual(result.preferred_term(self.t1),
                         result.preferred_term(self.t3))
        self.assertNotEqual(result.preferred_term(self.t1),
                         result.preferred_term(self.t6))



class TestClusterFunctions(unittest.TestCase):

    def setUp(self):
        self.t0 = c.Entity('vitamin C', 'GO:000')
        self.t1 = c.Entity('ascorbic acid', 'GO:000')
        self.t2 = c.Entity('ascorbate', 'GO:000')
        self.c0 = c.Cluster(self.t0, {self.t0, self.t1, self.t2})

        self.t3 = c.Entity('vitamin C', 'GO:111')
        self.t4 = c.Entity('L-ascorbic acid', 'GO:111')
        self.t5 = c.Entity('L-ascorbate', 'GO:111')
        self.c1 = c.Cluster(self.t3, {self.t3, self.t4, self.t5})

        self.t6 = c.Entity('vitamin B12', 'GO:222')
        self.t7 = c.Entity('cobalamin', 'GO:222')
        self.c2 = c.Cluster(self.t6, {self.t6, self.t7})

    def test_has_common(self):
        self.assertTrue(c.has_common(self.c0, self.c1))
        self.assertFalse(c.has_common(self.c1, self.c2))

    def test_jaccard(self):
        result = c.jaccard(self.c0, self.c1)
        wanted = 3.0/7
        self.assertEqual(result, wanted)

    def test_sim(self):
        result = c.sim(self.c0, self.c1)
        wanted = 3.0/7
        self.assertEqual(result, wanted)

        result = c.sim(self.c0, self.c2)
        wanted = 0
        self.assertEqual(result, wanted)

class TestConcept(unittest.TestCase):

    def setUp(self):
        goid = 'GO:testing'
        name = 'testing concept'
        namespace = 'biological_process'
        synonym_list = ['testing idea', 'fake concept']
        parent_list = []
        self.concept = c.Concept(goid, name, namespace, synonym_list, parent_list)

    def test_init(self):
        self.assertEqual(self.concept.ns, 'BP')
        self.assertEqual(self.concept.density, -1)
