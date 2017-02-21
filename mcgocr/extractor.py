#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from collections import defaultdict, namedtuple
import re

from acora import AcoraBuilder

from mcgocr.pattern_regex import regex_out
from mcgocr.concept import Entity, Pattern, Constraint, Evidence


Grounds = namedtuple('Grounds', 'evidences sentence')

def _fit_border(text, span):
    start, end = span
    left_border = text[max(0, start-1):start+1]
    right_border = text[end-1:end+1]
    judge = re.compile(r'(.\b.|^.$)').match
    return all([judge(left_border),
                judge(right_border)])
                
class Index(dict):
    
    def __init__(self):
        self.use_default = True
        
    def __add__(self, other):
        for key, value_set in other.items():
            self[key] |= value_set
        return self
    
    def __repr__(self):
        template = '{}<{} key(s)>'
        return template.format(self.__class__.__name__, len(self))
        
    def __missing__(self, key):
        if self.use_default:
            self[key] = set()
            return self[key]
        else:
            return set()
            
            
class SolidExtractor(object):
    def __init__(self, term_index):
        self.term_index = term_index
        
        builder = AcoraBuilder()
        for text in term_index:
            builder.add(text)
        self.ac = builder.build()
    
    def findall(self, sentence):
        
        ac = self.ac
        term_index = self.term_index
        result = []
        offset = sentence.offset
        for text, raw_start in ac.findall(sentence.text):
            for primary_term in term_index[text]:
                start = raw_start + offset
                raw_end = raw_start + len(text)
                end = start + len(text)
                if _fit_border(sentence.text, (raw_start, raw_end)):
                    if isinstance(primary_term, Entity):
                        Class_ = Entity
                    elif isinstance(primary_term, Constraint):
                        Class_ = Constraint
                    else:
                        continue
                    lemma = primary_term.lemma
                    ref = primary_term.ref
                    term = Class_(lemma, ref)
                    evidence = Evidence(term, text, start, end)
                    result.append(evidence)
        return result
    
    def to_grounds(self, sentence):
        evidences = self.findall(sentence)
        grounds = Grounds(evidences, sentence)
        return grounds
                    
class SoftExtractor(object):
    def __init__(self, pattern_regex):
        self.pattern_ex = re.compile(pattern_regex)
    
    def findall(self, sentence):
        ex = self.pattern_ex
        offset = sentence.offset
        result = []
        for m in ex.finditer(sentence.text):
            lemma = list(filter(lambda item: item[1] is not None, m.groupdict().items()))[0][0]
            raw_start, raw_end = m.span()
            text = sentence.text[raw_start:raw_end]
            start, end = raw_start + offset, raw_end + offset
            term = Pattern(lemma, 'annotator')
            evidence = Evidence(term, text, start, end)
            result.append(evidence)
        return result
    
    def to_grounds(self, sentence):
        evidences = self.findall(sentence)
        grounds = Grounds(evidences, sentence)
        return grounds

class JoinExtractor(object):
    def __init__(self, extractors):
        self.extractors = extractors
        
    def findall(self, sentence):
        result = []
        for extractor in self.extractors:
            result.extend(extractor.findall(sentence))
        result.sort(key=lambda e: e.start)
            
        return result
    
    def to_grounds(self, sentence):
        evidences = self.findall(sentence)
        grounds = Grounds(evidences, sentence)
        return grounds        
