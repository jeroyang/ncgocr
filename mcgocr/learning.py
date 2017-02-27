#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from collections import OrderedDict, defaultdict

from intervaltree import Interval, IntervalTree

"""
The measurements of features
"""
def concept_measurements(candidate, godata):
    """
    Measure the ceoncept features: GOID, STATID, NAMESPACE
    from the given candidate
    """
    statement = candidate.statement
    statid = statement.statid
    goid, sep, sulfix = statid.partition('%')
    namespace = godata[goid].namespace
    measurements = OrderedDict([('GOID', goid), 
                            ('STATID', statid),
                            ('NAMESPACE', namespace)])
    return measurements
    
def evidence_measurements(candidate):
    """
    Measure the evidence features: LENGTH, TEXT and 
    TEXT[:3], TEXT[-3:] from the given candidate
    """
    evidences = candidate.evidences
    sentence_text = candidate.sentence.text
    offset = candidate.sentence.offset
    starts = [e.start for e in evidences]
    ends = [e.end for e in evidences]
    raw_start = min(starts) -  offset
    raw_end = max(ends) - offset
    length = raw_end - raw_start
    text = sentence_text[raw_start:raw_end]
    measurements = OrderedDict([('LENGTH', length),
                            ('TEXT', text),
                            ('TEXT[:3]', text[:3]),
                            ('TEXT[-3:]', text[-3:])])
    return measurements
    
def bias_measurements(candidate):
    """
    Measure the bias features: OMIT, SATURATION from the 
    given candidate
    """
    measurements = OrderedDict()
    statement = candidate.statement
    evidences = candidate.evidences
    terms_in_evidences = set([e.term for e in evidences])
    measurements['OMIT'] = [term.lemma for term in statement.terms() if term not in terms_in_evidences]
    measurements['SATURATION'] = len(evidences) / len(statement.evidences)
    return measurements
    
def all_measurements(candidate, godata):
    """
    Return all the measurements from the given candidate
    """
    measurements = OrderedDict()
    measurements.update(concept_measurements(candidate))
    measurements.update(evidence_measurements(candidate))
    measurements.update(bias_measurements(candidate))
    return measurements



class LabelMarker(object):
    """
    Handeling the labels from given goldstandard
    """
    def __init__(self, goldstandard):
        self.goldstandard = goldstandard
        forest = defaultdict(IntervalTree)
        for pmid, goid, start, end, text in goldstandard:
            t = forest[pmid]
            t[start:end] = (goid, text)
        self.forest = dict(forest)
        
    def mark(self, candidate):
        statid = candidate.statement.statid
        evidences = candidate.evidences
        goid = statid.partition('%')[0]
        starts = [e.start for e in evidences]
        ends = [e.end for e in evidences]
        start = min(starts)
        end = max(ends)
        span = (start, end)
        gold_goids = {iv.data[0] for iv in forest[pmid][slice(*span)]}
        if goid in gold_goids:
            return 1
        return 0
        
    def markall(self, candidates):
        labels = []
        for candidate in candidates:
            result.append(self.check(candidate))
        return labels