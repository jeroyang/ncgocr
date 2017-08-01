# McGOCR

[![](https://img.shields.io/travis/jeroyang/mcgocr.svg)](https://travis-ci.org/jeroyang/mcgocr)
[![](https://img.shields.io/pypi/v/mcgocr.svg)](https://pypi.python.org/pypi/mcgocr)

- Mini Concept Gene Ontology Concept Recognition
- Automatic recognize Gene Ontology (GO) concepts from context.

## Installation

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

# Load the GO
godata = GoData('data/craft-1.0/ontologies/GO.obo')

# Initiate MCGOCR
mcgocr = MCGOCR(godata)

# Train the model
mcgocr.fit(corpus, goldstandard)

# Load the testing_corpus
# The testing text files are put into the folder `input/`
corpus_name = 'testing corpus'
testing_corpus = Corpus.from_dir('data/craft-1.0/txt/', corpus_name)

# Get the system result
result = mcgocr.predict(testing_corpus)

# Evaluate
from mcgocr.learning import evaluate
report = evaluate(result, goldstandard, 'using the training corpus as the testing corpus')
print(report)


```


## License
* Free software: MIT license
