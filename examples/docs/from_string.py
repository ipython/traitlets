#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example of using TraitType.from_string, for docs"""
from __future__ import annotations

from binascii import a2b_hex

from traitlets import Bytes
from traitlets.config import Application


class HexBytes(Bytes):
    def from_string(self, s):
        return a2b_hex(s)


class App(Application):
    aliases = {"key": "App.key"}
    key = HexBytes(
        help="""
        Key to be used.

        Specify as hex on the command-line.
        """,
        config=True,
    )

    def start(self):
        print(f"key={self.key.decode('utf8')}")


if __name__ == "__main__":
    App.launch_instance()
