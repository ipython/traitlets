"""Yet another implementation of bunch

attribute-access of items on a dict.
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

class Bunch(dict):
    """A dict with attribute-access"""
    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(key)
    
    def __setattr__(self, key, value):
        self.__setitem__(key, value)
    
    def __dir__(self):
        names = super(Bunch, self).__dir__()
        names.extend(self.keys())
        return names

