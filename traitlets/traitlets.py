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
import collections
import os
import re
import sys
import types
import copy
import enum
import itertools
import spectate
from weakref import ref
from collections import defaultdict
try:
    from types import ClassType, InstanceType
    ClassTypes = (ClassType, type)
except:
    ClassTypes = (type,)
from warnings import warn, warn_explicit

import six

from .utils.getargspec import getargspec
from .utils.importstring import import_item
from .utils.sentinel import Sentinel
from .utils.bunch import Bunch
from .utils.descriptions import describe, class_of, add_article, repr_type

SequenceTypes = (list, tuple, set, frozenset)
MutableBuiltins = (list, set, dict)

# exports:

__all__ = [
    'default',
    'validate',
    'observe',
    'observe_compat',
    'link',
    'directional_link',
    'dlink',
    'Undefined',
    'All',
    'NoDefaultSpecified',
    'TraitError',
    'HasDescriptors',
    'HasTraits',
    'MetaHasDescriptors',
    'MetaHasTraits',
    'BaseDescriptor',
    'TraitType',
]

# any TraitType subclass (that doesn't start with _) will be added automatically

#-----------------------------------------------------------------------------
# Basic classes
#-----------------------------------------------------------------------------


Undefined = Sentinel('Undefined', 'traitlets',
'''
Used in Traitlets to specify that no defaults are set in kwargs
'''
)

All = Sentinel('All', 'traitlets',
'''
Used in Traitlets to listen to all types of notification or to notifications
from all trait attributes.
'''
)

# Deprecated alias
NoDefaultSpecified = Undefined

class TraitError(Exception):
    pass

#-----------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

from ipython_genutils.py3compat import cast_unicode_py2

_name_re = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")

def isidentifier(s):
    if six.PY2:
        return bool(_name_re.match(s))
    else:
        return s.isidentifier()

_deprecations_shown = set()
def _should_warn(key):
    """Add our own checks for too many deprecation warnings.

    Limit to once per package.
    """
    env_flag = os.environ.get('TRAITLETS_ALL_DEPRECATIONS')
    if env_flag and env_flag != '0':
        return True

    if key not in _deprecations_shown:
        _deprecations_shown.add(key)
        return True
    else:
        return False

def _deprecated_method(method, cls, method_name, msg):
    """Show deprecation warning about a magic method definition.

    Uses warn_explicit to bind warning to method definition instead of triggering code,
    which isn't relevant.
    """
    warn_msg = "{classname}.{method_name} is deprecated in traitlets 4.1: {msg}".format(
        classname=cls.__name__, method_name=method_name, msg=msg
    )

    for parent in inspect.getmro(cls):
        if method_name in parent.__dict__:
            cls = parent
            break
    # limit deprecation messages to once per package
    package_name = cls.__module__.split('.', 1)[0]
    key = (package_name, msg)
    if not _should_warn(key):
        return
    try:
        fname = inspect.getsourcefile(method) or "<unknown>"
        lineno = inspect.getsourcelines(method)[1] or 0
    except (IOError, TypeError) as e:
        # Failed to inspect for some reason
        warn(warn_msg + ('\n(inspection failed) %s' % e), DeprecationWarning)
    else:
        warn_explicit(warn_msg, DeprecationWarning, fname, lineno)


def is_trait(t):
    """ Returns whether the given value is an instance or subclass of TraitType.
    """
    return (isinstance(t, TraitType) or
            (isinstance(t, type) and issubclass(t, TraitType)))


def parse_notifier_name(names):
    """Convert the name argument to a list of names.

    Examples
    --------

    >>> parse_notifier_name([])
    [All]
    >>> parse_notifier_name('a')
    ['a']
    >>> parse_notifier_name(['a', 'b'])
    ['a', 'b']
    >>> parse_notifier_name(All)
    [All]
    """
    if names is All or isinstance(names, six.string_types):
        return [names]
    else:
        if not names or All in names:
            return [All]
        for n in names:
            if not isinstance(n, six.string_types):
                raise TypeError("names must be strings, not %r" % n)
        return names


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
    transform: iterable with two callables (optional)
        Data transformation between source and target and target and source.

    Examples
    --------

    >>> c = link((src, 'value'), (tgt, 'value'))
    >>> src.value = 5  # updates other objects as well
    """
    updating = False

    def __init__(self, source, target, transform=None):
        _validate_link(source, target)
        self.source, self.target = source, target
        self._transform, self._transform_inv = (
            transform if transform else (lambda x: x,) * 2)

        self.link()

    def link(self):
        try:
            setattr(self.target[0], self.target[1],
                    self._transform(getattr(self.source[0], self.source[1])))

        finally:
            self.source[0].observe(self._update_target, names=self.source[1])
            self.target[0].observe(self._update_source, names=self.target[1])

    @contextlib.contextmanager
    def _busy_updating(self):
        self.updating = True
        try:
            yield
        finally:
            self.updating = False

    def _update_target(self, change):
        if self.updating:
            return
        with self._busy_updating():
            setattr(self.target[0], self.target[1], self._transform(change.new))
            if getattr(self.source[0], self.source[1]) != change.new:
                raise TraitError(
                    "Broken link {}: the source value changed while updating "
                    "the target.".format(self))

    def _update_source(self, change):
        if self.updating:
            return
        with self._busy_updating():
            setattr(self.source[0], self.source[1],
                    self._transform_inv(change.new))
            if getattr(self.target[0], self.target[1]) != change.new:
                raise TraitError(
                    "Broken link {}: the target value changed while updating "
                    "the source.".format(self))

    def unlink(self):
        self.source[0].unobserve(self._update_target, names=self.source[1])
        self.target[0].unobserve(self._update_source, names=self.target[1])


class directional_link(object):
    """Link the trait of a source object with traits of target objects.

    Parameters
    ----------
    source : (object, attribute name) pair
    target : (object, attribute name) pair
    transform: callable (optional)
        Data transformation between source and target.

    Examples
    --------

    >>> c = directional_link((src, 'value'), (tgt, 'value'))
    >>> src.value = 5  # updates target objects
    >>> tgt.value = 6  # does not update source object
    """
    updating = False

    def __init__(self, source, target, transform=None):
        self._transform = transform if transform else lambda x: x
        _validate_link(source, target)
        self.source, self.target = source, target
        self.link()

    def link(self):
        try:
            setattr(self.target[0], self.target[1],
                    self._transform(getattr(self.source[0], self.source[1])))
        finally:
            self.source[0].observe(self._update, names=self.source[1])

    @contextlib.contextmanager
    def _busy_updating(self):
        self.updating = True
        try:
            yield
        finally:
            self.updating = False

    def _update(self, change):
        if self.updating:
            return
        with self._busy_updating():
            setattr(self.target[0], self.target[1],
                    self._transform(change.new))

    def unlink(self):
        self.source[0].unobserve(self._update, names=self.source[1])

dlink = directional_link


#-----------------------------------------------------------------------------
# Base Descriptor Class
#-----------------------------------------------------------------------------


class BaseDescriptor(object):
    """Base descriptor class
    Notes
    -----
    This implements Python's descriptor protocol.
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
    _parent = None

    @property
    def absolute_name(self):
        return list(self._lineage())[-1].name

    def class_init(self, cls, name, parent=None):
        """Part of the initialization which may depend on the underlying
        HasDescriptors class.
        It is typically overloaded for specific types.
        This method is called by :meth:`MetaHasDescriptors.__init__`
        passing the class (`cls`) and `name` under which the descriptor
        has been assigned.
        """
        self.this_class = cls
        self.name = name
        if parent is not None:
            self._parent = ref(parent)

    def subclass_init(self, cls):
        pass

    def instance_init(self, obj):
        """Part of the initialization which may depend on the underlying
        HasDescriptors instance.
        It is typically overloaded for specific types.
        This method is called by :meth:`HasTraits.__new__` and in the
        :meth:`BaseDescriptor.instance_init` method of descriptors holding
        other descriptors.
        """
        pass

    def _lineage(self):
        parent = self
        yield parent
        while parent._parent is not None:
            parent = parent._parent()
            yield parent

    def __str__(self):
        if self.this_class is not None:
            lineage = list(self._lineage())
            absolute_name = lineage[-1].name
            info = " ".join(map(lambda t: describe("the", t, "of"), lineage))
            info += " %s.%s" % (self.this_class.__name__, absolute_name)
        else:
            info = super(BaseDescriptor, self).__str__()
        return info


