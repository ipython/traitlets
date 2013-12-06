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
import sys
import textwrap
from string import Formatter

from . import py3compat

#-----------------------------------------------------------------------------
# Declarations
#-----------------------------------------------------------------------------

# datetime.strftime date format for ipython
if sys.platform == 'win32':
    date_format = "%B %d, %Y"
else:
    date_format = "%B %-d, %Y"


#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


# FIXME: We need to reimplement type specific displayhook and then add this
# back as a custom printer. This should also be moved outside utils into the
# core.

# def print_slist(arg):
#     """ Prettier (non-repr-like) and more informative printer for SList """
#     print "SList (.p, .n, .l, .s, .grep(), .fields(), sort() available):"
#     if hasattr(arg,  'hideonce') and arg.hideonce:
#         arg.hideonce = False
#         return
#
#     nlprint(arg)   # This was a nested list printer, now removed.
#
# print_slist = result_display.when_type(SList)(print_slist)


def indent(instr,nspaces=4, ntabs=0, flatten=False):
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


def list_strings(arg):
    """Always return a list of strings, given a string or list of strings
    as input.

    :Examples:

        In [7]: list_strings('A single string')
        Out[7]: ['A single string']

        In [8]: list_strings(['A single string in a list'])
        Out[8]: ['A single string in a list']

        In [9]: list_strings(['A','list','of','strings'])
        Out[9]: ['A', 'list', 'of', 'strings']
    """

    if isinstance(arg, py3compat.string_types): return [arg]
    else: return arg


def marquee(txt='',width=78,mark='*'):
    """Return the input string centered in a 'marquee'.

    :Examples:

        In [16]: marquee('A test',40)
        Out[16]: '**************** A test ****************'

        In [17]: marquee('A test',40,'-')
        Out[17]: '---------------- A test ----------------'

        In [18]: marquee('A test',40,' ')
        Out[18]: '                 A test                 '

    """
    if not txt:
        return (mark*width)[:width]
    nmark = (width-len(txt)-2)//len(mark)//2
    if nmark < 0: nmark =0
    marks = mark*nmark
    return '%s %s %s' % (marks,txt,marks)


ini_spaces_re = re.compile(r'^(\s+)')

def num_ini_spaces(strng):
    """Return the number of initial spaces in a string"""

    ini_spaces = ini_spaces_re.match(strng)
    if ini_spaces:
        return ini_spaces.end()
    else:
        return 0


def format_screen(strng):
    """Format a string for screen printing.

    This removes some latex-type format codes."""
    # Paragraph continue
    par_re = re.compile(r'\\$',re.MULTILINE)
    strng = par_re.sub('',strng)
    return strng


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
    splits = text.split('\n',1)
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


class EvalFormatter(Formatter):
    """A String Formatter that allows evaluation of simple expressions.
    
    Note that this version interprets a : as specifying a format string (as per
    standard string formatting), so if slicing is required, you must explicitly
    create a slice.
    
    This is to be used in templating cases, such as the parallel batch
    script templates, where simple arithmetic on arguments is useful.

    Examples
    --------
    
    In  [1]: f = EvalFormatter()
    In  [2]: f.format('{n//4}', n=8)
    Out [2]: '2'
    
    In  [3]: f.format("{greeting[slice(2,4)]}", greeting="Hello")
    Out [3]: 'll'
    """
    def get_field(self, name, args, kwargs):
        v = eval(name, kwargs)
        return v, name


#-----------------------------------------------------------------------------
# Utils to columnize a list of string
#-----------------------------------------------------------------------------

def _chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in py3compat.xrange(0, len(l), n):
        yield l[i:i+n]


def _find_optimal(rlist , separator_size=2 , displaywidth=80):
    """Calculate optimal info to columnize a list of string"""
    for nrow in range(1, len(rlist)+1) :
        chk = list(map(max,_chunks(rlist, nrow)))
        sumlength = sum(chk)
        ncols = len(chk)
        if sumlength+separator_size*(ncols-1) <= displaywidth :
            break;
    return {'columns_numbers' : ncols,
            'optimal_separator_width':(displaywidth - sumlength)/(ncols-1) if (ncols -1) else 0,
            'rows_numbers' : nrow,
            'columns_width' : chk
           }


def _get_or_default(mylist, i, default=None):
    """return list item number, or default if don't exist"""
    if i >= len(mylist):
        return default
    else :
        return mylist[i]



def get_text_list(list_, last_sep=' and ', sep=", ", wrap_item_with=""):
    """
    Return a string with a natural enumeration of items

    >>> get_text_list(['a', 'b', 'c', 'd'])
    'a, b, c and d'
    >>> get_text_list(['a', 'b', 'c'], ' or ')
    'a, b or c'
    >>> get_text_list(['a', 'b', 'c'], ', ')
    'a, b, c'
    >>> get_text_list(['a', 'b'], ' or ')
    'a or b'
    >>> get_text_list(['a'])
    'a'
    >>> get_text_list([])
    ''
    >>> get_text_list(['a', 'b'], wrap_item_with="`")
    '`a` and `b`'
    >>> get_text_list(['a', 'b', 'c', 'd'], " = ", sep=" + ")
    'a + b + c = d'
    """
    if len(list_) == 0:
        return ''
    if wrap_item_with:
        list_ = ['%s%s%s' % (wrap_item_with, item, wrap_item_with) for
                 item in list_]
    if len(list_) == 1:
        return list_[0]
    return '%s%s%s' % (
        sep.join(i for i in list_[:-1]),
        last_sep, list_[-1])
