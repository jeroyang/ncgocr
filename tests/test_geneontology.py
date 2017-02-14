#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

"""
test_geneontology
----------------------------------

Tests for `geneontology` module.
"""

import unittest

from mcgocr import geneontology as g
from mcgocr import gopattern

PATTERN_PATH = 'tests/pattern_definition.txt'


class TestSplitFunctions(unittest.TestCase):
    def setUp(self):
        label = 'upregulation of gene slicing via miRNA'
        self.label = label
        self.main_trunk = g.Trunk('upregulation of gene slicing', 'main', 0, len('upregulation of gene slicing'))
        self.constraint_trunk = g.Trunk('miRNA', 'constraint', label.index('miRNA'), len(label))
    
    def test_clean(self):
        fragment = 'to Hello Kitty'
        wanted = 'Hello Kitty'
        result = g._clean(fragment)
        self.assertEqual(result, wanted)
        
        fragment = 'Mickey in'
        wanted = 'Mickey'
        result = g._clean(fragment)
        self.assertEqual(result, wanted)
        
    def test_split_trunk(self):
        label = self.label
        main_trunk = self.main_trunk
        constraint_trunk = self.constraint_trunk
        wanted = [main_trunk, constraint_trunk]
        result = g.split_trunk(label)
        self.assertEqual(result, wanted)
        
        
    def test_split_pattern(self):
        regex_in = gopattern.PatternManager.from_definition(PATTERN_PATH).regex_in()
        trunk = self.main_trunk
        p0 = (g.Pattern, 'positregulate', 'upregulation', 0, len('upregulation'))
        e0 = (g.Entity, 'gene slicing', 'gene slicing', self.label.index('gene slicing'), len(trunk.text))
        wanted = [p0, e0]
        result = g.split_pattern(trunk, regex_in)
        self.assertEqual(result, wanted)
        
        trunk = self.constraint_trunk
        c0 = (g.Constraint, 'miRNA', 'miRNA', self.label.index('miRNA'), len(self.label))
        wanted = [c0]
        result = g.split_pattern(trunk, regex_in)
        self.assertEqual(result, wanted)
        
    def test_evidence_split(self):
        goid = 'GO:testing'
        label = 'upregulation of gene slicing via miRNA'
        trunk = self.main_trunk
        t1 = g.Pattern('positregulate', 'annotator')
        e1 = g.Evidence(t1, 'upregulation', 0, len('upregulation'))
        t2 = g.Entity('gene slicing', 'GO:testing')
        e2 = g.Evidence(t2, 'gene slicing', self.label.index('gene slicing'), len(trunk.text))
        t3 = g.Constraint('miRNA', 'GO:testing')
        e3 = g.Evidence(t3, 'miRNA', self.label.index('miRNA'), len(self.label))
        
    
class TestEvidence(unittest.TestCase):
    
    def setUp(self):
        term0 = g.Term('lemma', 'GO:testing')
        term1 = g.Term('text', 'GO:testing')
        self.evidence0 = g.Evidence(term0, 'lemma', 12, 17)
        self.evidence1 = g.Evidence(term1, 'text', 18, 22)
        
    def test_sub(self):
        e0 = self.evidence0
        e1 = self.evidence1
        result = e1-e0
        self.assertEqual(result, 1)
        
        result = e0-e1
        self.assertEqual(result, -10)
        
class TestStatement(unittest.TestCase):

    def setUp(self):
        self.t0 = g.Term('lemma', 'GO:testing')
        self.t1 = g.Term('text', 'GO:testing')
        self.t2 = g.Pattern('regulation', 'annotator')
        self.e0 = g.Evidence(self.t0, 'lemma', 12, 17)
        self.e1 = g.Evidence(self.t1, 'text', 18, 22)
        self.e2 = g.Evidence(self.t2, 'increase', 23, 31)
        self.s0 = g.Statement('s0', [self.e0, self.e2])
        self.s1 = g.Statement('s1', [self.e1, self.e2])

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
        self.t0 = g.Entity('number', 'GO:testing')
        self.t1 = g.Entity('amount', 'GO:testing')
        self.t2 = g.Entity('size', 'GO:testing')
        self.t3 = g.Entity('count', 'GO:testing')
        self.c0 = g.Cluster(self.t0, {self.t0, self.t1})
        self.c1 = g.Cluster(self.t2, {self.t2, self.t3})
        
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
        wanted = g.Cluster(self.t0, {self.t0, self.t1, self.t2, self.t3})
        self.assertEqual(c0, wanted)

class TestClusterBook(unittest.TestCase):
    def setUp(self):
        self.t0 = g.Entity('number', 'GO:testing')
        self.t1 = g.Entity('amount', 'GO:testing')
        self.c0 = g.Cluster(self.t0, {self.t0, self.t1})
        
        self.t2 = g.Entity('size', 'GO:testing')
        self.t3 = g.Entity('count', 'GO:testing')
        self.c1 = g.Cluster(self.t2, {self.t2, self.t3})

        self.t4 = g.Entity('teacher', 'GO:testing')
        self.t5 = g.Entity('tutor', 'GO:testing')
        self.c2 = g.Cluster(self.t4, {self.t4, self.t5})
        
        self.cb = g.ClusterBook()
        
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

class TestClusterFunctions(unittest.TestCase):
    
    def setUp(self):
        self.t0 = g.Entity('vitamin C', 'GO:000')
        self.t1 = g.Entity('ascorbic acid', 'GO:000')
        self.t2 = g.Entity('ascorbate', 'GO:000')
        self.c0 = g.Cluster(self.t0, {self.t0, self.t1, self.t2})
        
        self.t3 = g.Entity('vitamin C', 'GO:111')
        self.t4 = g.Entity('L-ascorbic acid', 'GO:111')
        self.t5 = g.Entity('L-ascorbate', 'GO:111')
        self.c1 = g.Cluster(self.t3, {self.t3, self.t4, self.t5})

        self.t6 = g.Entity('vitamin B12', 'GO:222')
        self.t7 = g.Entity('cobalamin', 'GO:222')
        self.c2 = g.Cluster(self.t6, {self.t6, self.t7})
        
    def test_has_common(self):
        self.assertTrue(g.has_common(self.c0, self.c1))
        self.assertFalse(g.has_common(self.c1, self.c2))
    
    def test_jaccard(self):
        result = g.jaccard(self.c0, self.c1)
        wanted = 3.0/7
        self.assertEqual(result, wanted)
        
    def test_sim(self):
        result = g.sim(self.c0, self.c1)
        wanted = 3.0/7
        self.assertEqual(result, wanted)
        
        result = g.sim(self.c0, self.c2)
        wanted = 0
        self.assertEqual(result, wanted)
        
class TestConcept(unittest.TestCase):

    def setUp(self):
        goid = 'GO:testing'
        name = 'testing concept'
        namespace = 'biological_process'
        synonym_list = ['testing idea', 'fake concept']
        parent_list = []
        self.concept = g.Concept(goid, name, namespace, synonym_list, parent_list)

    def test_init(self):
        self.assertEqual(self.concept.ns, 'BP')
        self.assertEqual(self.concept.density, -1)