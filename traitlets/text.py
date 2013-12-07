# encoding: utf-8
"""
Utilities for working with strings and text.

Inheritance diagram:

.. inheritance-diagram:: IPython.utils.text
   :parts: 3
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import re
import textwrap


#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def indent(instr, nspaces=4, ntabs=0, flatten=False):
    """Indent a string a given number of spaces or tabstops.

    indent(str,nspaces=4,ntabs=0) -> indent str by ntabs+nspaces.

    Parameters
    ----------

    instr : basestring
        The string to be indented.
    nspaces : int (default: 4)
        The number of spaces to be indented.
    ntabs : int (default: 0)
        The number of tabs to be indented.
    flatten : bool (default: False)
        Whether to scrub existing indentation.  If True, all lines will be
        aligned to the same indentation.  If False, existing indentation will
        be strictly increased.

    Returns
    -------

    str|unicode : string indented by ntabs and nspaces.

    """
    if instr is None:
        return
    ind = '\t'*ntabs+' '*nspaces
    if flatten:
        pat = re.compile(r'^\s*', re.MULTILINE)
    else:
        pat = re.compile(r'^', re.MULTILINE)
    outstr = re.sub(pat, ind, instr)
    if outstr.endswith(os.linesep+ind):
        return outstr[:-len(ind)]
    else:
        return outstr


def dedent(text):
    """Equivalent of textwrap.dedent that ignores unindented first line.

    This means it will still dedent strings like:
    '''foo
    is a bar
    '''

    For use in wrap_paragraphs.
    """

    if text.startswith('\n'):
        # text starts with blank line, don't ignore the first line
        return textwrap.dedent(text)

    # split first line
    splits = text.split('\n', 1)
    if len(splits) == 1:
        # only one line
        return textwrap.dedent(text)

    first, rest = splits
    # dedent everything but the first line
    rest = textwrap.dedent(rest)
    return '\n'.join([first, rest])


def wrap_paragraphs(text, ncols=80):
    """Wrap multiple paragraphs to fit a specified width.

    This is equivalent to textwrap.wrap, but with support for multiple
    paragraphs, as separated by empty lines.

    Returns
    -------

    list of complete paragraphs, wrapped to fill `ncols` columns.
    """
    paragraph_re = re.compile(r'\n(\s*\n)+', re.MULTILINE)
    text = dedent(text).strip()
    paragraphs = paragraph_re.split(text)[::2] # every other entry is space
    out_ps = []
    indent_re = re.compile(r'\n\s+', re.MULTILINE)
    for p in paragraphs:
        # presume indentation that survives dedent is meaningful formatting,
        # so don't fill unless text is flush.
        if indent_re.search(p) is None:
            # wrap paragraph
            p = textwrap.fill(p, ncols)
        out_ps.append(p)
    return out_ps


def long_substr(data):
    """Return the longest common substring in a list of strings.
    
    Credit: http://stackoverflow.com/questions/2892931/longest-common-substring-from-more-than-two-strings-python
    """
    substr = ''
    if len(data) > 1 and len(data[0]) > 0:
        for i in range(len(data[0])):
            for j in range(len(data[0])-i+1):
                if j > len(substr) and all(data[0][i:i+j] in x for x in data):
                    substr = data[0][i:i+j]
    elif len(data) == 1:
        substr = data[0]
    return substr


def strip_email_quotes(text):
    """Strip leading email quotation characters ('>').

    Removes any combination of leading '>' interspersed with whitespace that
    appears *identically* in all lines of the input text.

    Parameters
    ----------
    text : str

    Examples
    --------

    Simple uses::

        In [2]: strip_email_quotes('> > text')
        Out[2]: 'text'

        In [3]: strip_email_quotes('> > text\\n> > more')
        Out[3]: 'text\\nmore'

    Note how only the common prefix that appears in all lines is stripped::

        In [4]: strip_email_quotes('> > text\\n> > more\\n> more...')
        Out[4]: '> text\\n> more\\nmore...'

    So if any line has no quote marks ('>') , then none are stripped from any
    of them ::
    
        In [5]: strip_email_quotes('> > text\\n> > more\\nlast different')
        Out[5]: '> > text\\n> > more\\nlast different'
    """
    lines = text.splitlines()
    matches = set()
    for line in lines:
        prefix = re.match(r'^(\s*>[ >]*)', line)
        if prefix:
            matches.add(prefix.group(1))
        else:
            break
    else:
        prefix = long_substr(list(matches))
        if prefix:
            strip = len(prefix)
            text = '\n'.join([ ln[strip:] for ln in lines])
    return text
