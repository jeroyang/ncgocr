#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

import argparse

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