class TraitType(BaseDescriptor):
    """A base class for all trait types.
    """

    eventful = False
    metadata = {}
    allow_none = False
    read_only = False
    info_text = 'any value'
    default_value = Undefined

    def __init__(self, default_value=Undefined, allow_none=False, read_only=None, help=None,
        config=None, **kwargs):
        """Declare a traitlet.

        If *allow_none* is True, None is a valid value in addition to any
        values that are normally valid. The default is up to the subclass.
        For most trait types, the default value for ``allow_none`` is False.

        Extra metadata can be associated with the traitlet using the .tag() convenience method
        or by using the traitlet instance's .metadata dictionary.
        """
        if default_value is not Undefined:
            self.default_value = default_value
        if allow_none:
            self.allow_none = allow_none
        if read_only is not None:
            self.read_only = read_only
        self.help = help if help is not None else ''

        if len(kwargs) > 0:
            stacklevel = 1
            f = inspect.currentframe()
            # count supers to determine stacklevel for warning
            while f.f_code.co_name == '__init__':
                stacklevel += 1
                f = f.f_back
            mod = f.f_globals.get('__name__') or ''
            pkg = mod.split('.', 1)[0]
            key = tuple(['metadata-tag', pkg] + sorted(kwargs))
            if _should_warn(key):
                warn("metadata %s was set from the constructor. "
                     "With traitlets 4.1, metadata should be set using the .tag() method, "
                     "e.g., Int().tag(key1='value1', key2='value2')" % (kwargs,),
                     DeprecationWarning, stacklevel=stacklevel)
            if len(self.metadata) > 0:
                self.metadata = self.metadata.copy()
                self.metadata.update(kwargs)
            else:
                self.metadata = kwargs
        else:
            self.metadata = self.metadata.copy()
        if config is not None:
            self.metadata['config'] = config

        # We add help to the metadata during a deprecation period so that
        # code that looks for the help string there can find it.
        if help is not None:
            self.metadata['help'] = help

    def default(self, obj=None):
        """The default generator for this trait

        Notes
        -----
        This method is registered to HasTraits classes during ``class_init``
        in the same way that dynamic defaults defined by ``@default`` are.
        """
        if self.default_value is not Undefined:
            return self.default_value
        elif hasattr(self, 'make_dynamic_default'):
            return self.make_dynamic_default()
        else:
            # Undefined will raise in TraitType.get
            return Undefined

    def get_default_value(self):
        """DEPRECATED: Retrieve the static default value for this trait.

        Use self.default_value instead
        """
        warn("get_default_value is deprecated in traitlets 4.0: use the .default_value attribute", DeprecationWarning,
             stacklevel=2)
        return self.default_value

    def init_default_value(self, obj):
        """DEPRECATED: Set the static default value for the trait type.
        """
        warn("init_default_value is deprecated in traitlets 4.0, and may be removed in the future", DeprecationWarning,
             stacklevel=2)
        value = self._validate(obj, self.default_value)
        obj._trait_values[self.name] = value
        return value

    def get(self, obj, cls=None):
        try:
            value = obj._trait_values[self.name]
        except KeyError:
            # Check for a dynamic initializer.
            default = obj.trait_defaults(self.name)
            if default is Undefined:
                raise TraitError("No default value found for "
                    "the '%s' trait named '%s' of %r" % (
                    type(self).__name__, self.name, obj))
            with obj.cross_validation_lock:
                value = self._validate(obj, default)
            obj._trait_values[self.name] = value
            obj._notify_observers(Bunch(
                name=self.name,
                value=value,
                owner=obj,
                type='default',
            ))
            return value
        except Exception:
            # This should never be reached.
            raise TraitError('Unexpected error in TraitType: '
                             'default value not set properly')
        else:
            return value

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
            return self.get(obj, cls)

    def set(self, obj, value):
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

    def __set__(self, obj, value):
        """Set the value of the trait by self.name for the instance.

        Values pass through a validation stage where errors are raised when
        impropper types, or types that cannot be coerced, are encountered.
        """
        if self.read_only:
            raise TraitError('The "%s" trait is read-only.' % self.name)
        else:
            self.set(obj, value)

    def _validate(self, obj, value):
        if value is None and self.allow_none:
            return value
        if hasattr(self, 'validate'):
            value = self.validate(obj, value)
        if obj._cross_validation_lock is False:
            value = self._cross_validate(obj, value)
        return value

    def _cross_validate(self, obj, value):
        if self.name in obj._trait_validators:
            proposal = Bunch({'trait': self, 'value': value, 'owner': obj})
            value = obj._trait_validators[self.name](obj, proposal)
        elif hasattr(obj, '_%s_validate' % self.name):
            meth_name = '_%s_validate' % self.name
            cross_validate = getattr(obj, meth_name)
            _deprecated_method(cross_validate, obj.__class__, meth_name,
                "use @validate decorator instead.")
            value = cross_validate(value, self)
        return value

    def __or__(self, other):
        if isinstance(other, Union):
            return Union([self] + other.trait_types)
        else:
            return Union([self, other])

    def info(self):
        return self.info_text

    def error(self, obj, value, error=None, info=None):
        """Raise a TraitError

        Parameters
        ----------
        obj: HasTraits or None
            This is a legacy argument that is not used.
        value: any
            The value that caused the error.
        error: Exception (default: None)
            An error that was caused by the value.
        info: str (default: None)
            The reason value caused an error.
        """
        if error is not None:
            if isinstance(error, TraitError):
                raise
            else:
                msg = (
                    "{value} caused {error} in "
                    "{trait} because {info}."
                ).format(
                    trait=self,
                    info=info or error,
                    value=describe("the", value),
                    error=describe("a", type(error)),
                )
        else:
            if info is None:
                info = self.info()
                msg = "{trait} expeted {info}, not {value}."
            else:
                msg = "{value} caused an error in {trait} because {info}."
            msg = msg.format(trait=self, value=describe("the", value), info=info)
        raise TraitError(msg)

    def get_metadata(self, key, default=None):
        """DEPRECATED: Get a metadata value.

        Use .metadata[key] or .metadata.get(key, default) instead.
        """
        if key == 'help':
            msg = "use the instance .help string directly, like x.help"
        else:
            msg = "use the instance .metadata dictionary directly, like x.metadata[key] or x.metadata.get(key, default)"
        warn("Deprecated in traitlets 4.1, " + msg, DeprecationWarning, stacklevel=2)
        return self.metadata.get(key, default)

    def set_metadata(self, key, value):
        """DEPRECATED: Set a metadata key/value.

        Use .metadata[key] = value instead.
        """
        if key == 'help':
            msg = "use the instance .help string directly, like x.help = value"
        else:
            msg = "use the instance .metadata dictionary directly, like x.metadata[key] = value"
        warn("Deprecated in traitlets 4.1, " + msg, DeprecationWarning, stacklevel=2)
        self.metadata[key] = value

    def tag(self, **metadata):
        """Sets metadata and returns self.

        This allows convenient metadata tagging when initializing the trait, such as:

        >>> Int(0).tag(config=True, sync=True)
        """
        maybe_constructor_keywords = set(metadata.keys()).intersection({'help','allow_none', 'read_only', 'default_value'})
        if maybe_constructor_keywords:
            warn('The following attributes are set in using `tag`, but seem to be constructor keywords arguments: %s '%
                    maybe_constructor_keywords, UserWarning, stacklevel=2)

        self.metadata.update(metadata)
        return self

    def default_value_repr(self):
        return repr(self.default())

#-----------------------------------------------------------------------------
# The HasTraits implementation
#-----------------------------------------------------------------------------

class _CallbackWrapper(object):
    """An object adapting a on_trait_change callback into an observe callback.

    The comparison operator __eq__ is implemented to enable removal of wrapped
    callbacks.
    """

    def __init__(self, cb):
        self.cb = cb
        # Bound methods have an additional 'self' argument.
        offset = -1 if isinstance(self.cb, types.MethodType) else 0
        self.nargs = len(getargspec(cb)[0]) + offset
        if (self.nargs > 4):
            raise TraitError('a trait changed callback must have 0-4 arguments.')

    def __eq__(self, other):
        # The wrapper is equal to the wrapped element
        if isinstance(other, _CallbackWrapper):
            return self.cb == other.cb
        else:
            return self.cb == other

    def __call__(self, change):
        # The wrapper is callable
        if self.nargs == 0:
            self.cb()
        elif self.nargs == 1:
            self.cb(change.name)
        elif self.nargs == 2:
            self.cb(change.name, change.new)
        elif self.nargs == 3:
            self.cb(change.name, change.old, change.new)
        elif self.nargs == 4:
            self.cb(change.name, change.old, change.new, change.owner)

def _callback_wrapper(cb):
    if isinstance(cb, _CallbackWrapper):
        return cb
    else:
        return _CallbackWrapper(cb)


class MetaHasDescriptors(type):
    """A metaclass for HasDescriptors.

    This metaclass makes sure that any TraitType class attributes are
    instantiated and sets their name attribute.
    """

    def __new__(mcls, name, bases, classdict):
        """Create the HasDescriptors class."""
        for k, v in classdict.items():
            # ----------------------------------------------------------------
            # Support of deprecated behavior allowing for TraitType types
            # to be used instead of TraitType instances.
            if inspect.isclass(v) and issubclass(v, TraitType):
                warn("Traits should be given as instances, not types (for example, `Int()`, not `Int`)."
                     " Passing types is deprecated in traitlets 4.1.",
                     DeprecationWarning, stacklevel=2)
                classdict[k] = v()
            # ----------------------------------------------------------------

        return super(MetaHasDescriptors, mcls).__new__(mcls, name, bases, classdict)

    def __init__(cls, name, bases, classdict):
        """Finish initializing the HasDescriptors class."""
        super(MetaHasDescriptors, cls).__init__(name, bases, classdict)
        cls.setup_class(classdict)

    def setup_class(cls, classdict):
        """Setup descriptor instance on the class

        This sets the :attr:`this_class` and :attr:`name` attributes of each
        BaseDescriptor in the class dict of the newly created ``cls`` before
        calling their :attr:`class_init` method.
        """
        for k, v in classdict.items():
            if isinstance(v, BaseDescriptor):
                v.class_init(cls, k)

        for k, v in getmembers(cls):
            if isinstance(v, BaseDescriptor):
                v.subclass_init(cls)


class MetaHasTraits(MetaHasDescriptors):
    """A metaclass for HasTraits."""

    def setup_class(cls, classdict):
        cls._trait_default_generators = {}
        super(MetaHasTraits, cls).setup_class(classdict)




def observe(*names, **kwargs):
    """A decorator which can be used to observe Traits on a class.

    The handler passed to the decorator will be called with one ``change``
    dict argument. The change dictionary at least holds a 'type' key and a
    'name' key, corresponding respectively to the type of notification and the
    name of the attribute that triggered the notification.

    Other keys may be passed depending on the value of 'type'. In the case
    where type is 'change', we also have the following keys:
    * ``owner`` : the HasTraits instance
    * ``old`` : the old value of the modified trait attribute
    * ``new`` : the new value of the modified trait attribute
    * ``name`` : the name of the modified trait attribute.

    Parameters
    ----------
    *names
        The str names of the Traits to observe on the object.
    type: str, kwarg-only
        The type of event to observe (e.g. 'change')
    """
    if not names:
        raise TypeError("Please specify at least one trait name to observe.")
    for name in names:
        if name is not All and not isinstance(name, six.string_types):
            raise TypeError("trait names to observe must be strings or All, not %r" % name)
    return ObserveHandler(names, type=kwargs.get('type', 'change'))


def observe_compat(func):
    """Backward-compatibility shim decorator for observers

    Use with:

    @observe('name')
    @observe_compat
    def _foo_changed(self, change):
        ...

    With this, `super()._foo_changed(self, name, old, new)` in subclasses will still work.
    Allows adoption of new observer API without breaking subclasses that override and super.
    """
    def compatible_observer(self, change_or_name, old=Undefined, new=Undefined):
        if isinstance(change_or_name, dict):
            change = change_or_name
        else:
            clsname = self.__class__.__name__
            warn("A parent of %s._%s_changed has adopted the new (traitlets 4.1) @observe(change) API" % (
                clsname, change_or_name), DeprecationWarning)
            change = Bunch(
                type='change',
                old=old,
                new=new,
                name=change_or_name,
                owner=self,
            )
        return func(self, change)
    return compatible_observer


def validate(*names):
    """A decorator to register cross validator of HasTraits object's state
    when a Trait is set.

    The handler passed to the decorator must have one ``proposal`` dict argument.
    The proposal dictionary must hold the following keys:
    * ``owner`` : the HasTraits instance
    * ``value`` : the proposed value for the modified trait attribute
    * ``trait`` : the TraitType instance associated with the attribute

    Parameters
    ----------
    names
        The str names of the Traits to validate.

    Notes
    -----
    Since the owner has access to the ``HasTraits`` instance via the 'owner' key,
    the registered cross validator could potentially make changes to attributes
    of the ``HasTraits`` instance. However, we recommend not to do so. The reason
    is that the cross-validation of attributes may run in arbitrary order when
    exiting the ``hold_trait_notifications`` context, and such changes may not
    commute.
    """
    if not names:
        raise TypeError("Please specify at least one trait name to validate.")
    for name in names:
        if name is not All and not isinstance(name, six.string_types):
            raise TypeError("trait names to validate must be strings or All, not %r" % name)
    return ValidateHandler(names)


