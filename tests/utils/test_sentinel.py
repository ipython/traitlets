"""Tests for traitlets.utils.sentinel"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import copy

from traitlets.utils.sentinel import Sentinel


def test_repr_includes_the_module():
    assert repr(Sentinel("Undefined", "traitlets")) == "traitlets.Undefined"


def test_docstring_is_optional():
    assert Sentinel("Thing", "mod", "The docs.").__doc__ == "The docs."
    # Without one, the class docstring is left alone.
    assert Sentinel("Thing", "mod").__doc__ == Sentinel.__doc__


def test_copies_are_the_same_object():
    sentinel = Sentinel("Undefined", "traitlets")
    assert copy.copy(sentinel) is sentinel
    assert copy.deepcopy(sentinel) is sentinel
    assert copy.deepcopy([sentinel])[0] is sentinel
