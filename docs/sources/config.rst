.. _config_overview:

==============================================
Overview of the traitlets configuration system
==============================================

This section describes the traitletsuration system. 

The main concepts
=================

There are a number of abstractions that the traitletsuration system uses.
Each of these abstractions is represented by a Python class.

Configuration object: :class:`~traitlets.loader.Config`
    A configuration object is a simple dictionary-like class that holds
    configuration attributes and sub-configuration objects. These classes
    support dotted attribute style access (``Foo.bar``) in addition to the
    regular dictionary style access (``Foo['bar']``). Configuration objects
    are smart. They know how to merge themselves with other configuration
    objects and they automatically create sub-configuration objects.

Configurable: :class:`~traitlets.configurable.Configurable`
    A configurable is a regular Python class that serves as a base class for
    all main classes in an application. The
    :class:`~traitlets.configurable.Configurable` base class is
    lightweight and only does one things.

    This :class:`~traitlets.configurable.Configurable` is a subclass
    of :class:`~traitlets.traitlets.HasTraits` that knows how to configure
    itself. Class level traits with the metadata ``config=True`` become
    values that can be configured from the command line and configuration
    files.
    
    Developers create :class:`~traitlets.configurable.Configurable`
    subclasses that implement all of the logic in the application. Each of
    these subclasses has its own configuration information that controls how
    instances are created.

Singletons: :class:`~traitlets.configurable.SingletonConfigurable`
    Any object for which there is a single canonical instance. These are
    just like Configurables, except they have a class method 
    :meth:`~traitlets.configurable.SingletonConfigurable.instance`,
    that returns the current active instance (or creates one if it
    does not exist).  Examples of singletons include
    :class:`~traitlets.application.Application`s and
    :class:`~IPython.core.interactiveshell.InteractiveShell`.  This lets
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


Class based configuration inheritance
=====================================

There is another aspect of configuration where inheritance comes into play.
Sometimes, your classes will have an inheritance hierarchy that you want
to be reflected in the configuration system.  Here is a simple example::

    from traitlets.configurable import Configurable
    from traitlets.traitlets import Int, Float, Unicode, Bool
    
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

