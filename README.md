# MCGOCR 

[![](https://img.shields.io/travis/jeroyang/mcgocr.svg)](https://travis-ci.org/jeroyang/mcgocr)
[![](https://img.shields.io/pypi/v/mcgocr.svg)](https://pypi.python.org/pypi/mcgocr)

MCGOCR (Micro Concept Gene Ontology Concept Recognition)  
Automatic recognize Gene Ontology (GO) concepts from context.

## Installation

```bash
$ pip install -U mcgocr
```

## Usage

### Use as a command line tool
```bash
mcgocr fulltext.txt -o output.txt
```
The format in the output.txt is:  
*start_position, end_position(exclusive), GOID, text*

## License
* Free software: MIT license
