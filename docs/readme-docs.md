# Documenting traitlets

[Documentation for `traitlets`](https://traitlets.readthedocs.io/en/latest/) is hosted on ReadTheDocs.

## Build documentation locally

With [`hatch`](https://hatch.pypa.io/), one can build environments, docs, and serve it in one command:

```
pip install hatch
hatch run docs:build
```

#### Build documentation manually

Otherwise to build docs manually,

```
cd docs
```

Create virtual environment (and install relevant dependencies):

```
    virtualenv traitlets_docs -p python3
    pip install -r traitlets[docs]
```

The virtualenv should have been automatically activated. If not:

```
source activate
```

##### Build documentation using:

- Makefile for Linux and OS X:

  ```
    make html
  ```

- make.bat for Windows:

  ```
    make.bat html
  ```

##### Display the documentation locally

- Navigate to `build/html/index.html` in your browser.

- Or alternatively you may run a local server to display
  the docs. In Python 3:

  ```
    python -m http.server 8000
  ```

  In your browser, go to `http://localhost:8000`.

## Developing Documentation

[Jupyter documentation guide](https://jupyter.readthedocs.io/en/latest/contrib_docs/index.html)

## Helpful files and directories

- `source/conf.py` - Sphinx build configuration file
- `source` directory - source for documentation
- `source/index.rst` - Main landing page of the Sphinx documentation
