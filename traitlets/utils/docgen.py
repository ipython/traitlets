# encoding: utf-8
"""
Functions for generating class specific documentation of traits and event handlers
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import types

PY3 = sys.version_info >= (3, 0)

_indent = 4
nl = '\n'
t = ' '*_indent

def _clip(l, delimiter, interval=60):
    divs = range(0, len(l), interval)
    cuts = [l[i:i + interval] for i in divs]
    return delimiter.join(cuts)

# - - - - - - - - -
# Raw Data Parsers
# - - - - - - - - -

def _gen_trait_help_docs(help):
    h = _clip(help, nl + t*2 + '   ')
    return (nl + t + ':help: ' if h else '') + h + (nl if h else '')

def _gen_trait_metadata_docs(metadata):
    data_list = ['``' + k + " = " + str(v) + '``' for k, v in metadata.items()]
    return (nl + '*').join(_clip(d, nl + t + '  ') for d in sorted(data_list))

def _gen_trait_event_docs(event_objs):
    events = [_format_event(e, n) for n, e in event_objs.items()]
    return (nl+'*').join(_clip(e, nl + t + '  ') for e in sorted(events) if e)

def _format_event(e, name):
    try:
        c = e.this_class.__name__
        m = ':method:`' + c + '.' + e.name + '`'
        return m + ' - ' + e.info()
    except:
        # event was not properly
        # setup or has no info
        return ''


# - - - - - - - - - - - - - - - - - - - - - -
# Consolidated Doc Parser For A Single Trait
# - - - - - - - - - - - - - - - - - - - - - -

def _help_by_name(cls, name):
    trait = getattr(cls, name)
    try:
        main_title = trait.name + " : " + trait.info()
    except:
        # info was not a string or trait has no name
        return

    # add main title
    docs = nl + main_title

    # parse trait help
    raw_help = trait.metadata.pop('help', None)
    if raw_help:
        docs += _gen_trait_help_docs(raw_help)

    # parse the metadata
    raw_metadata = trait.metadata.copy()
    data = _gen_trait_metadata_docs(raw_metadata)
    if data:
        data = nl + '*' + data

    # parse event handlers
    raw_event_objs = cls.trait_events(name)
    events = _gen_trait_event_docs(raw_event_objs)
    if events:
        events = nl + '*' + events

    # add section titles
    data_title = t + '- trait metadata' if data else ''
    event_title = t + '- event handlers' if events else ''

    docs += nl if data else ''
    docs += data_title + data
    docs += nl if events else ''
    docs += event_title + events

    # add extra tabs for bullets
    bullets = docs.split('*')
    docs = (t*2 + '* ').join(bullets)

    return docs

# - - - - - - - - - - - - - - - -
# Public Documentation Generator
# - - - - - - - - - - - - - - - -

def trait_documentation(cls, name=None):
    """Generate documentaiton for traits and event handlers on the class

    Parameters
    ----------
    cls: HasTraits
        The class whose trait documentation will be gathered and parsed
    name: str (default: None)
        The name of a particular trait or event handler on the given class,
        whose documentation should be returned. If name is ``None``, then the
        documentation for all traits and event handlers will be returned.

    Returns
    -------
    A doc string with information about traits and event handlers. If no
    documentation exists, will return ``None`` instead.
    """
    if name is not None:
        return _help_by_name(cls, name)
    else:
        trait_title = ":Traits of :class:`%s` Instances:" % cls.__name__
        trait_helps = [_help_by_name(cls, n) for n in sorted(cls.trait_names())]
        trait_helps = "\n".join(h for h in trait_helps if h)
        if trait_helps:
            return trait_title + nl + '-'*len(trait_title) + trait_helps

if PY3:
    def copy_func(f, name=None):
        return types.FunctionType(f.__code__, f.__globals__, name or f.__name__,
                                  f.__defaults__, f.__closure__)

    def write_docs_to_class(cls, docs):
        """Write traitlet documentation for this class to __init__"""
        __init__ = copy_func(cls.__init__)

        if __init__.__doc__ is not None:
            __init__.__doc__ += '\n\n' + docs
        else:
            __init__.__doc__ = docs

        cls.__init__ = __init__
else:
    def copy_func(f, name=None):
        return types.FunctionType(f.func_code, f.func_globals, name or f.func_name,
                                  f.func_defaults, f.func_closure)

    def write_docs_to_class(cls, docs):
        """Write traitlet documentation for this class to __init__"""
        im_func = copy_func(cls.__init__.im_func)

        if im_func.__doc__ is not None:
            im_func.__doc__ += '\n\n' + docs
        else:
            im_func.__doc__ = docs

        cls.__init__ = types.MethodType(im_func, None, cls)