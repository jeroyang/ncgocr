#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import logging

import argparse
import pickle
from grepc.models import *
from mcgocr.pattern_regex import regex_out
from experiment import corpus

ItemA = namedtuple('ItemA', 'GOID start end source text')

class Annotation(list):
    def __repr__(self):
        return 'Annotation<{} items>'.format(len(list))

    def to_csv(self, fp):
        import csv
        with open(fp, 'w') as f:
            w = csv.writer(f)
            w.writerows(self)

    def to_json(self, fp):
        import json
        with open(fp, 'w') as f:
            json.dump(self, f)


class MCGOCR(object):
    def __init__(self, Ie, Im, Ie_boost, feature_hasher, classifier):
        self.Ie = Ie
        self.Im = Im
        self.Ie_boost = Ie_boost
        self.feature_hasher = feature_hasher
        self.classifier = classifier

        self.extractor = JoinExtractor([
            SolidExtractor(Ie),
            SolidExtractor(Ie_boost),
            SoftExtractor(regex_out)
        ])

    def _candidate_generation(self, corpus):
        pass

    def _feature_extract(self, candidates):
        pass

    def scan(self, corpus):
        """
        Input: Corpus object
        Output: Annotation object
        """
        candidates = self._candidate_generate(corpus)
        features = self._feature_extract(candidates)
        X = feature_hasher.transform(measures)
        pred_y = classifier.predict(X)
        annotation = annotate(candidates, pred_y)
        return annotation

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
