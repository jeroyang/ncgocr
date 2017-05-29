from collections import defaultdict, namedtuple
from functools import partial
import re

from acora import AcoraBuilder
from collections import defaultdict
from collections import namedtuple
from collections import ChainMap
import random

import pickle

from grepc import gopattern

Sentence = namedtuple('Sentence', 'text offset ref')
Grounds = namedtuple('Grounds', 'evidences sentence')
Candidate = namedtuple('Candidate', 'statement density evidences grounds')
Basket = namedtuple('Basket', 'candidates more_info')

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
        self.statements = [name] + self.synonym_list
        
    def __repr__(self):
        return 'Concept<{} {} {}>'.format(self.goid, self.ns, self.name)


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
                self._fragments |= set(term.token.split(' '))
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
        

class Corpus(object):
    def __init__(self, sentences):
        self.sentences = sentences
        self.pmid_set = set([s.ref for s in sentences])
        self.bins = {i:set() for i in range(10)}
        pmid_list = sorted(list(self.pmid_set))
        random.seed(0)
        random.shuffle(pmid_list)
        for i, pmid in enumerate(pmid_list):
            b = i % 10
            self.bins[b].add(pmid)
            
    def get_training_testing(self, bin_number):
        """The bin_number should in range(10)"""
        training = []
        testing = []
        for sentence in self.sentences:
            if sentence.docid not in self.bins[bin_number]:
                training.append(sentence)
            else:
                testing.append(sentence)
        return training, testing


class TermIndex(defaultdict):
    def __add__(self, other):
        result = TermIndex(set)
        for key in self.keys() | other.keys():
            result[key] = self[key] | other[key]
        return result
        
    def __repr__(self):
        return 'TermIndex<{} terms, {} mini concepts>'.format(len(self), sum([len(value) for value in self.values()]))
        
def _fit_border(text, span):
    start, end = span
    left_border = text[max(0, start-1):start+1]
    right_border = text[end-1:end+1]
    judge = re.compile(r'(.\b.|^.$)').match
    return all([judge(left_border),
                judge(right_border)])

class SolidExtractor(object):
    def __init__(self, text2primary_terms):
        self.text2primary_terms = text2primary_terms
        
        builder = AcoraBuilder()
        for text in text2primary_terms:
            builder.add(text)
        self.ac = builder.build()
    
    def findall(self, sentence):
        ac = self.ac
        text2primary_terms = self.text2primary_terms
        result = []
        offset = sentence.offset
        for text, raw_start in ac.findall(sentence.text):
            for primary_term in text2primary_terms[text]:
                start = raw_start + offset
                raw_end = raw_start + len(text)
                end = start + len(text)
                if _fit_border(sentence.text, (raw_start, raw_end)):
                    if isinstance(primary_term, Entity):
                        Class_ = Entity
                    elif isinstance(primary_term, Constraint):
                        Class_ = Constraint
                    else:
                        continue
                    lemma = primary_term.lemma
                    ref = primary_term.ref
                    term = Class_(lemma, ref)
                    evidence = Evidence(term, text, start, end)
                    result.append(evidence)
        return result
                    
class SoftExtractor(object):
    def __init__(self, pattern_regex):
        self.pattern_ex = re.compile(pattern_regex)
    
    def findall(self, sentence):
        ex = self.pattern_ex
        offset = sentence.offset
        result = []
        for m in ex.finditer(sentence.text):
            lemma = list(filter(lambda item: item[1] is not None, m.groupdict().items()))[0][0]
            raw_start, raw_end = m.span()
            text = sentence.text[raw_start:raw_end]
            start, end = raw_start + offset, raw_end + offset
            term = Pattern(lemma, 'annotator')
            evidence = Evidence(term, text, start, end)
            result.append(evidence)
        return result

class JoinExtractor(object):
    def __init__(self, extractors):
        self.extractors = extractors
        
    def findall(self, sentence):
        result = []
        for extractor in self.extractors:
            result.extend(extractor.findall(sentence))
        result.sort(key=lambda e: e.start)
        return result

def gather_evidences(statement, index, term2index_evidence):
    evidences = []
    for term in statement.terms():
        try:
            i_evidence = [(abs(index - i), evidence) for i, evidence in term2index_evidence[term]]
            evidence = sorted(i_evidence, key=lambda x:x[0])
            evidences.append(evidence[0][1])
        except:
            pass
    return evidences
        
