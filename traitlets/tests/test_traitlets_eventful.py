from unittest import TestCase
from traitlets import *
from traitlets.utils.bunch import Bunch
from contextlib import contextmanager


class TestEventfulBase(TestCase):

    class Event(Bunch):

        def __init__(self, name, owner, value, depth, etype):
            self.name = name
            self.owner = owner
            self.value = value
            self.depth = depth
            self.type = etype
            self.events = []

        def __call__(self, **data):
            self.events.append(data)
            return self

    def setUp(self):
        traits = {}
        for name in dir(self):
            if name.startswith("_") and not name.startswith("__"):
                try:
                    v = getattr(type(self), name)
                except:
                    pass
                else:
                    if isinstance(v, TraitType):
                        traits[name[1:]] = v
        has_traits_type = type("Object", (HasTraits,), traits)
        self.obj = has_traits_type()

    @contextmanager
    def event_tester(self, name, value, depth, etype):
        log = []
        event = self.Event(name, self.obj, value, depth, etype)

        f = lambda change: log.append(change)
        self.obj.observe(f, name, etype)

        try:
            yield event
        finally:
            self.obj.unobserve(f, name, etype)

        assert len(log) == 1, "get more events than expected"

        logged_events = log[0].pop("events")
        test_events = event.pop("events")

        assert event == log[0]

        found = []
        for e in test_events:
            try:
                logged_events.remove(e)
            except:
                assert False, e
        if logged_events:
            assert False, "extra events occured - %r" % logged_events


class TestEventfulList(TestEventfulBase):

    _l = List(
        eventful=True,
    )
    _l_of_i = List(
        Int(castable=float),
        eventful=True,
    )
    _l_of_l = List(
        List(eventful=True),
        default_value=[[]],
        eventful=True,
    )

    def test_setitem(self):
        self.obj.l.append(1)
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l[0] = 2
            t(old=1, new=2, index=0)

    def test_delitem(self):
        self.obj.l.extend([1, 2])
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            del self.obj.l[0]
            t(index=0, old=1, new=2)
            t(index=1, old=2, new=Undefined)
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            del self.obj.l[0]
            t(index=0, old=2, new=Undefined)

    def test_append(self):
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.append(1)
            t(old=Undefined, new=1, index=0)

    def test_extend(self):
        new = [1, 2, 3]
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.extend(new)
            for i, x in enumerate(new):
                t(old=Undefined, new=x, index=i)

    def test_insert(self):
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.insert(0, 2)
            t(index=0, old=Undefined, new=2)
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.insert(0, 1)
            t(index=0, old=2, new=1)
            t(index=1, old=Undefined, new=2)

    def test_remove(self):
        self.obj.l.extend([1, 2])
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.remove(1)
            t(index=0, old=1, new=2)
            t(index=1, old=2, new=Undefined)
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.remove(2)
            t(index=0, old=2, new=Undefined)

    def test_sort(self):
        self.obj.l.extend([1, 2, 3])
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.sort(reverse=True)
            t(old=1, new=3, index=0)
            t(old=3, new=1, index=2)
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.sort()
            t(old=3, new=1, index=0)
            t(old=1, new=3, index=2)
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.sort(key=lambda x: -x)
            t(old=1, new=3, index=0)
            t(old=3, new=1, index=2)

    def test_reverse(self):
        self.obj.l.extend([1, 2, 3])
        with self.event_tester("l", self.obj.l, 0, "mutation") as t:
            self.obj.l.reverse()
            t(old=1, new=3, index=0)
            t(old=3, new=1, index=2)

    def test_coercive_subtrait(self):
        with self.event_tester("l_of_i", self.obj.l_of_i, 0, "mutation") as t:
            self.obj.l_of_i.append(1.5)
            t(index=0, old=Undefined, new=1.5)
            t(index=0, old=1.5, new=1)

    def test_coercive_subtrait(self):
        with self.event_tester("l_of_i", self.obj.l_of_i, 0, "mutation") as t:
            self.obj.l_of_i.append(1.5)
            t(index=0, old=Undefined, new=1.5)
            t(index=0, old=1.5, new=1)

    def test_nested_eventful(self):
        with self.event_tester("l_of_l", self.obj.l_of_l[0], 1, "mutation") as t:
            self.obj.l_of_l[0].append(1)
            t(index=0, old=Undefined, new=1)
