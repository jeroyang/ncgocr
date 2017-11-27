#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module handles the processes on CRAFT corpus
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import urllib.request
import tarfile
import os
import re

from lxml import etree
from progressbar import ProgressBar

from txttk import corpus as c

BASE_URL = 'https://sourceforge.net/projects/bionlp-corpora/files/CRAFT/'
CRAFT1_URL = BASE_URL + 'v1.0/craft-1.0.tar.gz/download'
CRAFT2_URL = BASE_URL + 'v2.0/craft-2.0.tar.gz/download'

def wanted_members(members):
    for tarinfo in members:
        filepath = tarinfo.name
        if not any([dirname in filepath for dirname in ['knowtator-xml/go_', 'articles/txt/', 'ontologies/']]):
            continue
        if not any([filepath.endswith(ext) for ext in ['txt', 'xml', 'GO.obo']]):
            continue
        yield(tarinfo)


class Craft(object):
    def __init__(self, local_path, version='1.0'):
        if version=='1.0':
            self.url = CRAFT1_URL
            self.filename = 'craft-1.0.tar.gz'
        elif version=='2.0':
            self.url = CRAFT2_URL
            self.filename = 'craft-2.0.tar.gz'
        else:
            raise ValueError('Unsupport CRAFT version')

        self.version = version
        self.local_path = local_path
        self.tarball_path = os.path.join(self.local_path, self.filename)
        self.craft_path = os.path.join(self.local_path, 'craft-'+version)
        self.go_path = os.path.join(self.craft_path, 'ontologies', 'GO.obo')
        os.makedirs(self.local_path, exist_ok=True)

    def download(self):
        pbar = ProgressBar()
        def dlProgress(count, blockSize, totalSize):
            pbar.update(int(count * blockSize * 100 / totalSize))

        print('Downloading the corpus...')
        urllib.request.urlretrieve(self.url, self.tarball_path, reporthook=dlProgress)

    def slim_extract(self):
        if not os.path.isfile(self.tarball_path):
            self.download()

        print('Extracting the corpus...')
        with tarfile.open(self.tarball_path, 'r:gz') as tar:
            tar.extractall(path=self.local_path,
                           members=wanted_members(tar))

    def get_corpus(self):
        txtdir = os.path.join(self.craft_path, 'articles', 'txt')
        if not os.path.isdir(txtdir):
            self.slim_extract()
        print('Reading the corpus...')
        corpus = c.Corpus.from_dir(txtdir, 'CRAFT')
        return corpus

    def get_goldstandard(self):
        xmldir = os.path.join(self.craft_path, 'knowtator-xml')
        if not os.path.isdir(xmldir):
            self.slim_extract()

        craft_path = self.craft_path

        print('Reading the goldstandard of GO...')
        goldstandard = c.Annotation()
        for xml_folder in ['go_bpmf', 'go_cc']:
            xml_dir = os.path.join(craft_path, 'knowtator-xml', xml_folder)
            for filename in os.listdir(xml_dir):
                filepath = os.path.join(xml_dir, filename)
                pmid = re.findall(r'/(\d+)\.txt\.knowtator\.xml', filepath)[0]
                t = etree.parse(filepath)
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

                for mentionid in key_left:
                    goid = mentionid2goid[mentionid]
                    if goid.startswith('GO:'):
                        start, end, spannedtext = mentionid2span[mentionid]
                        goldstandard.add((pmid, goid, start, end, spannedtext))

        return goldstandard
