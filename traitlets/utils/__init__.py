
# vestigal things from IPython_genutils.
def cast_unicode(s, encoding=None):
    if isinstance(s, bytes):
        return decode(s, encoding)
    return s
