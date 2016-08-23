
# void functions used as a callback placeholders.
def _default_pre_set(self, key, value):
    return value

def _default_post_set(self, key, value):
    pass

def _default_pre_del(self, key):
    pass

def _default_post_del(self, key):
    pass


class edict(dict):

    pre_set = _default_pre_set
    post_set = _default_post_set
    pre_del = _default_pre_del
    post_del = _default_post_del

    def pop(self, key):
        self.pre_del(key)
        ret =  dict.pop(self, key)
        self.post_del(key)
        return ret

    def popitem(self):
        key = next(iter(self))
        return key, self.pop(key)

    def update(self, other_dict):
        for (key, value) in other_dict.items():
            self[key] = value

    def clear(self):
        for key in list(self.keys()):
            del self[key]

    def __setitem__(self, key, value):
        value = self.pre_set(key, value)
        ret = dict.__setitem__(self, key, value)
        self.post_set(key, value)
        return ret

    def __delitem__(self, key):
        value = self.pre_del(key)
        ret = dict.__delitem__(self, key)
        value = self.post_del(key)
        return ret

