#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example of using Application flags, for docs"""
from __future__ import annotations

from traitlets import Bool
from traitlets.config import Application, Configurable


class Foo(Configurable):
    enabled = Bool(False, help="whether enabled").tag(config=True)


class App(Application):
    classes = [Foo]
    dry_run = Bool(False, help="dry run test").tag(config=True)
    flags = {
        "dry-run": ({"App": {"dry_run": True}}, dry_run.help),
        ("f", "enable-foo"): (
            {
                "Foo": {"enabled": True},
            },
            "Enable foo",
        ),
        ("disable-foo"): (
            {
                "Foo": {"enabled": False},
            },
            "Disable foo",
        ),
    }


if __name__ == "__main__":
    App.launch_instance()
