"""A simple configuration system.

Inheritance diagram:

.. inheritance-diagram:: IPython.config.loader
   :parts: 3

Authors
-------
* Brian Granger
* Fernando Perez
* Min RK
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import copy

from .py3compat import  iteritems
from .traitlets import HasTraits, List, Any, TraitError

#-----------------------------------------------------------------------------
# Exceptions
#-----------------------------------------------------------------------------


class ConfigError(Exception):
    pass

#-----------------------------------------------------------------------------
# Config class for holding config information
#-----------------------------------------------------------------------------

class LazyConfigValue(HasTraits):
    """Proxy object for exposing methods on configurable containers
    
    Exposes:
    
    - append, extend, insert on lists
    - update on dicts
    - update, add on sets
    """
    
    _value = None
    
    # list methods
    _extend = List()
    _prepend = List()
    
    def append(self, obj):
        self._extend.append(obj)
    
    def extend(self, other):
        self._extend.extend(other)
    
    def prepend(self, other):
        """like list.extend, but for the front"""
        self._prepend[:0] = other
    
    _inserts = List()
    def insert(self, index, other):
        if not isinstance(index, int):
            raise TypeError("An integer is required")
        self._inserts.append((index, other))
    
    # dict methods
    # update is used for both dict and set
    _update = Any()
    def update(self, other):
        if self._update is None:
            if isinstance(other, dict):
                self._update = {}
            else:
                self._update = set()
        self._update.update(other)
    
    # set methods
    def add(self, obj):
        self.update({obj})
    
    def get_value(self, initial):
        """construct the value from the initial one
        
        after applying any insert / extend / update changes
        """
        if self._value is not None:
            return self._value
        value = copy.deepcopy(initial)
        if isinstance(value, list):
            for idx, obj in self._inserts:
                value.insert(idx, obj)
            value[:0] = self._prepend
            value.extend(self._extend)
        
        elif isinstance(value, dict):
            if self._update:
                value.update(self._update)
        elif isinstance(value, set):
            if self._update:
                value.update(self._update)
        self._value = value
        return value
    
    def to_dict(self):
        """return JSONable dict form of my data
        
        Currently update as dict or set, extend, prepend as lists, and inserts as list of tuples.
        """
        d = {}
        if self._update:
            d['update'] = self._update
        if self._extend:
            d['extend'] = self._extend
        if self._prepend:
            d['prepend'] = self._prepend
        elif self._inserts:
            d['inserts'] = self._inserts
        return d


def _is_section_key(key):
    """Is a Config key a section name (does it start with a capital)?"""
    if key and key[0].upper()==key[0] and not key.startswith('_'):
        return True
    else:
        return False


class Config(dict):
    """An attribute based dict that can do smart merges."""

    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self._ensure_subconfig()
    
    def _ensure_subconfig(self):
        """ensure that sub-dicts that should be Config objects are
        
        casts dicts that are under section keys to Config objects,
        which is necessary for constructing Config objects from dict literals.
        """
        for key in self:
            obj = self[key]
            if _is_section_key(key) \
                    and isinstance(obj, dict) \
                    and not isinstance(obj, Config):
                setattr(self, key, Config(obj))
    
    def _merge(self, other):
        """deprecated alias, use Config.merge()"""
        self.merge(other)
    
    def merge(self, other):
        """merge another config object into this one"""
        to_update = {}
        for k, v in iteritems(other):
            if k not in self:
                to_update[k] = copy.deepcopy(v)
            else: # I have this key
                if isinstance(v, Config) and isinstance(self[k], Config):
                    # Recursively merge common sub Configs
                    self[k].merge(v)
                else:
                    # Plain updates for non-Configs
                    to_update[k] = copy.deepcopy(v)

        self.update(to_update)

    def __contains__(self, key):
        # allow nested contains of the form `"Section.key" in config`
        if '.' in key:
            first, remainder = key.split('.', 1)
            if first not in self:
                return False
            return remainder in self[first]
        
        return super(Config, self).__contains__(key)
    
    # .has_key is deprecated for dictionaries.
    has_key = __contains__
    
    def _has_section(self, key):
        return _is_section_key(key) and key in self
    
    def copy(self):
        return type(self)(dict.copy(self))

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        return type(self)(copy.deepcopy(list(self.items())))
    
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if _is_section_key(key):
                c = Config()
                dict.__setitem__(self, key, c)
                return c
            else:
                # undefined, create lazy value, used for container methods
                v = LazyConfigValue()
                dict.__setitem__(self, key, v)
                return v

    def __setitem__(self, key, value):
        if _is_section_key(key):
            if not isinstance(value, Config):
                raise ValueError('values whose keys begin with an uppercase '
                                 'char must be Config instances: %r, %r' % (key, value))
        dict.__setitem__(self, key, value)

    def __getattr__(self, key):
        if key.startswith('__'):
            return dict.__getattr__(self, key)
        try:
            return self.__getitem__(key)
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, key, value):
        if key.startswith('__'):
            return dict.__setattr__(self, key, value)
        try:
            self.__setitem__(key, value)
        except KeyError as e:
            raise AttributeError(e)

    def __delattr__(self, key):
        if key.startswith('__'):
            return dict.__delattr__(self, key)
        try:
            dict.__delitem__(self, key)
        except KeyError as e:
            raise AttributeError(e)

