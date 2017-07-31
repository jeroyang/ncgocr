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

class TestFunctions(unittest.TestCase):
    def test_is_title(self):
        positive = ['Jesus Loves Me',
                    'Bring to the Front!',
                    'The Basic Idea of Games']
        negative = ['Who is the first lady?',
                    'The function of BRCA1',
                    'Windows XP never die']
        for case in positive:
            self.assertTrue(c.is_title(case))

        for case in negative:
            self.assertFalse(c.is_title(case))

    def test_is_abbr(self):
        positive = ['BRCA1',
                    'EFR2',
                    'CA3',
                    'TXTs']
        negative = ['home',
                    'Basic',
                    'Hello']

        for case in positive:
            self.assertTrue(c.is_abbr(case))

        for case in negative:
            self.assertFalse(c.is_abbr(case))

    def test_is_word(self):
        positive = ['Dream',
                    'best',
                    'talk',
                    'A']
        negative = ['brca1',
                    'NBA',
                    'A*']

        for case in positive:
            self.assertTrue(c.is_word(case))

        for case in negative:
            self.assertFalse(c.is_word(case))

    def test_normalize(self):
        cases = ['Dream',
                 'Hello',
                 'NBA',
                 'BRCA1',
                 'best']
        targets = ['dream',
                   'hello',
                   'NBA',
                   'BRCA1',
                   'best']
        for case, target in zip(cases, targets):
            self.assertEqual(c.normalize(case), target)

    def test_normalize_sent(self):
        cases = ['Jesus Loves Me',
                'Bring to the Front!',
                'The Basic Idea of Games',
                'Who is the first lady?',
                'The function of BRCA1',
                'Windows XP never die']
        targets = ['jesus loves me',
                    'bring to the front!',
                    'the basic idea of games',
                    'who is the first lady?',
                    'the function of BRCA1',
                    'windows XP never die']

        for case, target in zip(cases, targets):
            self.assertEqual(c.normalize_sent(case), target)

class TestSentence(unittest.TestCase):
    def setUp(self):
        self.sentence = c.Sentence('Jesus Loves Me', 15, 'diary')

    def test_init(self):
        text = self.sentence.text
        wanted = 'jesus loves me'
        self.assertEqual(text, wanted)

    def test_repr(self):
        result = self.sentence.__repr__()
        wanted = "Sentence<'Jesus Loves Me' 15@diary>"
        self.assertEqual(result, wanted)

class TestCorpus(unittest.TestCase):

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
        corpus_list = self.corpus_a.divide(5, 0)
        self.assertEqual(len(corpus_list), 5)
        for corpus in corpus_list:
            self.assertEqual(len(corpus), 10)
        result = sum(corpus_list, c.Corpus())
        result.title = 'testing_a'
        wanted = self.corpus_a
        self.assertEqual(set(result), set(wanted))
