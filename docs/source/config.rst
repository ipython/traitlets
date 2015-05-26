==========================================
Configurable objects with traitlets.config
==========================================

.. module:: traitlets.config

This document describes :mod:`traitlets.config`,
the traitlets-based configuration system used by IPython and Jupyter.

The main concepts
=================

There are a number of abstractions that the IPython configuration system uses.
Each of these abstractions is represented by a Python class.

Configuration object: :class:`~traitlets.config.Config`
    A configuration object is a simple dictionary-like class that holds
    configuration attributes and sub-configuration objects. These classes
    support dotted attribute style access (``cfg.Foo.bar``) in addition to the
    regular dictionary style access (``cfg['Foo']['bar']``).
    The Config object is a wrapper around a simple dictionary with some convenience methods,
    such as merging and automatic section creation.

Application: :class:`~traitlets.config.Application`
    An application is a process that does a specific job. The most obvious
    application is the :command:`ipython` command line program. Each
    application reads *one or more* configuration files and a single set of
    command line options
    and then produces a master configuration object for the application. This
    configuration object is then passed to the configurable objects that the
    application creates. These configurable objects implement the actual logic
    of the application and know how to configure themselves given the
    configuration object.

    Applications always have a `log` attribute that is a configured Logger.
    This allows centralized logging configuration per-application.

Configurable: :class:`~traitlets.config.Configurable`
    A configurable is a regular Python class that serves as a base class for
    all main classes in an application. The
    :class:`~traitlets.config.Configurable` base class is
    lightweight and only does one things.

    This :class:`~traitlets.config.Configurable` is a subclass
    of :class:`~traitlets.HasTraits` that knows how to configure
    itself. Class level traits with the metadata ``config=True`` become
    values that can be configured from the command line and configuration
    files.

    Developers create :class:`~traitlets.config.Configurable`
    subclasses that implement all of the logic in the application. Each of
    these subclasses has its own configuration information that controls how
    instances are created.

Singletons: :class:`~traitlets.config.SingletonConfigurable`
    Any object for which there is a single canonical instance. These are
    just like Configurables, except they have a class method
    :meth:`~traitlets.config.SingletonConfigurable.instance`,
    that returns the current active instance (or creates one if it
    does not exist). :class:`~traitlets.config.Application`s is a singleton.
    This lets
    objects easily connect to the current running Application without passing
    objects around everywhere.  For instance, to get the current running
    Application instance, simply do: ``app = Application.instance()``.


.. note::

    Singletons are not strictly enforced - you can have many instances
    of a given singleton class, but the :meth:`instance` method will always
    return the same one.

Having described these main concepts, we can now state the main idea in our
configuration system: *"configuration" allows the default values of class
attributes to be controlled on a class by class basis*. Thus all instances of
a given class are configured in the same way. Furthermore, if two instances
need to be configured differently, they need to be instances of two different
classes. While this model may seem a bit restrictive, we have found that it
expresses most things that need to be configured extremely well. However, it
is possible to create two instances of the same class that have different
trait values. This is done by overriding the configuration.

Now, we show what our configuration objects and files look like.

Configuration objects and files
===============================

A configuration object is little more than a wrapper around a dictionary.
A configuration *file* is simply a mechanism for producing that object.
The main IPython configuration file is a plain Python script,
which can perform extensive logic to populate the config object.
IPython 2.0 introduces a JSON configuration file,
which is just a direct JSON serialization of the config dictionary,
which is easily processed by external software.

When both Python and JSON configuration file are present, both will be loaded,
with JSON configuration having higher priority.

Python configuration Files
--------------------------

A Python configuration file is a pure Python file that populates a configuration object.
This configuration object is a :class:`~traitlets.config.Config` instance.
It is available inside the config file as ``c``, and you simply set
attributes on this. All you have to know is:

* The name of the class to configure.
* The name of the attribute.
* The type of each attribute.

The answers to these questions are provided by the various
:class:`~traitlets.config.Configurable` subclasses that an
application uses. Let's look at how this would work for a simple configurable
subclass::

    # Sample configurable:
    from traitlets.config.configurable import Configurable
    from traitlets import Int, Float, Unicode, Bool

    class MyClass(Configurable):
        name = Unicode(u'defaultname', config=True)
        ranking = Integer(0, config=True)
        value = Float(99.0)
        # The rest of the class implementation would go here..

