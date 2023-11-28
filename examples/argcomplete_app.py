#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example to test CLI completion with `traitlets.Application`

Follow the installation instructions in
https://github.com/kislyuk/argcomplete#installation
to install argcomplete. For example for bash, you can set up global completion
via something like::

   $ activate-global-python-argcomplete --dest=~/.bash_completion.d

and ``source ~/.bash_completion.d`` in your ``~/.bashrc``. To use the
`global-python-argcomplete`, your `traitlets.Application`-based script should
have the string ``PYTHON_ARGCOMPLETE_OK`` in the first few lines of the script.

Afterwards, try tab completing options to this script::

    # Option completion, show flags, aliases and --Class.
    $ examples/argcomplete_app.py --[TAB]
    --Application.     --JsonPrinter.     --env-vars         --s
    --ArgcompleteApp.  --e                --help             --skip-if-missing
    --EnvironPrinter.  --env-var          --json-indent      --style

    $ examples/argcomplete_app.py --A[TAB]
    --Application.     --ArgcompleteApp.

    # Complete class config traits
    $ examples/argcomplete_app.py --EnvironPrinter.[TAB]
    --EnvironPrinter.no_complete      --EnvironPrinter.style
    --EnvironPrinter.skip_if_missing  --EnvironPrinter.vars

    # Using argcomplete's provided EnvironCompleter
    $ examples/argcomplete_app.py --EnvironPrinter.vars=[TAB]
    APPDATA                       LS_COLORS
    COMP_LINE                     NAME
    COMP_POINT                    OLDPWD
    COMP_TYPE                     PATH
    ...

    $ examples/argcomplete_app.py --EnvironPrinter.vars USER [TAB]
    APPDATA                       LS_COLORS
    COMP_LINE                     NAME
    COMP_POINT                    OLDPWD
    COMP_TYPE                     PATH
    ...

    # Alias for --EnvironPrinter.vars
    $ examples/argcomplete_app.py --env-vars P[TAB]
    PATH        PWD         PYTHONPATH

    # Custom completer example
    $ examples/argcomplete_app.py --env-vars PWD --json-indent [TAB]
    2  4  8

    # Enum completer example
    $ examples/argcomplete_app.py --style [TAB]
    ndjson   posix    verbose

    # Bool completer example
    $ examples/argcomplete_app.py --Application.show_config_json [TAB]
    0      1      false  true

If completions are not showing, you can set the environment variable ``_ARC_DEBUG=1``
to assist in debugging argcomplete. This was last checked with ``argcomplete==1.12.3``.
"""
from __future__ import annotations

import json
import os

try:
    from argcomplete.completers import EnvironCompleter, SuppressCompleter
except ImportError:
    EnvironCompleter = SuppressCompleter = None
from traitlets import Bool, Enum, Int, List, Unicode
from traitlets.config.application import Application
from traitlets.config.configurable import Configurable


def _indent_completions(**kwargs):
    """Example of a custom completer, which could be dynamic"""
    return ["2", "4", "8"]


class JsonPrinter(Configurable):
    indent = Int(None, allow_none=True).tag(config=True, argcompleter=_indent_completions)

    def print(self, obj):
        print(json.dumps(obj, indent=self.indent))


class EnvironPrinter(Configurable):
    """A class that has configurable, typed attributes."""

    vars = List(trait=Unicode(), help="Environment variable").tag(
        # NOTE: currently multiplicity is ignored by the traitlets CLI.
        # Refer to issue GH#690 for discussion
        config=True,
        multiplicity="+",
        argcompleter=EnvironCompleter,
    )
    no_complete = Unicode().tag(config=True, argcompleter=SuppressCompleter)
    style = Enum(values=["posix", "ndjson", "verbose"], default_value="posix").tag(config=True)
    skip_if_missing = Bool(False, help="Skip variable if not set").tag(config=True)

    def print(self):
        for env_var in self.vars:
            if env_var not in os.environ:
                if self.skip_if_missing:
                    continue
                raise KeyError(f"Environment variable not set: {env_var}")

            value = os.environ[env_var]
            if self.style == "posix":
                print(f"{env_var}={value}")
            elif self.style == "verbose":
                print(f">> key: {env_var} value:\n{value}\n")
            elif self.style == "ndjson":
                JsonPrinter(parent=self).print({"key": env_var, "value": value})


def bool_flag(trait, value=True):
    return ({trait.this_class.__name__: {trait.name: value}}, trait.help)


class ArgcompleteApp(Application):
    name = Unicode("argcomplete-example-app")
    description = Unicode("prints requested environment variables")
    classes = [JsonPrinter, EnvironPrinter]

    config_file = Unicode("", help="Load this config file").tag(config=True)

    aliases = {
        ("e", "env-var", "env-vars"): "EnvironPrinter.vars",
        ("s", "style"): "EnvironPrinter.style",
        ("json-indent"): "JsonPrinter.indent",
    }

    flags = {
        "skip-if-missing": bool_flag(EnvironPrinter.skip_if_missing),
    }

    def initialize(self, argv=None):
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)

    def start(self):
        EnvironPrinter(parent=self).print()


if __name__ == "__main__":
    ArgcompleteApp.launch_instance()
