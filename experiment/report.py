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
        return len(self.tp) / len(self.tp | self.fn)
    
    def precision(self):
        return len(self.tp) / len(self.tp | self.fp)
    
    def f1(self):
        r = self.recall()
        p = self.precision()
        return 2 * r * p / (r + p)
    
    def __repr__(self):
        r = self.recall()
        p = self.precision()
        f = self.f1()
        syntax = 'Report<R{r:.2%} P{p:.2%} F{f:.2%} {m!r}>'
        return syntax.format(r=r, p=p, f=f, m=self.message)
    
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
        mif = self.mif1()
        maf = self.maf1()
        syntax = 'MetaReport<R{r:.2%} P{p:.2%} mF{mif:.2%} MF{maf:.2%} {m!r}>'
        return syntax.format(r=r, p=p, mif=mif, maf=maf, m=self.message)
    
    def recall(self):
        return sum([report.recall() for report in self.reports]) / len(self.reports)
    
    def precision(self):
        return sum([report.precision() for report in self.reports]) / len(self.reports)
    
    def mif1(self):
        return sum([report.f1() for report in self.reports]) / len(self.reports)
    
    def maf1(self):
        r = self.recall()
        p = self.precision()
        return 2 * r * p / (r + p)
    