def default(name):
    """A decorator which assigns a dynamic default for a Trait on a HasTraits object.

    Parameters
    ----------
    name
        The str name of the Trait on the object whose default should be generated.

    Notes
    -----
    Unlike observers and validators which are properties of the HasTraits
    instance, default value generators are class-level properties.

    Besides, default generators are only invoked if they are registered in
    subclasses of `this_type`.

    ::

        class A(HasTraits):
            bar = Int()

            @default('bar')
            def get_bar_default(self):
                return 11


        class B(A):
            bar = Float()  # This trait ignores the default generator defined in
                           # the base class A


        class C(B):

            @default('bar')
            def some_other_default(self):  # This default generator should not be
                return 3.0                 # ignored since it is defined in a
                                           # class derived from B.a.this_class.
    """
    if not isinstance(name, six.string_types):
        raise TypeError("Trait name must be a string or All, not %r" % name)
    return DefaultHandler(name)


class EventHandler(BaseDescriptor):

    def _init_call(self, func):
        self.func = func
        return self

    def __call__(self, *args, **kwargs):
        """Pass `*args` and `**kwargs` to the handler's function if it exists."""
        if hasattr(self, 'func'):
            return self.func(*args, **kwargs)
        else:
            return self._init_call(*args, **kwargs)

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        return types.MethodType(self.func, inst)


class ObserveHandler(EventHandler):

    def __init__(self, names, type):
        self.trait_names = names
        self.type = type

    def instance_init(self, inst):
        inst.observe(self, self.trait_names, type=self.type)


class ValidateHandler(EventHandler):

    def __init__(self, names):
        self.trait_names = names

    def instance_init(self, inst):
        inst._register_validator(self, self.trait_names)


class DefaultHandler(EventHandler):

    def __init__(self, name):
        self.trait_name = name

    def class_init(self, cls, name, parent=None):
        super(DefaultHandler, self).class_init(cls, name, parent)
        cls._trait_default_generators[self.trait_name] = self


class HasDescriptors(six.with_metaclass(MetaHasDescriptors, object)):
    """The base class for all classes that have descriptors.
    """

    def __new__(*args, **kwargs):
        # Pass cls as args[0] to allow "cls" as keyword argument
        cls = args[0]
        args = args[1:]

        # This is needed because object.__new__ only accepts
        # the cls argument.
        new_meth = super(HasDescriptors, cls).__new__
        if new_meth is object.__new__:
            inst = new_meth(cls)
        else:
            inst = new_meth(cls, *args, **kwargs)
        inst.setup_instance(*args, **kwargs)
        return inst

    def setup_instance(*args, **kwargs):
        """
        This is called **before** self.__init__ is called.
        """
        # Pass self as args[0] to allow "self" as keyword argument
        self = args[0]
        args = args[1:]

        self._cross_validation_lock = False
        cls = self.__class__
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
                    value.instance_init(self)


