# encoding: utf-8
"""
A lightweight Traits like module.

This is designed to provide a lightweight, simple, pure Python version of
many of the capabilities of enthought.traits.  This includes:

* Validation
* Type specification with defaults
* Static and dynamic notification
* Basic predefined types
* An API that is similar to enthought.traits

We don't support:

* Delegation
* Automatic GUI generation
* A full set of trait types.  Most importantly, we don't provide container
  traits (list, dict, tuple) that can trigger notifications if their
  contents change.
* API compatibility with enthought.traits

There are also some important difference in our design:

* enthought.traits does not validate default values.  We do.

We choose to create this module because we need these capabilities, but
we need them to be pure Python so they work in all Python implementations,
including Jython and IronPython.

Inheritance diagram:

.. inheritance-diagram:: traitlets.traitlets
   :parts: 3
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
#
# Adapted from enthought.traits, Copyright (c) Enthought, Inc.,
# also under the terms of the Modified BSD License.

import contextlib
import inspect
import re
import sys
import types
from types import FunctionType
try:
    from types import ClassType, InstanceType
    ClassTypes = (ClassType, type)
except:
    ClassTypes = (type,)
from warnings import warn

from ipython_genutils import py3compat
from ipython_genutils.py3compat import iteritems, string_types

from .utils.getargspec import getargspec
from .utils.importstring import import_item
from .utils.sentinel import Sentinel
SequenceTypes = (list, tuple, set, frozenset)

#-----------------------------------------------------------------------------
# Basic classes
#-----------------------------------------------------------------------------


Undefined = Sentinel('Undefined', 'traitlets',
'''
Used in Traitlets to specify that no defaults are set in kwargs
'''
)

# Deprecated alias
NoDefaultSpecified = Undefined

class TraitError(Exception):
    pass

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------


def class_of ( object ):
    """ Returns a string containing the class name of an object with the
    correct indefinite article ('a' or 'an') preceding it (e.g., 'an Image',
    'a PlotValue').
    """
    if isinstance( object, py3compat.string_types ):
        return add_article( object )

    return add_article( object.__class__.__name__ )


def add_article ( name ):
    """ Returns a string containing the correct indefinite article ('a' or 'an')
    prefixed to the specified string.
    """
    if name[:1].lower() in 'aeiou':
       return 'an ' + name

    return 'a ' + name


def repr_type(obj):
    """ Return a string representation of a value and its type for readable
    error messages.
    """
    the_type = type(obj)
    if (not py3compat.PY3) and the_type is InstanceType:
        # Old-style class.
        the_type = obj.__class__
    msg = '%r %r' % (obj, the_type)
    return msg


def is_trait(t):
    """ Returns whether the given value is an instance or subclass of TraitType.
    """
    return (isinstance(t, TraitType) or
            (isinstance(t, type) and issubclass(t, TraitType)))


def parse_notifier_name(name):
    """Convert the name argument to a list of names.

    Examples
    --------

    >>> parse_notifier_name('a')
    ['a']
    >>> parse_notifier_name(['a','b'])
    ['a', 'b']
    >>> parse_notifier_name(None)
    ['anytrait']
    """
    if isinstance(name, string_types):
        return [name]
    elif name is None:
        return ['anytrait']
    elif isinstance(name, (list, tuple)):
        for n in name:
            assert isinstance(n, string_types), "names must be strings"
        return name


class _SimpleTest:
    def __init__ ( self, value ): self.value = value
    def __call__ ( self, test  ):
        return test == self.value
    def __repr__(self):
        return "<SimpleTest(%r)" % self.value
    def __str__(self):
        return self.__repr__()


def getmembers(object, predicate=None):
    """A safe version of inspect.getmembers that handles missing attributes.

    This is useful when there are descriptor based attributes that for
    some reason raise AttributeError even though they exist.  This happens
    in zope.inteface with the __provides__ attribute.
    """
    results = []
    for key in dir(object):
        try:
            value = getattr(object, key)
        except AttributeError:
            pass
        else:
            if not predicate or predicate(value):
                results.append((key, value))
    results.sort()
    return results

def _validate_link(*tuples):
    """Validate arguments for traitlet link functions"""
    for t in tuples:
        if not len(t) == 2:
            raise TypeError("Each linked traitlet must be specified as (HasTraits, 'trait_name'), not %r" % t)
        obj, trait_name = t
        if not isinstance(obj, HasTraits):
            raise TypeError("Each object must be HasTraits, not %r" % type(obj))
        if not trait_name in obj.traits():
            raise TypeError("%r has no trait %r" % (obj, trait_name))


class link(object):
    """Link traits from different objects together so they remain in sync.

    Parameters
    ----------
    source : (object / attribute name) pair
    target : (object / attribute name) pair

    Examples
    --------

    >>> c = link((src, 'value'), (tgt, 'value'))
    >>> src.value = 5  # updates other objects as well
    """
    updating = False

    def __init__(self, source, target):
        _validate_link(source, target)
        self.source, self.target = source, target
        try:
            setattr(target[0], target[1], getattr(source[0], source[1]))
        finally:
            source[0].on_trait_change(self._update_target, source[1])
            target[0].on_trait_change(self._update_source, target[1])

    @contextlib.contextmanager
    def _busy_updating(self):
        self.updating = True
        try:
            yield
        finally:
            self.updating = False

    def _update_target(self, name, old, new):
        if self.updating:
            return
        with self._busy_updating():
            setattr(self.target[0], self.target[1], new)

    def _update_source(self, name, old, new):
        if self.updating:
            return
        with self._busy_updating():
            setattr(self.source[0], self.source[1], new)

    def unlink(self):
        self.source[0].on_trait_change(self._update_target, self.source[1], remove=True)
        self.target[0].on_trait_change(self._update_source, self.target[1], remove=True)
        self.source, self.target = None, None


class directional_link(object):
    """Link the trait of a source object with traits of target objects.

    Parameters
    ----------
    source : (object, attribute name) pair
    target : (object, attribute name) pair

    Examples
    --------

    >>> c = directional_link((src, 'value'), (tgt, 'value'))
    >>> src.value = 5  # updates target objects
    >>> tgt.value = 6  # does not update source object
    """
    updating = False

    def __init__(self, source, target):
        _validate_link(source, target)
        self.source, self.target = source, target
        try:
            setattr(target[0], target[1], getattr(source[0], source[1]))
        finally:
            self.source[0].on_trait_change(self._update, self.source[1])

    @contextlib.contextmanager
    def _busy_updating(self):
        self.updating = True
        try:
            yield
        finally:
            self.updating = False

    def _update(self, name, old, new):
        if self.updating:
            return
        with self._busy_updating():
            setattr(self.target[0], self.target[1], new)

    def unlink(self):
        self.source[0].on_trait_change(self._update, self.source[1], remove=True)
        self.source, self.target = None, None

dlink = directional_link


#-----------------------------------------------------------------------------
# Base Descriptor Class 
#-----------------------------------------------------------------------------

class BaseDescriptor(object):
    """Base descriptor class

    Notes
    -----
    This implements Python's descriptor prototol.  

    This class is the base class for all such descriptors.  The
    only magic we use is a custom metaclass for the main :class:`HasTraits`
    class that does the following:

    1. Sets the :attr:`name` attribute of every :class:`BaseDescriptor`
       instance in the class dict to the name of the attribute.
    2. Sets the :attr:`this_class` attribute of every :class:`BaseDescriptor`
       instance in the class dict to the *class* that declared the trait.
       This is used by the :class:`This` trait to allow subclasses to
       accept superclasses for :class:`This` values.
    """

    name = None
    this_class = None

    def instance_init(self, obj):
        """Part of the initialization which may depend on the underlying
        HasTraits instance.

        It is typically overloaded for specific types.

        This method is called by :meth:`HasTraits.__new__` and in the
        :meth:`BaseDescriptor.instance_init` method of descriptors holding
        other descriptors.
        """
        pass


class TraitType(BaseDescriptor):
    """A base class for all trait types.
    """

    metadata = {}
    default_value = Undefined
    allow_none = False
    info_text = 'any value'

    def __init__(self, default_value=Undefined, allow_none=None, **metadata):
        """Declare a traitlet.

        If *allow_none* is True, None is a valid value in addition to any
        values that are normally valid. The default is up to the subclass, but
        most trait types have ``allow_none=False`` by default.

        Extra information about the traitlet can be passed in as keyword
        arguments (``**metadata``). For instance, the config system uses 'config'
        and 'help' keywords.
        """
        if default_value is not Undefined:
            self.default_value = default_value
        if allow_none is not None:
            self.allow_none = allow_none

        if 'default' in metadata:
            # Warn the user that they probably meant default_value.
            warn(
                "Parameter 'default' passed to TraitType. "
                "Did you mean 'default_value'?"
            )

        if len(metadata) > 0:
            if len(self.metadata) > 0:
                self._metadata = self.metadata.copy()
                self._metadata.update(metadata)
            else:
                self._metadata = metadata
        else:
            self._metadata = self.metadata

        self.init()

    def init(self):
        pass

    def get_default_value(self):
        """DEPRECATED: Retrieve the static default value for this trait.

        Use self.default_value instead
        """
        warn("get_default_value is deprecated: use the .default_value attribute",
             stacklevel=2)
        return self.default_value

    def init_default_value(self, obj):
        """DEPRECATED: Set the static default value for the trait type.
        """
        warn("init_default_value is deprecated, and may be removed in the future",
             stacklevel=2)
        value = self._validate(obj, self.default_value)
        obj._trait_values[self.name] = value
        return value

    def _dynamic_default_callable(self, obj):
        """Retrieve a callable to calculate the default for this traitlet.

        This looks for:

        - obj._{name}_default() on the class with the traitlet, or a subclass
          that obj belongs to.
        - trait.make_dynamic_default, which is defined by Instance

        If neither exist, it returns None
        """
        # Traitlets without a name are not on the instance, e.g. in List or Union
        if self.name:
            mro = type(obj).mro()
            meth_name = '_%s_default' % self.name
            for cls in mro[:mro.index(self.this_class)+1]:
                if meth_name in cls.__dict__:
                    return getattr(obj, meth_name)

        return getattr(self, 'make_dynamic_default', None)

    def instance_init(self, obj):
        # If no dynamic initialiser is present, and the trait implementation or
        # use provides a static default, transfer that to obj._trait_values.
        if (self._dynamic_default_callable(obj) is None) \
                and (self.default_value is not Undefined):
            v = self._validate(obj, self.default_value)
            if self.name is not None:
                obj._trait_values[self.name] = v

    def __get__(self, obj, cls=None):
        """Get the value of the trait by self.name for the instance.

        Default values are instantiated when :meth:`HasTraits.__new__`
        is called.  Thus by the time this method gets called either the
        default value or a user defined value (they called :meth:`__set__`)
        is in the :class:`HasTraits` instance.
        """
        if obj is None:
            return self
        else:
            try:
                value = obj._trait_values[self.name]
            except KeyError:
                # Check for a dynamic initializer.
                dynamic_default = self._dynamic_default_callable(obj)
                if dynamic_default is None:
                    raise TraitError("No default value found for %s trait of %r"
                                     % (self.name, obj))
                value = self._validate(obj, dynamic_default())
                obj._trait_values[self.name] = value
                return value
            except Exception:
                # This should never be reached.
                raise TraitError('Unexpected error in TraitType: '
                                 'default value not set properly')
            else:
                return value

    def __set__(self, obj, value):
        new_value = self._validate(obj, value)
        try:
            old_value = obj._trait_values[self.name]
        except KeyError:
            old_value = self.default_value

        obj._trait_values[self.name] = new_value
        try:
            silent = bool(old_value == new_value)
        except:
            # if there is an error in comparing, default to notify
            silent = False
        if silent is not True:
            # we explicitly compare silent to True just in case the equality
            # comparison above returns something other than True/False
            obj._notify_trait(self.name, old_value, new_value)

    def _validate(self, obj, value):
        if value is None and self.allow_none:
            return value
        if hasattr(self, 'validate'):
            value = self.validate(obj, value)
        if obj._cross_validation_lock is False:
            value = self._cross_validate(obj, value)
        return value

    def _cross_validate(self, obj, value):
        if hasattr(obj, '_%s_validate' % self.name):
            cross_validate = getattr(obj, '_%s_validate' % self.name)
            value = cross_validate(value, self)
        return value

    def __or__(self, other):
        if isinstance(other, Union):
            return Union([self] + other.trait_types)
        else:
            return Union([self, other])

    def info(self):
        return self.info_text

    def error(self, obj, value):
        if obj is not None:
            e = "The '%s' trait of %s instance must be %s, but a value of %s was specified." \
                % (self.name, class_of(obj),
                   self.info(), repr_type(value))
        else:
            e = "The '%s' trait must be %s, but a value of %r was specified." \
                % (self.name, self.info(), repr_type(value))
        raise TraitError(e)

    def get_metadata(self, key, default=None):
        return getattr(self, '_metadata', {}).get(key, default)

    def set_metadata(self, key, value):
        getattr(self, '_metadata', {})[key] = value


#-----------------------------------------------------------------------------
# The HasTraits implementation
#-----------------------------------------------------------------------------


class MetaHasTraits(type):
    """A metaclass for HasTraits.

    This metaclass makes sure that any TraitType class attributes are
    instantiated and sets their name attribute.
    """

    def __new__(mcls, name, bases, classdict):
        """Create the HasTraits class.

        This instantiates all TraitTypes in the class dict and sets their
        :attr:`name` attribute.
        """
        # print "MetaHasTraitlets (mcls, name): ", mcls, name
        # print "MetaHasTraitlets (bases): ", bases
        # print "MetaHasTraitlets (classdict): ", classdict
        for k,v in iteritems(classdict):
            if isinstance(v, BaseDescriptor):
                v.name = k
            elif inspect.isclass(v):
                if issubclass(v, TraitType):
                    vinst = v()
                    vinst.name = k
                    classdict[k] = vinst
        return super(MetaHasTraits, mcls).__new__(mcls, name, bases, classdict)

    def __init__(cls, name, bases, classdict):
        """Finish initializing the HasTraits class.

        This sets the :attr:`this_class` attribute of each BaseDescriptor in the
        class dict to the newly created class ``cls``.
        """
        for k, v in iteritems(classdict):
            if isinstance(v, BaseDescriptor):
                v.this_class = cls
        super(MetaHasTraits, cls).__init__(name, bases, classdict)


class HasTraits(py3compat.with_metaclass(MetaHasTraits, object)):
    """The base class for all classes that have traitlets.
    """

    def __new__(cls, *args, **kw):
        # This is needed because object.__new__ only accepts
        # the cls argument.
        new_meth = super(HasTraits, cls).__new__
        if new_meth is object.__new__:
            inst = new_meth(cls)
        else:
            inst = new_meth(cls, **kw)
        inst._trait_values = {}
        inst._trait_notifiers = {}
        inst._cross_validation_lock = True
        # Here we tell all the TraitType instances to set their default
        # values on the instance.
        for key in dir(cls):
            # Some descriptors raise AttributeError like zope.interface's
            # __provides__ attributes even though they exist.  This causes
            # AttributeErrors even though they are listed in dir(cls).
            try:
                value = getattr(cls, key)
            except AttributeError:
                pass
            else:
                if isinstance(value, BaseDescriptor):
                    value.instance_init(inst)
        inst._cross_validation_lock = False
        return inst

    def __init__(self, *args, **kw):
        # Allow trait values to be set using keyword arguments.
        # We need to use setattr for this to trigger validation and
        # notifications.
        with self.hold_trait_notifications():
            for key, value in iteritems(kw):
                setattr(self, key, value)

    @contextlib.contextmanager
    def hold_trait_notifications(self):
        """Context manager for bundling trait change notifications and cross
        validation.

        Use this when doing multiple trait assignments (init, config), to avoid
        race conditions in trait notifiers requesting other trait values.
        All trait notifications will fire after all values have been assigned.
        """
        if self._cross_validation_lock is True:
            yield
            return
        else:
            cache = {}
            _notify_trait = self._notify_trait

            def merge(previous, current):
                """merges notifications of the form (name, old, value)"""
                if previous is None:
                    return current
                else:
                    return (current[0], previous[1], current[2])

            def hold(*a):
                cache[a[0]] = merge(cache.get(a[0]), a)

            try:
                self._notify_trait = hold
                self._cross_validation_lock = True
                yield
                for name in list(cache.keys()):
                    if hasattr(self, '_%s_validate' % name):
                        cross_validate = getattr(self, '_%s_validate' % name)
                        setattr(self, name, cross_validate(getattr(self, name), self))
            except TraitError as e:
                self._notify_trait = lambda *x: None
                for name, value in cache.items():
                    if value[1] is not Undefined:
                        setattr(self, name, value[1])
                    else:
                        self._trait_values.pop(name)
                cache = {}
                raise e
            finally:
                self._notify_trait = _notify_trait
                self._cross_validation_lock = False
                if isinstance(_notify_trait, types.MethodType):
                    # FIXME: remove when support is bumped to 3.4.
                    # when original method is restored,
                    # remove the redundant value from __dict__
                    # (only used to preserve pickleability on Python < 3.4)
                    self.__dict__.pop('_notify_trait', None)

                # trigger delayed notifications
                for v in cache.values():
                    self._notify_trait(*v)

    def _notify_trait(self, name, old_value, new_value):

        # First dynamic ones
        callables = []
        callables.extend(self._trait_notifiers.get(name,[]))
        callables.extend(self._trait_notifiers.get('anytrait',[]))

        # Now static ones
        try:
            cb = getattr(self, '_%s_changed' % name)
        except:
            pass
        else:
            callables.append(cb)

        # Call them all now
        for c in callables:
            # Traits catches and logs errors here.  I allow them to raise
            if callable(c):
                argspec = getargspec(c)

                nargs = len(argspec[0])
                # Bound methods have an additional 'self' argument
                # I don't know how to treat unbound methods, but they
                # can't really be used for callbacks.
                if isinstance(c, types.MethodType):
                    offset = -1
                else:
                    offset = 0
                if nargs + offset == 0:
                    c()
                elif nargs + offset == 1:
                    c(name)
                elif nargs + offset == 2:
                    c(name, new_value)
                elif nargs + offset == 3:
                    c(name, old_value, new_value)
                else:
                    raise TraitError('a trait changed callback '
                                        'must have 0-3 arguments.')
            else:
                raise TraitError('a trait changed callback '
                                    'must be callable.')

    def _add_notifiers(self, handler, name):
        if name not in self._trait_notifiers:
            nlist = []
            self._trait_notifiers[name] = nlist
        else:
            nlist = self._trait_notifiers[name]
        if handler not in nlist:
            nlist.append(handler)

    def _remove_notifiers(self, handler, name):
        if name in self._trait_notifiers:
            nlist = self._trait_notifiers[name]
            try:
                index = nlist.index(handler)
            except ValueError:
                pass
            else:
                del nlist[index]

    def on_trait_change(self, handler, name=None, remove=False):
        """Setup a handler to be called when a trait changes.

        This is used to setup dynamic notifications of trait changes.

        Static handlers can be created by creating methods on a HasTraits
        subclass with the naming convention '_[traitname]_changed'.  Thus,
        to create static handler for the trait 'a', create the method
        _a_changed(self, name, old, new) (fewer arguments can be used, see
        below).

        Parameters
        ----------
        handler : callable
            A callable that is called when a trait changes.  Its
            signature can be handler(), handler(name), handler(name, new)
            or handler(name, old, new).
        name : list, str, None
            If None, the handler will apply to all traits.  If a list
            of str, handler will apply to all names in the list.  If a
            str, the handler will apply just to that name.
        remove : bool
            If False (the default), then install the handler.  If True
            then unintall it.
        """
        if remove:
            names = parse_notifier_name(name)
            for n in names:
                self._remove_notifiers(handler, n)
        else:
            names = parse_notifier_name(name)
            for n in names:
                self._add_notifiers(handler, n)

    @classmethod
    def class_trait_names(cls, **metadata):
        """Get a list of all the names of this class' traits.

        This method is just like the :meth:`trait_names` method,
        but is unbound.
        """
        return cls.class_traits(**metadata).keys()

    @classmethod
    def class_traits(cls, **metadata):
        """Get a `dict` of all the traits of this class.  The dictionary
        is keyed on the name and the values are the TraitType objects.

        This method is just like the :meth:`traits` method, but is unbound.

        The TraitTypes returned don't know anything about the values
        that the various HasTrait's instances are holding.

        The metadata kwargs allow functions to be passed in which
        filter traits based on metadata values.  The functions should
        take a single value as an argument and return a boolean.  If
        any function returns False, then the trait is not included in
        the output.  This does not allow for any simple way of
        testing that a metadata name exists and has any
        value because get_metadata returns None if a metadata key
        doesn't exist.
        """
        traits = dict([memb for memb in getmembers(cls) if
                     isinstance(memb[1], TraitType)])

        if len(metadata) == 0:
            return traits

        for meta_name, meta_eval in metadata.items():
            if type(meta_eval) is not FunctionType:
                metadata[meta_name] = _SimpleTest(meta_eval)

        result = {}
        for name, trait in traits.items():
            for meta_name, meta_eval in metadata.items():
                if not meta_eval(trait.get_metadata(meta_name)):
                    break
            else:
                result[name] = trait

        return result

    @classmethod
    def class_own_traits(cls, **metadata):
        """Get a dict of all the traitlets defined on this class, not a parent.

        Works like `class_traits`, except for excluding traits from parents.
        """
        sup = super(cls, cls)
        return {n: t for (n, t) in cls.class_traits(**metadata).items()
                if getattr(sup, n, None) is not t}

    def has_trait(self, name):
        """Returns True if the object has a trait with the specified name."""
        return isinstance(getattr(self.__class__, name, None), TraitType)
        
    def trait_names(self, **metadata):
        """Get a list of all the names of this class' traits."""
        return self.traits(**metadata).keys()

    def traits(self, **metadata):
        """Get a `dict` of all the traits of this class.  The dictionary
        is keyed on the name and the values are the TraitType objects.

        The TraitTypes returned don't know anything about the values
        that the various HasTrait's instances are holding.

        The metadata kwargs allow functions to be passed in which
        filter traits based on metadata values.  The functions should
        take a single value as an argument and return a boolean.  If
        any function returns False, then the trait is not included in
        the output.  This does not allow for any simple way of
        testing that a metadata name exists and has any
        value because get_metadata returns None if a metadata key
        doesn't exist.
        """
        traits = dict([memb for memb in getmembers(self.__class__) if
                     isinstance(memb[1], TraitType)])

        if len(metadata) == 0:
            return traits

        for meta_name, meta_eval in metadata.items():
            if type(meta_eval) is not FunctionType:
                metadata[meta_name] = _SimpleTest(meta_eval)

        result = {}
        for name, trait in traits.items():
            for meta_name, meta_eval in metadata.items():
                if not meta_eval(trait.get_metadata(meta_name)):
                    break
            else:
                result[name] = trait

        return result

    def trait_metadata(self, traitname, key, default=None):
        """Get metadata values for trait by key."""
        try:
            trait = getattr(self.__class__, traitname)
        except AttributeError:
            raise TraitError("Class %s does not have a trait named %s" %
                                (self.__class__.__name__, traitname))
        else:
            return trait.get_metadata(key, default)

    def add_traits(self, **traits):
        """Dynamically add trait attributes to the HasTraits instance."""
        self.__class__ = type(self.__class__.__name__, (self.__class__,),
                              traits)
        for trait in traits.values():
            trait.instance_init(self)

