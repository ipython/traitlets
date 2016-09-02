# Documenting traitlets

[Documentation for `traitlets`](https://traitlets.readthedocs.io/en/latest/)
is hosted on ReadTheDocs.

## Build Documentation locally

1. Change directory to documentation root:

           $ cd docs

2. Create environment

   - [**conda**] Create conda env (and install relevant dependencies):

           $ conda env create -f environment.yml

   - [**pip**] Create virtual environment (and install relevant dependencies):

           $ virtualenv traitlets_docs -p python3
           $ pip install -r requirements.txt


3. Activate the newly built environment `traitlets_docs`

   - [**conda**] Activate conda env:

           $ source activate traitlets_docs

   - [**pip**] The virtualenv should have been automatically activated. If
   not:

           $ source activate

4. Build documentation using Makefile for Linux and OS X:

           $ make html

  or on Windows:

           $ make.bat html

5. Display the documentation locally by navigating to
   ``build/html/index.html`` in your browser:

   Or alternatively you may run a local server to display
   the docs. In Python 3:

           $ python -m http.server 8000

   In your browser, go to `http://localhost:8000`.

## Developing Documentation

### Helpful files and directories

* `source/conf.py` - Sphinx build configuration file
* `source` directory - source for documentation
* `source/index.rst` - Main landing page of the Sphinx documentation
