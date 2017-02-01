import inspect
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


class Thing(object):
	def func(inst, a, b, c=None, d=None, *e, **f):
		return inst,  a, b, c, d, e, f

def check_answer(checklist, inst, name, a, b, c=None, d=None, *e, **f):
	args, kwargs = condense(a, b, c, d, *e, **f)
	checklist.append(Bunch(
		name=name,
		value=(inst, a, b, c, d, e, f),
		before=Bunch(
			name=name,
			args=args,
			kwargs=kwargs))
	)
	getattr(inst, name)(a, b, c, d, *e, **f)

condense = lambda *a, **kw: (a, kw)


def test_beforeback_afterback():
	checklist = []

	WatchedThing = watched_type('WatchedThing', Thing, 'func')
	wt = WatchedThing()

	# callback stores call information
	def beforeback(inst, call):
		return call
	def afterback(inst, answer):
		assert checklist[-1] == answer

	wt.instance_spectator.callback('func',
		before=beforeback, after=afterback)

	check_answer(checklist, wt, 'func', 1, 2, c=3)
	check_answer(checklist, wt, 'func', 1, 2, d=3)
	check_answer(checklist, wt, 'func', 1, 2, 3, 4, 5)
	check_answer(checklist, wt, 'func', 1, 2, d=3, f=4)

def test_callback_closure():
	checklist = []

	WatchedThing = watched_type('WatchedThing', Thing, 'func')
	wt = WatchedThing()

	def callback(inst, call):
		def closure(value):
			assert (checklist[-1] == Bunch(
				name=call.name, value=value,
				before=call))

	wt.instance_spectator.callback('func', callback)

	check_answer(checklist, wt, 'func', 1, 2, c=3)
	check_answer(checklist, wt, 'func', 1, 2, d=3)
	check_answer(checklist, wt, 'func', 1, 2, 3, 4, 5)
	check_answer(checklist, wt, 'func', 1, 2, d=3, f=4)
