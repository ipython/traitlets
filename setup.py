#!/usr/bin/env python

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.


# the name of the project
name = 'traitlets'

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------

import sys


if sys.version_info < (3, 7):
    pip_message = 'This may be due to an out of date pip. Make sure you have pip >= 9.0.1.'
    try:
        import pip
        pip_version = tuple([int(x) for x in pip.__version__.split('.')[:3]])
        if pip_version < (9, 0, 1) :
            pip_message = 'Your pip version is out of date, please install pip >= 9.0.1. '\
            'pip {} detected.'.format(pip.__version__)
        else:
            # pip is new enough - it must be something else
            pip_message = ''
    except Exception:
        pass


    error = """
Traitlets 5.0+ supports Python 3.7 and above, following NEP 29.

For any earlier version of Python use traitlets 4.x

Python {py} detected.
{pip}
""".format(py=sys.version_info, pip=pip_message )

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


with open(os.path.join(here, "README.md")) as f:
    long_description = f.read()

setup_args = dict(
    name            = name,
    version         = version_ns['__version__'],
    scripts         = glob(pjoin('scripts', '*')),
    packages        = packages,
    description     = "Traitlets Python configuration system",
    long_description= long_description,
    long_description_content_type = "text/markdown",
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

if 'develop' in sys.argv or any(a.startswith('bdist') for a in sys.argv) or any(a.startswith('sdist') for a in sys.argv):
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
