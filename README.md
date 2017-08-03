# McGOCR

[![](https://img.shields.io/travis/jeroyang/mcgocr.svg)](https://travis-ci.org/jeroyang/mcgocr)
[![](https://img.shields.io/pypi/v/mcgocr.svg)](https://pypi.python.org/pypi/mcgocr)

- Mini Concept Gene Ontology Concept Recognition
- Automatic recognize Gene Ontology (GO) concepts from context.

## Installation

Using 'pip' to install the Python module
```bash
$ pip install -U mcgocr
```

## Usage
```python
from mcgocr import Craft, GoData, MCGOCR, Corpus

# Load the CRAFT corpus for training
craft = Craft('data')
corpus = craft.get_corpus()
goldstandard = craft.get_goldstandard()

print('Loading GO...')
godata = GoData('data/craft-1.0/ontologies/GO.obo')

print('Initiating MCGOCR...')
mcgocr = MCGOCR(godata)

print('Training the model...')
mcgocr.fit(corpus, goldstandard)

print('Loading the testing corpus...')
corpus_name = 'testing corpus'
testing_corpus = Corpus.from_dir('data/craft-1.0/txt/', corpus_name)

print('predicting the results...')
result = mcgocr.predict(testing_corpus)

print('Show the first 10 results...')
print(result.to_list()[:10])

print('Evaluate the results...')
from mcgocr.learning import evaluate
report = evaluate(result, goldstandard, 'using the training corpus as the testing corpus')
print(report)
```


## License
* Free software: MIT license