In this example, we see that :class:`MyClass` has three attributes, two
of which (``name``, ``ranking``) can be configured.  All of the attributes
are given types and default values.  If a :class:`MyClass` is instantiated,
but not configured, these default values will be used.  But let's see how
to configure this class in a configuration file::

    # Sample config file
    c.MyClass.name = 'coolname'
    c.MyClass.ranking = 10

After this configuration file is loaded, the values set in it will override
the class defaults anytime a :class:`MyClass` is created.  Furthermore,
these attributes will be type checked and validated anytime they are set.
This type checking is handled by the :mod:`traitlets` module,
which provides the :class:`~traitlets.Unicode`, :class:`~traitlets.Integer` and
:class:`~traitlets.Float` types; see :doc:`trait_types` for the full list.

It should be very clear at this point what the naming convention is for
configuration attributes::

    c.ClassName.attribute_name = attribute_value

Here, ``ClassName`` is the name of the class whose configuration attribute you
want to set, ``attribute_name`` is the name of the attribute you want to set
and ``attribute_value`` the the value you want it to have. The ``ClassName``
attribute of ``c`` is not the actual class, but instead is another
:class:`~traitlets.config.Config` instance.

.. note::

    The careful reader may wonder how the ``ClassName`` (``MyClass`` in
    the above example) attribute of the configuration object ``c`` gets
    created. These attributes are created on the fly by the
    :class:`~traitlets.config.Config` instance, using a simple naming
    convention. Any attribute of a :class:`~traitlets.config.Config`
    instance whose name begins with an uppercase character is assumed to be a
    sub-configuration and a new empty :class:`~traitlets.config.Config`
    instance is dynamically created for that attribute. This allows deeply
    hierarchical information created easily (``c.Foo.Bar.value``) on the fly.

JSON configuration Files
------------------------

A JSON configuration file is simply a file that contains a
:class:`~traitlets.config.Config` dictionary serialized to JSON.
A JSON configuration file has the same base name as a Python configuration file,
but with a .json extension.

Configuration described in previous section could be written as follows in a
JSON configuration file:

.. sourcecode:: json

    {
      "version": "1.0",
      "MyClass": {
        "name": "coolname",
        "ranking": 10
      }
    }

JSON configuration files can be more easily generated or processed by programs
or other languages.


Configuration files inheritance
===============================

.. note::

    This section only applies to Python configuration files.

Let's say you want to have different configuration files for various purposes.
Our configuration system makes it easy for one configuration file to inherit
the information in another configuration file. The :func:`load_subconfig`
command can be used in a configuration file for this purpose. Here is a simple
example that loads all of the values from the file :file:`base_config.py`::

    # base_config.py
    c = get_config()
    c.MyClass.name = 'coolname'
    c.MyClass.ranking = 100

into the configuration file :file:`main_config.py`::

    # main_config.py
    c = get_config()

    # Load everything from base_config.py
    load_subconfig('base_config.py')

    # Now override one of the values
    c.MyClass.name = 'bettername'

In a situation like this the :func:`load_subconfig` makes sure that the
search path for sub-configuration files is inherited from that of the parent.
Thus, you can typically put the two in the same directory and everything will
just work.


Class based configuration inheritance
=====================================

There is another aspect of configuration where inheritance comes into play.
Sometimes, your classes will have an inheritance hierarchy that you want
to be reflected in the configuration system.  Here is a simple example::

    from traitlets.config.configurable import Configurable
    from traitlets import Int, Float, Unicode, Bool

    class Foo(Configurable):
        name = Unicode(u'fooname', config=True)
        value = Float(100.0, config=True)

    class Bar(Foo):
        name = Unicode(u'barname', config=True)
        othervalue = Int(0, config=True)

Now, we can create a configuration file to configure instances of :class:`Foo`
and :class:`Bar`::

    # config file
    c = get_config()

    c.Foo.name = u'bestname'
    c.Bar.othervalue = 10

This class hierarchy and configuration file accomplishes the following:

* The default value for :attr:`Foo.name` and :attr:`Bar.name` will be
  'bestname'.  Because :class:`Bar` is a :class:`Foo` subclass it also
  picks up the configuration information for :class:`Foo`.
* The default value for :attr:`Foo.value` and :attr:`Bar.value` will be
  ``100.0``, which is the value specified as the class default.