def gather_baskets(grounds, more_info, term2statements):
    baskets = []
    term2index_evidence = defaultdict(list)
    queue = []
    evidences = grounds.evidences
    for i, evidence in enumerate(evidences):
        term = evidence.term
        term2index_evidence[term].append((i, evidence))
        if isinstance(term, Entity) or isinstance(term, Pattern):
            queue.append((i, term))
    term2index_evidence = dict(term2index_evidence)
    for i, ep in queue:
        candidates = []
        statements = term2statements.get(ep, set())

        for statement in statements:
            statid = statement.statid
            goid = statid.partition('%')[0]
            density = gd.goid2density[goid]
            evidences = gather_evidences(statement, i, term2index_evidence)
            candidate = Candidate(statement, 
                                  density, 
                                  gather_evidences(statement, i, term2index_evidence),
                                  grounds)
            candidates.append(candidate)
        candidates.sort(key=lambda c: c.density, reverse=True)
        baskets.append(Basket(candidates, more_info))
    return baskets
    
def concept_features(candidate):
    statement = candidate.statement
    statid = statement.statid
    goid, sep, sulfix = statid.partition('%')
    namespace = gd[goid].namespace
    features = {'GOID': goid,
                'STATID': statid,
                'STATLEN': len(statement.evidences),
                #'IS_DYN': 'dyn' in sulfix,
                #'DENSITY': candidate.density, 
                'NAMESPACE': namespace}
    return features
    
def evidence_features(candidate):
    evidences = candidate.evidences
    sentence_text = candidate.grounds.sentence.text
    offset = candidate.grounds.sentence.offset
    starts = [e.start for e in evidences]
    ends = [e.end for e in evidences]
    raw_start = min(starts) -  offset
    raw_end = max(ends) - offset
    length = raw_end - raw_start
    text = sentence_text[raw_start:raw_end]
    features = {'LENGTH': length,
                'TEXT': text,
                'TEXT[:3]': text[:3],
                'TEXT[-3:]': text[-3:]}
    return features
    
def bias_features(candidate):
    features = dict()
    statement = candidate.statement
    evidences = candidate.evidences
    terms_in_evidences = set([e.term for e in evidences])
    features['OMIT'] = [term.lemma for term in statement.terms() if term not in terms_in_evidences]
    features['SATURATION'] = len(evidences) / len(statement.evidences)
    return features
    
    
def candidate2features(candidate):
    return dict(ChainMap(concept_features(candidate), evidence_features(candidate), bias_features(candidate)))
    
def grounds2features(grounds):
    evidences = grounds.evidences
    features = {#'GROUNDS': {e.text for e in evidences},
                #'LEMMA': {e.term.lemma for e in evidences}
                }
    return features
    
    
def sentence2baskets(sentence, extractor, term2statements):
    grounds = Grounds(extractor.findall(sentence), sentence)
    more_info = grounds2features(grounds)
    more_info.update({'PMID': sentence.docid})
    baskets = gather_baskets(grounds, more_info, term2statements)
    return baskets
    
def join_baskets(sentences, extractor, term2statements):
    all_baskets = []
    for sentence in sentences:
        baskets = sentence2baskets(sentence, extractor, term2statements)
        all_baskets.extend(baskets)
    return all_baskets
    
    
def basket2features(basket):
    candidate_features = []
    for candidate in basket.candidates:
        features = candidate2features(candidate)
        features.update(basket.more_info)
        candidate_features.append(features)
        
    return candidate_features
    
    """
    final_features = []
    for i, features in enumerate(candidate_features):
        features.update({'SOB': False,
                         'EOB': False,
                         'DENSITY[i-1]': False,
                         'DENSITY[i+1]': False,
                         'SATURATION[i-1]': False,
                         'SATURATION[i+1]': False})
        if i == 0:
            features.update({'SOB': True})
        else:
            last_density = candidate_features[i-1]['DENSITY']
            last_saturation = candidate_features[i-1]['SATURATION']
            features.update({'DENSITY[i-1]': last_density,
                             'SATURATION[i-1]': last_saturation})
        if i == len(candidate_features) - 1:
            features.update({'EOB': True})
        else:
            next_density = candidate_features[i+1]['DENSITY']
            next_saturation = candidate_features[i+1]['SATURATION']
            features.update({'DENSITY[i+1]': next_density,
                             'SATURATION[i+1]': next_saturation})
        final_features.append(features)
    return final_features"""
    
def baskets2X(baskets):
    X = []
    for basket in baskets:
        X.append(basket2features(basket))
    return X
    
import os
import re
from lxml import etree

