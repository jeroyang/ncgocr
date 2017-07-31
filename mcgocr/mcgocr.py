#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import logging

import argparse

from experiment.corpus import Corpus
from mcgocr.pattern_regex import regex_out
from mcgocr.concept import GoData, Index, Entity, Evidence, Statement
from mcgocr.extractor import SoftExtractor, SolidExtractor, JoinExtractor, CandidateReconizer
from mcgocr.learning import bulk_measurements, LabelMarker, recover, evaluate

from sklearn.feature_extraction import FeatureHasher
from sklearn import svm

def boost(training_gold, godata):
    Ie_boost = Index()
    Im_boost = Index()
    for pmid, goid, start, end, text in training_gold:
        for statement in godata[goid].statements:
            if len(statement.evidences) == 1:
                term = statement.evidences[0].term
                lemma = term.lemma
                if text!=lemma:
                    Ie_boost[text].add(term)
        else:
            if ' ' not in text:
                cm = Entity(text, 'boost')
                null = Entity('NULL#' + goid, 'boost')
                evidences = [Evidence(null, '', 0, 0), Evidence(cm, text, 0, len(text))]
                new_statement = Statement('%'.join([goid, text]), evidences)
                Ie_boost[text].add(cm)
                Im_boost[cm].add(new_statement)
    return Ie_boost, Im_boost

class MCGOCR(object):
    def __init__(self, godata):
        self.godata = godata
        Ie = godata.get_Ie()
        Im = godata.get_Im()
        self.e0 = SolidExtractor(Ie)
        self.e1 = SoftExtractor(regex_out)
        self.basic_Im = Im
        self.measure = bulk_measurements
        self.vectorizer = None
        self.classifier = None
        self.use_boost = True

    def fit(self, training_corpus, training_gold):
        boost_Ie, self.boost_Im = boost(training_gold, self.godata)
        self.e2 = SolidExtractor(boost_Ie)

        if self.use_boost:
            self.extractor = JoinExtractor([self.e0, self.e1, self.e2])
            self.candidate_recognizer = CandidateReconizer(self.basic_Im + self.boost_Im)
        else:
            self.extractor = JoinExtractor([self.e0, self.e1])
            self.candidate_recognizer = CandidateReconizer(self.basic_Im)

        label_marker = LabelMarker(training_gold)
        training_grounds = self.extractor.process(training_corpus)
        training_candidates = self.candidate_recognizer.process(training_grounds)
        training_measurements = self.measure(training_candidates, self.godata)

        self.vectorizer = FeatureHasher(n_features=1024)
        training_X = self.vectorizer.fit_transform(training_measurements).toarray()

        training_y = label_marker.process(training_candidates)

        self.classifier = svm.LinearSVC(random_state=0)
        self.classifier.fit(training_X, training_y)

    def predict(self, testing_corpus):
        testing_grounds = self.extractor.process(testing_corpus)
        testing_candidates = self.candidate_recognizer.process(testing_grounds)
        testing_measurements = self.measure(testing_candidates, self.godata)
        testing_X = self.vectorizer.transform(testing_measurements).toarray()
        system_y = self.classifier.predict(testing_X)

        system_results = recover(testing_candidates, system_y)
        return system_results



if __name__ == '__main__':

    description = """
     _______ _______  ______  _____  _______  ______
     |  |  | |       |  ____ |     | |       |_____/
     |  |  | |_____  |_____| |_____| |_____  |    \_

    Micro Concept Gene Ontology Concept Recognizer """
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
