# encoding: utf-8
"""
A utility for mapping unhashable objects to values
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from itertools import chain

class isdict(object):
    
    def __init__(self, pairs=None):
        """A dict-like object that maps unhashable keys to values

        NOTE
        ----
        Objects used as keys in an isdict are not stored as references.
        Thus the keys of an won't be garbage collected until the :class:`isdict`
        instance itself is released.
        """
        # maps ids to values
        self._dict = {}
        # maps ids to true key objects
        self._refs = {}
        self.update(pairs)
        
    def __getitem__(self, key):
        try:
            return self._dict[id(key)]
        except KeyError:
            raise KeyError(key)
        
    def __setitem__(self, key, value):
        i = id(key)
        self._refs[i] = key
        self._dict[i] = value
            
    def __delitem__(self, key):
        try:
            i = id(key)
            del self._dict[i]
            del self._refs[i]
        except ValueError:
            raise KeyError(key)
    
    def __iter__(self):
        return self.keys()

    def update(self, pairs=None):
        if pairs is not None:
            lengths = set(map(len, pairs))
            if 2 not in lengths or len(lengths)>1:
                # invalid update sequence
                for i in range(len(pairs)):
                    if len(pairs[i]) != 2:
                        t = (str(i), str(len(pairs)))
                        raise ValueError("update sequence element #%s has"
                                         " length %s; 2 is required" % t)
            else:
                keys, values = zip(*pairs)

            ids = map(id, keys)
            self._dict.update(zip(ids, values))
            self._refs.update(zip(ids, keys))

    def pop(self, key):
        try:
            i = id(key)
            del self._refs[i]
            return self._dict.pop(i)
        except ValueError:
            raise KeyError(key)

    def get(self, key, default=None):
        if key in self:
            return self.__getitem__(key)
        else:
            return default

    def ids(self):
        return self._dict.keys()
    
    def keys(self):
        return self._refs.values().__iter__()
    
    def values(self):
        return self._dict.values().__iter__()
        
    def items(self):
        return zip(self._refs.values(), self._dict.values())

    def __repr__(self):
        body = []
        for k, v in self.items():
            body.append(repr(k) + ': ' + repr(v))
        return '{' + ', '.join(body) + '}'


class eqdict(object):
 
    def __init__(self, pairs=None):
        """A dict-like object for mapping equivalent keys to a set of values"""
        self._keys = []
        self._vals = []
        self.update(pairs)
        
    def __getitem__(self, key):
        enum = enumerate(self._keys)
        values = [self._vals[i] for i, k in enum if k == key]
        if len(values) == 0:
            raise KeyError(key)
        else:
            return values
        
    def __setitem__(self, key, value):
        try:
            i = self._keys.index(key)
        except ValueError:
            self._keys.append(key)
            self._vals.append(value)
        else:
            self._vals[i] = value
            
    def __delitem__(self, key):
        try:
            i = self._keys.index(key)
        except ValueError:
            raise KeyError(key)
        else:
            del self._keys[i]
            del self._vals[i]

    def __iter__(self):
        return self.keys()

    def update(self, pairs=None):
        if pairs is not None:
            lengths = set(map(len, pairs))
            if 2 not in lengths or len(lengths)>1:
                # invalid update sequence
                for i in range(len(pairs)):
                    if len(pairs[i]) != 2:
                        t = (str(i), str(len(pairs)))
                        raise ValueError("update sequence element #%s has"
                                         " length %s; 2 is required" % t)
            else:
                for k, v in zip(*pairs):
                    self.__setitem__(k, v)

    def get(self, key, default=None):
        if key in self:
            return self.__getitem__(key)
        else:
            return default

    def pop(self, key):
        try:
            i = self._keys.index(key)
        except ValueError:
            raise KeyError(key)
        else:
            del self._keys[i]
            return self._vals.pop(i)
    
    def keys(self):
        return self._keys.__iter__()
    
    def values(self):
        return self._vals.__iter__()
        
    def items(self):
        return zip(self._keys, self._vals)

    def __repr__(self):
        body = []
        for k, v in self.items():
            body.append(repr(k) + ': ' + repr(v))
        return '{' + ', '.join(body) + '}'

class mapping(object):

    def __init__(self):
        """A dict-like object for mapping any key to a set of values"""
        # handles unhashables
        self._is = isdict()
        # handles custom equivalence
        self._eq = eqdict()
        # all other values
        self._dict = {}

    def __getitem__(self, key):
        values = []
        try:
            hash(key)
        except:
            if key in self._is[key]:
                values.append(self._is[key])
        else:
            # note that python 2 classes with
            # __eq__ or __cmp__ are hashable
            if key in self._dict:
                values.append(self._dict[key])
        if key in self._eq:
            values.extend(self._eq[key])
        if len(values) == 0:
            raise KeyError(key)
        return values

    def __setitem__(self, key, value):
        self.get_internal_dict(key)[key] = value

    def __iter__(self):
        return self.keys()

    def get_internal_dict(self, key):
        """Return the sub-dict to which this key would be assigned"""
        try:
            hash(key)
        except:
            if hasattr(key, '__eq__') or hasattr(key, '__cmp__'):
                return self._eq
            else:
                return self._is
        else:
            # note that python 2 classes with
            # __eq__ or __cmp__ are hashable
            return self._dict

    def keys(self):
        return chain(self._is.keys(), self._eq.keys(), self._dict.keys())

    def values(self):
        return chain(self._is.values(), elf._eq.values(), self._dict.values())

    def items(self):
        return chain(self._is.items(), self._eq.items(), self._dict.items())

    def get(self, key, default=None):
        if key in self:
            return self.__getitem__(key)
        else:
            return default

    def __repr__(self):
        body = []
        for k, v in self.items():
            body.append(repr(k) + ': ' + repr(v))
        return '{' + ', '.join(body) + '}'
