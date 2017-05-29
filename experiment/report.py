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
        return sum([report.recall() for report in self.reports]) / len(self.reports)
    
    def precision(self):
        return sum([report.precision() for report in self.reports]) / len(self.reports)
    
    def f_measure(self):
        return sum([report.f1() for report in self.reports]) / len(self.reports)
    
