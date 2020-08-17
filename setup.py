#!/usr/bin/env python

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.


# the name of the project
name = 'traitlets'

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------

import sys

v = sys.version_info
if v[:2] < (3,7):
    error = "ERROR: %s requires Python version 3.7 or above." % name
    print(error, file=sys.stderr)
    sys.exit(1)

#-----------------------------------------------------------------------------
# get on with it
#-----------------------------------------------------------------------------

import os
from glob import glob

from distutils.core import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
pkg_root = pjoin(here, name)

packages = []
for d, _, _ in os.walk(pjoin(here, name)):
    if os.path.exists(pjoin(d, '__init__.py')):
        packages.append(d[len(here)+1:].replace(os.path.sep, '.'))

version_ns = {}
with open(pjoin(here, name, '_version.py')) as f:
    exec(f.read(), {}, version_ns)


long_desc = """
Traitlets is a pure Python library enabling:

- the enforcement of strong typing for attributes of Python objects
  (typed attributes are called *"traits"*);
- dynamically calculated default values;
- automatic validation and coercion of trait attributes when attempting a
  change;
- registering for receiving notifications when trait values change;
- reading configuring values from files or from command line
  arguments - a distinct layer on top of traitlets, so you may use
  traitlets without the configuration machinery.

Its implementation relies on the [descriptor](https://docs.python.org/howto/descriptor.html)
pattern, and it is a lightweight pure-python alternative of the
[*traits* library](http://code.enthought.com/pages/traits.html).

Traitlets powers the configuration system of IPython and Jupyter
and the declarative API of IPython interactive widgets.
"""


setup_args = dict(
    name            = name,
    version         = version_ns['__version__'],
    scripts         = glob(pjoin('scripts', '*')),
    packages        = packages,
    description     = "Traitlets Python configuration system",
    long_description= long_desc,
    author          = 'IPython Development Team',
    author_email    = 'ipython-dev@python.org',
    url             = 'https://github.com/ipython/traitlets',
    project_urls={
          'Documentation': 'https://traitlets.readthedocs.io/',
          'Funding'      : 'https://numfocus.org/',
          'Source'       : 'https://github.com/ipython/traitlets',
          'Tracker'      : 'https://github.com/ipython/traitlets/issues',
    },
    license         = 'BSD',
    platforms       = "Linux, Mac OS X, Windows",
    keywords        = ['Interactive', 'Interpreter', 'Shell', 'Web'],
    python_requires = '>=3.7',
    classifiers     = [
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)

if 'develop' in sys.argv or any(a.startswith('bdist') for a in sys.argv):
    import setuptools

setuptools_args = {}

install_requires = setuptools_args['install_requires'] = [
    'ipython_genutils',
]

extras_require = setuptools_args['extras_require'] = {
    'test': ['pytest'],
}

if 'setuptools' in sys.modules:
    setup_args.update(setuptools_args)

if __name__ == '__main__':
    setup(**setup_args)
