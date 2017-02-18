# McGOCR

[![](https://img.shields.io/travis/jeroyang/mcgocr.svg)](https://travis-ci.org/jeroyang/mcgocr)
[![](https://img.shields.io/pypi/v/mcgocr.svg)](https://pypi.python.org/pypi/mcgocr)

McGOCR (Micro-concept Gene Ontology Concept Recognition)  
Automatic recognize Gene Ontology (GO) concepts from context.

## Installation

```bash
$ pip install -U mcgocr
```

## Usage

### Use as a command line tool
```bash
mcgocr scan <path_to_input.txt> -o <path_to_output.txt>
```
The format in the output.txt is:  
*start_position, end_position(exclusive), GOID, text*

### Process on a specific GO.OBO
Download the wanted go.obo data from http://geneontology.org/page/download-ontology

```bash
mcgocr read <path_to_go.obo>
``` 
A new file with a name like go\_20161222.info will be created in the ~/data/go folder. The date in the filename means the date of the GO data. 

### Check the available GO repositories
```bash
mcgocr list
```
### Switch between different versions of GO database
```bash
mcgocr use <date of the go>
```


## License
* Free software: MIT license
