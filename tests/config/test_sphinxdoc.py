"""Tests for traitlets.config.sphinxdoc"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

from collections import defaultdict

from traitlets import Bool, Enum, Int, Undefined, Unicode
from traitlets.config.application import Application
from traitlets.config.configurable import Configurable
from traitlets.config.sphinxdoc import (
    class_config_rst_doc,
    format_aliases,
    interesting_default_value,
    reverse_aliases,
    setup,
    write_doc,
)


class ExplodingInt(Int):
    """An Int whose default cannot be rendered, like a trait holding an object."""

    def default_value_repr(self):
        raise ValueError("cannot repr this default")


class Sample(Configurable):
    count = Int(0, help="How many things.").tag(config=True)
    mode = Enum(["a", "b"], default_value="a", help="Which mode.").tag(config=True)
    name = Unicode("bob", help="A name.").tag(config=True)
    undocumented = Bool(False).tag(config=True)
    long_default = Unicode("x" * 100, help="A long one.").tag(config=True)
    newlined = Unicode("a\nb", help="Has a newline.").tag(config=True)
    boom = ExplodingInt(5, help="Unrenderable default.").tag(config=True)
    not_configurable = Int(0, help="Not tagged.")


class SampleApp(Application):
    classes = [Sample]
    aliases = {"n": "Sample.name", "count": "Sample.count"}
    flags = {
        "flagged": ({"Sample": {"undocumented": True}}, "sets one trait to True"),
        "off": ({"Sample": {"undocumented": False}}, "sets it to False, not an alias"),
        "two-classes": (
            {"Sample": {"undocumented": True}, "Other": {"x": True}},
            "touches two classes",
        ),
        "two-traits": ({"Sample": {"undocumented": True, "count": True}}, "two traits"),
    }


class StubSphinxApp:
    """Stands in for the Sphinx application passed to the extension's setup()."""

    def __init__(self):
        self.object_types = []

    def add_object_type(self, *args, **kwargs):
        self.object_types.append((args, kwargs))


def test_setup_registers_the_configtrait_object_type():
    app = StubSphinxApp()
    metadata = setup(app)
    assert app.object_types == [
        (("configtrait", "configtrait"), {"objname": "Config option"}),
    ]
    assert metadata == {"parallel_read_safe": True, "parallel_write_safe": True}


def test_uninteresting_default_values():
    for dv in (None, Undefined, "", [], (), {}, set()):
        assert not interesting_default_value(dv)


def test_interesting_default_values():
    # Note that a falsy non-container, such as 0, still counts as interesting.
    for dv in ("x", ["a"], ("a",), {"a": 1}, {"a"}, 0, False):
        assert interesting_default_value(dv)


def test_format_aliases_picks_the_dash_count_by_length():
    assert format_aliases(["v"]) == "``-v``"
    assert format_aliases(["v", "verbose"]) == "``-v``, ``--verbose``"
    assert format_aliases([]) == ""


def test_class_config_rst_doc():
    aliases = defaultdict(list)
    aliases["Sample.name"] = ["n", "name"]
    doc = class_config_rst_doc(Sample, aliases)

    assert ".. configtrait:: Sample.count" in doc
    assert "How many things." in doc
    assert ":trait type: Int" in doc
    # Enum traits list their choices instead of their type.
    assert ":options: ``'a'``, ``'b'``" in doc
    assert ":trait type: Enum" not in doc
    assert ":default: ``'bob'``" in doc
    assert ":CLI option: ``-n``, ``--name``" in doc


def test_class_config_rst_doc_describes_undocumented_traits():
    doc = class_config_rst_doc(Sample, defaultdict(list))
    assert "No description" in doc


def test_class_config_rst_doc_skips_traits_that_are_not_config():
    doc = class_config_rst_doc(Sample, defaultdict(list))
    assert "Sample.not_configurable" not in doc


def test_class_config_rst_doc_truncates_long_defaults():
    doc = class_config_rst_doc(Sample, defaultdict(list))
    # 61 characters of the repr are kept, the first of which is its quote.
    assert "``'" + "x" * 60 + "...``" in doc
    assert "x" * 100 not in doc


def test_class_config_rst_doc_doubles_backslashes():
    doc = class_config_rst_doc(Sample, defaultdict(list))
    assert "``'a\\\\nb'``" in doc


def test_class_config_rst_doc_omits_defaults_it_cannot_render():
    doc = class_config_rst_doc(Sample, defaultdict(list))
    boom = doc.split(".. configtrait:: Sample.boom")[1].split(".. configtrait::")[0]
    assert "Unrenderable default." in boom
    assert ":default:" not in boom


def test_reverse_aliases_maps_traits_to_their_aliases():
    res = reverse_aliases(SampleApp())
    assert res["Sample.name"] == ["n"]
    assert res["Sample.count"] == ["count"]


def test_reverse_aliases_treats_true_setting_flags_as_aliases():
    res = reverse_aliases(SampleApp())
    assert res["Sample.undocumented"] == ["flagged"]


def test_reverse_aliases_ignores_flags_that_are_not_simple_aliases():
    res = reverse_aliases(SampleApp())
    for aliases in res.values():
        assert "off" not in aliases
        assert "two-classes" not in aliases
        assert "two-traits" not in aliases


def test_write_doc(tmp_path):
    path = tmp_path / "options.rst"
    write_doc(str(path), "Sample options", SampleApp(), preamble="Some preamble.")
    text = path.read_text(encoding="utf-8")

    assert text.startswith("Sample options\n==============\n")
    assert "Some preamble." in text
    assert ".. configtrait:: Sample.count" in text
    assert ":CLI option: ``--count``" in text


def test_write_doc_without_a_preamble(tmp_path):
    path = tmp_path / "options.rst"
    write_doc(str(path), "Sample options", SampleApp())
    text = path.read_text(encoding="utf-8")

    assert text.startswith("Sample options\n==============\n")
    assert "Some preamble." not in text
    # The application's own config traits are documented alongside Sample's.
    assert ".. configtrait:: Application.log_datefmt" in text
    assert ".. configtrait:: Sample.count" in text
