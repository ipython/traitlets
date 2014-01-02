
import unittest

from traitlets.traitlets import Instance, TraitError, HasTraits

from numpy import ndarray, can_cast, allclose, dtype, array, zeros

class TestEq(unittest.TestCase):
    def test_id(self):
        self.assertEqual(NDArray(eq='id').eq, 'id')
    def test_all(self):
        self.assertEqual(NDArray(eq='all').eq, 'all')
    def test_allclose(self):
        self.assertEqual(NDArray(eq='allclose').eq, 'allclose')
    def test_badeq(self):
        with self.assertRaises(ValueError):
            NDArray(eq='foo')

class TestAllowNone(unittest.TestCase):
    def test_non_default(self):
        self.assertEqual(NDArray(allow_none=True)._allow_none, True)
    def test_default(self):
        self.assertEqual(NDArray()._allow_none, False)

class TestInfo(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(NDArray().info(), 'a ndarray')
    def test_allow_none(self):
        self.assertEqual(NDArray(allow_none=True).info(), 'a ndarray or None')
    def test_shape(self):
        self.assertEqual(NDArray(shape=(-1, 2)).info(), 'a ndarray, with shape (-1, 2)')
    def test_bcast(self):
        self.assertEqual(NDArray(shape=(-1, 2), bcast=True).info(), 'a ndarray, broadcasting to (-1, 2)')
    def test_dtype(self):
        self.assertEqual(NDArray(dtype='f32').info(), "a ndarray, of dtype('float32')")

class TestValidation(unittest.TestCase):

    class TestBed(HasTraits):
        x = NDArray()
        y = NDArray(dtype='i')
        z = NDArray(dtype='f')
        A = NDArray(shape=(3, 4))
        B = NDArray(shape=(-1, 3))
        C = NDArray(shape=(1, 3, -1), bcast=True)

    def test_instance_check(self):
        tb = self.TestBed()
        with self.assertRaises(TraitError):
            tb.x = 'foo'
        x = array([1.0, 2.0])
        tb.x = x
        self.assertEqual(id(tb.x), id(x))

    def test_dtype_check(self):
        tb = self.TestBed()
        f = array([1.0], 'd')
        i = array([1], 'i')
        tb.x = f
        tb.y = f
        with self.assertRaises(TraitError):
            tb.z = i

    def test_shape_normal(self):
        tb = self.TestBed()
        tb.A = zeros((3, 4))
        with self.assertRaises(TraitError):
            tb.A = zeros((4, 5))
    
    def test_shape_free(self):
        tb = self.TestBed()
        for n in [1, 5, 10]:
            tb.B = zeros((n, 3))
        for n in [1, 5, 10]:
            tb.B = zeros((n, 3, 2, 3))
        with self.assertRaises(TraitError):
            tb.B = zeros((2, 4))

    def test_shape_bcast(self):
        tb = self.TestBed()
        tb.C = zeros((2, 3, 4))
        tb.C = zeros((5, 4, 3, 1))
        tb.C = zeros((1, 3, 1, 2))
        tb.C = zeros((1, 2, 3, 4))
        with self.assertRaises(TraitError):
            tb.C = zeros((1, 3, 2, 2))


class TestEquality(unittest.TestCase):

    class TestBed(HasTraits):
        A = NDArray(eq='id')
        _A_has_changed = False
        def _A_changed(self):
            self._A_has_changed = True

        B = NDArray(eq='all')
        _B_has_changed = False
        def _B_changed(self):
            self._B_has_changed = True

        C = NDArray(eq='allclose')
        _C_has_changed = False
        def _C_changed(self):
            self._C_has_changed = True

    def test_eq_id(self):
        tb = self.TestBed()
        x = array([1, 2, 3]).astype('f')

        # set A first time, id has changed
        tb.A = x
        self.assertTrue(tb._A_has_changed)
        tb._A_has_changed = False

        # second time, no change in id
        tb.A = x
        self.assertFalse(tb._A_has_changed)
        tb._A_has_changed = False

        # third time, id changes but not values
        tb.A = x.copy()
        self.assertTrue(tb._A_has_changed)

        # 'all' first, see change
        tb.B = x
        self.assertTrue(tb._B_has_changed)
        tb._B_has_changed = False

        # but doesn't change on copy as with id testing
        tb.B = x.copy()
        self.assertFalse(tb._B_has_changed)

        # 'allclose' first, see change
        tb.C = x
        self.assertTrue(tb._C_has_changed)
        tb._C_has_changed = False

        # doesn't change on small variations
        tb.C = x.copy() + 1e-10
        self.assertFalse(tb._C_has_changed)
        tb._C_has_changed = False

        # but does change on large variations
        tb.C = x.copy() + 1e-1
        self.assertTrue(tb._C_has_changed)

