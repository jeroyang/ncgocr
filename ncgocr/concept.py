#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module read the GO.OBO and do the essential proccesses
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import datetime
import time
import re
import pickle

from collections import namedtuple, defaultdict
from functools import partial
from copy import copy

import progressbar

from ncgocr import pattern_regex


class Index(dict):
    def __init__(self):
        self.use_default = True

    def __add__(self, other):
        result = copy(self)
        for key, value_set in other.items():
            result[key] |= value_set
        return result

    def __repr__(self):
        template = '{}<{} key(s)>'
        return template.format(self.__class__.__name__, len(self))

    def __missing__(self, key):
        if self.use_default:
            self[key] = set()
            return self[key]
        else:
            return set()
    @classmethod
    def join(cls, indices):
        output = cls()
        for index in indices:
            output += index
        return output


Trunk = namedtuple('Trunk', 'text type start end')



class Term(namedtuple('Term', 'lemma ref')):

    def __repr__(self):
        template = self.__class__.__name__ + '<{} {}>'
        return template.format(self.lemma, self.ref)

    def __hash__(self):
        return hash(self.__class__.__name__) + hash(self.lemma) + hash(self.ref)

    def __eq__(self, other):
        if all([hash(self) == hash(other),
                self.lemma == other.lemma,
                self.ref == other.ref]):
            return True
        return False

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

    def __repr__(self):
        template = 'Statement<{} {}>'
        components = [repr(term) for term in self.terms()]
        return template.format(self.statid, ' '.join(components))

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
    stopwords = '(of|in|to|and|or|the|a)'
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
        r'^(?P<main_trunk>.+?),?\s*\b(?:involved in|during|via|using|by|acting on|from|in)\s(?P<constraint_trunk>.*)$',
        r'^(?P<main_trunk>.+?),\s*\b(?P<constraint_trunk>.*)[\ \-](?:related|dependent)$']

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


