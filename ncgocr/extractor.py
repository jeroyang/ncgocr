#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from collections import defaultdict, namedtuple
import re

from acora import AcoraBuilder

from ncgocr.concept import Entity, Pattern, Constraint, Evidence, Index
from experiment.corpus import Candidate

Grounds = namedtuple('Grounds', 'evidences sentence')

def _fit_border(text, span):
    start, end = span
    left_border = text[max(0, start-1):start+1]
    right_border = text[end-1:end+1]
    judge = re.compile(r'(.\b.|^.$)').match
    return all([judge(left_border),
                judge(right_border)])

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
        try:
            for text, raw_start in ac.findall(sentence.text):
                for primary_term in term_index[text]:
                    start = raw_start + offset
                    raw_end = raw_start + len(text)
                    end = start + len(text)
                    if _fit_border(sentence.text, (raw_start, raw_end)):
                        evidence = Evidence(primary_term, text, start, end)
                        result.append(evidence)
        except TypeError: # caused by empty ac
            return []
        return result

    def to_grounds(self, sentence):
        evidences = self.findall(sentence)
        grounds = Grounds(evidences, sentence)
        return grounds

class SoftExtractor(object):
    def __init__(self, regex_out):
        self.pattern_ex = re.compile(regex_out)

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

    def process(self, corpus):
        corpus_grounds = []
        for sentence in corpus:
            corpus_grounds.append(self.to_grounds(sentence))
        return corpus_grounds


def nearest_evidences(current_position, wanted_terms, position_index):
    found_evidences = []
    for term in wanted_terms:
        positional_evidences = position_index[term]
        if len(positional_evidences) > 0:
            distance_evidence = [(abs(current_position - position), evidence)
                for position, evidence in positional_evidences]
            distance_evidence.sort(key=lambda it:it[0])
            found_evidences.append(distance_evidence[0][1])
            found_evidences.sort()
    return found_evidences


def has_entity(statement):
    if any([isinstance(term, Entity) for term in statement.terms()]):
        return True
    return False

class CandidateReconizer(object):
    def __init__(self, Im):
        """stat_index = Index()
        for goid, concept in godata.items():
            for statement in concept.statements:
                for term in statement.terms():
                    if has_entity(statement) and isinstance(term, Entity):
                        stat_index[term].add(statement)
                    elif not has_entity(statement):
                        stat_index[term].add(statement)

        stat_index.use_default = False"""
        self.Im = Im

    def generate(self, grounds):
        """
        This function looks so complex because I only want to report the nearest evidence
        Maybe there is a more elegant way, but I have no idea, currently.
        """
        stat_index = self.Im
        result_candidates = []

        positional_evidences = list(enumerate(grounds.evidences))

        #The first loop, build the positional_index
        position_index = defaultdict(list)
        for position, evidence in positional_evidences:
            position_index[evidence.term].append((position, evidence))

        #The second loop, gathering evidences
        for position, evidence in positional_evidences:
            statements = stat_index[evidence.term]
            for statement in statements:
                wanted_terms = statement.terms()
                found_evidences = nearest_evidences(position, wanted_terms, position_index)
                candidate = Candidate(statement, found_evidences, grounds.sentence)
                result_candidates.append(candidate)
        return result_candidates

    def process(self, corpus_grounds):
        corpus_candidates = []
        for grounds in corpus_grounds:
            candidates = self.generate(grounds)
            corpus_candidates.extend(candidates)
        return corpus_candidates


"""
class CandidateFinder(object):
    def __init__(self, extractor):
        solid_extractor = SolidExtractor(Ie)
        soft_extractor = SoftExtractor(regex_out)
        if boost_Ie is None:
            self.extractor = JoinExtractor([solid_extractor, soft_extractor])
        else:
            boost_extractor = SolidExtractor(boost_Ie)
            self.ex
        soft_extractor = SoftExtractor(regex_out)
        if auxiliary_extractor is not None:
            self.extractor = JoinExtractor([solid_extractor,
                                            soft_extractor,
                                            auxiliary_extractor])
        else:
            self.extractor = JoinExtractor([solid_extractor,
                                            soft_extractor])
        self.recognizer = CandidateReconizer(godata)

    def _findall(self, sentence):
        grounds = self.extractor.to_grounds(sentence)
        candidates = self.recognizer.generate(grounds)
        return candidates

    def findall(self, corpus):
        result = []
        for sentence in corpus:
            result.extend(self._findall(sentence))
        return result
"""