#-----------------------------------------------------------------------------
# Actual TraitTypes implementations/subclasses
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# TraitTypes subclasses for handling classes and instances of classes
#-----------------------------------------------------------------------------


class ClassBasedTraitType(TraitType):
    """
    A trait with error reporting and string -> type resolution for Type,
    Instance and This.
    """

    def _resolve_string(self, string):
        """
        Resolve a string supplied for a type into an actual object.
        """
        return import_item(string)

    def error(self, obj, value):
        kind = type(value)
        if (not py3compat.PY3) and kind is InstanceType:
            msg = 'class %s' % value.__class__.__name__
        else:
            msg = '%s (i.e. %s)' % ( str( kind )[1:-1], repr( value ) )

        if obj is not None:
            e = "The '%s' trait of %s instance must be %s, but a value of %s was specified." \
                % (self.name, class_of(obj),
                   self.info(), msg)
        else:
            e = "The '%s' trait must be %s, but a value of %r was specified." \
                % (self.name, self.info(), msg)

        raise TraitError(e)


class Type(ClassBasedTraitType):
    """A trait whose value must be a subclass of a specified class."""

    def __init__ (self, default_value=Undefined, klass=None, **metadata):
        """Construct a Type trait

        A Type trait specifies that its values must be subclasses of
        a particular class.

        If only ``default_value`` is given, it is used for the ``klass`` as
        well. If neither are given, both default to ``object``.

        Parameters
        ----------
        default_value : class, str or None
            The default value must be a subclass of klass.  If an str,
            the str must be a fully specified class name, like 'foo.bar.Bah'.
            The string is resolved into real class, when the parent
            :class:`HasTraits` class is instantiated.
        klass : class, str [ default object ]
            Values of this trait must be a subclass of klass.  The klass
            may be specified in a string like: 'foo.bar.MyClass'.
            The string is resolved into real class, when the parent
            :class:`HasTraits` class is instantiated.
        allow_none : bool [ default False ]
            Indicates whether None is allowed as an assignable value.
        """
        if default_value is Undefined:
            new_default_value = object if (klass is None) else klass
        else:
            new_default_value = default_value

        if klass is None:
            if (default_value is None) or (default_value is Undefined):
                klass = object
            else:
                klass = default_value

        if not (inspect.isclass(klass) or isinstance(klass, py3compat.string_types)):
            raise TraitError("A Type trait must specify a class.")

        self.klass       = klass

        super(Type, self).__init__(new_default_value, **metadata)

    def validate(self, obj, value):
        """Validates that the value is a valid object instance."""
        if isinstance(value, py3compat.string_types):
            try:
                value = self._resolve_string(value)
            except ImportError:
                raise TraitError("The '%s' trait of %s instance must be a type, but "
                                 "%r could not be imported" % (self.name, obj, value))
        try:
            if issubclass(value, self.klass):
                return value
        except:
            pass

        self.error(obj, value)

    def info(self):
        """ Returns a description of the trait."""
        if isinstance(self.klass, py3compat.string_types):
            klass = self.klass
        else:
            klass = self.klass.__module__+'.'+self.klass.__name__
        result = "a subclass of '%s'" % klass
        if self.allow_none:
            return result + ' or None'
        return result

    def instance_init(self, obj):
        self._resolve_classes()
        super(Type, self).instance_init(obj)

    def _resolve_classes(self):
        if isinstance(self.klass, py3compat.string_types):
            self.klass = self._resolve_string(self.klass)
        if isinstance(self.default_value, py3compat.string_types):
            self.default_value = self._resolve_string(self.default_value)


