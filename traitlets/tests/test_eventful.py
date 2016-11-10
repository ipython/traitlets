from ..traitlets import HasTraits
from ..eventful import Eventful, Bunch, Beforeback, Afterback

def test_beforeback():
	class A(HasTraits):
		e = Eventful()

	before = lambda inst, call: (inst, call)
	bb = Beforeback(A.e, 'type', before)

	inst, call = bb(A(), Bunch())
	assert call == Bunch(owner=inst,
		type='type', trait=A.e)

def test_afterback():
	class A(HasTraits):
		e = Eventful()

	a = A()
	call = Bunch(name='func', args=(), kwargs={})

	# beforeback returns a value for an afterback
	before = lambda inst, call: (inst, call)

	make_answer = lambda : Bunch(
		before=before(a, call),
		name='func', value=None)

	after = lambda inst, answer: (inst, answer)
	ab = Afterback(A.e, 'type', after)

	answer = make_answer()
	result = ab(a, answer)
	assert result == (a, answer)

	# beforeback returns a closure instead of a value
	before = lambda inst, call: lambda value: (inst, call, value)

	# afterback must be None to trigger closure
	ab = Afterback(A.e, 'type', None)

	answer = make_answer()
	result = ab(a, answer)
	assert result == (a, call, None)
