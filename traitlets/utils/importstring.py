# encoding: utf-8
"""
A simple utility to import something by its string name.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from sys import version_info


def _check_stringlike(s, types):
    if not isinstance(s, types):
        raise TypeError(
            "import_item expected input of type "
            "{0[0]} or {0[1]}, but got '{1}' instead.".format(
                types, type(s),
            )
        )


if version_info.major == 2:
    # PY2 __import__ expects bytes
    def _to_module_str(s):
        _check_stringlike(s, (bytes, unicode))
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        return s
elif version_info.major == 3:
    # PY3 __import__ expects unicode
    def _to_module_str(s):
        _check_stringlike(s, (bytes, str))
        if isinstance(s, bytes):
            s = s.decode('utf-8')
        return s


def import_item(name):
    """Import and return ``bar`` given the string ``foo.bar``.

    Calling ``bar = import_item("foo.bar")`` is the functional equivalent of
    executing the code ``from foo import bar``.

    Parameters
    ----------
    name : string
      The fully qualified name of the module/package being imported.

    Returns
    -------
    mod : module object
       The module that was imported.
    """
    name = _to_module_str(name)
    parts = name.rsplit('.', 1)
    if len(parts) == 2:
        # called with 'foo.bar....'
        package, obj = parts
        module = __import__(package, fromlist=[obj])
        try:
            pak = getattr(module, obj)
        except AttributeError:
            raise ImportError('No module named %s' % obj)
        return pak
    else:
        # called with un-dotted string
        return __import__(parts[0])
