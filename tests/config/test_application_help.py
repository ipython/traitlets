"""Tests for the help emitters and environment loading of Application.

The existing help tests in test_application.py drive the application through a
subprocess, so the emitters themselves are never measured. These exercise them
in process, one method at a time.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import json
import os

import pytest

from traitlets import Bool, Int, Unicode
from traitlets.config.application import Application, boolean_flag, get_config
from traitlets.config.configurable import Configurable


class Bar(Configurable):
    enabled = Bool(False, help="Whether bar is enabled.").tag(config=True)


class Foo(Configurable):
    name = Unicode("bob", help="The name to use.").tag(config=True)
    count = Int(0, help="How many times to go around.").tag(config=True)


class SubApp(Application):
    name = "subapp"


class HelpApp(Application):
    name = "helpapp"
    version = "1.2.3"
    description = "An application used to exercise the help emitters."
    examples = """
    helpapp --name=alice
    helpapp sub
    """
    classes = [Foo, Bar]
    aliases = {
        "name": "Foo.name",
        "c": "Foo.count",
        ("v", "verbose"): "Foo.name",
    }
    flags = {
        "enable": ({"Bar": {"enabled": True}}, "Enable bar."),
        ("d", "disable"): ({"Bar": {"enabled": False}}, "Disable bar."),
    }
    subcommands = {"sub": (SubApp, "Run the subcommand.")}


class BareApp(Application):
    """A docstring standing in for a description."""

    name = "bareapp"
    # Application supplies --log-level and --debug by default, and a
    # non-empty description, so an app with nothing of its own has to say so.
    description = ""
    aliases = {}
    flags = {}


@pytest.fixture
def app():
    return HelpApp()


# Windows upper-cases every key in os.environ, so HELPAPP__Foo__name arrives as
# HELPAPP__FOO__NAME. load_config_environ splits the trait name off the end and
# assigns it as-is, and Config refuses a key starting with an uppercase letter
# unless the value is another Config:
#
#     ValueError: values whose keys begin with an uppercase char must be
#     Config instances: 'NAME', DeferredConfigString('...')
#
# Every trait name is upper-cased the same way, so this is not specific to the
# names used here. See the "Warning, case sensitive!" note in the method.
needs_case_sensitive_environ = pytest.mark.skipif(
    os.name == "nt",
    reason="Windows upper-cases environment variable names",
)


def test_emit_alias_help(app):
    lines = list(app.emit_alias_help())
    text = "\n".join(lines)
    assert "--name=<Unicode>" in text
    assert "Equivalent to: [--Foo.name]" in text
    assert "The name to use." in text
    # Single-character aliases get one dash, and tuples list every spelling.
    assert "-c=<Int>" in text
    assert "-v, --verbose=<Unicode>" in text


def test_emit_alias_help_without_aliases():
    assert list(BareApp().emit_alias_help()) == []


def test_emit_flag_help(app):
    text = "\n".join(app.emit_flag_help())
    assert "--enable" in text
    assert "Enable bar." in text
    assert "-d, --disable" in text


def test_emit_flag_help_without_flags():
    assert list(BareApp().emit_flag_help()) == []


def test_emit_options_help(app):
    lines = list(app.emit_options_help())
    assert lines[0] == "Options"
    assert lines[1] == "======="
    text = "\n".join(lines)
    # The options section carries both the flags and the aliases.
    assert "--enable" in text
    assert "Equivalent to: [--Foo.name]" in text


def test_emit_options_help_without_flags_or_aliases():
    assert list(BareApp().emit_options_help()) == []


def test_emit_subcommands_help(app):
    lines = list(app.emit_subcommands_help())
    assert lines[0] == "Subcommands"
    assert lines[1] == "==========="
    text = "\n".join(lines)
    assert "sub" in text
    assert "Run the subcommand." in text


def test_emit_subcommands_help_without_subcommands():
    assert list(BareApp().emit_subcommands_help()) == []


def test_emit_description_uses_the_description(app):
    text = "\n".join(app.emit_description())
    assert "exercise the help emitters" in text


def test_emit_description_falls_back_to_the_docstring():
    text = "\n".join(BareApp().emit_description())
    assert "A docstring standing in for a description." in text


def test_emit_examples(app):
    lines = list(app.emit_examples())
    assert lines[0] == "Examples"
    assert lines[1] == "--------"
    assert "helpapp --name=alice" in "\n".join(lines)


def test_emit_examples_without_examples():
    assert list(BareApp().emit_examples()) == []


def test_emit_help_epilogue_points_at_help_all(app):
    assert "To see all available configurables, use `--help-all`." in list(
        app.emit_help_epilogue(classes=False)
    )


def test_emit_help_epilogue_is_silent_for_help_all(app):
    assert list(app.emit_help_epilogue(classes=True)) == []


def test_emit_help(app):
    text = "\n".join(app.emit_help())
    assert "exercise the help emitters" in text
    assert "Subcommands" in text
    assert "Options" in text
    assert "Examples" in text
    assert "--help-all" in text
    # Without classes=True the per-class options are left out.
    assert "Class options" not in text


def test_emit_help_with_classes(app):
    text = "\n".join(app.emit_help(classes=True))
    assert "Class options" in text
    assert "Foo.name" in text
    assert "Bar.enabled" in text
    # The epilogue is dropped, though --help-all is still mentioned by the
    # keyvalue description that introduces the class options.
    assert "To see all available configurables" not in text


def test_document_config_options(app):
    doc = app.document_config_options()
    assert "Foo.name" in doc
    assert "Bar.enabled" in doc


def test_print_help(app, capsys):
    app.print_help()
    assert "Options" in capsys.readouterr().out


def test_print_help_with_classes(app, capsys):
    app.print_help(classes=True)
    assert "Class options" in capsys.readouterr().out


def test_print_alias_help(app, capsys):
    app.print_alias_help()
    assert "Equivalent to: [--Foo.name]" in capsys.readouterr().out


def test_print_flag_help(app, capsys):
    app.print_flag_help()
    assert "Enable bar." in capsys.readouterr().out


def test_print_options(app, capsys):
    app.print_options()
    assert "Options" in capsys.readouterr().out


def test_print_subcommands(app, capsys):
    app.print_subcommands()
    assert "Run the subcommand." in capsys.readouterr().out


def test_print_description(app, capsys):
    app.print_description()
    assert "exercise the help emitters" in capsys.readouterr().out


def test_print_examples(app, capsys):
    app.print_examples()
    assert "helpapp --name=alice" in capsys.readouterr().out


def test_print_version(app, capsys):
    app.print_version()
    assert capsys.readouterr().out.strip() == "1.2.3"


def test_start_show_config(app, capsys):
    app.config.Foo.name = "alice"
    app.start_show_config()
    out = capsys.readouterr().out
    assert "Foo" in out
    assert ".name = 'alice'" in out


def test_start_show_config_lists_loaded_files(app, capsys):
    app._loaded_config_files = ["/config/one.py", "/config/two.py"]
    app.start_show_config()
    out = capsys.readouterr().out
    assert "Loaded config files:" in out
    assert "/config/one.py" in out


def test_start_show_config_skips_empty_sections(app, capsys):
    app.config.Foo  # touching a section creates it, empty
    app.start_show_config()
    assert "Foo" not in capsys.readouterr().out


def test_start_show_config_json(app, capsys):
    app.show_config_json = True
    app.config.Foo.name = "alice"
    app.start_show_config()
    loaded = json.loads(capsys.readouterr().out)
    assert loaded["Foo"]["name"] == "alice"


def test_start_show_config_hides_its_own_flags(app, capsys):
    app.config.HelpApp.show_config = True
    app.config.HelpApp.show_config_json = False
    app.config.Foo.name = "alice"
    app.start_show_config()
    out = capsys.readouterr().out
    assert "show_config" not in out


@needs_case_sensitive_environ
def test_load_config_environ(app, monkeypatch):
    monkeypatch.setenv("HELPAPP__Foo__name", "from-the-environment")
    app.load_config_environ()
    assert Foo(config=app.config).name == "from-the-environment"


@needs_case_sensitive_environ
def test_load_config_environ_nested_sections(app, monkeypatch):
    # Sections are separated by __, so a deeper path nests further in.
    monkeypatch.setenv("HELPAPP__Deep__Foo__name", "nested")
    app.load_config_environ()
    assert app.config.Deep.Foo.name == "nested"


def test_load_config_environ_ignores_other_variables(app, monkeypatch):
    monkeypatch.setenv("SOMETHINGELSE__Foo__name", "not-mine")
    app.load_config_environ()
    assert Foo(config=app.config).name == "bob"


@needs_case_sensitive_environ
def test_load_config_environ_keeps_the_command_line_winning(app, monkeypatch):
    app.cli_config.Foo.name = "from-the-command-line"
    monkeypatch.setenv("HELPAPP__Foo__name", "from-the-environment")
    app.load_config_environ()
    assert Foo(config=app.config).name == "from-the-command-line"


def test_boolean_flag_defaults():
    flags = boolean_flag("bar", "Bar.enabled")
    assert flags["bar"] == ({"Bar": {"enabled": True}}, "set Bar.enabled=True")
    assert flags["no-bar"] == ({"Bar": {"enabled": False}}, "set Bar.enabled=False")


def test_boolean_flag_with_help_strings():
    flags = boolean_flag("bar", "Bar.enabled", "Turn it on.", "Turn it off.")
    assert flags["bar"][1] == "Turn it on."
    assert flags["no-bar"][1] == "Turn it off."


def test_get_config_without_an_application():
    Application.clear_instance()
    assert get_config() == {}


def test_get_config_with_an_application():
    try:
        app = Application.instance()
        app.config.Foo.name = "alice"
        assert get_config().Foo.name == "alice"
    finally:
        Application.clear_instance()


def test_launch_instance():
    class LaunchedApp(Application):
        name = "launched"
        started = False

        def start(self):
            type(self).started = True

    try:
        LaunchedApp.launch_instance(argv=[])
        assert LaunchedApp.started
        assert LaunchedApp.initialized()
    finally:
        LaunchedApp.clear_instance()