class HasTraits(six.with_metaclass(MetaHasTraits, HasDescriptors)):

    def setup_instance(*args, **kwargs):
        # Pass self as args[0] to allow "self" as keyword argument
        self = args[0]
        args = args[1:]

        self._trait_values = {}
        self._trait_notifiers = {}
        self._trait_validators = {}
        super(HasTraits, self).setup_instance(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        # Allow trait values to be set using keyword arguments.
        # We need to use setattr for this to trigger validation and
        # notifications.
        super_args = args
        super_kwargs = {}
        with self.hold_trait_notifications():
            for key, value in kwargs.items():
                if self.has_trait(key):
                    setattr(self, key, value)
                else:
                    # passthrough args that don't set traits to super
                    super_kwargs[key] = value
        try:
            super(HasTraits, self).__init__(*super_args, **super_kwargs)
        except TypeError as e:
            arg_s_list = [ repr(arg) for arg in super_args ]
            for k, v in super_kwargs.items():
                arg_s_list.append("%s=%r" % (k, v))
            arg_s = ', '.join(arg_s_list)
            warn(
                "Passing unrecoginized arguments to super({classname}).__init__({arg_s}).\n"
                "{error}\n"
                "This is deprecated in traitlets 4.2."
                "This error will be raised in a future release of traitlets."
                .format(
                    arg_s=arg_s, classname=self.__class__.__name__,
                    error=e,
                ),
                DeprecationWarning,
                stacklevel=2,
            )

    def __getstate__(self):
        d = self.__dict__.copy()
        # event handlers stored on an instance are
        # expected to be reinstantiated during a
        # recall of instance_init during __setstate__
        d['_trait_notifiers'] = {}
        d['_trait_validators'] = {}
        return d

    def __setstate__(self, state):
        self.__dict__ = state.copy()

        # event handlers are reassigned to self
        cls = self.__class__
        for key in dir(cls):
            # Some descriptors raise AttributeError like zope.interface's
            # __provides__ attributes even though they exist.  This causes
            # AttributeErrors even though they are listed in dir(cls).
            try:
                value = getattr(cls, key)
            except AttributeError:
                pass
            else:
                if isinstance(value, EventHandler):
                    value.instance_init(self)

    @property
    @contextlib.contextmanager
    def cross_validation_lock(self):
        """
        A contextmanager for running a block with our cross validation lock set
        to True.

        At the end of the block, the lock's value is restored to its value
        prior to entering the block.
        """
        if self._cross_validation_lock:
            yield
            return
        else:
            try:
                self._cross_validation_lock = True
                yield
            finally:
                self._cross_validation_lock = False

    @contextlib.contextmanager
    def hold_trait_notifications(self):
        """Context manager for bundling trait change notifications and cross
        validation.

        Use this when doing multiple trait assignments (init, config), to avoid
        race conditions in trait notifiers requesting other trait values.
        All trait notifications will fire after all values have been assigned.
        """
        if self._cross_validation_lock:
            yield
            return
        else:
            cache = {}
            notify_change = self.notify_change

            def compress(past_changes, change):
                """Merges the provided change with the last if possible."""
                if past_changes is None:
                    return [change]
                else:
                    if past_changes[-1]['type'] == 'change' and change.type == 'change':
                        past_changes[-1]['new'] = change.new
                    elif past_changes[-1]['type'] == 'mutation' and change.type == 'mutation':
                        past_changes[-1].events.extend(change.events)
                    else:
                        # In case of changes other than 'change', append the notification.
                        past_changes.append(change)
                    return past_changes

            def hold(change):
                name = change.name
                cache[name] = compress(cache.get(name), change)

            try:
                # Replace notify_change with `hold`, caching and compressing
                # notifications, disable cross validation and yield.
                self.notify_change = hold
                self._cross_validation_lock = True
                yield
                # Cross validate final values when context is released.
                for name in list(cache.keys()):
                    trait = getattr(self.__class__, name)
                    value = trait._cross_validate(self, getattr(self, name))
                    self.set_trait(name, value)
            except TraitError as e:
                # Roll back in case of TraitError during final cross validation.
                self.notify_change = lambda x: None
                for name, changes in cache.items():
                    for change in changes[::-1]:
                        # TODO: Separate in a rollback function per notification type.
                        if change.type == 'change':
                            if change.old is not Undefined:
                                self.set_trait(name, change.old)
                            else:
                                self._trait_values.pop(name)
                cache = {}
                raise e
            finally:
                self._cross_validation_lock = False
                # Restore method retrieval from class
                del self.notify_change

                # trigger delayed notifications
                for changes in cache.values():
                    for change in changes:
                        self.notify_change(change)

    def _notify_trait(self, name, old_value, new_value):
        self.notify_change(Bunch(
            name=name,
            old=old_value,
            new=new_value,
            owner=self,
            type='change',
        ))

    def notify_change(self, change):
        """Notify observers of a change event"""
        return self._notify_observers(change)

    def _notify_observers(self, event):
        """Notify observers of any event"""
        if not isinstance(event, Bunch):
            # cast to bunch if given a dict
            event = Bunch(event)
        name, type = event.name, event.type

        callables = []
        callables.extend(self._trait_notifiers.get(name, {}).get(type, []))
        callables.extend(self._trait_notifiers.get(name, {}).get(All, []))
        callables.extend(self._trait_notifiers.get(All, {}).get(type, []))
        callables.extend(self._trait_notifiers.get(All, {}).get(All, []))

        # Now static ones
        magic_name = '_%s_changed' % name
        if event.type == "change" and hasattr(self, magic_name):
            class_value = getattr(self.__class__, magic_name)
            if not isinstance(class_value, ObserveHandler):
                _deprecated_method(class_value, self.__class__, magic_name,
                    "use @observe and @unobserve instead.")
                cb = getattr(self, magic_name)
                # Only append the magic method if it was not manually registered
                if cb not in callables:
                    callables.append(_callback_wrapper(cb))

        # Call them all now
        # Traits catches and logs errors here.  I allow them to raise
        for c in callables:
            # Bound methods have an additional 'self' argument.

            if isinstance(c, _CallbackWrapper):
                c = c.__call__
            elif isinstance(c, EventHandler) and c.name is not None:
                c = getattr(self, c.name)

            c(event)

    def _add_notifiers(self, handler, name, type):
        if name not in self._trait_notifiers:
            nlist = []
            self._trait_notifiers[name] = {type: nlist}
        else:
            if type not in self._trait_notifiers[name]:
                nlist = []
                self._trait_notifiers[name][type] = nlist
            else:
                nlist = self._trait_notifiers[name][type]
        if handler not in nlist:
            nlist.append(handler)

    def _remove_notifiers(self, handler, name, type):
        try:
            if handler is None:
                del self._trait_notifiers[name][type]
            else:
                self._trait_notifiers[name][type].remove(handler)
        except KeyError:
            pass

    def on_trait_change(self, handler=None, name=None, remove=False):
        """DEPRECATED: Setup a handler to be called when a trait changes.

        This is used to setup dynamic notifications of trait changes.

        Static handlers can be created by creating methods on a HasTraits
        subclass with the naming convention '_[traitname]_changed'.  Thus,
        to create static handler for the trait 'a', create the method
        _a_changed(self, name, old, new) (fewer arguments can be used, see
        below).

        If `remove` is True and `handler` is not specified, all change
        handlers for the specified name are uninstalled.

        Parameters
        ----------
        handler : callable, None
            A callable that is called when a trait changes.  Its
            signature can be handler(), handler(name), handler(name, new),
            handler(name, old, new), or handler(name, old, new, self).
        name : list, str, None
            If None, the handler will apply to all traits.  If a list
            of str, handler will apply to all names in the list.  If a
            str, the handler will apply just to that name.
        remove : bool
            If False (the default), then install the handler.  If True
            then unintall it.
        """
        warn("on_trait_change is deprecated in traitlets 4.1: use observe instead",
             DeprecationWarning, stacklevel=2)
        if name is None:
            name = All
        if remove:
            self.unobserve(_callback_wrapper(handler), names=name)
        else:
            self.observe(_callback_wrapper(handler), names=name)

    def observe(self, handler, names=All, type='change'):
        """Setup a handler to be called when a trait changes.

        This is used to setup dynamic notifications of trait changes.

        Parameters
        ----------
        handler : callable
            A callable that is called when a trait changes. Its
            signature should be ``handler(change)``, where ``change`` is a
            dictionary. The change dictionary at least holds a 'type' key.
            * ``type``: the type of notification.
            Other keys may be passed depending on the value of 'type'. In the
            case where type is 'change', we also have the following keys:
            * ``owner`` : the HasTraits instance
            * ``old`` : the old value of the modified trait attribute
            * ``new`` : the new value of the modified trait attribute
            * ``name`` : the name of the modified trait attribute.
        names : list, str, All
            If names is All, the handler will apply to all traits.  If a list
            of str, handler will apply to all names in the list.  If a
            str, the handler will apply just to that name.
        type : str, All (default: 'change')
            The type of notification to filter by. If equal to All, then all
            notifications are passed to the observe handler.
        """
        names = parse_notifier_name(names)
        for n in names:
            self._add_notifiers(handler, n, type)

    def unobserve(self, handler, names=All, type='change'):
        """Remove a trait change handler.

        This is used to unregister handlers to trait change notifications.

        Parameters
        ----------
        handler : callable
            The callable called when a trait attribute changes.
        names : list, str, All (default: All)
            The names of the traits for which the specified handler should be
            uninstalled. If names is All, the specified handler is uninstalled
            from the list of notifiers corresponding to all changes.
        type : str or All (default: 'change')
            The type of notification to filter by. If All, the specified handler
            is uninstalled from the list of notifiers corresponding to all types.
        """
        names = parse_notifier_name(names)
        for n in names:
            self._remove_notifiers(handler, n, type)

    def unobserve_all(self, name=All):
        """Remove trait change handlers of any type for the specified name.
        If name is not specified, removes all trait notifiers."""
        if name is All:
            self._trait_notifiers = {}
        else:
            try:
                del self._trait_notifiers[name]
            except KeyError:
                pass

    def _register_validator(self, handler, names):
        """Setup a handler to be called when a trait should be cross validated.

        This is used to setup dynamic notifications for cross-validation.

        If a validator is already registered for any of the provided names, a
        TraitError is raised and no new validator is registered.

        Parameters
        ----------
        handler : callable
            A callable that is called when the given trait is cross-validated.
            Its signature is handler(proposal), where proposal is a Bunch (dictionary with attribute access)
            with the following attributes/keys:
                * ``owner`` : the HasTraits instance
                * ``value`` : the proposed value for the modified trait attribute
                * ``trait`` : the TraitType instance associated with the attribute
        names : List of strings
            The names of the traits that should be cross-validated
        """
        for name in names:
            magic_name = '_%s_validate' % name
            if hasattr(self, magic_name):
                class_value = getattr(self.__class__, magic_name)
                if not isinstance(class_value, ValidateHandler):
                    _deprecated_method(class_value, self.__class__, magic_name,
                        "use @validate decorator instead.")
        for name in names:
            self._trait_validators[name] = handler

    def add_traits(self, **traits):
        """Dynamically add trait attributes to the HasTraits instance."""
        self.__class__ = type(self.__class__.__name__, (self.__class__,),
                              traits)
        for trait in traits.values():
            trait.instance_init(self)

    def set_trait(self, name, value):
        """Forcibly sets trait attribute, including read-only attributes."""
        cls = self.__class__
        if not self.has_trait(name):
            raise TraitError("Class %s does not have a trait named %s" %
                                (cls.__name__, name))
        else:
            getattr(cls, name).set(self, value)

    @classmethod
    def class_trait_names(cls, **metadata):
        """Get a list of all the names of this class' traits.

        This method is just like the :meth:`trait_names` method,
        but is unbound.
        """
        return list(cls.class_traits(**metadata))

    @classmethod
    def class_traits(cls, **metadata):
        """Get a ``dict`` of all the traits of this class.  The dictionary
        is keyed on the name and the values are the TraitType objects.

        This method is just like the :meth:`traits` method, but is unbound.

        The TraitTypes returned don't know anything about the values
        that the various HasTrait's instances are holding.

        The metadata kwargs allow functions to be passed in which
        filter traits based on metadata values.  The functions should
        take a single value as an argument and return a boolean.  If
        any function returns False, then the trait is not included in
        the output.  If a metadata key doesn't exist, None will be passed
        to the function.
        """
        traits = dict([memb for memb in getmembers(cls) if
                     isinstance(memb[1], TraitType)])

        if len(metadata) == 0:
            return traits

        result = {}
        for name, trait in traits.items():
            for meta_name, meta_eval in metadata.items():
                if not callable(meta_eval):
                    meta_eval = _SimpleTest(meta_eval)
                if not meta_eval(trait.metadata.get(meta_name, None)):
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

    def trait_has_value(self, name):
        """Returns True if the specified trait has a value.

        This will return false even if ``getattr`` would return a
        dynamically generated default value. These default values
        will be recognized as existing only after they have been
        generated.

        Example

        .. code-block:: python
            class MyClass(HasTraits):
                i = Int()

            mc = MyClass()
            assert not mc.trait_has_value("i")
            mc.i # generates a default value
            assert mc.trait_has_value("i")
        """
        return name in self._trait_values

    def trait_values(self, **metadata):
        """A ``dict`` of trait names and their values.

        The metadata kwargs allow functions to be passed in which
        filter traits based on metadata values.  The functions should
        take a single value as an argument and return a boolean.  If
        any function returns False, then the trait is not included in
        the output.  If a metadata key doesn't exist, None will be passed
        to the function.

        Returns
        -------
        A ``dict`` of trait names and their values.

        Notes
        -----
        Trait values are retrieved via ``getattr``, any exceptions raised
        by traits or the operations they may trigger will result in the
        absence of a trait value in the result ``dict``.
        """
        return {name: getattr(self, name) for name in self.trait_names(**metadata)}

    def _get_trait_default_generator(self, name):
        """Return default generator for a given trait

        Walk the MRO to resolve the correct default generator according to inheritance.
        """
        method_name = '_%s_default' % name
        if method_name in self.__dict__:
            return getattr(self, method_name)
        cls = self.__class__
        trait = getattr(cls, name)
        assert isinstance(trait, TraitType)
        # truncate mro to the class on which the trait is defined
        mro = cls.mro()
        try:
            mro = mro[:mro.index(trait.this_class) + 1]
        except ValueError:
            # this_class not in mro
            pass
        for c in mro:
            if method_name in c.__dict__:
                return getattr(c, method_name)
            if name in c.__dict__.get('_trait_default_generators', {}):
                return c._trait_default_generators[name]
        return trait.default

    def trait_defaults(self, *names, **metadata):
        """Return a trait's default value or a dictionary of them

        Notes
        -----
        Dynamically generated default values may
        depend on the current state of the object."""
        for n in names:
            if not self.has_trait(n):
                raise TraitError("'%s' is not a trait of '%s' "
                    "instances" % (n, type(self).__name__))

        if len(names) == 1 and len(metadata) == 0:
            return self._get_trait_default_generator(names[0])(self)

        trait_names = self.trait_names(**metadata)
        trait_names.extend(names)

        defaults = {}
        for n in trait_names:
            defaults[n] = self._get_trait_default_generator(n)(self)
        return defaults

    def trait_names(self, **metadata):
        """Get a list of all the names of this class' traits."""
        return list(self.traits(**metadata))

    def traits(self, **metadata):
        """Get a ``dict`` of all the traits of this class.  The dictionary
        is keyed on the name and the values are the TraitType objects.

        The TraitTypes returned don't know anything about the values
        that the various HasTrait's instances are holding.

        The metadata kwargs allow functions to be passed in which
        filter traits based on metadata values.  The functions should
        take a single value as an argument and return a boolean.  If
        any function returns False, then the trait is not included in
        the output.  If a metadata key doesn't exist, None will be passed
        to the function.
        """
        traits = dict([memb for memb in getmembers(self.__class__) if
                     isinstance(memb[1], TraitType)])

        if len(metadata) == 0:
            return traits

        result = {}
        for name, trait in traits.items():
            for meta_name, meta_eval in metadata.items():
                if not callable(meta_eval):
                    meta_eval = _SimpleTest(meta_eval)
                if not meta_eval(trait.metadata.get(meta_name, None)):
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
        metadata_name = '_' + traitname + '_metadata'
        if hasattr(self, metadata_name) and key in getattr(self, metadata_name):
            return getattr(self, metadata_name).get(key, default)
        else:
            return trait.metadata.get(key, default)

    @classmethod
    def class_own_trait_events(cls, name):
        """Get a dict of all event handlers defined on this class, not a parent.

        Works like ``event_handlers``, except for excluding traits from parents.
        """
        sup = super(cls, cls)
        return {n: e for (n, e) in cls.events(name).items()
                if getattr(sup, n, None) is not e}

    @classmethod
    def trait_events(cls, name=None):
        """Get a ``dict`` of all the event handlers of this class.

        Parameters
        ----------
        name: str (default: None)
            The name of a trait of this class. If name is ``None`` then all
            the event handlers of this class will be returned instead.

        Returns
        -------
        The event handlers associated with a trait name, or all event handlers.
        """
        events = {}
        for k, v in getmembers(cls):
            if isinstance(v, EventHandler):
                if name is None:
                    events[k] = v
                elif name in v.trait_names:
                    events[k] = v
                elif hasattr(v, 'tags'):
                    if cls.trait_names(**v.tags):
                        events[k] = v
        return events

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


class Type(ClassBasedTraitType):
    """A trait whose value must be a subclass of a specified class."""

    def __init__ (self, default_value=Undefined, klass=None, **kwargs):
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

        if not (inspect.isclass(klass) or isinstance(klass, six.string_types)):
            raise TraitError("A Type trait must specify a class.")

        self.klass = klass

        super(Type, self).__init__(new_default_value, **kwargs)

    def validate(self, obj, value):
        """Validates that the value is a valid object instance."""
        if isinstance(value, six.string_types):
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
        if isinstance(self.klass, six.string_types):
            klass = self.klass
        else:
            klass = self.klass.__module__ + '.' + self.klass.__name__
        result = "a subclass of '%s'" % klass
        if self.allow_none:
            return result + ' (or None)'
        return result

    def instance_init(self, obj):
        self._resolve_classes()
        super(Type, self).instance_init(obj)

    def _resolve_classes(self):
        if isinstance(self.klass, six.string_types):
            self.klass = self._resolve_string(self.klass)
        if isinstance(self.default_value, six.string_types):
            self.default_value = self._resolve_string(self.default_value)

    def default_value_repr(self):
        value = self.default()
        if isinstance(value, six.string_types):
            return repr(value)
        else:
            return repr('{}.{}'.format(value.__module__, value.__name__))


class Instance(ClassBasedTraitType):
    """A trait whose value must be an instance of a specified class.

    The value can also be an instance of a subclass of the specified class.

    Subclasses can declare default classes by overriding the klass attribute
    """

    klass = None
    info_text = None
    _cast_types = ()

    def __init__(self, *args, **kwargs):
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
        castable : type or tuple of types
            The classes which are allowed to be cast to ``klass``.
            Similar rules for specifying classes with strings
            (e.g. 'foo.bar.Bar') apply. If given as None, then
            only instances of ``klass`` are allowed.
        allow_none : bool [ default False ]
            Indicates whether None is allowed as a value.

        Notes
        -----
        If both ``args`` and ``kw`` are None, then the default value is None.
        If ``args`` is a tuple and ``kw`` is a dict, then the default is
        created as ``klass(*args, **kw)``.  If exactly one of ``args`` or ``kw`` is
        None, the None is replaced by ``()`` or ``{}``, respectively.
        """
        self._cast_types = kwargs.pop("castable", self._cast_types)
        if not isinstance(self._cast_types, tuple):
            self._cast_types = (self._cast_types,)
        if self.klass is None:
            klass, ar, kw = args + (
                kwargs.pop("klass", None),
                kwargs.pop("args", None),
                kwargs.pop("kw", None)
            )[len(args):]
            args = args[3:]
            if klass is None:
                raise TraitError("No class was given")
            elif not (inspect.isclass(klass) or isinstance(klass, six.string_types)):
                raise TraitError("Expected a class or import string, not %r" % klass)
            if (kw is not None) and not isinstance(kw, dict):
                raise TraitError("The 'kw' argument must be a dict or None.")
            if (ar is not None) and not isinstance(ar, tuple):
                raise TraitError("The 'args' argument must be a tuple or None.")
            self.klass = klass
            self.default_args = ar
            self.default_kwargs = kw
        else:
            self.default_args = None
            self.default_kwargs = None
        super(Instance, self).__init__(*args, **kwargs)
        # validate a static default value if one was given
        # and attempt to coerce it if that's needed.
        default = self.default_value
        if Undefined not in (default, self.klass):
            if not (self.allow_none and default is None):
                if not isinstance(default, self.klass):
                    if self.castable(default):
                        self.default_value = self.cast(default)
                    if not isinstance(self.default_value, self.klass):
                        self.error(None, self.default_value)

    def validate(self, obj, value):
        if self.castable(value):
            try:
                value = self.cast(value)
            except:
                raise self.cast_error(value)
        if isinstance(value, self.klass):
            return value
        else:
            self.error(obj, value)

    def cast(self, value):
        """Return a value that will pass validation.

        This is only triggered if the value in question is :meth:`castable`.
        """
        return self.klass(value)

    def castable(self, value):
        """Returns a boolean indicating whether or not a value can be cast."""
        return isinstance(value, self._cast_types)

    def cast_error(self, value, error=None):
        error = error or sys.exc_info()[1]
        if error is None:
            raise TraitError("%s failed to cast %s to %s." % (
                self, describe("the", value), describe("a", self.klass)))
        else:
            raise TraitError("%s failed to cast %s to %s because: %s" % (
                self, describe("the", value), describe("a", self.klass), error))

    def info(self):
        if self.info_text:
            return self.info_text
        result = describe("a", self.klass)
        cast_info = self._cast_info()
        if cast_info is not None:
            if self.allow_none:
                result += " (or None, or %s)" % cast_info
            else:
                result += " (or %s)" % cast_info
        elif self.allow_none:
            result += " (or None)"
        return result

    def _cast_info(self):
        if len(self._cast_types):
            castables = [
                describe("a", c)
                for c in self._cast_types
            ]
            if len(castables) > 1:
                the_types = (', '.join(castables[:-1])
                    + ', or %s' % castables[-1])
            else:
                the_types = castables[0]
            return the_types

    def instance_init(self, obj):
        self._resolve_classes()
        super(Instance, self).instance_init(obj)

    def _resolve_classes(self):
        if isinstance(self.klass, six.string_types):
            self.klass = self._resolve_string(self.klass)
        self._cast_types = tuple(
            self._resolve_string(c) if
            isinstance(c, six.string_types)
            else c for c in self._cast_types)

    def make_dynamic_default(self):
        if (self.default_args, self.default_kwargs) != (None, None):
            a = self.default_args or ()
            kw = self.default_kwargs or {}
            return self.klass(*a, **kw)
        elif not self.allow_none:
            return Undefined

    def default_value_repr(self):
        if self.default_value is not Undefined:
            val = self.default_value
        else:
            val = self.make_dynamic_default()
        return repr(val)


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

    def __init__(self, **kwargs):
        super(This, self).__init__(None, **kwargs)

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

    def __init__(self, trait_types, **kwargs):
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
        self.trait_types = list(trait_types)
        self.info_text = " or ".join([tt.info() for tt in self.trait_types])
        super(Union, self).__init__(**kwargs)

    def default(self, obj=None):
        default = super(Union, self).default(obj)
        for t in self.trait_types:
            if default is Undefined:
                default = t.default(obj)
            else:
                break
        return default

    def class_init(self, cls, name, parent=None):
        for trait_type in reversed(self.trait_types):
            trait_type.class_init(cls, None, self)
        super(Union, self).class_init(cls, name, parent)

    def instance_init(self, obj):
        for trait_type in reversed(self.trait_types):
            trait_type.instance_init(obj)
        super(Union, self).instance_init(obj)

    def validate(self, obj, value):
        with obj.cross_validation_lock:
            for trait_type in self.trait_types:
                try:
                    v = trait_type._validate(obj, value)
                    # In the case of an element trait, the name is None
                    if self.name is not None:
                        setattr(obj, '_' + self.name + '_metadata', trait_type.metadata)
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
    allow_none = True
    info_text = 'any value'


class Bounded(Instance):
    """A base trait for values with min and max boundaries."""

    def __init__(self, default_value=Undefined, allow_none=False, **kwargs):
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)
        super(Bounded, self).__init__(
            default_value=default_value,
            allow_none=allow_none, **kwargs)

    def validate(self, obj, value):
        value = super(Bounded, self).validate(obj, value)
        return self._validate_bounds(obj, value)

    def _validate_bounds(self, obj, value):
        """Validate that a number to be applied to a trait is between bounds.
        If value is not between min_bound and max_bound, this raises a
        TraitError with an error message appropriate for this trait.
        """
        if self.min is not None and value < self.min:
            raise TraitError(
                "The value of the '{name}' trait of {klass} instance should "
                "not be less than {min_bound}, but a value of {value} was "
                "specified".format(name=self.name, klass=describe("an", obj),
                    value=value, min_bound=self.min))
        if self.max is not None and value > self.max:
            raise TraitError(
                "The value of the '{name}' trait of {klass} instance should "
                "not be greater than {max_bound}, but a value of {value} was "
                "specified".format(name=self.name, klass=describe("an", obj),
                    value=value, max_bound=self.max))
        return value


class Int(Bounded):
    """An int trait."""

    klass = int
    default_value = 0


class CInt(Int):
    """A casting version of the int trait."""
    _cast_types = object


if six.PY2:
    class Long(Bounded):
        """A long integer trait."""

        klass = long
        _cast_types = int
        default_value = 0


    class CLong(Long):
        """A casting version of the long integer trait."""
        _cast_types = object


    class Integer(Bounded):
        """An integer trait.
        Longs that are unnecessary (<= sys.maxint) are cast to ints."""

        klass = int
        # downcast longs that fit in int:
        if sys.platform == 'cli':
            from System import Int64
            _cast_types = (long, Int64)
        else:
            _cast_types = long

        def validate(self, obj, value):
            if isinstance(value, long) and isinstance(int(value), long):
                # int(long > sys.maxint) is a long: we need a special
                # condition here to avoid raising a trait error
                return value
            else:
                return super(Integer, self).validate(obj, value)

        default_value = 0

else:
    Long, CLong = Int, CInt
    Integer = Int


class Float(Bounded):
    """A float trait."""

    default_value = 0.0
    klass = float
    _cast_types = int


class CFloat(Float):
    """A casting version of the float trait."""
    _cast_types = object


class Complex(Bounded):
    """A trait for complex numbers."""

    klass = complex
    _cast_types = (float, int)

    default_value = 0.0 + 0.0j
    info_text = 'a complex number'


class CComplex(Complex):
    """A casting version of the complex number trait."""
    _cast_types = object


# We should always be explicit about whether we're using bytes or unicode, both
# for Python 3 conversion and for reliable unicode behaviour on Python 2. So
# we don't have a Str type.
class Bytes(Instance):
    """A trait for byte strings."""

    default_value = b''
    info_text = 'a bytes object'
    klass = bytes

class CBytes(Bytes):
    """A casting version of the byte string trait."""
    _cast_types = object


class Unicode(Instance):
    """A trait for unicode strings."""

    default_value = u''
    info_text = 'a unicode string'
    klass = six.text_type

    _cast_types = (bytes,)

    def cast(self, value):
        try:
            return value.decode('ascii', 'strict')
        except UnicodeDecodeError:
            raise TraitError("Could not strictly decode %r to ascii." % value)


class CUnicode(Unicode):
    """A casting version of the unicode trait."""
    _cast_types = object
    cast = Instance.cast


class ObjectName(Instance):
    """A string holding a valid object name in this version of Python.

    This does not check that the name exists in any scope."""

    info_text = "a valid object identifier in Python"

    klass = six.string_types

    if six.PY2:

        cast = str
        _cast_types = unicode

    def validate(self, obj, value):
        value = super(ObjectName, self).validate(obj, value)
        if not isidentifier(value):
            self.error(obj, value)
        return value


class DottedObjectName(ObjectName):
    """A string holding a valid dotted object name in Python, such as A.b3._c"""
    def validate(self, obj, value):
        value = super(ObjectName, self).validate(obj, value)
        if not all(isidentifier(a) for a in value.split('.')):
            self.error(obj, value)
        return value


class Bool(Instance):
    """A boolean (True, False) trait."""
    klass = bool
    default_value = False


class CBool(Bool):
    """A casting version of the boolean trait."""
    _cast_types = object


class Enum(TraitType):
    """An enum whose value must be in a given sequence."""

    def __init__(self, values, default_value=Undefined, **kwargs):
        self.values = values
        if kwargs.get('allow_none', False) and default_value is Undefined:
            default_value = None
        super(Enum, self).__init__(default_value, **kwargs)

    def validate(self, obj, value):
        if value in self.values:
                return value
        self.error(obj, value)

    def _choices_str(self, as_rst=False):
        """ Returns a description of the trait choices (not none)."""
        choices = self.values
        if as_rst:
            choices = '|'.join('``%r``' % x for x in choices)
        else:
            choices = repr(list(choices))
        return choices

    def _info(self, as_rst=False):
        """ Returns a description of the trait."""
        none = (' or %s' % ('`None`' if as_rst else 'None')
                if self.allow_none else
                '')
        return 'any of %s%s' % (self._choices_str(as_rst), none)

    def info(self):
        return self._info(as_rst=False)

    def info_rst(self):
        return self._info(as_rst=True)


class CaselessStrEnum(Enum):
    """An enum of strings where the case should be ignored."""

    def __init__(self, values, default_value=Undefined, **kwargs):
        values = [cast_unicode_py2(value) for value in values]
        super(CaselessStrEnum, self).__init__(values, default_value=default_value, **kwargs)

    def validate(self, obj, value):
        if isinstance(value, str):
            value = cast_unicode_py2(value)
        if not isinstance(value, six.string_types):
            self.error(obj, value)

        for v in self.values:
            if v.lower() == value.lower():
                return v
        self.error(obj, value)

    def _info(self, as_rst=False):
        """ Returns a description of the trait."""
        none = (' or %s' % ('`None`' if as_rst else 'None')
                if self.allow_none else
                '')
        return 'any of %s (case-insensitive)%s' % (self._choices_str(as_rst), none)

    def info(self):
        return self._info(as_rst=False)

    def info_rst(self):
        return self._info(as_rst=True)


class FuzzyEnum(Enum):
    """An case-ignoring enum matching choices by unique prefixes/substrings."""

    case_sensitive = False
    #: If True, choices match anywhere in the string, otherwise match prefixes.
    substring_matching = False

    def __init__(self, values, default_value=Undefined,
                 case_sensitive=False, substring_matching=False, **kwargs):
        self.case_sensitive = case_sensitive
        self.substring_matching = substring_matching
        values = [cast_unicode_py2(value) for value in values]
        super(FuzzyEnum, self).__init__(values, default_value=default_value, **kwargs)

    def validate(self, obj, value):
        if isinstance(value, str):
            value = cast_unicode_py2(value)
        if not isinstance(value, six.string_types):
            self.error(obj, value)

        conv_func = (lambda c: c) if self.case_sensitive else lambda c: c.lower()
        substring_matching = self.substring_matching
        match_func = ((lambda v, c: v in c)
                      if substring_matching
                      else (lambda v, c: c.startswith(v)))
        value = conv_func(value)
        choices = self.values
        matches = [match_func(value, conv_func(c)) for c in choices]
        if sum(matches) == 1:
            for v, m in zip(choices, matches):
                if m:
                    return v

        self.error(obj, value)

    def _info(self, as_rst=False):
        """ Returns a description of the trait."""
        none = (' or %s' % ('`None`' if as_rst else 'None')
                if self.allow_none else
                '')
        case = 'sensitive' if self.case_sensitive else 'insensitive'
        substr = 'substring' if self.substring_matching else 'prefix'
        return 'any case-%s %s of %s%s' % (case, substr,
                                           self._choices_str(as_rst),
                                           none)

    def info(self):
        return self._info(as_rst=False)

    def info_rst(self):
        return self._info(as_rst=True)


class _Notifier(object):
    """An object for collecting, and distributing eventful notifications.
    """

    def __init__(self, cb, v):
        self.callback = cb
        self.value = v
        self._events = defaultdict(list)

    def __call__(self, etype, **data):
        """Gather a notification.

        Parameters
        ----------
        etype : str
            The type of event that will be sent to the :class:`HasTraits` instance.
        **data : any
            A description of the event that occured."""
        self._events[etype].append(data)

    def send(self, validate=False):
        """Send all gathered notifications.

        Noticications are sent with six attributes:

        type : A classification for the notification that will be sent.
        owner : The :class:`HasTraits` instance that will be notified.
        events : A list of data objects which were gathered.
        name : The name of the trait to be notified.
        depth : How nested the trait is that produced the notification where
            indexing begins at 0. Given ``trait = List(List())`` the outer list
            trait has a depth of 0, while the inner one has a depth of 1.
        value : The instance whose method was called.
        """
        lineage = list(self.callback.trait._lineage())
        with self.callback.owner.hold_trait_notifications():
            for etype, data in self._events.items():
                self.callback.owner.notify_change(Bunch(
                    owner=self.callback.owner,
                    events=list(map(Bunch, data)),
                    name=lineage[-1].name,
                    depth=len(lineage) - 1,
                    value=self.value,
                    type=etype,
                ))
            self._events.clear()
            if validate:
                self.callback.trait._validate_mutation(
                    self.callback.owner, self.value)


class _Callback(object):
    """A wrapper for the callbacks of a :class:`Mutable` subclass.

    This object will not be seen by the user unless they disect a value's spectator.
    """

    notify = False

    def __init__(self, owner, trait, function):
        """Define the attributes of a callback.

        Parameters
        ----------
        owner : HasTraits
            The instance which owns the given trait.
        trait : TraitType
            The trait whose values will have a :class:`Spectator`.
        function : callable
            The callback method defined on an :class:`Eventful` subclass.
        """
        self._owner = ref(owner)
        self.trait = trait
        self.function = function

    def __eq__(self, other):
        """Compare this callback to a callable or other callback.

        If compared to an object which is not a Callback,
        a check is made to see if it is the function of this
        callback instead.
        """
        if not isinstance(other, _Callback):
            return self.function == other
        else:
            return other is self

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, self.function)

    @property
    def owner(self):
        o = self._owner()
        if o is None:
            raise RuntimeError("You must retain a reference to the owner of "
                "%r to prevent it from being garbage collected." % self.trait)
        return o


class _Beforeback(_Callback):

    def __call__(self, value, call):
        """A callback that responds before a method call has been made.

        Parameters
        ----------
        value : any
            The value of the trait, whose method was called.
        call: Bunch
            Data created by :class:`Specatator` about what
            method was called, and with what arguments.

        Returns
        -------
        The output of the callback's handler function.

        Notifications
        -------------
        If/when this callback notifies its owner, it passes a :class:`Bunch` containing:

        + ``name``: The name of the trait that changed.
        + ``owner``: The owner of the trait that changed.
        + ``type``: The name of the event passed to the ``notify`` closure
        + ``events``: A list of all the data passed to the ``notify`` closure.

        See :mod:`spectate` for more info on beforebacks and afterbacks.
        """
        if self.function is not None:
            notify = _Notifier(self, value)
            result = self.function(value, call, notify)
            notify.send()
            return result


class _Afterback(_Callback):

    def __call__(self, value, answer):
        """A callback that responds before a method call has been made

        Parameters
        ----------
        value : any
            The value of the trait, whose method was called.
        answer: Bunch
            Data created by :class:`Specatator` about what
            method was called, and with what arguments.

        Notifications
        -------------
        If/when this callback notifies its owner, it passes a :class:`Bunch` containing:

        + ``name``: The name of the trait that changed.
        + ``owner``: The owner of the trait that changed.
        + ``type``: The name of the event passed to the ``notify`` closure
        + ``events``: A list of all the data passed to the ``notify`` closure.

        See :mod:`spectate` for more info on beforebacks and afterbacks.
        """
        notify = _Notifier(self, value)
        if self.function is None:
            if callable(answer.before):
                answer.before(answer.value, notify)
        else:
            self.function(value, answer, notify)
        notify.send(validate=True)


class Mutable(Instance):
    """A trait which can track changes to mutable data types.

    This trait provides a generic API for responding to method calls on its
    values. For example, standard traits do not react when users calls
    ``list.append`` to mutate a list attached to a ``HasTraits`` object. A
    ``Mutable`` trait on the other hand, provided it has the appropriate
    attributes and ``eventful=True`` is specified in the constructor.

    In order to report an event that has occurred on a trait value, we need
    an ``events`` dictionary, and callback methods. The ``events`` dictionary
    maps nicknames to one or more real method names. For example, to track when
    users set the contents of a dictionary we might say ``events = {"setitem":
    ["__setitem__", "setdefault"]}``. With this in place we can then define
    callbacks that trigger before or after the methods we specified in ``events``.
    The callbacks (hereafter referred to as Beforebacks and Afterbacks respectively)
    should be named ``_before_<nickname>`` and/or ``_after_<nickname>`` where the
    ``nickname`` should correspons to a key in the ``events`` dictionary. It's these
    Beforebacks and Afterbacks that give you the tools to create notifications:

    + Beforeback:
        + Signature: ``(value, call, notify)``
            1. ``value``: the instance whose method was called.
            2. ``call``: a bunch with the keys:
                + ``name``: name of the method called
                + ``args``: the arguments that method was called with
                + ``kwargs``: the keyword arguments the method was called with
            3. ``notify``: An object for sending notifications with the signature ``(type, **data)``.
                + ``type``: A string indication the type of event to be sent.
                + ``data``: Information that will be passed to ``@observe`` handlers under ``change['events']``
        + Return: a value, or an Afterback
            2. If a value is returned, it is sent to its corresponding Afterback.
            3. The afterback is a callable with a signature ``(returned, notify)``
                + ``returned``: is the output of the called method.
                + ``notify``: is the same as above.

    + Afterback
        + Signature: ``(value, answer, notify)``
        	1. ``value``: the value held by the trait.
        	2. ``answer``: a bunch with the keys:
        		+ ``name``: name of the method called
        		+ ``value``: the value returned by that call
        		+ ``before``: if a Beforeback was defined, this is the value it returned.
            3. ``notify``: is the same as above.

    Attributes
    ----------
    events : dict of strings or lists
        A dictionary which maps nicknames to one or many method names in the
        form ``{nickname: "method_1"}`` or ``{nickname: ["method_1", "method_2"]}``.
    _before_<nickname> : callable
        Methods of the form ``(value, call, notify)``.
    _after_<nickname> : callable
        Methods of the form ``(value, answer, notify)``.
    """

    events = {}
    eventful = False

    def __init__(self, *args, **kwargs):
        self.eventful = kwargs.pop("eventful", self.eventful)
        super(Mutable, self).__init__(*args, **kwargs)

    def default(self, obj=None):
        if self.default_value is not Undefined:
            return copy.copy(self.default_value)
        elif hasattr(self, "make_dynamic_default"):
            return self.make_dynamic_default()
        else:
            return Undefined

    def register_events(self, owner, value):
        """Add the events this trait defines to a watchable type.

        Parameters
        ----------
        owner : HasTraits
            The instance this trait belongs to.
        value : spectate.WatchedType
            The value to which the events should be registered.
        """
        spectator = spectate.watch(value)
        for method, before, after in self.iter_events():
            if not (before is None and after is None):
                spectator.callback(method,
                    _Beforeback(owner, self, before),
                    _Afterback(owner, self, after)
                )

    def unregister_events(self, value):
        """Remove the events this trait defines from a watchable type.

        Parameters
        ----------
        value : spectate.WatchedType
            The value from which the events should be removed.
        """
        if spectate.watchable(value) and spectate.watcher(value):
            spectator = spectate.watcher(value)
            for method, before, after in self.iter_events():
                if before is not None or after is not None:
                    spectator.remove_callback(method, before, after)

    def iter_events(self):
        """Iterate over the event callbacks this trait defined.

        They are yielded in the form ``(method, before, after)`` where
        ``method`` is the name of the method the callbacks react to,
        ``before`` the Beforeback, and ``after`` the Afteraback.
        """
        for name, on in self.events.items():
            for method in (on if isinstance(on, (tuple, list)) else (on,)):
                yield (
                    method,
                    getattr(self, "_before_" + name, None),
                    getattr(self, "_after_" + name, None),
                )

    def set(self, obj, val):
        if self.eventful:
            self._test_mutable_builtin(val)
        super(Mutable, self).set(obj, val)

    def validate(self, owner, value):
        """Registers the events this trait defines if it is eventful.

        Also unregisters events from an old value if it existed.
        """
        if owner.trait_has_value(self.name):
            self._test_mutable_builtin(value)
            old = getattr(owner, self.name)
        else:
            old = Undefined
        value = super(Mutable, self).validate(owner, value)
        if self.eventful and value is not None and value is not old:
            if not spectate.watchable(value):
                cls = type(value)
                methods = set(e[0] for e in self.iter_events())
                wtype = spectate.expose_as(cls.__name__, cls, *methods)
                try:
                    value.__class__ = wtype
                except TypeError:
                    value = wtype(value)
            self.register_events(owner, value)
            self.unregister_events(old)
        return value

    def _validate_mutation(self, owner, value):
        """Called after an eventful notification is sent.
        """
        pass

    def _test_mutable_builtin(self, value):
        if self.eventful and type(value) in MutableBuiltins:
            raise TraitError(
                "%r is a mutable builtin type, and cannot "
                "be assigned to eventful traits." % value)


class Container(Instance):
    """A base class for iterable types"""

    def validate(self, obj, value):
        validate = super(Container, self).validate
        value = self.validate_elements(obj, validate(obj, value))
        return validate(obj, value)

    def validate_elements(self, obj, value):
        return value


class Collection(Container):
    """A base trait for immutable container types"""

    _traits = None

    def __init__(self, *traits, **kwargs):
        default_value = kwargs.get("default_value", Undefined)
        if len(traits) == 1 and not is_trait(traits[0]) and default_value is Undefined:
            kwargs["default_value"], traits = traits[0], ()

        self._traits = []
        for i, trait in enumerate(traits):
            if inspect.isclass(trait) and issubclass(trait, TraitType):
                warn("Traits should be given as instances, not types "
                     "(for example, `Int()`, not `Int`). Passing "
                     "types is deprecated in traitlets 4.1.",
                     DeprecationWarning, stacklevel=3)
                trait = trait()
            if not isinstance(trait, TraitType):
                raise TypeError("Argument %i of 'traits' must be %s, not %s." %
                    (i, describe("a", TraitType), describe("the", trait)))
            else:
                self._traits.append(trait)

        super(Collection, self).__init__(**kwargs)

    def class_init(self, cls, name, parent=None):
        for trait in self._traits:
            if isinstance(trait, TraitType):
                trait.class_init(cls, None, self)
        super(Container, self).class_init(cls, name, parent)

    def instance_init(self, obj):
        for trait in self._traits:
            if isinstance(trait, TraitType):
                trait.instance_init(obj)
        super(Container, self).instance_init(obj)

    def validate_elements(self, obj, value):
        if not self._traits:
            return value
        if len(self._traits) != len(value):
            info = "a length %i" % len(self._traits)
            self.error(obj, len(value), info=info)
        new = []
        for t, v in zip(self._traits, value):
            try:
                v = t._validate(obj, v)
            except TraitError as error:
                self.error(obj, v, error)
            else:
                new.append(v)
        return tuple(new)


class Sequence(Mutable, Container):
    """A base trait for mutable container types
    """

    _trait = None
    allow_none = True

    def __init__(self, trait=None, default_value=Undefined,
                 minlen=0, maxlen=sys.maxsize, **kwargs):
        self._minlen, self._maxlen = minlen, maxlen
        if default_value is Undefined and not is_trait(trait):
            if trait is not None or kwargs.get("allow_none", False):
                kwargs['default_value'], trait = trait, None
        else:
            kwargs['default_value'] = default_value
        self._trait = trait
        super(Sequence, self).__init__(**kwargs)

        if inspect.isclass(trait) and issubclass(trait, TraitType):
            warn("Traits should be given as instances, not types "
                 "(for example, `Int()`, not `Int`). Passing "
                 "types is deprecated in traitlets 4.1.",
                 DeprecationWarning, stacklevel=3)
            trait = trait()
        if not isinstance(trait, TraitType) and trait is not None:
            raise TypeError("The argument 'trait' must be %s, not %s." %
                (describe("a", TraitType), describe("the", trait)))
        self._trait = trait
        super(Sequence, self).__init__(**kwargs)

    def class_init(self, cls, name, parent=None):
        if isinstance(self._trait, TraitType):
            self._trait.class_init(cls, None, self)
        super(Sequence, self).class_init(cls, name, parent)

    def instance_init(self, obj):
        if isinstance(self._trait, TraitType):
            self._trait.instance_init(obj)
        super(Sequence, self).instance_init(obj)

    def validate(self, obj, value):
        value = super(Sequence, self).validate(obj, value)
        length = len(value)
        if length < self._minlen:
            info = "a length <= %i" % self._minlen
            self.error(obj, length, info=info)
        elif length > self._maxlen:
            info = "a length >= %i" % self._maxlen
            self.error(obj, length, info=info)
        return value

    def _validate_mutation(self, owner, value):
        self.validate_elements(owner, value)

    def validate_elements(self, obj, value):
        if not self._trait:
            return value
        for original in value:
            try:
                new = self._trait._validate(obj, original)
            except TraitError as error:
                self.error(obj, original, error)
            else:
                if original is not new:
                    raise TraitError("The base Sequence class "
                        "does not support element coercion")
        return value


class Tuple(Collection):

    klass = tuple
    _cast_types = list
    default_value = ()


class Set(Sequence):

    klass = set
    _cast_types = (list, tuple)
    default_value = set()

    events = {
        "update": (
            "add", "clear", "update", "difference_update",
            "intersection_update", "pop", "remove",
            "symmetric_difference_update", "discard",
        )
    }

    def validate_elements(self, obj, value):
        if not self._trait:
            return value
        for original in value:
            try:
                new = self._trait._validate(obj, original)
            except TraitError as error:
                self.error(obj, original, error)
            else:
                if new is not original:
                    value.symmetric_difference_update({new, original})
        return value

    def _before_update(self, value, call, notify):
        return value.copy()

    def _after_update(self, value, answer, notify):
        new = value.difference(answer.before)
        old = answer.before.difference(value)
        if new or old:
            notify("mutation", new=new, old=old)


class List(Sequence):

    klass = list
    _cast_types = tuple
    default_value = []
    events = {
        'append': 'append',
        'extend': 'extend',
        'insert': 'insert',
        'setitem': '__setitem__',
        'remove': "remove",
        'delitem': '__delitem__',
        'reverse': 'reverse',
        'sort': 'sort',
    }

    def validate_elements(self, obj, value):
        if not self._trait:
            return value
        for i, original in enumerate(value):
            try:
                new = self._trait._validate(obj, original)
            except TraitError as error:
                self.error(obj, original, error)
            else:
                if new is not original:
                    value[i] = new
        return value

    @staticmethod
    def _before_setitem(value, call, notify):
        index = call.args[0]
        try:
            old = value[index]
        except KeyError:
            old = Undefined
        return index, old

    @staticmethod
    def _after_setitem(value, answer, notify):
        index, old = answer.before
        new = value[index]
        if new is not old:
            notify("mutation", index=index, old=old, new=new)

    @staticmethod
    def _before_delitem(value, call, notify):
        index = call.args[0]
        return index, value[index:]

    @staticmethod
    def _after_delitem(value, answer, notify):
        index, old = answer.before
        for i, x in enumerate(old):
            try:
                new = value[index + i]
            except IndexError:
                new = Undefined
            notify("mutation", index=(i + index), old=x, new=new)

    @staticmethod
    def _before_insert(value, call, notify):
        index = call.args[0]
        return index, value[index:]

    @staticmethod
    def _after_insert(value, answer, notify):
        index, old = answer.before
        for i in range(index, len(value)):
            try:
                o = old[i]
            except IndexError:
                o = Undefined
            notify("mutation", index=i, old=o, new=value[i])

    def _after_append(self, value, answer, notify):
        notify("mutation", index=len(value) - 1, old=Undefined, new=value[-1])

    def _before_extend(self, value, call, notify):
        return len(value)

    def _after_extend(self, value, answer, notify):
        for i in range(answer.before, len(value)):
            notify("mutation", index=i, old=Undefined, new=value[i])

    def _before_remove(self, value, call, notify):
        index = value.index(call.args[0])
        return index, value[index:]

    _after_remove = _after_delitem

    def _before_reverse(self, value, call, notify):
        return self.rearrangement(value)

    def _before_sort(self, value, call, notify):
        return self.rearrangement(value)

    @staticmethod
    def rearrangement(new):
        old = new[:]
        def after_rearangement(returned, notify):
            for i, v in enumerate(old):
                if v != new[i]:
                    notify("mutation", index=i, old=v, new=new[i])
        return after_rearangement


class Mapping(Mutable, Container):
    """A base class for mapping types.
    """

    _trait_mapping = None
    _value_trait = None
    _key_trait = None

    def __init__(self, trait, trait_mapping=None, default_value=Undefined, **kwargs):
        if default_value is Undefined and not is_trait(trait):
            default_value, trait = Undefined, None

        if not is_trait(trait) and trait is not None:
            key_trait, value_trait = trait
        else:
            value_trait = trait
            key_trait = None

        if is_trait(value_trait):
            if isinstance(value_trait, type):
                warn("Traits should be given as instances, not types (for example, `Int()`, not `Int`)"
                     " Passing types is deprecated in traitlets 4.1.",
                     DeprecationWarning, stacklevel=2)
                value_trait = value_trait()
        elif value_trait is not None:
            raise TypeError("`value_trait` must be a Trait or None, got %s" % repr_type(value_trait))

        if is_trait(key_trait):
            if isinstance(key_trait, type):
                warn("Traits should be given as instances, not types (for example, `Int()`, not `Int`)"
                     " Passing types is deprecated in traitlets 4.1.",
                     DeprecationWarning, stacklevel=2)
                key_trait = key_trait()
        elif key_trait is not None:
            raise TypeError("`key_trait` must be a Trait or None, got %s" % repr_type(key_trait))

        self._key_trait = key_trait
        self._value_trait = value_trait
        self._trait_mapping = trait_mapping

        super(Mapping, self).__init__(default_value=default_value, **kwargs)

    def class_init(self, cls, name, parent=None):
        if self._value_trait is not None:
            self._value_trait.class_init(cls, None, self)
        if self._key_trait is not None:
            self._key_trait.class_init(cls, None, self)
        if self._trait_mapping is not None:
            for trait in self._trait_mapping.values():
                trait.class_init(cls, None, self)
        super(Mapping, self).class_init(cls, name, parent)

    def instance_init(self, obj):
        if self._value_trait is not None:
            self._value_trait.instance_init(obj)
        if self._key_trait is not None:
            self._key_trait.instance_init(obj)
        if self._trait_mapping is not None:
            for trait in self._trait_mapping.values():
                trait.instance_init(obj)
        super(Mapping, self).instance_init(obj)

    def validate_elements(self, obj, new):
        key_trait, value_trait = self._key_trait, self._value_trait
        trait_mapping = self._trait_mapping or {}

        if not (key_trait or value_trait or trait_mapping):
            return new

        result = {}

        for k in new:
            # validate keys
            if key_trait is not None:
                try:
                    k = key_trait._validate(obj, k)
                except TraitError as error:
                    # an error occured while validating a key
                    info = "the key %r to be %s" % (k, key_trait.info())
                    self.error(obj, k, info=info, error=error)
            # validate values
            v = new[k]
            _value_trait = trait_mapping.get(k, value_trait)
            if _value_trait is not None:
                try:
                    v = _value_trait._validate(obj, v)
                except TraitError as error:
                    # an error occured while validating a value
                    info = "a value of the key %r to be %s" % (k, _value_trait.info())
                    self.error(obj, v, info=info, error=error)

            result[k] = v

        return result


class Dict(Mapping):
    """An instance of a Python dict.

    One or more traits can be passed to the constructor
    to validate the keys and/or values of the dict.
    If you need more detailed validation,
    you may use a custom validator method.

    .. versionchanged:: 5.0
        Added key_trait for validating dict keys.

    .. versionchanged:: 5.0
        Deprecated ambiguous ``trait``, ``traits`` args in favor of ``value_trait``, ``per_key_traits``.
    """

    klass = dict
    default_value = {}

    events = {
        'setitem': ('__setitem__', 'setdefault'),
        'delitem': ('__delitem__', 'pop'),
        'update': 'update',
        'clear': 'clear',
    }

    def __init__(self, value_trait=None, per_key_traits=None,
            key_trait=None, default_value=Undefined, **kwargs):
        """Create a dict trait type from a Python dict.

        The default value is created by doing ``dict(default_value)``,
        which creates a copy of the ``default_value``.

        Parameters
        ----------

        value_trait : TraitType [ optional ]
            The specified trait type to check and use to restrict the values of
            the dict. If unspecified, values are not checked.

        per_key_traits : Dictionary of {keys:trait types} [ optional, keyword-only ]
            A Python dictionary containing the types that are valid for
            restricting the values of the dict on a per-key basis.
            Each value in this dict should be a Trait for validating

        key_trait : TraitType [ optional, keyword-only ]
            The type for restricting the keys of the dict. If
            unspecified, the types of the keys are not checked.

        default_value : SequenceType [ optional, keyword-only ]
            The default value for the Dict.  Must be dict, tuple, or None, and
            will be cast to a dict if not None. If any key or value traits are specified,
            the `default_value` must conform to the constraints.

        Examples
        --------

        >>> d = Dict(Unicode())
        a dict whose values must be text

        >>> d2 = Dict(per_key_traits={'n': Integer(), 's': Unicode()})
        d2['n'] must be an integer
        d2['s'] must be text

        >>> d3 = Dict(value_trait=Integer(), key_trait=Unicode())
        d3's keys must be text
        d3's values must be integers
        """

        # handle deprecated keywords
        trait = kwargs.pop('trait', None)
        if trait is not None:
            if value_trait is not None:
                raise TypeError("Found a value for both `value_trait` and its deprecated alias `trait`.")
            value_trait = trait
            warn("Keyword `trait` is deprecated in traitlets 5.0, use `value_trait` instead", DeprecationWarning)
        traits = kwargs.pop('traits', None)
        if traits is not None:
            if per_key_traits is not None:
                raise TypeError("Found a value for both `per_key_traits` and its deprecated alias `traits`.")
            per_key_traits = traits
            warn("Keyword `traits` is deprecated in traitlets 5.0, use `per_key_traits` instead", DeprecationWarning)

        # Handling positional arguments
        if default_value is Undefined and value_trait is not None:
            if not is_trait(value_trait):
                default_value = value_trait
                value_trait = None

        if key_trait is None and per_key_traits is not None:
            if is_trait(per_key_traits):
                key_trait = per_key_traits
                per_key_traits = None

        # Case where a type of TraitType is provided rather than an instance
        if is_trait(value_trait):
            if isinstance(value_trait, type):
                warn("Traits should be given as instances, not types (for example, `Int()`, not `Int`)"
                     " Passing types is deprecated in traitlets 4.1.",
                     DeprecationWarning, stacklevel=2)
                value_trait = value_trait()
            self._value_trait = value_trait
        elif value_trait is not None:
            raise TypeError("`value_trait` must be a Trait or None, got %s" % repr_type(value_trait))

        if is_trait(key_trait):
            if isinstance(key_trait, type):
                warn("Traits should be given as instances, not types (for example, `Int()`, not `Int`)"
                     " Passing types is deprecated in traitlets 4.1.",
                     DeprecationWarning, stacklevel=2)
                key_trait = key_trait()
            self._key_trait = key_trait
        elif key_trait is not None:
            raise TypeError("`key_trait` must be a Trait or None, got %s" % repr_type(key_trait))

        self._per_key_traits = per_key_traits

        super(Dict, self).__init__((key_trait, value_trait), per_key_traits, default_value=default_value, **kwargs)

    @staticmethod
    def _before_setitem(value, call, notify):
        key = call.args[0]
        old = value.get(key, Undefined)
        return key, old

    @staticmethod
    def _after_setitem(value, answer, notify):
        key, old = answer.before
        new = value[key]
        if new != old:
            notify("mutation", key=key, old=old, new=new)

    @staticmethod
    def _before_delitem(value, call, notify):
        key = call.args[0]
        try:
            old = value[key]
        except KeyError:
            pass
        else:
            def _after(returned, notify):
                notify("mutation", key=key, old=old, new=Undefined)
            return _after

    def _before_update(self, value, call, notify):
        if len(call.args):
            args = call.args[0]
            if inspect.isgenerator(arg):
                # copy generator so it doesn't get exhausted
                arg = itertools.tee(arg)[1]
            new = dict(arg)
            new.update(call.kwargs)
        else:
            new = call.kwargs
        old = {k: value.get(k, Undefined) for k in new}
        return old

    def _after_update(self, value, answer, notify):
        for k, v in answer.before.items():
            if value[k] != v:
                notify("mutation", key=k, old=v, new=value[k])

    def _before_clear(self, value, call, notify):
        return value.copy()

    def _after_clear(self, value, answer, notify):
        for k, v in answer.before.items():
            notify("mutation", key=k, old=v, new=Undefined)

    def _validate_mutation(self, owner, value):
        # TODO: implement this validation to cast
        # keys and values to their appropriate types.
        pass


class TCPAddress(TraitType):
    """A trait for an (ip, port) tuple.

    This allows for both IPv4 IP addresses as well as hostnames.
    """

    default_value = ('127.0.0.1', 0)
    info_text = 'an (ip, port) tuple'

    def validate(self, obj, value):
        if isinstance(value, tuple):
            if len(value) == 2:
                if isinstance(value[0], six.string_types) and isinstance(value[1], int):
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


class UseEnum(TraitType):
    """Use a Enum class as model for the data type description.
    Note that if no default-value is provided, the first enum-value is used
    as default-value.

    .. sourcecode:: python

        # -- SINCE: Python 3.4 (or install backport: pip install enum34)
        import enum
        from traitlets import HasTraits, UseEnum

        class Color(enum.Enum):
            red = 1         # -- IMPLICIT: default_value
            blue = 2
            green = 3

        class MyEntity(HasTraits):
            color = UseEnum(Color, default_value=Color.blue)

        entity = MyEntity(color=Color.red)
        entity.color = Color.green    # USE: Enum-value (preferred)
        entity.color = "green"        # USE: name (as string)
        entity.color = "Color.green"  # USE: scoped-name (as string)
        entity.color = 3              # USE: number (as int)
        assert entity.color is Color.green
    """
    default_value = None
    info_text = "Trait type adapter to a Enum class"

    def __init__(self, enum_class, default_value=None, **kwargs):
        assert issubclass(enum_class, enum.Enum), \
                          "REQUIRE: enum.Enum, but was: %r" % enum_class
        allow_none = kwargs.get("allow_none", False)
        if default_value is None and not allow_none:
            default_value = list(enum_class.__members__.values())[0]
        super(UseEnum, self).__init__(default_value=default_value, **kwargs)
        self.enum_class = enum_class
        self.name_prefix = enum_class.__name__ + "."

    def select_by_number(self, value, default=Undefined):
        """Selects enum-value by using its number-constant."""
        assert isinstance(value, int)
        enum_members = self.enum_class.__members__
        for enum_item in enum_members.values():
            if enum_item.value == value:
                return enum_item
        # -- NOT FOUND:
        return default

    def select_by_name(self, value, default=Undefined):
        """Selects enum-value by using its name or scoped-name."""
        assert isinstance(value, six.string_types)
        if value.startswith(self.name_prefix):
            # -- SUPPORT SCOPED-NAMES, like: "Color.red" => "red"
            value = value.replace(self.name_prefix, "", 1)
        return self.enum_class.__members__.get(value, default)

    def validate(self, obj, value):
        if isinstance(value, self.enum_class):
            return value
        elif isinstance(value, int):
            # -- CONVERT: number => enum_value (item)
            value2 = self.select_by_number(value)
            if value2 is not Undefined:
                return value2
        elif isinstance(value, six.string_types):
            # -- CONVERT: name or scoped_name (as string) => enum_value (item)
            value2 = self.select_by_name(value)
            if value2 is not Undefined:
                return value2
        elif value is None:
            if self.allow_none:
                return None
            else:
                return self.default_value
        self.error(obj, value)

    def _choices_str(self, as_rst=False):
        """ Returns a description of the trait choices (not none)."""
        choices = self.enum_class.__members__.keys()
        if as_rst:
            return '|'.join('``%r``' % x for x in choices)
        else:
            return repr(list(choices))  # Listify because py3.4- prints odict-class

    def _info(self, as_rst=False):
        """ Returns a description of the trait."""
        none = (' or %s' % ('`None`' if as_rst else 'None')
                if self.allow_none else
                '')
        return 'any of %s%s' % (self._choices_str(as_rst), none)

    def info(self):
        return self._info(as_rst=False)

    def info_rst(self):
        return self._info(as_rst=True)


class Callable(TraitType):
    """A trait which is callable.

    Notes
    -----
    Classes are callable, as are instances
    with a __call__() method."""

    info_text = 'a callable'

    def validate(self, obj, value):
        if six.callable(value):
            return value
        else:
            self.error(obj, value)

def _add_all():
    """add all trait types to `__all__`

    do in a function to avoid iterating through globals while defining local variables
    """
    for _name, _value in globals().items():
        if not _name.startswith('_') and isinstance(_value, type) and issubclass(_value, TraitType):
            __all__.append(_name)

_add_all()
