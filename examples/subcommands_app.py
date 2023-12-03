#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example to demonstrate subcommands with traitlets.Application

Example:

    $ examples/subcommands_app.py foo --print-name alice
    foo
    hello alice

    $ examples/subcommands_app.py bar --print-name bob
    bar
    hello bob
"""
from __future__ import annotations

from traitlets import Enum, Unicode
from traitlets.config.application import Application
from traitlets.config.configurable import Configurable


class PrintHello(Configurable):
    greet_name = Unicode("world").tag(config=True)
    greeting = Enum(values=["hello", "hi", "bye"], default_value="hello").tag(config=True)

    def run(self):
        print(f"{self.greeting} {self.greet_name}")


class FooApp(Application):
    name = Unicode("foo")
    classes = [PrintHello]
    aliases = {
        "print-name": "PrintHello.greet_name",
    }

    config_file = Unicode("", help="Load this config file").tag(config=True)

    def start(self):
        print(self.name)
        PrintHello(parent=self).run()


class BarApp(Application):
    name = Unicode("bar")
    classes = [PrintHello]
    aliases = {
        "print-name": "PrintHello.greet_name",
    }

    config_file = Unicode("", help="Load this config file").tag(config=True)

    def start(self):
        print(self.name)
        PrintHello(parent=self).run()

    @classmethod
    def get_subapp(cls, main_app: Application) -> Application:
        main_app.clear_instance()
        return cls.instance(parent=main_app)  # type: ignore[no-any-return]


class MainApp(Application):
    name = Unicode("subcommand-example-app")
    description = Unicode("demonstrates app with subcommands")
    subcommands = {
        # Subcommands should be a dictionary mapping from the subcommand name
        # to one of the following:
        # 1. The Application class to be instantiated e.g. FooApp
        # 2. A string e.g. "traitlets.examples.subcommands_app.FooApp"
        #    which will be lazily evaluated
        # 3. A callable which takes this Application and returns an instance
        #    (not class) of the subcommmand Application
        "foo": (FooApp, "run foo"),
        "bar": (BarApp.get_subapp, "run bar"),
    }


if __name__ == "__main__":
    MainApp.launch_instance()