class Instance(ClassBasedTraitType):
    """A trait whose value must be an instance of a specified class.

    The value can also be an instance of a subclass of the specified class.

    Subclasses can declare default classes by overriding the klass attribute
    """

    klass = None

    def __init__(self, klass=None, args=None, kw=None, **metadata):
        """Construct an Instance trait.

        This trait allows values that are instances of a particular
        class or its subclasses.  Our implementation is quite different
        from that of enthough.traits as we don't allow instances to be used
        for klass and we handle the ``args`` and ``kw`` arguments differently.

        Parameters
        ----------
        klass : class, str
            The class that forms the basis for the trait.  Class names
            can also be specified as strings, like 'foo.bar.Bar'.
        args : tuple
            Positional arguments for generating the default value.
        kw : dict
            Keyword arguments for generating the default value.
        allow_none : bool [default True]
            Indicates whether None is allowed as a value.

        Notes
        -----
        If both ``args`` and ``kw`` are None, then the default value is None.
        If ``args`` is a tuple and ``kw`` is a dict, then the default is
        created as ``klass(*args, **kw)``.  If exactly one of ``args`` or ``kw`` is
        None, the None is replaced by ``()`` or ``{}``, respectively.
        """
        if klass is None:
            klass = self.klass
        
        if (klass is not None) and (inspect.isclass(klass) or isinstance(klass, py3compat.string_types)):
            self.klass = klass
        else:
            raise TraitError('The klass attribute must be a class'
                                ' not: %r' % klass)

        if (kw is not None) and not isinstance(kw, dict):
            raise TraitError("The 'kw' argument must be a dict or None.")
        if (args is not None) and not isinstance(args, tuple):
            raise TraitError("The 'args' argument must be a tuple or None.")

        self.default_args = args
        self.default_kwargs = kw

        super(Instance, self).__init__(**metadata)

    def validate(self, obj, value):
        if isinstance(value, self.klass):
            return value
        else:
            self.error(obj, value)

    def info(self):
        if isinstance(self.klass, py3compat.string_types):
            klass = self.klass
        else:
            klass = self.klass.__name__
        result = class_of(klass)
        if self.allow_none:
            return result + ' or None'

        return result

    def instance_init(self, obj):
        self._resolve_classes()
        super(Instance, self).instance_init(obj)

    def _resolve_classes(self):
        if isinstance(self.klass, py3compat.string_types):
            self.klass = self._resolve_string(self.klass)

    def make_dynamic_default(self):
        if (self.default_args is None) and (self.default_kwargs is None):
            return None
        return self.klass(*(self.default_args or ()),
                          **(self.default_kwargs or {}))


