# coding: utf-8
"""Compatibility tricks for Python 3. Mainly to do with unicode."""
import sys

if sys.version_info[0] >= 3:
    PY3 = True

    string_types = (str,)
    unicode_type = str

    def isidentifier(s, dotted=False):
        if dotted:
            return all(isidentifier(a) for a in s.split("."))
        return s.isidentifier()

    def iteritems(d): return iter(d.items())

else:
    PY3 = False

    string_types = (str, unicode)
    unicode_type = unicode

    import re
    _name_re = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")

    def isidentifier(s, dotted=False):
        if dotted:
            return all(isidentifier(a) for a in s.split("."))
        return bool(_name_re.match(s))

    def iteritems(d): return d.iteritems()

# Parts below taken from six:
# Copyright (c) 2010-2013 Benjamin Peterson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta("_NewBase", bases, {})
