#!/usr/bin/env python

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
from glob import glob

from setuptools import setup  # type:ignore[import]

# the name of the project
name = "traitlets"

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
pkg_root = pjoin(here, name)

packages = []
for d, _, _ in os.walk(pjoin(here, name)):
    if os.path.exists(pjoin(d, "__init__.py")):
        packages.append(d[len(here) + 1 :].replace(os.path.sep, "."))

version_ns = {}  # type:ignore
with open(pjoin(here, name, "_version.py")) as f:
    exec(f.read(), {}, version_ns)


with open(os.path.join(here, "README.md")) as f:
    long_description = f.read()

setup_args = dict(
    name=name,
    version=version_ns["__version__"],
    scripts=glob(pjoin("scripts", "*")),
    packages=packages,
    include_package_data=True,
    description="Traitlets Python configuration system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="IPython Development Team",
    author_email="ipython-dev@python.org",
    url="https://github.com/ipython/traitlets",
    project_urls={
        "Documentation": "https://traitlets.readthedocs.io/",
        "Funding": "https://numfocus.org/",
        "Source": "https://github.com/ipython/traitlets",
        "Tracker": "https://github.com/ipython/traitlets/issues",
    },
    license="BSD",
    platforms="Linux, Mac OS X, Windows",
    keywords=["Interactive", "Interpreter", "Shell", "Web"],
    python_requires=">=3.7",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    extras_require={
        "test": ["pytest", "pre-commit"],
    },
)

if __name__ == "__main__":
    setup(**setup_args)
