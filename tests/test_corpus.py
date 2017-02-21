#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

"""
test_corpus
----------------------------------

Tests for `corpus` module.
"""

import unittest

from experiment import corpus as c

class TextCorpus(unittest.TestCase):
    
    def setUp(self):
        self.corpus_a = c.Corpus(title='testing_a')
        self.corpus_b = c.Corpus(title='testing_b')
        self.sentences = []
        for i in range(100):
            sentence = c.Sentence(str(i), i, 'doc'+str(i%10))
            self.sentences.append(sentence)
            if i < 50:
                self.corpus_a.append(sentence)
            else:
                self.corpus_b.append(sentence)
        
    def test_init(self):
        self.assertEqual(self.corpus_a.title, 'testing_a')
        
    def test_add(self):
        result = self.corpus_a + self.corpus_b
        wanted = c.Corpus('testing_a|testing_b',
                            self.sentences)
        self.assertEqual(result, wanted)
        
    def test_doc_set(self):
        wanted = {'doc'+str(i) for i in range(10)}
        result = self.corpus_a.doc_set()
        self.assertEqual(result, wanted)
        
    def test_divide(self):
        corpus_list = self.corpus_a.divide(5)
        self.assertEqual(len(corpus_list), 5)
        for corpus in corpus_list:
            self.assertEqual(len(corpus), 10)
        result = sum(corpus_list, c.Corpus())
        result.title = 'testing_a'
        wanted = self.corpus_a
        self.assertEqual(set(result), set(wanted))
        
        