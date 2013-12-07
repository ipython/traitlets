# encoding: utf-8
"""
Tests for was before in  traitlets.loader

Authors:

* Brian Granger
* Fernando Perez (design help)
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import pickle
import sys
from tempfile import mkstemp
from unittest import TestCase

from nose import SkipTest

from traitlets.configurable import (
    Config,
    LazyConfigValue,
    ConfigError,
)

#-----------------------------------------------------------------------------
# Actual tests
#-----------------------------------------------------------------------------


class TestConfig(TestCase):

    def test_setget(self):
        c = Config()
        c.a = 10
        self.assertEqual(c.a, 10)
        self.assertEqual('b' in c, False)

    def test_auto_section(self):
        c = Config()
        self.assertNotIn('A', c)
        assert not c._has_section('A')
        A = c.A
        A.foo = 'hi there'
        self.assertIn('A', c)
        assert c._has_section('A')
        self.assertEqual(c.A.foo, 'hi there')
        del c.A
        self.assertEqual(c.A, Config())

    def test_merge_doesnt_exist(self):
        c1 = Config()
        c2 = Config()
        c2.bar = 10
        c2.Foo.bar = 10
        c1.merge(c2)
        self.assertEqual(c1.Foo.bar, 10)
        self.assertEqual(c1.bar, 10)
        c2.Bar.bar = 10
        c1.merge(c2)
        self.assertEqual(c1.Bar.bar, 10)

    def test_merge_exists(self):
        c1 = Config()
        c2 = Config()
        c1.Foo.bar = 10
        c1.Foo.bam = 30
        c2.Foo.bar = 20
        c2.Foo.wow = 40
        c1.merge(c2)
        self.assertEqual(c1.Foo.bam, 30)
        self.assertEqual(c1.Foo.bar, 20)
        self.assertEqual(c1.Foo.wow, 40)
        c2.Foo.Bam.bam = 10
        c1.merge(c2)
        self.assertEqual(c1.Foo.Bam.bam, 10)

    def test_deepcopy(self):
        c1 = Config()
        c1.Foo.bar = 10
        c1.Foo.bam = 30
        c1.a = 'asdf'
        c1.b = range(10)
        import copy
        c2 = copy.deepcopy(c1)
        self.assertEqual(c1, c2)
        self.assertTrue(c1 is not c2)
        self.assertTrue(c1.Foo is not c2.Foo)

    def test_builtin(self):
        c1 = Config()
        c1.format = "json"
    
    def test_fromdict(self):
        c1 = Config({'Foo' : {'bar' : 1}})
        self.assertEqual(c1.Foo.__class__, Config)
        self.assertEqual(c1.Foo.bar, 1)
    
    def test_fromdictmerge(self):
        c1 = Config()
        c2 = Config({'Foo' : {'bar' : 1}})
        c1.merge(c2)
        self.assertEqual(c1.Foo.__class__, Config)
        self.assertEqual(c1.Foo.bar, 1)

    def test_fromdictmerge2(self):
        c1 = Config({'Foo' : {'baz' : 2}})
        c2 = Config({'Foo' : {'bar' : 1}})
        c1.merge(c2)
        self.assertEqual(c1.Foo.__class__, Config)
        self.assertEqual(c1.Foo.bar, 1)
        self.assertEqual(c1.Foo.baz, 2)
        self.assertNotIn('baz', c2.Foo)
    
    def test_contains(self):
        c1 = Config({'Foo' : {'baz' : 2}})
        c2 = Config({'Foo' : {'bar' : 1}})
        self.assertIn('Foo', c1)
        self.assertIn('Foo.baz', c1)
        self.assertIn('Foo.bar', c2)
        self.assertNotIn('Foo.bar', c1)
    
    def test_pickle_config(self):
        cfg = Config()
        cfg.Foo.bar = 1
        pcfg = pickle.dumps(cfg)
        cfg2 = pickle.loads(pcfg)
        self.assertEqual(cfg2, cfg)
    
    def test_getattr_section(self):
        cfg = Config()
        self.assertNotIn('Foo', cfg)
        Foo = cfg.Foo
        assert isinstance(Foo, Config)
        self.assertIn('Foo', cfg)

    def test_getitem_section(self):
        cfg = Config()
        self.assertNotIn('Foo', cfg)
        Foo = cfg['Foo']
        assert isinstance(Foo, Config)
        self.assertIn('Foo', cfg)

    def test_getattr_not_section(self):
        cfg = Config()
        self.assertNotIn('foo', cfg)
        foo = cfg.foo
        assert isinstance(foo, LazyConfigValue)
        self.assertIn('foo', cfg)

    def test_getitem_not_section(self):
        cfg = Config()
        self.assertNotIn('foo', cfg)
        foo = cfg['foo']
        assert isinstance(foo, LazyConfigValue)
        self.assertIn('foo', cfg)
    
    def test_merge_copies(self):
        c = Config()
        c2 = Config()
        c2.Foo.trait = []
        c.merge(c2)
        c2.Foo.trait.append(1)
        self.assertIsNot(c.Foo, c2.Foo)
        self.assertEqual(c.Foo.trait, [])
        self.assertEqual(c2.Foo.trait, [1])

