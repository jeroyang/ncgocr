#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
import sys
import os

if sys.argv[-1] == 'publish':
    os.system("python setup.py sdist bdist_wheel upload")
    sys.exit()

with open('README.md') as readme_file:
    readme = readme_file.read()

version = '1.0.2'

with open('requirements.txt') as f:
    requirements = f.read().split('\n')

test_requirements = [
    # TODO: put package test requirements here
]

input_fns = ['input/'+fn for fn in '11532192.txt 11597317.txt 11897010.txt 12079497.txt 12546709.txt 12585968.txt'.split(' ')]
setup(
    name='ncgocr',
    version=version,
    description="Named Concept Gene Ontology Concept Recognition",
    long_description=readme,
    author="Chia-Jung, Yang",
    author_email='jeroyang@gmail.com',
    url='https://github.com/jeroyang/ncgocr',
    packages=[
        'ncgocr'
    ],
    package_dir={'ncgocr': 'ncgocr'},
    data_files=[('input', input_fns)],
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='ncgocr',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
