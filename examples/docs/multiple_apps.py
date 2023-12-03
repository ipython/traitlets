#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example of one application calling another"""
from __future__ import annotations

from traitlets.config import Application


class OtherApp(Application):
    def start(self):
        print("other")


class MyApp(Application):
    classes = [OtherApp]

    def start(self):
        # similar to OtherApp.launch_instance(), but without singleton
        self.other_app = OtherApp(config=self.config)
        self.other_app.initialize(["--OtherApp.log_level", "INFO"])
        self.other_app.start()


if __name__ == "__main__":
    MyApp.launch_instance()
