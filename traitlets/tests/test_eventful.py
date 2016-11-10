from ..traitlets import HasTraits
from ..eventful import Eventful, Bunch, Beforeback, Afterback, Redirect
from ..utils import spectate

def test_beforeback():
	class A(HasTraits):
		# not a functional trait
		e = Eventful()

	before = lambda inst, call: (inst, call)
	bb = Beforeback(A.e, 'type', before)

	inst, call = bb(A(), Bunch())
	assert call == Bunch(owner=inst,
		type='type', trait=A.e)

def test_afterback_value():
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
	ab = Afterback(A.e, 'type', after=after)

	answer = make_answer()
	result = ab(a, answer)
	assert result == (a, answer)

def test_afterback_closure():
	class A(HasTraits):
		# not a functional trait
		e = Eventful()

	a = A()
	call = Bunch(name='func', args=(), kwargs={})

	# beforeback returns a closure instead of a value
	before = lambda inst, call: lambda value: (inst, call, value)

	make_answer = lambda : Bunch(
		before=before(a, call),
		name='func', value=None)

	# afterback must be None to trigger closure
	ab = Afterback(A.e, 'type', after=None)

	result = ab(a, make_answer())
	assert result == (a, call, None)

def test_redirect():
	class A(object):
		called_func_b = False
		def func_a(self, a):
			return a
		def func_b(self, b):
			self.called_func_b = True
			return b

	wa = spectate.watched_type('WA', A, 'func_a', 'func_b')()
	# beforeback returns a closure that returns method output
	def last_before(inst, call):
		def last_after(value):
			print(value)
			return value
		return last_after

	# register two beforebacks to test that
	# the redirect returns results from both
	wa.instance_spectator.callback('func_b', before=last_before)
	wa.instance_spectator.callback('func_b', before=last_before)

	def first_before(inst, call):
		# redirect to trigger the before/after backs of func_b
		return Redirect(inst, 'func_a', 'func_b', call.args, call.kwargs)

	captured_from_redirect = []

	def first_after(inst, answer):
		out = answer.before(answer.value)
		captured_from_redirect.extend(out)
		return out

	wa.instance_spectator.callback('func_a', before=first_before, after=first_after)

	wa.func_a(1)

	assert captured_from_redirect == [1, 1]
	assert not wa.called_func_b