class ForwardDeclaredMixin(object):
    """
    Mixin for forward-declared versions of Instance and Type.
    """
    def _resolve_string(self, string):
        """
        Find the specified class name by looking for it in the module in which
        our this_class attribute was defined.
        """
        modname = self.this_class.__module__
        return import_item('.'.join([modname, string]))


class ForwardDeclaredType(ForwardDeclaredMixin, Type):
    """
    Forward-declared version of Type.
    """
    pass


class ForwardDeclaredInstance(ForwardDeclaredMixin, Instance):
    """
    Forward-declared version of Instance.
    """
    pass


class This(ClassBasedTraitType):
    """A trait for instances of the class containing this trait.

    Because how how and when class bodies are executed, the ``This``
    trait can only have a default value of None.  This, and because we
    always validate default values, ``allow_none`` is *always* true.
    """

    info_text = 'an instance of the same type as the receiver or None'

    def __init__(self, **metadata):
        super(This, self).__init__(None, **metadata)

    def validate(self, obj, value):
        # What if value is a superclass of obj.__class__?  This is
        # complicated if it was the superclass that defined the This
        # trait.
        if isinstance(value, self.this_class) or (value is None):
            return value
        else:
            self.error(obj, value)


class Union(TraitType):
    """A trait type representing a Union type."""

    def __init__(self, trait_types, **metadata):
        """Construct a Union  trait.

        This trait allows values that are allowed by at least one of the
        specified trait types. A Union traitlet cannot have metadata on
        its own, besides the metadata of the listed types.

        Parameters
        ----------
        trait_types: sequence
            The list of trait types of length at least 1.

        Notes
        -----
        Union([Float(), Bool(), Int()]) attempts to validate the provided values
        with the validation function of Float, then Bool, and finally Int.
        """
        self.trait_types = trait_types
        self.info_text = " or ".join([tt.info_text for tt in self.trait_types])
        self.default_value = self.trait_types[0].default_value
        super(Union, self).__init__(**metadata)

    def instance_init(self, obj):
        for trait_type in self.trait_types:
            trait_type.this_class = self.this_class
            trait_type.instance_init(obj)
        super(Union, self).instance_init(obj)

    def validate(self, obj, value):
        for trait_type in self.trait_types:
            try:
                v = trait_type._validate(obj, value)
                self._metadata = trait_type._metadata
                return v
            except TraitError:
                continue
        self.error(obj, value)

    def __or__(self, other):
        if isinstance(other, Union):
            return Union(self.trait_types + other.trait_types)
        else:
            return Union(self.trait_types + [other])