* The default value for :attr:`Bar.othervalue` will be 10 as set in the
  configuration file.  Because :class:`Foo` is the parent of :class:`Bar`
  it doesn't know anything about the :attr:`othervalue` attribute.


.. _commandline:

Command-line arguments
======================

All configurable options can also be supplied at the command line when launching
the application. Applications use a parser called
:class:`~traitlets.config.loader.KeyValueLoader` to load values into a Config
object.

By default, values are assigned in much the same way as in a config file:

.. code-block:: bash

    $ ipython --InteractiveShell.use_readline=False --BaseIPythonApplication.profile='myprofile'

Is the same as adding:

.. sourcecode:: python

    c.InteractiveShell.use_readline=False
    c.BaseIPythonApplication.profile='myprofile'

to your config file. Key/Value arguments *always* take a value, separated by '='
and no spaces.

Common Arguments
----------------

Since the strictness and verbosity of the KVLoader above are not ideal for everyday
use, common arguments can be specified as flags_ or aliases_.

Flags and Aliases are handled by :mod:`argparse` instead, allowing for more flexible
parsing. In general, flags and aliases are prefixed by ``--``, except for those
that are single characters, in which case they can be specified with a single ``-``, e.g.:

.. code-block:: bash

    $ ipython -i -c "import numpy; x=numpy.linspace(0,1)" --profile testing --colors=lightbg

Flags and aliases are declared by specifying ``flags`` and ``aliases``
attributes as dictionaries on subclasses of :class:`~traitlets.config.Application`.

Aliases
*******

For convenience, applications have a mapping of commonly used traits, so you don't have
to specify the whole class name:

.. code-block:: bash

    $ ipython --profile myprofile
    # and
    $ ipython --profile='myprofile'
    # are equivalent to
    $ ipython --BaseIPythonApplication.profile='myprofile'

Flags
*****

Applications can also be passed **flags**. Flags are options that take no
arguments. They are simply wrappers for
setting one or more configurables with predefined values, often True/False.

For instance:

.. code-block:: bash

    $ ipcontroller --debug
    # is equivalent to
    $ ipcontroller --Application.log_level=DEBUG
    # and
    $ ipython --matplotlib
    # is equivalent to
    $ ipython --matplotlib auto
    # or
    $ ipython --no-banner
    # is equivalent to
    $ ipython --TerminalIPythonApp.display_banner=False

Subcommands
-----------

Configurable applications can also have **subcommands**. Subcommands are modeled
after :command:`git`, and are called with the form :command:`command subcommand
[...args]`. For instance, the QtConsole is a subcommand of terminal IPython:

.. code-block:: bash

    $ ipython qtconsole --profile myprofile

Subcommands are specified as a dictionary on :class:`~traitlets.config.Application`
instances, mapping subcommand names to 2-tuples containing:

1. The application class for the subcommand, or a string which can be imported
   to give this.
2. A short description of the subcommand for use in help output.

To see a list of the available aliases, flags, and subcommands for a configurable
application, simply pass ``-h`` or ``--help``. And to see the full list of
configurable options (*very* long), pass ``--help-all``.


Design requirements
===================

Here are the main requirements we wanted our configuration system to have:

* Support for hierarchical configuration information.

* Full integration with command line option parsers.  Often, you want to read
  a configuration file, but then override some of the values with command line
  options.  Our configuration system automates this process and allows each
  command line option to be linked to a particular attribute in the
  configuration hierarchy that it will override.

* Configuration files that are themselves valid Python code. This accomplishes
  many things. First, it becomes possible to put logic in your configuration
  files that sets attributes based on your operating system, network setup,
  Python version, etc. Second, Python has a super simple syntax for accessing
  hierarchical data structures, namely regular attribute access
  (``Foo.Bar.Bam.name``). Third, using Python makes it easy for users to
  import configuration attributes from one configuration file to another.
  Fourth, even though Python is dynamically typed, it does have types that can
  be checked at runtime. Thus, a ``1`` in a config file is the integer '1',
  while a ``'1'`` is a string.

* A fully automated method for getting the configuration information to the
  classes that need it at runtime. Writing code that walks a configuration
  hierarchy to extract a particular attribute is painful. When you have
  complex configuration information with hundreds of attributes, this makes
  you want to cry.

* Type checking and validation that doesn't require the entire configuration
  hierarchy to be specified statically before runtime. Python is a very
  dynamic language and you don't always know everything that needs to be
  configured when a program starts.

