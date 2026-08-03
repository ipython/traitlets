"""Tests for traitlets.utils.getargspec"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import functools
from functools import partial

import pytest

from traitlets.utils.getargspec import getargspec


def plain(a, b, c=3):
    pass


def no_defaults(a, b):
    pass


def with_kwonly(a, *, k=1):
    pass


class Sample:
    def method(self, a, b=2):
        pass


def test_plain_function():
    spec = getargspec(plain)
    assert spec.args == ["a", "b", "c"]
    assert spec.defaults == (3,)


def test_method_uses_the_underlying_function():
    spec = getargspec(Sample().method)
    assert spec.args == ["self", "a", "b"]
    assert spec.defaults == (2,)


def test_partial_drops_bound_positional_args():
    spec = getargspec(partial(plain, 1))
    assert spec.args == ["b", "c"]
    assert spec.defaults == (3,)


def test_partial_drops_bound_keyword_args():
    spec = getargspec(partial(plain, c=5))
    assert spec.args == ["a", "b"]
    assert spec.defaults == ()


def test_partial_keyword_without_a_default():
    # Deleting the default is skipped when the argument never had one.
    spec = getargspec(partial(no_defaults, b=2))
    assert spec.args == ["a"]
    assert spec.defaults == ()


def test_partial_drops_bound_keyword_only_args():
    spec = getargspec(partial(with_kwonly, k=2))
    assert spec.args == ["a"]
    assert spec.kwonlyargs == []
    assert spec.kwonlydefaults == {}


def test_nested_partials():
    spec = getargspec(partial(partial(plain, 1), 2))
    assert spec.args == ["c"]


def test_wrapped_functions_are_unwrapped():
    @functools.wraps(plain)
    def wrapper(*args, **kwargs):
        return plain(*args, **kwargs)

    spec = getargspec(wrapper)
    assert spec.args == ["a", "b", "c"]


def test_non_functions_are_rejected():
    with pytest.raises(TypeError, match="is not a Python function"):
        getargspec(len)
