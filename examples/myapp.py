#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example of how to use traitlets.config.application.Application.

This should serve as a simple example that shows how the traitlets config
system works. The main classes are:

* traitlets.config.Configurable
* traitlets.config.SingletonConfigurable
* traitlets.config.Config
* traitlets.config.Application

To see the command line option help, run this program from the command line::

    $ python myapp.py -h

To make one of your classes configurable (from the command line and config
files) inherit from Configurable and declare class attributes as traits (see
classes Foo and Bar below). To make the traits configurable, you will need
to set the following options:

* ``config``: set to ``True`` to make the attribute configurable.
* ``shortname``: by default, configurable attributes are set using the syntax
  "Classname.attributename". At the command line, this is a bit verbose, so
  we allow "shortnames" to be declared. Setting a shortname is optional, but
  when you do this, you can set the option at the command line using the
  syntax: "shortname=value".
* ``help``: set the help string to display a help message when the ``-h``
  option is given at the command line. The help string should be valid ReST.

When the config attribute of an Application is updated, it will fire all of
the trait's events for all of the config=True attributes.
"""
from __future__ import annotations

from traitlets import Bool, Dict, Enum, Int, List, Unicode
from traitlets.config.application import Application
from traitlets.config.configurable import Configurable


class SubConfigurable(Configurable):
    subvalue = Int(0, help="The integer subvalue.").tag(config=True)

    def describe(self):
        print("I am SubConfigurable with:")
        print("    subvalue =", self.subvalue)


class Foo(Configurable):
    """A class that has configurable, typed attributes."""

    i = Int(0, help="The integer i.").tag(config=True)
    j = Int(1, help="The integer j.").tag(config=True)
    name = Unicode("Brian", help="First name.").tag(config=True, shortname="B")
    mode = Enum(values=["on", "off", "other"], default_value="on").tag(config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # using parent=self allows configuration in the form c.Foo.SubConfigurable.subvalue=1
        # while c.SubConfigurable.subvalue=1 will still work, this allow to
        # target specific instances of SubConfigurables
        self.subconf = SubConfigurable(parent=self)

    def describe(self):
        print("I am Foo with:")
        print("    i    =", self.i)
        print("    j    =", self.j)
        print("    name =", self.name)
        print("    mode =", self.mode)
        self.subconf.describe()


class Bar(Configurable):
    enabled = Bool(True, help="Enable bar.").tag(config=True)
    mylist = List([1, 2, 3], help="Just a list.").tag(config=True)

    def describe(self):
        print("I am Bar with:")
        print("    enabled = ", self.enabled)
        print("    mylist  = ", self.mylist)
        self.subconf.describe()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # here we do not use parent=self, so configuration in the form
        # c.Bar.SubConfigurable.subvalue=1 will not work. Only
        # c.SubConfigurable.subvalue=1 will work and affect all instances of
        # SubConfigurable
        self.subconf = SubConfigurable(config=self.config)


class MyApp(Application):
    name = Unicode("myapp")
    running = Bool(False, help="Is the app running?").tag(config=True)
    classes = List([Bar, Foo])  # type:ignore[assignment]
    config_file = Unicode("", help="Load this config file").tag(config=True)

    aliases = Dict(  # type:ignore[assignment]
        dict(  # noqa: C408
            i="Foo.i",
            j="Foo.j",
            name="Foo.name",
            mode="Foo.mode",
            running="MyApp.running",
            enabled="Bar.enabled",
            log_level="MyApp.log_level",
        )
    )

    flags = Dict(  # type:ignore[assignment]
        dict(  # noqa: C408
            enable=({"Bar": {"enabled": True}}, "Enable Bar"),
            disable=({"Bar": {"enabled": False}}, "Disable Bar"),
            debug=({"MyApp": {"log_level": 10}}, "Set loglevel to DEBUG"),
        )
    )

    def init_foo(self):
        # You can pass self as parent to automatically propagate config.
        self.foo = Foo(parent=self)

    def init_bar(self):
        # Pass config to other classes for them to inherit the config.
        self.bar = Bar(config=self.config)

    def initialize(self, argv=None):
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)
        self.load_config_environ()
        self.init_foo()
        self.init_bar()

    def start(self):
        print("app.config:")
        print(self.config)
        self.describe()
        print("try running with --help-all to see all available flags")
        assert self.log is not None
        self.log.debug("Debug Message")
        self.log.info("Info Message")
        self.log.warning("Warning Message")
        self.log.critical("Critical Message")

    def describe(self):
        print("I am MyApp with", self.name, self.running, "and 2 sub configurables Foo and bar:")
        self.foo.describe()
        self.bar.describe()


def main():
    app = MyApp()
    app.initialize()
    app.start()


if __name__ == "__main__":
    main()
