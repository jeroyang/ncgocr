#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import re
from collections import namedtuple
from mcgocr import gopattern

Trunk = namedtuple('Trunk', 'text type start end')
Term = namedtuple('Term', 'lemma ref')
            
class Entity(Term):
    pass

class Pattern(Term):
    pass

class Constraint(Term):
    pass
    
class Evidence(namedtuple('Evidence', 'term text start end')):
    
    def __sub__(self, other):
        """
        Return distance between the start of this term to the end of another term
        Notice: abs(a - b) != abs(b - a)
        """
        return self.start - other.end

class Statement(namedtuple('Statement', 'statid evidences')):
    """
    A Statement is a collection of evidences
    """
    def __eq__(self, other):
        try:
            self.eq_terms(other)
            return True
        except:
            return False
    
    def __hash__(self):
        return hash('statement:' + self.statid)
    
    def terms(self):
        return [evidence.term for evidence in self.evidences]
        
    def eq_terms(self, other):
        terms = []
        if len(self.evidences) != len(other.evidences):
            raise ValueError('The two statements have different lengths of evidences')
        for this_evidence, other_evidence in zip(self.evidences, other.evidences):
            this_term, other_term = this_evidence.term, other_evidence.term
            if type(this_term) != type(other_term):
                raise ValueError('The two statements have different type sequences of terms')
            elif all([isinstance(this_term, Pattern),
                      not this_term == other_term]):
                raise ValueError('The two statements has different patterns')
            elif not any([isinstance(this_term, Pattern), 
                          this_term == other_term]):
                terms.append((other_term, this_term))
        return terms
    



def _clean(entity_frag):
    """
    Clean the given trunk (text contains entity and pattern)
    by removal of the leading and tailing puncutions and stopwords
    """
    stopwords = '(of|in|to|and|or|the)'
    head_regex = r'^\s*{}\b'.format(stopwords)
    tail_regex = r'\b{}\s*$'.format(stopwords)
    joined_regex = r'|'.join([head_regex, tail_regex])
    return re.sub(joined_regex, '', entity_frag).strip(' -,')
    
def split_trunk(label):
    """
    A GO label may contain two (or more) trunks, 
    split the trunk by regular expression. 
    
    TODO: split trunks correctly if there are more than two trunks
    """
    regex_list = [
        r'^(?P<main_trunk>.*?),?\s*\b(?:involved in|during|via|using|by|acting on|from|in)\s(?P<constraint_trunk>.*)$',
        r'^(?P<main_trunk>.*?),\s*\b(?P<constraint_trunk>.*)[\ \-](?:related|dependent)$']
    
    for regex in regex_list:
        m = re.match(regex, label)
        if m:
            main_text = m.group('main_trunk')
            main_start = label.index(main_text)
            main_end = main_start + len(main_text)
            main_trunk = Trunk(main_text, 'main', main_start, main_end)
            
            constraint_text = m.group('constraint_trunk')
            constraint_start = label.index(constraint_text)
            constraint_end = constraint_start + len(constraint_text)
            constraint_trunk = Trunk(constraint_text, 'constraint', constraint_start, constraint_end)
            return [main_trunk, constraint_trunk]
    return [Trunk(label, 'main', 0, len(label))]
    
def split_pattern(trunk, regex_in):
    """
    Given a trunk, and regex_in from pattern_manager,
    return the list of patterns and the list of entities
    """
    pre_terms = []
    text = trunk.text
    start = trunk.start
    if trunk.type == 'main':
        for m in re.finditer(regex_in, text):
            for lemma, token in m.groupdict().items():
                if token is not None:
                    token_start = start + m.start()
                    token_end = start + m.end()
                    pre_terms.append((Pattern, lemma, token, token_start, token_end))
    
    replaced = re.sub(regex_in, '###', text)
    dirty_tokens = replaced.split('###')
    for dirty_token in dirty_tokens:
        clean_token = _clean(dirty_token)
        if len(clean_token) > 0:
            token_start = start + text.index(clean_token)
            token_end = token_start + len(clean_token)
            if trunk.type == 'main':
                pre_terms.append((Entity, clean_token, clean_token, token_start, token_end))
            else:
                pre_terms.append((Constraint, clean_token, clean_token, token_start, token_end))
    return pre_terms
    
    
def evidence_split(goid, label):
    """
    Given a goid and one of its label, return a list of terms
    """
    pre_terms = [e for t in split_trunk(label) for e in split_pattern(t)]
    evidences = []
    for pre_term in pre_terms:
        if pre_term[0] is Pattern:
            term = Pattern(*pre_term[1:2], ref='annotator')
            evid = Evidence(term, *pre_term[2:])
            evidences.append(evid)
        else:
            term = pre_term[0](*pre_term[1:2], ref=goid)
            evid = Evidence(term, *pre_term[2:])
            evidences.append(evid)
    evidences.sort(key=lambda e: e.start)
    return evidences
    
    
class Cluster(object):
    def __init__(self, primary_term, terms=None):
        self.primary_term = primary_term
        if terms is None:
            self.terms = set()
        else:
            self.terms = set(terms)
            
        self.updated_fragments = False
        self._fragments = set()
        self._term_queue = list(self.terms)
    
    def __hash__(self):
        return hash(self.primary_term)
        
    def __eq__(self, other):
        return all([self.primary_term==other.primary_term,
                    self.terms==other.terms])
    
    def __repr__(self):
        return "Cluster({})<{} terms>".format(repr(self.primary_term), len(self.terms))
    
    def __iter__(self):
        for term in self.terms:
            yield term
    
    def fragments(self):
        if self.updated_fragments:
            return self._fragments
        
        else:
            for term in self._term_queue:
                self._fragments |= set(term.lemma.split(' '))
            self._term_queue = []
            self.updated_fragments = True
            return self._fragments
            
    def add(self, term):
        self.updated_fragments = False
        self._term_queue.append(term)
        self.terms.add(term)
    
    def merge(self, other):
        self.updated_fragments = False
        self.terms |= other.terms
        self._fragments |= other.fragments()
        del other
        
