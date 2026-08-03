"""Tests for traitlets.utils.descriptions"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import pytest

from traitlets.utils.descriptions import add_article, class_of, describe, repr_type


class Sample:
    def method(self):
        pass


class Described:
    def __repr__(self):
        return "<described>"


def a_function():
    pass


def test_describe_indefinite():
    assert describe("a", object()) == "an object"
    assert describe("a", object) == "an object"
    assert describe("a", type(object)) == "a type"


def test_describe_lowercases_the_article():
    assert describe("A", object()) == "an object"
    assert describe("The", object, "I will use") == "the object I will use"


def test_describe_capitalizes_on_request():
    assert describe("a", object(), capital=True) == "An object"
    assert describe("the", object, "I will use", capital=True) == "The object I will use"


def test_describe_with_no_article():
    # Classes are described indefinitely, instances definitely.
    assert describe(None, object) == "object"
    assert describe(None, object(), "I made") == "object I made"
    assert describe(None, object()).startswith("object at '0x")


def test_describe_definite():
    assert describe("the", object).startswith("the object object")
    assert describe("the", type(object)) == "the type type"
    assert describe("the", object()).startswith("the object at '0x")


def test_describe_functions_and_methods_are_tick_wrapped():
    assert describe("the", a_function) == "the function 'a_function'"
    assert describe("the", Sample().method) == "the method 'method'"


def test_describe_uses_the_repr_when_there_is_one():
    assert describe("the", Described()) == "the Described <described>"


def test_describe_verbose_includes_the_module():
    assert describe("a", Sample, verbose=True) == f"a {__name__}.Sample"
    # Builtins are not prefixed with their module.
    assert describe("a", object, verbose=True) == "an object"


def test_describe_verbose_function_names_the_module():
    result = describe("the", a_function, verbose=True)
    assert result.startswith("the ")
    assert f"{__name__}.a_function" in result


def test_describe_verbose_method_names_its_instance():
    result = describe("the", Sample().method, verbose=True)
    assert "Sample at '0x" in result
    assert "method" in result


def test_describe_rejects_other_articles():
    with pytest.raises(ValueError, match="should be 'the', 'a', 'an', or None"):
        describe("some", object())


def test_class_of():
    assert class_of(Sample) == "a Sample"
    assert class_of(Sample()) == "a Sample"
    assert class_of(object()) == "an object"


def test_add_article():
    assert add_article("object") == "an object"
    assert add_article("Sample") == "a Sample"
    assert add_article("object", definite=True) == "the object"
    assert add_article("object", definite=True, capital=True) == "The object"
    # Leading non-word characters do not decide between "a" and "an".
    assert add_article("_object") == "an _object"


def test_repr_type():
    assert repr_type(1) == "1 <class 'int'>"