def goldstandard_from_xml(fpath):
    pmid = re.findall(r'/(\d+)\.txt\.knowtator\.xml', fpath)[0]
    assert pmid.isdigit
    t = etree.parse(fpath)
    mentionid2goid = dict()
    mentionid2span = dict()
    for classmention in t.xpath('//classMention'):
        mentionid = ''.join(classmention.xpath('@id'))
        goid = ''.join(classmention.xpath('mentionClass/@id'))
        mentionid2goid[mentionid] = goid

    for annotation in t.xpath('//annotation'):
        mentionid = ''.join(annotation.xpath('mention/@id'))
        spannedtext = ''.join(annotation.xpath('spannedText/text()'))
        start = int(''.join(annotation.xpath('span/@start')))
        end = int(''.join(annotation.xpath('span/@end')))
        mentionid2span[mentionid] = (start, end, spannedtext)

    key_left = mentionid2goid.keys()
    key_right = mentionid2span.keys()
    assert key_left == key_right

    goldstandard = []
    for mentionid in key_left:
        goid = mentionid2goid[mentionid]
        start, end, spannedtext = mentionid2span[mentionid]
        goldstandard.append((pmid, goid, start, end, spannedtext))
        
    return goldstandard
    
from intervaltree import Interval, IntervalTree
from collections import defaultdict

def make_forest(gold):
    forest = defaultdict(IntervalTree)
    for pmid, goid, start, end, spannedtext in gold:
        t = forest[pmid]
        t[start:end] = (goid, spannedtext)
    forest = dict(forest)
    return forest


def basket2labels(basket, forest):
    labels = []
    pmid = basket.more_info['PMID']
    for candidate in basket.candidates:
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
            labels.append('BINGO')
        else:
            labels.append('NOT')
            
    return labels      
    
    
def baskets2y(baskets, forest):
    y = []
    for basket in baskets:
        y.append(basket2labels(basket, forest))
    return y
    
def candidate2result(candidate):
    pmid = candidate.grounds.sentence.docid
    goid = candidate.statement.statid.partition('%')[0]
    start = min([e.start for e in candidate.evidences])
    end = max([e.end for e in candidate.evidences])
    raw_start = start - candidate.grounds.sentence.offset
    raw_end = end - candidate.grounds.sentence.offset
    text = candidate.grounds.sentence.text[raw_start:raw_end]
    return (pmid, goid, start, end, text)
    
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

def _flaten_X(X):
    output = []
    for features_list in X:
        for features in features_list:
            new_features = {}
            for key, value in features.items():
                if isinstance(value, set) or isinstance(value, list):
                    new_features.update({'{}={}'.format(key, v): True for v in value})
                elif isinstance(value, str):
                    new_features.update({'{}={}'.format(key, value): True})
                else:
                    new_features.update({key: value})
            output.append(new_features)
    return output

def _flaten_y(y):
    new_y = []
    for label in [label for list_of_label in y for label in list_of_label]:
        if label == 'NOT':
            new_y.append(0)
        else:
            new_y.append(1)
    return new_y

def flaten(X, y):
    return _flaten_X(X), _flaten_y(y)

import copy
def remove_keys(list_of_features, feature_names):
    output = copy.deepcopy(list_of_features)
    for feature in output:
        for name in feature_names:
            del feature[name]
    return output

def feature_remove_filter(X, feature_names):
    out_X = []
    for list_of_features in X:
        list_of_features = remove_keys(list_of_features, feature_names)
        out_X.append(list_of_features)
    return out_X


def candidate2result(candidate):
    try:
        pmid = candidate.grounds.sentence.docid
    except: 
        pmid = candidate.sentence.docid
    goid = candidate.statement.statid.partition('%')[0]
    start = min([e.start for e in candidate.evidences])
    end = max([e.end for e in candidate.evidences])
    try:
        raw_start = start - candidate.grounds.sentence.offset
        raw_end = end - candidate.grounds.sentence.offset
        text = candidate.grounds.sentence.text[raw_start:raw_end]
    except:
        raw_start = start - candidate.sentence.offset
        raw_end = end - candidate.sentence.offset
        text = candidate.sentence.text[raw_start:raw_end]
    return (pmid, goid, start, end, text)

def recover(all_baskets, y):
    results = []
    for basket, labels in zip(all_baskets, y):
        basket_results = set()
        pmid = basket.more_info['PMID']
        for candidate, label in zip(basket.candidates, labels):
            if label == 1 or label == 'BINGO':
                 basket_results.add(candidate2result(candidate))
        sorted_basket_results = sorted(list(basket_results), key=lambda r:r[1])
        results.extend(sorted_basket_results)
    return results

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
        
def term_index_from(training_gold, goid2statement_lib):
    term_index = TermIndex(set)
    for pmid, goid, start, end, text in training_gold:
        for statement in goid2statement_lib[1][goid]:
            if len(statement.evidences) == 1:
                term = statement.evidences[0].term
                lemma = term.lemma
                if text!=lemma:
                    term_index[text].add(term)
    return term_index
                    
                    
def get_training_goldstandard(bin_number, gold):
    return [g for g in gold if all([g[0] not in corpus.bins[bin_number], g[1].startswith('GO:')])]

obo_path = 'data/craft-1.0/ontologies/GO.obo'
gd = GoData(obo_path)