#-----------------------------------------------------------------------------
# Basic TraitTypes implementations/subclasses
#-----------------------------------------------------------------------------


class Any(TraitType):
    """A trait which allows any value."""
    default_value = None
    info_text = 'any value'


class Int(TraitType):
    """An int trait."""

    default_value = 0
    info_text = 'an int'

    def __init__(self, default_value=Undefined,
                 allow_none=None, **kwargs):
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)
        super(Int, self).__init__(default_value=default_value,
                                  allow_none=allow_none, **kwargs)

    def validate(self, obj, value):
        if not isinstance(value, int):
            self.error(obj, value)
        if self.max is not None and value > self.max:        
            raise TraitError("The value of the '%s' trait of %s instance should "
                             "not be greater than %s, but a value of %s was "
                             "specified" % (self.name, class_of(obj),
                                            self.max, value))
        if self.min is not None and value < self.min:
            raise TraitError("The value of the '%s' trait of %s instance should "
                             "not be less than %s, but a value of %s was "
                             "specified" % (self.name, class_of(obj), 
                                            self.min, value))
        return value


class CInt(Int):
    """A casting version of the int trait."""

    def validate(self, obj, value):
        try:
            return int(value)
        except:
            self.error(obj, value)

if py3compat.PY3:
    Long, CLong = Int, CInt
    Integer = Int
