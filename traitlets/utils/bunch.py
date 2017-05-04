"""Yet another implementation of bunch

attribute-access of items on a dict.
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from six import with_metaclass


class EmptyMethodDescriptor(object):
    
    def __init__(self, name, etype, msg):
        self.name = name
        self.etype = etype
        self.msg = msg
    
    def __get__(self, inst, cls=None):
        if inst is not None:
            m = "'%s' object " % cls.__name__
        else:
            m = "type object '%s' " % cls.__name__
        raise self.etype(m + self.msg)


class Bunch(dict):
    """A dict with attribute access"""
    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(key)
    
    def __setattr__(self, key, value):
        self.__setitem__(key, value)
    
    def __dir__(self):
        # py2-compat: can't use super because dict doesn't have __dir__
        names = dir(type(self))
        names.extend(self.keys())
        return names


class MetaFrozenBunch(type):
    
    def __new__(mcls, name, bases, classdict):
        for n in ('clear', 'pop', 'popitem', 'setdefault', 'update'):
            classdict[n] = EmptyMethodDescriptor(n, AttributeError, 'has no attribute %s' % n)
        classdict['__setattr__'] = EmptyMethodDescriptor( '__setattr__',
                        TypeError, 'does not support attribute assignment')
        classdict['__delattr__'] = EmptyMethodDescriptor( '__delattr__',
                        TypeError, 'does not support attribute deletion')
        classdict['__setitem__'] = EmptyMethodDescriptor( '__setitem__',
                        TypeError, 'does not support item assignment')
        classdict['__delitem__'] = EmptyMethodDescriptor('__delitem__',
                        TypeError, 'does not support item deletion')
        return super(MetaFrozenBunch, mcls).__new__(mcls, name, bases, classdict)


class FrozenBunch(with_metaclass(MetaFrozenBunch, Bunch)):
    """A read-only dict with attribute access"""

    def __hash__(self):
        return hash(tuple(self.items()))

    def thaw(self):
        """Returns a mutable copy"""
        return Bunch(self)