def evidence_split(goid, label, regex_in):
    """
    Given a goid and one of its label, return a list of terms
    """
    pre_terms = [e for t in split_trunk(label) for e in split_pattern(t, regex_in)]
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

    def preferred_term(self, term):
        return self.index[term].primary_term

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

    def simplify(self, theshold):
        """
        Return a new clusterbook, in which, a pair of the clusters has a
        similarity greater than the theshold will be merged together
        """
        result = ClusterBook()
        Z = len(self.clusters)**2//10000
        with progressbar.ProgressBar(max_value=Z) as bar:
            for i, cluster in enumerate(self.clusters):
                if len(result.clusters) == 0:
                    result.add(cluster)
                for already_cluster in result.clusters:
                    if sim(cluster, already_cluster) >= theshold:
                        result.merge(already_cluster, cluster)
                        break
                else:
                    result.add(cluster)
                bar.update(i**2//10000)
        return result


def has_common(cluster1, cluster2):
    set1 = set([(t.__class__, t.lemma) for t in cluster1.terms])
    set2 = set([(t.__class__, t.lemma) for t in cluster2.terms])
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
        self._regex_in = pattern_regex.regex_in
        self._regex_out = pattern_regex.regex_out
        self._date = None
        self._read(obo_path)

        self.goid2mindepth = dict()
        self.goid2maxdepth = dict()
        self._calculate_depth()

        self.goid2above = dict()
        self.goid2below = dict()
        self.goid2density = dict()
        self.clusterbook = None
        self._raw_clusterbook = ClusterBook()
        self._calculate_density()

        self.biological_process = partial(self._get_namespace, 'biological_process')
        self.cellular_component = partial(self._get_namespace, 'cellular_component')
        self.molecular_function = partial(self._get_namespace, 'molecular_function')
        self._digest()

    def __repr__(self):
        template = "GoData<{} concepts, {} statements, on {}>"
        concept_count = len(self)
        statement_count = sum([len(s.statements) for s in self.values()])
        datestr = self.date.strftime('%Y/%m/%d')

        return template.format(concept_count, statement_count, datestr )

    def _read(self, obo_path):
        """Read GO data from OBO file"""

        with open(obo_path) as f:
            text = f.read()
        blocks = text.split('\n\n')
        basic_data = blocks[0]
        term_blocks = filter(lambda block:block[0:6]=='[Term]', blocks)

        dt = tuple(i.partition(': ')[2] for i in basic_data.split('\n') if i.partition(':')[0]=='date')[0]
        self.date = datetime.datetime(*time.strptime(dt, "%d:%m:%Y %H:%M")[:6])

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

    def _digest(self):
        """
        Digest the labels of concepts, write the statements,
        and aggregate clusters, save into the self.clusterbook
        """
        regex_in=self._regex_in

        with progressbar.ProgressBar(max_value=len(self)) as bar:

            for j, (goid, concept) in enumerate(self.items()):
                for i, label in enumerate(concept.labels):
                    statid = '%'.join([goid, str(i).zfill(3)])
                    evidences = evidence_split(goid, label, regex_in)
                    terms = [evidence.term for evidence in evidences]
                    statement = Statement(statid, evidences)

                    if len(concept.statements) == 0:
                        concept.statements.append(statement)
                        self._raw_clusterbook.add_terms(terms)
                        continue

                    for already_statement in concept.statements:
                        try:
                            eq_terms = statement.eq_terms(already_statement)
                            for term1, term2 in eq_terms:
                                self._raw_clusterbook.merge_term(term1, term2)
                            break

                        except ValueError:
                            pass
                    else:
                        concept.statements.append(statement)
                        self._raw_clusterbook.add_terms(terms)
                bar.update(j)

        if self.clusterbook is None:
            self.clusterbook = self._raw_clusterbook

    def _rewrite_statements(self):
        for goid, concept in self.items():
            statements = concept.statements
            new_statements = []
            for statement in statements:
                statid = statement.statid
                old_evidences = statement.evidences
                new_evidences = []
                for old_evidence in old_evidences:
                    old_term = old_evidence.term
                    text = old_term.lemma
                    new_term = self.clusterbook.preferred_term(old_term)
                    start = old_evidence.start
                    end = old_evidence.end
                    new_evidences.append(Evidence(new_term, text, start, end))

                new_statements.append(Statement(statid, new_evidences))
            concept.statements = new_statements

    def compression(self, theshold):
        simple_book = self._raw_clusterbook.simplify(theshold)
        self.clusterbook = simple_book
        self._rewrite_statements()

    def get_Ie(self):
        cb = self.clusterbook
        Ie = Index()
        for c in cb.clusters:
            for term in c.terms:
                Ie[term.lemma].add(c.primary_term)
        Ie.use_default = False
        return Ie

    def get_Im(self):
        Im = Index()
        for goid, concept in self.items():
            statements = concept.statements
            for statement in statements:
                if all([isinstance(term, Pattern) for term in statement.terms()]):
                    for term in statement.terms():
                        Im[term].add(statement)
                else:
                    for term in statement.terms():
                        if isinstance(term, Entity):
                            Im[term].add(statement)
        return Im

    def save(self, filepath):
        with open(filepath, 'wb') as f:
            pickle.dump(self, f, protocol=2)

    @classmethod
    def load(cls, filepath):
        with open(filepath, 'rb') as f:
            godata = pickle.load(f)
            return godata

class Concept(object):
    def __init__(self, goid, name, namespace, synonym_list, parent_list, density=-1):
        self.goid = goid
        self.name = name
        self.namespace = namespace
        self.ns = {'biological_process': 'BP',
                  'cellular_component': 'CC',
                  'molecular_function': 'MF'}[namespace]
        self.synonym_list = synonym_list
        self.labels = [name] + synonym_list
        self.parent_list = parent_list
        self.statements = []
        self.density = density

    def __repr__(self):
        return 'Concept<{} {} {}>'.format(self.goid, self.ns, self.name)
