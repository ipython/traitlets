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

from traitlets import Bool, Dict, Int, List, Unicode
from traitlets.config.application import Application
from traitlets.config.configurable import Configurable


class Foo(Configurable):
    """A class that has configurable, typed attributes."""

    i = Int(0, help="The integer i.").tag(config=True)
    j = Int(1, help="The integer j.").tag(config=True)
    name = Unicode("Brian", help="First name.").tag(config=True, shortname="B")


class Bar(Configurable):

    enabled = Bool(True, help="Enable bar.").tag(config=True)


class MyApp(Application):

    name = Unicode("myapp")
    running = Bool(False, help="Is the app running?").tag(config=True)
    classes = List([Bar, Foo])  # type:ignore[assignment]
    config_file = Unicode("", help="Load this config file").tag(config=True)

    aliases = Dict(  # type:ignore[assignment]
        dict(
            i="Foo.i",
            j="Foo.j",
            name="Foo.name",
            running="MyApp.running",
            enabled="Bar.enabled",
            log_level="MyApp.log_level",
        )
    )

    flags = Dict(  # type:ignore[assignment]
        dict(
            enable=({"Bar": {"enabled": True}}, "Enable Bar"),
            disable=({"Bar": {"enabled": False}}, "Disable Bar"),
            debug=({"MyApp": {"log_level": 10}}, "Set loglevel to DEBUG"),
        )
    )

    def init_foo(self):
        # Pass config to other classes for them to inherit the config.
        self.foo = Foo(config=self.config)

    def init_bar(self):
        # Pass config to other classes for them to inherit the config.
        self.bar = Bar(config=self.config)

    def initialize(self, argv=None):
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)
        self.init_foo()
        self.init_bar()

    def start(self):
        print("app.config:")
        print(self.config)
        print("try running with --help-all to see all available flags")
        self.log.info("Info Mesage")
        self.log.debug("DebugMessage")
        self.log.critical("Warning")
        self.log.critical("Critical mesage")


def main():
    app = MyApp()
    app.initialize()
    app.start()


if __name__ == "__main__":
    main()
