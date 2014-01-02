"""
traitlets.ndarray
-----------------

An NDArray which validates on certain shape and type
constraints and notifies for interesting kinds of
inequalities id(x)==id(y), (x==y).all(), allclose(x, y). 

Example

>>> class HasArrays(HasTraits):
...     
...     # insist only on value being an instance of `numpy.ndarray`
...     a = NDArray()
...     
...     # insist on data type
...     b = NDArray(dtype='i')
...     
...     # insist on shape, e.g. three columns, N rows
...     c = NDArray(shape=(-1, 3))

"""


from traitlets.traitlets import Instance, TraitError, HasTraits

from numpy import ndarray, can_cast, allclose, dtype, array, zeros

class NDArray(Instance):
    """
    An N-dimensional array trait.

    """

    def __init__(self, **metadata):

        # How to do with just an enum?
        self.eq = metadata.pop('eq', 'id')
        valideq = 'id all allclose'.split(' ')
        if self.eq not in valideq:
            msg = 'eq=%r invalid, expect one of %r' % (self.eq, valideq)
            raise ValueError(msg)

        super(NDArray, self).__init__(
            klass=ndarray,
            args=(map(abs, metadata.get('shape', ())), ),
            allow_none=metadata.pop('allow_none', False),
            **metadata
        )

    def info(self):

        info = super(NDArray, self).info()

        dt = self.get_metadata('dtype')
        if dt:
            info += ', of %r' % (dtype(dt), )

        shape = self.get_metadata('shape')
        if shape:
            if self.get_metadata('bcast'):
                info += ', broadcasting to %r'
            else:
                info += ', with shape %r'
            info %= (shape, )

        return info

    def validate(self, obj, value):

        # this just checks instance
        val = super(NDArray, self).validate(obj, value)

        # maybe check dtype castable
        # TODO exact dtype match
        dt = self.get_metadata('dtype')
        if dt:
            if not can_cast(dtype(dt), value.dtype):
                msg = 'Expected type castable with %r, received %r'
                msg %= (dtype(dt), value.dtype)
                raise TraitError(msg)

        # maybe check shape
        shape = self.get_metadata('shape')
        if shape:
            # TODO implement implicit transpose, shape of (-1, 3), value.shape(3, -1), transpose it. 
            # TODO implement exact shape mode, len(shape) == len(value.shape)
            if len(shape) > len(value.shape):
                msg = 'Expected at least %d dimensions, received %d'
                msg %= (len(shape), len(value.shape))
                raise t.TraitError(msg)

            # broadcast mode, ignore 1s and start from right
            if self.get_metadata('bcast'):
                for i, (e, v) in enumerate(zip(reversed(shape), reversed(value.shape))):
                    if not (e==-1 or (e==1 or v==1) or e==v):
                        msg = 'Expected axis %d to have dim %d, received %d'
                        msg %= (len(value.shape) - i, e, v)
                        raise TraitError(msg)

            # normal, ignore -1 and start from left
            else:
                for i, (e, v) in enumerate(zip(shape, value.shape)):
                    if not (e==-1 or e==v):
                        msg = 'Expected axis %d to have dim %d, received %d'
                        msg %= (i, e, v)
                        raise TraitError(msg)

        return val

    def __set__(self, obj, value):

        new = self._validate(obj, value)
        old = self.__get__(obj)

        # handle array equality as requested
        if self.eq == 'id':
            same = id(new) == id(old)

        else:
            # place in common try-catch because both
            # can fail due to non-broadcastable shapes
            try:
                same = (old==new).all() if self.eq=='all' else allclose(old, new)
            except ValueError:
                same = False

        if not same:
            obj._trait_values[self.name] = new
            obj._notify_trait(self.name, old, new)
