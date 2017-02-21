#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from collections import namedtuple
import random
import os 

from txttk.nlptools import sent_tokenize, count_start

Sentence = namedtuple('Sentence', 'text offset docid')
Grounds = namedtuple('Grounds', 'evidences sentence')
Candidate = namedtuple('Candidate', 'statement density evidences grounds')

class Corpus(list):
    def __init__(self, title='', sentences=None):
        self.title = title
        if sentences is not None:
            self.extend(sentences)
        
    def __repr__(self):
        template = '{}<{} documents, {} sentences, {}>'
        return template.format(self.__class__.__name__,
                               len(self.doc_set()),
                               len(self), 
                               repr(self.title))
        
    def __add__(self, other):
        title = '|'.join([self.title, other.title])
        corpus = Corpus(title)
        corpus.extend(self)
        corpus.extend(other)
        return corpus
        
    def doc_set(self):
        return set([s.docid for s in self])
        
    def divide(self, k, random_state=0):
        size = len(self.doc_set())
        if not k <= size:
            raise ValueError('The k should be lesser equal than the document size of the courpus ({}).'.format(size))
        random.seed(random_state)
        docids = list(self.doc_set())
        random.shuffle(docids)
        i2ids = {i: set() for i in range(1, k+1)}
        for i, docid in enumerate(docids):
            b = i % k + 1
            i2ids[b].add(docid)
        index = {docid:key for key, value in i2ids.items() for docid in value}
        i2corpus = {i: Corpus('{} {}/{}'.format(self.title, i, k)) for i in i2ids.keys()}
        for sentence in self:
            goto = index[sentence.docid]
            i2corpus[goto].append(sentence)
        
        return list(i2corpus.values())
        
    @classmethod
    def from_text(cls, text, docid, sent_toker=None):
        corpus = cls()
        if sent_toker is None:
            sent_toker = sent_tokenize
        sent_toker = count_start(sent_toker)
        offset_text = sent_toker(text, 0)
        for offset, text in offset_text:
            corpus.append(Sentence(text, offset, docid))
        return corpus
    
    @classmethod
    def from_dir(cls, dirpath, title, filename_extension='.txt', sent_toker=None):
        corpus = Corpus(title)
        for filename in os.listdir(dirpath):
            if not filename.endswith(filename_extension):
                continue
            filepath = os.path.join(dirpath, filename)
            with open(filepath) as f:
                text = f.read()
                docid = filename[:-len(filename_extension)]
                corpus += cls.from_text(text, docid, sent_toker)
        return corpus