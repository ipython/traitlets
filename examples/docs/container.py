#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example of using container traits in Application command-line"""
from __future__ import annotations

from traitlets import Dict, Integer, List, Unicode
from traitlets.config import Application


class App(Application):
    aliases = {"x": "App.x", "y": "App.y"}
    x = List(Unicode(), config=True)
    y = Dict(Integer(), config=True)

    def start(self):
        print(f"x={self.x}")
        print(f"y={self.y}")


if __name__ == "__main__":
    App.launch_instance()
