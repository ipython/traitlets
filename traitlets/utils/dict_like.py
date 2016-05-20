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
            if key in self._is:
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

    def __delitem__(self, key):
        complete = False
        try:
            hash(key)
        except:
            if key in self._is:
                complete = True
                del self._is[key]
        else:
            # note that python 2 classes with
            # __eq__ or __cmp__ are hashable
            if key in self._dict:
                complete = True
                del self._dict[key]
        if key in self._eq:
            complete = True
            del self._eq[key]
        if not complete:
            raise KeyError(key)

    def __iter__(self):
        return self.keys()

    def __len__(self):
        return len(list(self.keys()))

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

    def get_in_dicts(self, key):
        """Return a list of internal dicts, the key is in"""
        values = []
        try:
            hash(key)
        except:
            if key in self._is:
                values.append(self._is)
        else:
            # note that python 2 classes with
            # __eq__ or __cmp__ are hashable
            if key in self._dict:
                values.append(self._dict)
        if key in self._eq:
            values.append(self._eq)
        if len(values) == 0:
            raise KeyError(key)
        return values

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


class TraitNotifierMapping(object):

    def __init__(self):
        self._named = {}
        self._tagged = {}
        # remember all
        # stoarge paths
        self.named_paths = []
        self.tagged_paths = []

    def __repr__(self):
        c = repr(self.__class__)
        n = "'named': " + repr(self._named)
        t = "'tagged': " + repr(self._tagged)
        return c + "({" + n ", " + t + "})"

    def clear_named(self):
        """Remove all named notifiers of all type"""
        self._named = {}

    def clear_tagged(self):
        """Remove all tagged notifiers of all type"""
        self._tagged = {}

    def add_named_notifier(self, notifier, name, type):
        """Corrispond a notifier to a trait name and type"""
        if type in self._named:
            d = self._named[type]
        else:
            d = {}
            self._named[type] = d

        if name in d:
            l = d[name]
        else:
            l = []
            d[name] = l

        if notifier not in l:
            self.named_paths.append((name, type))
            l.append(notifier)

    def add_tagged_notifier(self, notifier, key, value, type):
        """Corrispond a notifier to a trait tag and type"""
        if type in self._tagged:
            d = self._tagged[type]
        else:
            d = {}
            self._tagged[type] = d

        if key in d:
            m = d[key]
        else:
            m = mapping()
            d[key] = m

        i = m.get_internal_dict(value)

        if value in i:
            l = i[value]
        else:
            l = []
            i[value] = l
        
        if notifier not in l:
            self.tagged_paths.append((key, value, type))
            l.append(notifier)

    def del_named_notifier(self, notifier, name, type):
        """Delete the notifier corrisponding to the name and type"""
        try:
            if notifier is None:
                del self._named[type][name]
            else:
                l = self._named[type][name]
                l.remove(notifier)
                # clean up
                if len(l) == 0:
                    del self._named[type][name]
            self.named_paths.remove((name, type))
            # more clean up
            if len(self._named[type]) == 0:
                del self._named[type]
        except:
            pass

    def del_tagged_notifier(self, notifier, key, value, type):
        """Delete the notifier corrisponding to the tag and type"""
        try:
            if notifier is None:
                del self._tagged[type][key][value]
            else:
                for d in self._tagged[type][key].get_in_dicts(value):
                    if isinstance(d, eqdict):
                        ll = d[value]
                        for l in ll:
                            try:
                                l.remove(notifier)
                                # clean up
                                if len(l) == 0:
                                    ll.remove(l)
                            except:
                                pass
                        if len(ll) == 0:
                            del d[value]
                    else:
                        try:
                            l = d[value]
                            l.remove(notifier)
                            # clean up
                            if len(l) == 0:
                                del d[value]
                        except:
                            pass
            self.tagged_paths.remove((key, value, type))
            # more clean up
            if len(self._tagged[type][key]) == 0:
                del self._tagged[type][key]
                if len(self._tagged[type]) == 0:
                    del self._tagged[type]
        except KeyError, ValueError:
            pass

    def get_named_notifiers(self, name, type):
        """Get the notifiers corrisponding to the name and type"""
        notifiers = []
        if type in self._named and name in self._named[type]:
            notifiers.extend(self._named[type][name])
        return notifiers

    def get_tagged_notifiers(self, key, value, type):
        """Get the notifiers corrisponding to the tag and type"""
        notifiers = []
        d = self._tagged
        if type in d and key in d[type] and value in d[type][key]:
            list_of_lists = self._tagged[type][key][value]
            for n in list(chain(*list_of_lists)):
                if n not in notifiers:
                    notifiers.append(n)
        return notifiers
