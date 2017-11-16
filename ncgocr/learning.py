#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from collections import OrderedDict, defaultdict, ChainMap
from intervaltree import Interval, IntervalTree
import numpy as np

from experiment.report import Report

from experiment.corpus import Annotation

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
    text = sentence_text[raw_start:raw_end].lower()
    boostscore = {'boost':1, 'boost2': 100}
    boostlevel = max([boostscore.get(term.ref, 0) for term in candidate.statement.terms()])
    measurements = OrderedDict([('LENGTH', length),
                            ('TEXT=' + text, True),
                            ('TEXT[:3]=' + text[:3], True),
                            ('TEXT[-3:]=' + text[-3:], True),
                            ('BOOST', boostlevel)])
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
    for term in statement.terms():
        if term in terms_in_evidences:
            continue
        key = 'OMIT=' + term.lemma
        measurements[key] = True
    measurements['SATURATION'] = len(evidences) / len(statement.evidences)
    return measurements

def all_measurements(candidate, godata):
    """
    Return all the measurements from the given candidate
    """
    measurements = OrderedDict()
    measurements.update(concept_measurements(candidate, godata))
    measurements.update(evidence_measurements(candidate))
    measurements.update(bias_measurements(candidate))
    return measurements

def bulk_measurements(candidates, godata):
    result = []
    for candidate in candidates:
        result.append(all_measurements(candidate, godata))
    return result


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
        pmid = candidate.sentence.docid
        statid = candidate.statement.statid
        evidences = candidate.evidences
        goid = statid.partition('%')[0]
        starts = [e.start for e in evidences]
        ends = [e.end for e in evidences]
        start = min(starts)
        end = max(ends)
        span = (start, end)
        gold_goids = {iv.data[0] for iv in self.forest[pmid][slice(*span)]}
        if goid in gold_goids:
            return 1
        return 0

    def markall(self, candidates):
        labels = []
        for candidate in candidates:
            labels.append(self.mark(candidate))
        return labels

    def process(self, candidates):
        return np.array(self.markall(candidates))


def recover(candidates, y):
    result = Annotation()
    for candidate, label in zip(candidates, y):
        if label == 0:
            continue
        pmid = candidate.sentence.docid
        statid = candidate.statement.statid
        goid = statid.partition('%')[0]
        start = min([e.start for e in candidate.evidences])
        end = max([e.end for e in candidate.evidences])
        raw_start = start - candidate.sentence.offset
        raw_end = end - candidate.sentence.offset
        text = candidate.sentence.text[raw_start:raw_end]
        result.add((pmid, goid, start, end, text))
    return result


def evaluate(system, goldstandard, message):
    slim_system = {i[:4] for i in system}
    slim_goldstandard = {i[:4] for i in goldstandard}
    slim2gold = ChainMap({i[:4]: i for i in goldstandard},
                         {i[:4]: i for i in system})
    slim_tp = slim_system & slim_goldstandard
    slim_fp = slim_system - slim_goldstandard
    slim_fn = slim_goldstandard - slim_system
    tp = {slim2gold[i] for i in slim_tp}
    fp = {slim2gold[i] for i in slim_fp}
    fn = {slim2gold[i] for i in slim_fn}
    return Report(tp, fp, fn, message)
