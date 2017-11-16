#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

class Report(object):
    def __init__(self, tp, fp, fn, message):
        self.tp = tp
        self.fp = fp
        self.fn = fn
        self.message = message

    def recall(self):
        return float(len(self.tp)) / len(self.tp | self.fn)

    def precision(self):
        return float(len(self.tp)) / len(self.tp | self.fp)

    def f1(self):
        r = self.recall()
        p = self.precision()
        return float(2 * r * p) / (r + p)

    def __repr__(self):
        r = self.recall()
        p = self.precision()
        f = self.f1()
        syntax = 'Report<P{p:.3f} R{r:.3f} F{f:.3f} {m!r}>'
        return syntax.format(r=r, p=p, f=f, m=self.message)

class MetaReport(object):
    def __init__(self, message, reports=None):
        self.message = message
        self._precision = None
        self._recall = None
        self._f_measure = None
        if reports is None:
            self.reports = []
        else:
            self.reports = reports

    def __repr__(self):
        r = self.recall()
        p = self.precision()
        f = self.f_measure()
        syntax = 'MetaReport<P{p:.3f} R{r:.3f} F{f:.3f} {m!r}>'
        return syntax.format(r=r, p=p, f=f, m=self.message)

    def recall(self):
        try:
            self._recall
        except:
            self._recall = None

        if self._recall:
            return self._recall
        return sum([report.recall() for report in self.reports]) / len(self.reports)

    def precision(self):
        try:
            self._precision
        except:
            self._precision = None

        if self._precision:
            return self._precision
        return sum([report.precision() for report in self.reports]) / len(self.reports)

    def f_measure(self):
        try:
            self._f_measure
        except:
            self._f_measure = None

        if self._f_measure:
            return self._f_measure
        return sum([report.f1() for report in self.reports]) / len(self.reports)

    @classmethod
    def from_PR(cls, message, precision, recall):
        metareport = cls(message)
        metareport._precision = precision
        metareport._recall = recall
        metareport._f_measure = float(2 * recall * precision) / (recall + precision)
        return metareport

    @classmethod
    def from_case(cls, message, tp, fp, fn):
        report = Report({i for i in range(0, tp)},
                        {i for i in range(tp, tp+fp)},
                        {i for i in range(tp+fp, tp+fp+fn)},
                        'PseudoReport')
        metareport = cls(message, [report])
        return metareport
