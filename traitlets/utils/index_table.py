"""A dict-like table mapping keys to values based on indexing"""

import warnings

class itable(object):
    
    def __init__(self, keys=None, values=None):
        """A dict-like table mapping keys to values based on indexing"""
        if keys is not None and values is not None:
            self.update(keys, values)
        elif keys is None and values is None:
            self.__keys__ = []
            self.__values__ = []
        else:
            raise TypeError('Must provide a sequence for both keys and values')
        
    def __getitem__(self, key):
        try:
            i = self.__keys__.index(key)
        except ValueError:
            raise KeyError(key)
        else:
            return self.__values__[i]
        
    def __setitem__(self, key, value):
        try:
            i = self.__keys__.index(key)
        except ValueError:
            try:
                hash(key)
            except:
                pass
            else:
                warnings.warn('got a hashable mapping; use `dict` instead')
            self.__keys__.append(key)
            self.__values__.append(value)
        else:
            self.__values__[i] = value
            
    def __delitem__(self, key):
        try:
            i = self.__keys__.index(key)
        except ValueError:
            raise KeyError(key)
        else:
            del self.__keys__[i]
            del self.__values__[i]
    
    def __iter__(self):
        return self.__keys__.__iter__()

    def update(self, keys, values):
        if len(keys) != len(values):
            raise ValueError('keys and values must have the same length')
        try:
            map(hash, keys)
        except:
            pass
        else:
            warnings.warn('got a hashable mapping; use `dict` instead')

        try:
            # repeated keys are not removed,
            # however they will be ignored
            self.__keys__ = list(keys)[::-1]
            self.__values__ = list(values)[::-1]
        except:
            raise ValueError('keys and values must be iterable')

    def pop(self, key):
        try:
            i = self.__keys__.index(key)
        except ValueError:
            raise KeyError(key)
        else:
            del self.__keys__[i]
            return self.__values__.pop(i)
    
    def keys(self):
        return self.__keys__[:]
    
    def values(self):
        return self.__values__[:]
        
    def items(self):
        return zip(self.__keys__, self.__values__)

    def __repr__(self):
        body = []
        for k, v in self.items():
            body.append(repr(k) + ': ' + repr(v))
        return '{' + ', '.join(body) + '}'