class ClusterBook(object):
    def __init__(self):
        self.clusters = set()
        self.index = dict()
        
    def __repr__(self):
        return 'ClusterBook <{} clusters, {} terms>'.format(len(self.clusters), len(self.index.keys()))
    
    def add(self, cluster):
        self.clusters.add(cluster)
        for term in cluster:
            self.index[term] = cluster
    
    def merge(self, cluster1, cluster2):
        if cluster1 in self.clusters:
            for term in cluster2:
                self.index[term] = cluster1
            cluster1.merge(cluster2)
            
        elif cluster2 in self.clusters:
            for term in cluster1:
                self.index[term] = cluster2
            cluster2.merge(cluster1)
        else:
            raise ValueError
    
    def merge_term(self, term1, term2):
        cluster = self.index[term1]
        cluster.add(term2)
        self.index[term2] = cluster
    
    def add_terms(self, terms):
        for term in terms:
            if not term in self.index:
                primary_term = term
                cluster = Cluster(primary_term, [term])
                self.add(cluster)
        
def has_common(cluster1, cluster2):
    set1 = set([t.lemma for t in cluster1.terms])
    set2 = set([t.lemma for t in cluster2.terms])
    if len(set1 & set2) == 0:
        return False
    return True

def jaccard(cluster1, cluster2):
    set1 = cluster1.fragments()
    set2 = cluster2.fragments()
    return len(set1 & set2)/len(set1 | set2)

def sim(cluster1, cluster2):
    if not has_common(cluster1, cluster2):
        return 0.0
    else:
        return jaccard(cluster1, cluster2)
        
        
class GoData(dict):
    def __init__(self, obo_path):
        
        self._read(obo_path)
        
        self.goid2mindepth = dict()
        self.goid2maxdepth = dict()
        self._calculate_depth()
        
        self.goid2above = dict()
        self.goid2below = dict()
        self.goid2density = dict()
        self._calculate_density()
        
        self.biological_process = partial(self._get_namespace, 'biological_process')
        self.cellular_component = partial(self._get_namespace, 'cellular_component')
        self.molecular_function = partial(self._get_namespace, 'molecular_function')
    
    def _read(self, obo_path):
        """Read GO data from OBO file"""
        
        with open(obo_path) as f:
            text = f.read()
        blocks = text.split('\n\n')
        term_blocks = filter(lambda block:block[0:6]=='[Term]', 
                             blocks)
        
        for term_block in term_blocks:
            goid = None
            name = None
            namespace = None
            synonym_list = list()
            parent_list = list()
            
            if 'is_obsolete: true' in term_block:
                continue
            lines = term_block.split('\n')
            for line in lines[1:]:
                key, sep, value = line.partition(':')
                if key == 'id':
                    goid = value.strip()
                if key == 'name':
                    name = value.strip()
                if key == 'synonym':
                    synotext = value.strip()
                    synonym = re.findall(r'"(.*?)"', synotext)[0]
                    synonym_list.append(synonym)
                if key == 'namespace':
                    namespace = value.strip()
                if key == 'is_a':
                    parent_id, sep , parent_name = value.partition('!')
                    parent_list.append(parent_id.strip())
                    
            concept = Concept(goid, name, namespace, synonym_list, parent_list)
            self[goid] = concept
    
    def _calculate_depth(self):
        
        cache = dict()
        
        def _calc_depth(goid, func):
            if goid in {'GO:0003674', 'GO:0008150', 'GO:0005575'}:
                return 1
            try:
                return cache[goid]
            except KeyError:
                concept = self[goid]
                return func(_calc_depth(parent_id, func) for parent_id in concept.parent_list) + 1
        
        for goid in self.keys():
            self.goid2maxdepth[goid] = _calc_depth(goid, max)
            self.goid2mindepth[goid] = _calc_depth(goid, min)
    
    def _calculate_density(self):
        
        above_cache = self.goid2above
        
        def _above(goid):
            if goid in {'GO:0003674', 'GO:0008150', 'GO:0005575'}:
                return set()
            try:
                return above_cache[goid]
            except KeyError:
                concept = self[goid]
                above = set.union(*[_above(parent_id) for parent_id in concept.parent_list])
                above |= set(concept.parent_list)
                above_cache[goid] = above
                return above
        
        for goid in self.keys():
            above_cache[goid] = _above(goid)
        
        below_cache = defaultdict(set)
        
        for goid, above in above_cache.items():
            for parent_id in above:
                below_cache[parent_id].add(goid)
        
        self.goid2below = below_cache
        
        total = len(self)
        for goid in self.keys():
            below = self.goid2below.get(goid, set())
            self.goid2density[goid] = float(len(below) + 1) / total
        
        for concept in self.values():
            goid = concept.goid
            concept.density = self.goid2density[goid]

    def _get_namespace(self, namespace):
        for goid, concept in self.items():
            if concept.namespace == namespace:
                yield concept
                
class Concept(object):
    def __init__(self, goid, name, namespace, synonym_list, parent_list, density=-1):
        self.goid = goid
        self.name = name
        self.namespace = namespace
        self.ns = {'biological_process': 'BP', 
                  'cellular_component': 'CC', 
                  'molecular_function': 'MF'}[self.namespace]
        self.synonym_list = synonym_list
        self.labels = [name] + synonym_list
        self.parent_list = parent_list
        self.statements = []
        self.density = density
        
    def __repr__(self):
        return 'Concept<{} {} {}>'.format(self.goid, self.ns, self.name)