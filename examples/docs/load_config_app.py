#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example of loading configs and overriding

Example:

    $ ./examples/docs/load_config_app.py
    The school Caltech has a rank of 1.

    $ ./examples/docs/load_config_app.py --name Duke
    The school Duke has a rank of 1.

    $ ./examples/docs/load_config_app.py --name Duke --MyApp.MyClass.ranking=12
    The school Duke has a rank of 12.

    $ ./examples/docs/load_config_app.py -c ""
    The school MIT has a rank of 1.
"""
from __future__ import annotations

from pathlib import Path

from traitlets import Int, Unicode
from traitlets.config import Application, Configurable


class School(Configurable):
    name = Unicode(default_value="MIT").tag(config=True)
    ranking = Int(default_value=1).tag(config=True)

    def __str__(self):
        return f"The school {self.name} has a rank of {self.ranking}."


class MyApp(Application):
    classes = [School]
    config_file = Unicode(default_value="main_config", help="base name of config file").tag(
        config=True
    )
    aliases = {
        "name": "School.name",
        "ranking": "School.ranking",
        ("c", "config-file"): "MyApp.config_file",
    }

    def initialize(self, argv=None):
        super().initialize(argv=argv)
        if self.config_file:
            self.load_config_file(self.config_file, [Path(__file__).parent / "configs"])

    def start(self):
        print(School(parent=self))


if __name__ == "__main__":
    MyApp.launch_instance()
