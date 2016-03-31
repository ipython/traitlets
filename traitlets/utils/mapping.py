# encoding: utf-8
"""
A utility for mapping unhashable objects to values
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import warnings

class isdict(object):
    
    def __init__(self, pairs=None):
        """A dict-like mapping that keys objects on their id

        Note
        ----
        Objects used as keys in an idict are not stored as references.
        Thus the keys of an :class:`idict` won't be garbage collected
        until the :class:`idict` instance itself is released.
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
        return self._refs.values().__iter__()

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

    def ids(self):
        return self._dict.keys()
    
    def keys(self):
        return self._refs.values()
    
    def values(self):
        return self._dict.values()
        
    def items(self):
        return zip(self._refs.values(), self._dict.values())

    def __repr__(self):
        body = []
        for k, v in self.items():
            body.append(repr(k) + ': ' + repr(v))
        return '{' + ', '.join(body) + '}'
