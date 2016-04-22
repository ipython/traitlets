# encoding: utf-8
"""
Functions for generating class specific documentation of traits and event handlers
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

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
    raw_event_objs = cls.events(name)
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

def traitlet_documentation(cls, name=None):
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