else:
    class Long(TraitType):
        """A long integer trait."""

        default_value = 0
        info_text = 'a long'

        def validate(self, obj, value):
            if isinstance(value, long):
                return value
            if isinstance(value, int):
                return long(value)
            self.error(obj, value)


    class CLong(Long):
        """A casting version of the long integer trait."""

        def validate(self, obj, value):
            try:
                return long(value)
            except:
                self.error(obj, value)

    class Integer(TraitType):
        """An integer trait.

        Longs that are unnecessary (<= sys.maxint) are cast to ints."""

        default_value = 0
        info_text = 'an integer'

        def validate(self, obj, value):
            if isinstance(value, int):
                return value
            if isinstance(value, long):
                # downcast longs that fit in int:
                # note that int(n > sys.maxint) returns a long, so
                # we don't need a condition on this cast
                return int(value)
            if sys.platform == "cli":
                from System import Int64
                if isinstance(value, Int64):
                    return int(value)
            self.error(obj, value)


class Float(TraitType):
    """A float trait."""

    default_value = 0.0
    info_text = 'a float'

    def __init__(self, default_value=Undefined,
                 allow_none=None, **kwargs):
        self.min = kwargs.pop('min', -float('inf'))
        self.max = kwargs.pop('max', float('inf'))
        super(Float, self).__init__(default_value=default_value, 
                                    allow_none=allow_none, **kwargs)

    def validate(self, obj, value):
        if isinstance(value, int):
            value = float(value)
        if not isinstance(value, float):
            self.error(obj, value)
        if value > self.max or value < self.min:
            raise TraitError("The value of the '%s' trait of %s instance should "
                             "be between %s and %s, but a value of %s was "
                             "specified" % (self.name, class_of(obj),
                                            self.min, self.max, value))
        return value


class CFloat(Float):
    """A casting version of the float trait."""

    def validate(self, obj, value):
        try:
            return float(value)
        except:
            self.error(obj, value)

class Complex(TraitType):
    """A trait for complex numbers."""

    default_value = 0.0 + 0.0j
    info_text = 'a complex number'

    def validate(self, obj, value):
        if isinstance(value, complex):
            return value
        if isinstance(value, (float, int)):
            return complex(value)
        self.error(obj, value)


class CComplex(Complex):
    """A casting version of the complex number trait."""

    def validate (self, obj, value):
        try:
            return complex(value)
        except:
            self.error(obj, value)

# We should always be explicit about whether we're using bytes or unicode, both
# for Python 3 conversion and for reliable unicode behaviour on Python 2. So
# we don't have a Str type.
class Bytes(TraitType):
    """A trait for byte strings."""

    default_value = b''
    info_text = 'a bytes object'

    def validate(self, obj, value):
        if isinstance(value, bytes):
            return value
        self.error(obj, value)


class CBytes(Bytes):
    """A casting version of the byte string trait."""

    def validate(self, obj, value):
        try:
            return bytes(value)
        except:
            self.error(obj, value)


class Unicode(TraitType):
    """A trait for unicode strings."""

    default_value = u''
    info_text = 'a unicode string'

    def validate(self, obj, value):
        if isinstance(value, py3compat.unicode_type):
            return value
        if isinstance(value, bytes):
            try:
                return value.decode('ascii', 'strict')
            except UnicodeDecodeError:
                msg = "Could not decode {!r} for unicode trait '{}' of {} instance."
                raise TraitError(msg.format(value, self.name, class_of(obj)))
        self.error(obj, value)


class CUnicode(Unicode):
    """A casting version of the unicode trait."""

    def validate(self, obj, value):
        try:
            return py3compat.unicode_type(value)
        except:
            self.error(obj, value)


class ObjectName(TraitType):
    """A string holding a valid object name in this version of Python.

    This does not check that the name exists in any scope."""
    info_text = "a valid object identifier in Python"

    if py3compat.PY3:
        # Python 3:
        coerce_str = staticmethod(lambda _,s: s)

    else:
        # Python 2:
        def coerce_str(self, obj, value):
            "In Python 2, coerce ascii-only unicode to str"
            if isinstance(value, unicode):
                try:
                    return str(value)
                except UnicodeEncodeError:
                    self.error(obj, value)
            return value

    def validate(self, obj, value):
        value = self.coerce_str(obj, value)

        if isinstance(value, string_types) and py3compat.isidentifier(value):
            return value
        self.error(obj, value)

class DottedObjectName(ObjectName):
    """A string holding a valid dotted object name in Python, such as A.b3._c"""
    def validate(self, obj, value):
        value = self.coerce_str(obj, value)

        if isinstance(value, string_types) and py3compat.isidentifier(value, dotted=True):
            return value
        self.error(obj, value)


