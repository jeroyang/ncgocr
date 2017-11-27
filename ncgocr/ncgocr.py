#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import logging

import argparse

from txttk.corpus import Corpus
from ncgocr.pattern_regex import regex_out
from ncgocr.concept import GoData, Index, Entity, Evidence, Statement
from ncgocr.extractor import SoftExtractor, SolidExtractor, JoinExtractor, CandidateReconizer
from ncgocr.learning import bulk_measurements, LabelMarker, recover, evaluate

from sklearn.feature_extraction import FeatureHasher
from sklearn.ensemble import RandomForestClassifier

class NCGOCR(object):
    def __init__(self, godata, measure=bulk_measurements, use_boost=True, n=10):
        self.godata = godata
        self.basic_Ie = godata.get_Ie()
        self.basic_Im = godata.get_Im()
        self.e0 = SolidExtractor(self.basic_Ie)
        self.e1 = SoftExtractor(regex_out)
        self.measure = measure
        self.vectorizer = FeatureHasher(n_features=1024)
        self.classifier = RandomForestClassifier(n_estimators=n, n_jobs=-1)
        self.use_boost = use_boost
        self.boost_Ie = Index()
        self.boost_Im = Index()

    def boost(self, training_gold):
        for pmid, goid, start, end, text in training_gold:
            for statement in self.godata[goid].statements:
                if len(statement.evidences) == 1:
                    term = statement.evidences[0].term
                    lemma = term.lemma
                    if text!=lemma:
                        self.boost_Ie[text].add(term)
            else:
                if ' ' not in text:
                    cm = Entity(text, 'boost')
                    null = Entity('NULL#' + goid, 'boost')
                    evidences = [Evidence(null, '', 0, 0), Evidence(cm, text, 0, len(text))]
                    new_statement = Statement('%'.join([goid, text]), evidences)
                    self.boost_Ie[text].add(cm)
                    self.boost_Im[cm].add(new_statement)

    def train(self, training_corpus, training_gold):
        if self.use_boost:
            self.boost(training_gold)
        self.e2 = SolidExtractor(self.boost_Ie)
        self.extractor = JoinExtractor([self.e0, self.e1, self.e2])
        self.candidate_recognizer = CandidateReconizer(self.basic_Im + self.boost_Im)

        label_marker = LabelMarker(training_gold)
        training_grounds = self.extractor.process(training_corpus)
        training_candidates = self.candidate_recognizer.process(training_grounds)
        training_measurements = self.measure(training_candidates, self.godata)

        training_X = self.vectorizer.fit_transform(training_measurements).toarray()
        training_y = label_marker.process(training_candidates)

        self.classifier.fit(training_X, training_y)

    def process(self, testing_corpus, testing_gold=None):
        testing_grounds = self.extractor.process(testing_corpus)
        testing_candidates = self.candidate_recognizer.process(testing_grounds)
        testing_measurements = self.measure(testing_candidates, self.godata)
        testing_X = self.vectorizer.transform(testing_measurements).toarray()
        system_y = self.classifier.predict(testing_X)
        system_results = recover(testing_candidates, system_y)
        return system_results


if __name__ == '__main__':

    description = """
__    _   ___    ___     ___     ___  .___
 |\   |  .'   \ .'   \  .'   `. .'   \ /   \
 | \  |  |      |       |     | |      |__-'
 |  \ |  |      |    _  |     | |      |  \
 |   \|   `.__,  `.___|  `.__.'  `.__, /   \

Named Concept Gene Ontology Concept Recognizer """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('command', type=str, nargs=1,
                        help='command')
    parser.add_argument('--output', dest='accumulate', action='store_const',
                        const=sum, default=max,
                        help='sum the integers (default: find the max)')

    args = parser.parse_args()

    def load_components():
        """
        Load the components from pickle files,
        If the file is defined in the 'data/', load it
        else, load the default file from 'data/default/'
        return tuple (Ie, Im, feature_hasher, classifier)
        """
        def _load_pickle(item):
            path = 'data/{}.pickle'.format(item)

            try:
                logging.info('Loading the {}...'.format(item))
                with open(path) as f:
                    return pickle.load(f)
            except:
                path = 'data/default/{}.pickle'.format(item)
                with open(path) as f:
                    return pickle.load(f)

        Ie = _load_pickle('index_Ie')
        Im = _load_pickle('index_Im')
        Ie_boost = _load_pickle('index_Ie_boost')

        feature_hasher = _load_pickle('feature_hasher')
        classifier = _load_pickle('classifier')

    Ie, Im, Ie_boost, feature_hasher, classifier = load_components()
    recognizer = MCGOCR(Ie, Im, Ie_boost, feature_hasher, classifier)
    corpus = corpus.Corpus.from_dir('input')
    annotation = recognizer.scan(corpus)
