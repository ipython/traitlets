# encoding: utf-8
"""Tests for Traitlets.text"""
from __future__ import print_function

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import math
import random

import nose.tools as nt

from Traitlets import text

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

def eval_formatter_check(f):
    ns = dict(n=12, pi=math.pi, stuff='hello there', os=os, u=u"café", b="café")
    s = f.format("{n} {n//4} {stuff.split()[0]}", **ns)
    nt.assert_equal(s, "12 3 hello")
    s = f.format(' '.join(['{n//%i}'%i for i in range(1,8)]), **ns)
    nt.assert_equal(s, "12 6 4 3 2 2 1")
    s = f.format('{[n//i for i in range(1,8)]}', **ns)
    nt.assert_equal(s, "[12, 6, 4, 3, 2, 2, 1]")
    s = f.format("{stuff!s}", **ns)
    nt.assert_equal(s, ns['stuff'])
    s = f.format("{stuff!r}", **ns)
    nt.assert_equal(s, repr(ns['stuff']))
    
    # Check with unicode:
    s = f.format("{u}", **ns)
    nt.assert_equal(s, ns['u'])
    # This decodes in a platform dependent manner, but it shouldn't error out
    s = f.format("{b}", **ns)
        
    nt.assert_raises(NameError, f.format, '{dne}', **ns)

def eval_formatter_slicing_check(f):
    ns = dict(n=12, pi=math.pi, stuff='hello there', os=os)
    s = f.format(" {stuff.split()[:]} ", **ns)
    nt.assert_equal(s, " ['hello', 'there'] ")
    s = f.format(" {stuff.split()[::-1]} ", **ns)
    nt.assert_equal(s, " ['there', 'hello'] ")
    s = f.format("{stuff[::2]}", **ns)
    nt.assert_equal(s, ns['stuff'][::2])
    
    nt.assert_raises(SyntaxError, f.format, "{n:x}", **ns)

def eval_formatter_no_slicing_check(f):
    ns = dict(n=12, pi=math.pi, stuff='hello there', os=os)
    
    s = f.format('{n:x} {pi**2:+f}', **ns)
    nt.assert_equal(s, "c +9.869604")
    
    s = f.format('{stuff[slice(1,4)]}', **ns)
    nt.assert_equal(s, 'ell')
    
    nt.assert_raises(SyntaxError, f.format, "{a[:]}")

def test_long_substr():
    data = ['hi']
    nt.assert_equal(text.long_substr(data), 'hi')


def test_long_substr2():
    data = ['abc', 'abd', 'abf', 'ab']
    nt.assert_equal(text.long_substr(data), 'ab')

def test_long_substr_empty():
    data = []
    nt.assert_equal(text.long_substr(data), '')

def test_strip_email():
    src = """\
        >> >>> def f(x):
        >> ...   return x+1
        >> ... 
        >> >>> zz = f(2.5)"""
    cln = """\
>>> def f(x):
...   return x+1
... 
>>> zz = f(2.5)"""
    nt.assert_equal(text.strip_email_quotes(src), cln)


def test_strip_email2():
    src = '> > > list()'
    cln = 'list()'
    nt.assert_equal(text.strip_email_quotes(src), cln)
