import pytest
from ..bunch import Bunch, FrozenBunch

def test_bunch():
    b = Bunch(x=5, y=10)
    assert 'y' in b
    assert 'x' in b
    assert b.x == 5
    assert b['x'] == 5
    b['a'] = 'hi'
    assert b.a == 'hi'

def test_bunch_dir():
    b = Bunch(x=5, y=10)
    assert 'x' in dir(b)
    assert 'keys' in dir(b)

def test_frozenbunch():
    b = FrozenBunch(x=1)

    pytest.raises(TypeError, "b.y = 1")
    pytest.raises(TypeError, "b['y'] = 1")
    pytest.raises(TypeError, "del b['x']")
    pytest.raises(TypeError, "del b.x")

    for attr in ('clear', 'pop', 'popitem', 'setdefault', 'update'):
        pytest.raises(AttributeError, "getattr(b, attr)")

    b = FrozenBunch(clear=1)
    assert b.clear == 1

    assert isinstance(b.thaw(), Bunch)
    assert b.thaw() == b

    # frozen bunches are hashable
    hash(b)
    {b: 1}
