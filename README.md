# NCGOCR

[![](https://img.shields.io/travis/jeroyang/ncgocr.svg)](https://travis-ci.org/jeroyang/ncgocr)
[![](https://img.shields.io/pypi/v/ncgocr.svg)](https://pypi.python.org/pypi/ncgocr)

- Named Concept Gene Ontology Concept Recognition
- Automatic recognize Gene Ontology (GO) concepts from context.

## Installation

Using 'pip' to install the Python module
```bash
$ pip install -U ncgocr
```

## Usage
```python
from ncgocr import Craft, GoData, NCGOCR, Corpus

craft = Craft('data')
corpus = craft.get_corpus()
goldstandard = craft.get_goldstandard()

print('Loading GO...')
godata = GoData('data/craft-1.0/ontologies/GO.obo')

print('Initiating NCGOCR...')
ncgocr = NCGOCR(godata)

print('Training the model...')
ncgocr.train(corpus, goldstandard)

print('Loading the testing corpus...')
corpus_name = 'testing corpus'
testing_corpus = Corpus.from_dir('data/craft-1.0/articles/txt/', corpus_name)

print('predicting the results...')
result = ncgocr.process(testing_corpus)

print('Show the first 10 results...')
print(result.to_list()[:10])

print('Evaluate the results...')
from ncgocr.learning import evaluate
report = evaluate(result, goldstandard, 'Using the training corpus as the testing corpus')
print(report)
```


## License
* Free software: MIT license