class Bool(TraitType):
    """A boolean (True, False) trait."""

    default_value = False
    info_text = 'a boolean'

    def validate(self, obj, value):
        if isinstance(value, bool):
            return value
        self.error(obj, value)


class CBool(Bool):
    """A casting version of the boolean trait."""

    def validate(self, obj, value):
        try:
            return bool(value)
        except:
            self.error(obj, value)


class Enum(TraitType):
    """An enum whose value must be in a given sequence."""

    def __init__(self, values, default_value=Undefined, **metadata):
        self.values = values
        if metadata.get('allow_none', False) and default_value is Undefined:
            default_value = None
        super(Enum, self).__init__(default_value, **metadata)

    def validate(self, obj, value):
        if value in self.values:
                return value
        self.error(obj, value)

    def info(self):
        """ Returns a description of the trait."""
        result = 'any of ' + repr(self.values)
        if self.allow_none:
            return result + ' or None'
        return result

class CaselessStrEnum(Enum):
    """An enum of strings where the case should be ignored."""

    def validate(self, obj, value):
        if not isinstance(value, py3compat.string_types):
            self.error(obj, value)

        for v in self.values:
            if v.lower() == value.lower():
                return v
        self.error(obj, value)

class Container(Instance):
    """An instance of a container (list, set, etc.)

    To be subclassed by overriding klass.
    """
    klass = None
    _cast_types = ()
    _valid_defaults = SequenceTypes
    _trait = None

    def __init__(self, trait=None, default_value=None, **metadata):
        """Create a container trait type from a list, set, or tuple.

        The default value is created by doing ``List(default_value)``,
        which creates a copy of the ``default_value``.

        ``trait`` can be specified, which restricts the type of elements
        in the container to that TraitType.

        If only one arg is given and it is not a Trait, it is taken as
        ``default_value``:

        ``c = List([1,2,3])``

        Parameters
        ----------

        trait : TraitType [ optional ]
            the type for restricting the contents of the Container.  If unspecified,
            types are not checked.

        default_value : SequenceType [ optional ]
            The default value for the Trait.  Must be list/tuple/set, and
            will be cast to the container type.

        allow_none : bool [ default False ]
            Whether to allow the value to be None

        **metadata : any
            further keys for extensions to the Trait (e.g. config)

        """
        # allow List([values]):
        if default_value is None and not is_trait(trait):
            default_value = trait
            trait = None

        if default_value is None:
            args = ()
        elif isinstance(default_value, self._valid_defaults):
            args = (default_value,)
        else:
            raise TypeError('default value of %s was %s' %(self.__class__.__name__, default_value))

        if is_trait(trait):
            self._trait = trait() if isinstance(trait, type) else trait
        elif trait is not None:
            raise TypeError("`trait` must be a Trait or None, got %s" % repr_type(trait))

        super(Container,self).__init__(klass=self.klass, args=args, **metadata)

    def element_error(self, obj, element, validator):
        e = "Element of the '%s' trait of %s instance must be %s, but a value of %s was specified." \
            % (self.name, class_of(obj), validator.info(), repr_type(element))
        raise TraitError(e)

    def validate(self, obj, value):
        if isinstance(value, self._cast_types):
            value = self.klass(value)
        value = super(Container, self).validate(obj, value)
        if value is None:
            return value

        value = self.validate_elements(obj, value)

        return value

    def validate_elements(self, obj, value):
        validated = []
        if self._trait is None or isinstance(self._trait, Any):
            return value
        for v in value:
            try:
                v = self._trait._validate(obj, v)
            except TraitError:
                self.element_error(obj, v, self._trait)
            else:
                validated.append(v)
        return self.klass(validated)

    def instance_init(self, obj):
        if isinstance(self._trait, TraitType):
            self._trait.this_class = self.this_class
            self._trait.instance_init(obj)
        super(Container, self).instance_init(obj)


class List(Container):
    """An instance of a Python list."""
    klass = list
    _cast_types = (tuple,)

    def __init__(self, trait=None, default_value=None, minlen=0, maxlen=sys.maxsize, **metadata):
        """Create a List trait type from a list, set, or tuple.

        The default value is created by doing ``list(default_value)``,
        which creates a copy of the ``default_value``.

        ``trait`` can be specified, which restricts the type of elements
        in the container to that TraitType.

        If only one arg is given and it is not a Trait, it is taken as
        ``default_value``:

        ``c = List([1,2,3])``

        Parameters
        ----------

        trait : TraitType [ optional ]
            the type for restricting the contents of the Container.
            If unspecified, types are not checked.

        default_value : SequenceType [ optional ]
            The default value for the Trait.  Must be list/tuple/set, and
            will be cast to the container type.

        minlen : Int [ default 0 ]
            The minimum length of the input list

        maxlen : Int [ default sys.maxsize ]
            The maximum length of the input list
        """
        self._minlen = minlen
        self._maxlen = maxlen
        super(List, self).__init__(trait=trait, default_value=default_value,
                                **metadata)

    def length_error(self, obj, value):
        e = "The '%s' trait of %s instance must be of length %i <= L <= %i, but a value of %s was specified." \
            % (self.name, class_of(obj), self._minlen, self._maxlen, value)
        raise TraitError(e)

    def validate_elements(self, obj, value):
        length = len(value)
        if length < self._minlen or length > self._maxlen:
            self.length_error(obj, value)

        return super(List, self).validate_elements(obj, value)

    def validate(self, obj, value):
        value = super(List, self).validate(obj, value)
        value = self.validate_elements(obj, value)
        return value


class Set(List):
    """An instance of a Python set."""
    klass = set
    _cast_types = (tuple, list)

    # Redefine __init__ just to make the docstring more accurate.
    def __init__(self, trait=None, default_value=None, minlen=0, maxlen=sys.maxsize,
                 **metadata):
        """Create a Set trait type from a list, set, or tuple.

        The default value is created by doing ``set(default_value)``,
        which creates a copy of the ``default_value``.

        ``trait`` can be specified, which restricts the type of elements
        in the container to that TraitType.

        If only one arg is given and it is not a Trait, it is taken as
        ``default_value``:

        ``c = Set({1,2,3})``

        Parameters
        ----------

        trait : TraitType [ optional ]
            the type for restricting the contents of the Container.
            If unspecified, types are not checked.

        default_value : SequenceType [ optional ]
            The default value for the Trait.  Must be list/tuple/set, and
            will be cast to the container type.

        minlen : Int [ default 0 ]
            The minimum length of the input list

        maxlen : Int [ default sys.maxsize ]
            The maximum length of the input list
        """
        super(Set, self).__init__(trait, default_value, minlen, maxlen, **metadata)


