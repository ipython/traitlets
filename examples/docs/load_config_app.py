#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example of loading configs and overriding

Example:

    $ ./examples/docs/load_config_app.py
    bettername ranking:100

    $ ./examples/docs/load_config_app.py --name cli_name
    cli_name ranking:100

    $ ./examples/docs/load_config_app.py --name cli_name --MyApp.MyClass.ranking=99
    cli_name ranking:99

    $ ./examples/docs/load_config_app.py -c ""
    default ranking:0
"""

from pathlib import Path

from traitlets import Int, Unicode
from traitlets.config import Application, Configurable


class MyClass(Configurable):
    name = Unicode(default_value="default").tag(config=True)
    ranking = Int().tag(config=True)

    def __str__(self):
        return f"{self.name} ranking:{self.ranking}"


class MyApp(Application):
    classes = [MyClass]
    config_file = Unicode(default_value="main_config", help="base name of config file").tag(
        config=True
    )
    aliases = {
        "name": "MyClass.name",
        "ranking": "MyClass.ranking",
        ("c", "config-file"): "MyApp.config_file",
    }

    def initialize(self, argv=None):
        super().initialize(argv=argv)
        if self.config_file:
            self.load_config_file(self.config_file, [Path(__file__).parent / "configs"])

    def start(self):
        print(MyClass(parent=self))


if __name__ == "__main__":
    MyApp.launch_instance()
