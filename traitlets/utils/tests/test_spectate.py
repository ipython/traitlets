import inspect
from unittest import TestCase
from ..spectate import watched_type, WatchedType, MethodSpectator, Spectator, Bunch

def test_watched_type():
	WatchedList = watched_type(
		'WatchedList', list, 'append')

	assert WatchedList.__name__ == 'WatchedList'
	assert issubclass(WatchedList, list)
	assert issubclass(WatchedList, WatchedType)
	assert isinstance(WatchedList.append, MethodSpectator)

	wl = WatchedList()
	assert hasattr(wl, 'instance_spectator')
	assert isinstance(wl.instance_spectator, Spectator)

def test_method_spectator():
	MethodSpectator._compile_count = 0
	WatchedList = watched_type(
		'WatchedList', list, 'append')
	assert MethodSpectator._compile_count == 1
	append = WatchedList.append

	assert append.basemethod is list.append
	assert append.name == 'append'

	wl = WatchedList()
	wl.append(1)
	wl.append(2)
	assert wl == [1, 2]

	class Thing(object):
		def func(self, a, b, c=None, d=None, *e, **f):
			pass

	WatchedThing = watched_type('WatchedThing', Thing, 'func')
	assert MethodSpectator._compile_count == 2
	assert (inspect.getargspec(Thing().func) ==
		inspect.getargspec(WatchedThing().func))

def expected_answer(func, *args, **kwargs):
	name = func.__name__
	inspect.getargspec(func)


def test_spectator():
	hold = []
	def beforeback(inst, call):
		return call
	def afterback(inst, answer):
		hold.append(answer)

	class Thing(object):
		def func(self, a, b, c=None, d=None, *e, **f):
			return self, a, b, c, d, e, f

	condense = lambda *a, **kw: (a, kw)

	def verify_answer(inst, name, a, b, c=None, d=None, *e, **f):
		getattr(inst, name)(a, b, c, d, *e, **f)
		args, kwargs = condense(inst, a, b, c, d, *e, **f)
		assert hold[-1] == Bunch(
			name=name,
			value=(inst, a, b, c, d, e, f),
			before=Bunch(
				name=name,
				args=args,
				kwargs=kwargs))

	WatchedThing = watched_type('WatchedThing', Thing, 'func')
	wt = WatchedThing()

	wt.instance_spectator.callback('func',
		before=beforeback, after=afterback)

	verify_answer(wt, 'func', 1, 2, c=3)
	verify_answer(wt, 'func', 1, 2, d=3)
	verify_answer(wt, 'func', 1, 2, 3, 4, 5)
	verify_answer(wt, 'func', 1, 2, d=3, f=4)
