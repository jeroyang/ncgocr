#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from collections import namedtuple
import random
import os
import string

from txttk.nlptools import sent_tokenize, count_start, word_tokenize

stop_words = "a,able,about,across,after,all,almost,also,am,among,an,and,any,are,as,at,"\
             "be,because,been,but,by,can,cannot,could,dear,did,do,does,either,else,ever,"\
             "every,for,from,get,got,had,has,have,he,her,hers,him,his,how,however,i,if,"\
             "in,into,is,it,its,just,least,let,like,likely,may,me,might,most,must,my,"\
             "neither,no,nor,not,of,off,often,on,only,or,other,our,own,rather,said,say,"\
             "says,she,should,since,so,some,than,that,the,their,them,then,there,these,"\
             "they,this,tis,to,too,twas,us,wants,was,we,were,what,when,where,which,while,"\
             "who,whom,why,will,with,would,yet,you,your".split(',')

Grounds = namedtuple('Grounds', 'evidences sentence')

def is_title(text):
    tokens = word_tokenize(text)
    bol_list = []
    for i, token in enumerate(tokens):
        if i==0:
            bol_list.append(True)
        elif token.lower() in stop_words:
            bol_list.append(True)
        elif token[0] not in string.ascii_lowercase:
            bol_list.append(True)
        else:
            bol_list.append(False)
    return all(bol_list)

def is_abbr(token):
    return len(set(token[1:]) & set(string.ascii_uppercase)) > 0

def is_word(token):
    if len(set(token) & (set(string.punctuation) | set(string.digits))) > 0:
        return False
    if len(token) == 1:
        return True
    elif is_abbr(token):
        return False
    else:
        return True

def normalize(token):
    if is_word(token):
        return token.lower()
    else:
        return token

def normalize_sent(text):
    output = []
    tokens = list(word_tokenize(text))
    if is_title(text):
        for token in tokens:
            output.append(normalize(token))
    else:
        output.append(normalize(tokens[0]))
        output.extend(tokens[1:])
    return ''.join(output)

class Sentence(object):
    def __init__(self, text, offset, docid):
        self.original_text = text
        self.offset = offset
        self.docid = docid
        self.text = normalize_sent(text)

    def __repr__(self):
        template = '{}<{} {}@{}>'
        return template.format(self.__class__.__name__,
                               repr(self.original_text),
                               self.offset,
                               self.docid)


class Candidate(object):
    def __init__(self, statement, evidences, sentence):
        self.statement = statement
        self.evidences = evidences
        self.sentence = sentence
        self.label = None
        self.pred_label = None

    def __repr__(self):
        template = '{}<{} evidences={} sentence={}>'
        return template.format(self.__class__.__name__,
                               self.statement.statid,
                               self.evidences,
                               self.sentence)

    def __hash__(self):
        return hash(repr(self))

    def __eq__(self, other):
        if hash(self) == hash(other):
            return True
        return False

class Bag(set):
    def __init__(self, iterable=[]):
        self |= set(iterable)

    def __repr__(self):
        template = '{}<{} items>'
        text = template.format(self.__class__.__name__,
                               len(self))
        return text


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
    def join(cls, title, corpora):
        output = cls(title)
        for corpus in corpora:
            output.extend(corpus)
        return output

    @classmethod
    def from_text(cls, text, docid, sent_toker=None):
        corpus = cls()
        if sent_toker is None:
            sent_toker = sent_tokenize
        sent_toker = count_start(sent_toker)
        offset_text = sent_toker(text, 0)
        for text, offset in offset_text:
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