class Tuple(Container):
    """An instance of a Python tuple."""
    klass = tuple
    _cast_types = (list,)

    def __init__(self, *traits, **metadata):
        """Create a tuple from a list, set, or tuple.

        Create a fixed-type tuple with Traits:

        ``t = Tuple(Int, Str, CStr)``

        would be length 3, with Int,Str,CStr for each element.

        If only one arg is given and it is not a Trait, it is taken as
        default_value:

        ``t = Tuple((1,2,3))``

        Otherwise, ``default_value`` *must* be specified by keyword.

        Parameters
        ----------

        `*traits` : TraitTypes [ optional ]
            the types for restricting the contents of the Tuple.  If unspecified,
            types are not checked. If specified, then each positional argument
            corresponds to an element of the tuple.  Tuples defined with traits
            are of fixed length.

        default_value : SequenceType [ optional ]
            The default value for the Tuple.  Must be list/tuple/set, and
            will be cast to a tuple. If `traits` are specified, the
            `default_value` must conform to the shape and type they specify.
        """
        default_value = metadata.pop('default_value', None)

        # allow Tuple((values,)):
        if len(traits) == 1 and default_value is None and not is_trait(traits[0]):
            default_value = traits[0]
            traits = ()

        if default_value is None:
            args = ()
        elif isinstance(default_value, self._valid_defaults):
            args = (default_value,)
        else:
            raise TypeError('default value of %s was %s' %(self.__class__.__name__, default_value))

        self._traits = []
        for trait in traits:
            t = trait() if isinstance(trait, type) else trait
            self._traits.append(t)

        if self._traits and default_value is None:
            # don't allow default to be an empty container if length is specified
            args = None
        super(Container,self).__init__(klass=self.klass, args=args, **metadata)

    def validate_elements(self, obj, value):
        if not self._traits:
            # nothing to validate
            return value
        if len(value) != len(self._traits):
            e = "The '%s' trait of %s instance requires %i elements, but a value of %s was specified." \
                % (self.name, class_of(obj), len(self._traits), repr_type(value))
            raise TraitError(e)

        validated = []
        for t, v in zip(self._traits, value):
            try:
                v = t._validate(obj, v)
            except TraitError:
                self.element_error(obj, v, t)
            else:
                validated.append(v)
        return tuple(validated)

    def instance_init(self, obj):
        for trait in self._traits:
            if isinstance(trait, TraitType):
                trait.this_class = self.this_class
                trait.instance_init(obj)
        super(Container, self).instance_init(obj)


class Dict(Instance):
    """An instance of a Python dict."""
    _trait = None

    def __init__(self, trait=None, traits=None, default_value=Undefined,
                 **metadata):
        """Create a dict trait type from a dict.

        The default value is created by doing ``dict(default_value)``,
        which creates a copy of the ``default_value``.

        trait : TraitType [ optional ]
            The type for restricting the contents of the Container. If
            unspecified, types are not checked.

        traits : Dictionary of trait types [optional]
            The type for restricting the content of the Dictionary for certain
            keys.

        default_value : SequenceType [ optional ]
            The default value for the Dict.  Must be dict, tuple, or None, and
            will be cast to a dict if not None. If `trait` is specified, the
            `default_value` must conform to the constraints it specifies.
        """
        # Handling positional arguments
        if default_value is Undefined and trait is not None:
            if not is_trait(trait):
                default_value = trait
                trait = None

        # Handling default value
        if default_value is Undefined:
            default_value = {}
        if default_value is None:
            args = None
        elif isinstance(default_value, dict):
            args = (default_value,)
        elif isinstance(default_value, SequenceTypes):
            args = (default_value,)
        else:
            raise TypeError('default value of Dict was %s' % default_value)

        # Case where a type of TraitType is provided rather than an instance
        if is_trait(trait):
            self._trait = trait() if isinstance(trait, type) else trait
        elif trait is not None:
            raise TypeError("`trait` must be a Trait or None, got %s" % repr_type(trait))

        self._traits = traits

        super(Dict, self).__init__(klass=dict, args=args, **metadata)

    def element_error(self, obj, element, validator):
        e = "Element of the '%s' trait of %s instance must be %s, but a value of %s was specified." \
            % (self.name, class_of(obj), validator.info(), repr_type(element))
        raise TraitError(e)

    def validate(self, obj, value):
        value = super(Dict, self).validate(obj, value)
        if value is None:
            return value
        value = self.validate_elements(obj, value)
        return value

    def validate_elements(self, obj, value):
        if self._traits is not None:
            for key in self._traits:
                if key not in value:
                    raise TraitError("Missing required '%s' key for the '%s' trait of %s instance"
                                     % (key, self.name, class_of(obj)))
        if self._traits is None and (self._trait is None or
                                     isinstance(self._trait, Any)):
            return value
        validated = {}
        for key in value:
            v = value[key]
            try:
                if self._traits is not None and key in self._traits:
                    v = self._traits[key]._validate(obj, v)
                else:
                    v = self._trait._validate(obj, v)
            except TraitError:
                self.element_error(obj, v, self._trait)
            else:
                validated[key] = v
        return self.klass(validated)

    def instance_init(self, obj):
        if isinstance(self._trait, TraitType):
            self._trait.this_class = self.this_class
            self._trait.instance_init(obj)
        if self._traits is not None:
            for trait in self._traits.values():
                trait.this_class = self.this_class
                trait.instance_init(obj)
        super(Dict, self).instance_init(obj)


class TCPAddress(TraitType):
    """A trait for an (ip, port) tuple.

    This allows for both IPv4 IP addresses as well as hostnames.
    """

    default_value = ('127.0.0.1', 0)
    info_text = 'an (ip, port) tuple'

    def validate(self, obj, value):
        if isinstance(value, tuple):
            if len(value) == 2:
                if isinstance(value[0], py3compat.string_types) and isinstance(value[1], int):
                    port = value[1]
                    if port >= 0 and port <= 65535:
                        return value
        self.error(obj, value)

class CRegExp(TraitType):
    """A casting compiled regular expression trait.

    Accepts both strings and compiled regular expressions. The resulting
    attribute will be a compiled regular expression."""

    info_text = 'a regular expression'

    def validate(self, obj, value):
        try:
            return re.compile(value)
        except:
            self.error(obj, value)
