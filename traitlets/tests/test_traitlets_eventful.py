import spectate
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

        assert len(log) == 1, "expected 1 event, got %s instead" % len(log)

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


class TestMutable(TestEventfulBase):

    def test_eventful_flag(self):
        assert Mutable(list, eventful=True).eventful is True
        assert Mutable(list).eventful is False

    def test_copy_default(self):
        class MyClass(HasTraits):
            l1 = Mutable(list, default_value=[])
            l2 = Mutable(list, default_value=[])
        mc = MyClass()
        assert mc.l1 == []
        assert mc.l2 == []
        assert mc.l1 is not mc.l2

    def test_iter_events(self):

        class MyMutableTrait(Mutable):

            events = {
                "nickname_1": "method_1",
                "nickname_2": ["method_1", "method_2"],
            }

            def _before_nickname_1(self, value, call, notify): pass
            def _before_nickname_2(self, value, call, notify): pass
            def _after_nickname_2(self, value, call, notify): pass

        mmt = MyMutableTrait(object)

        assert set(mmt.iter_events()) == {
            ("method_1", mmt._before_nickname_1, None),
            ("method_1", mmt._before_nickname_2, mmt._after_nickname_2),
            ("method_2", mmt._before_nickname_2, mmt._after_nickname_2),
        }

    def test_register_events(self):

        class EventfulElements(Mutable):

            events = {
                "setitem": "__setitem__",
                "delitem": "__delitem__",
            }

            def _before_setitem(self, value, call, notify): pass
            def _after_setitem(self, value, call, notify): pass
            def _before_delitem(self, value, call, notify): pass
            def _after_delitem(self, value, call, notify): pass

        class MyClass(HasTraits):
            l = EventfulElements(list, eventful=True, default_value=[])

        mc = MyClass()
        spectator = spectate.watcher(mc.l)
        spectator._callback_registry["__setitem__"] == [
            (MyClass.l._before_setitem, MyClass.l._after_setitem)
        ]
        spectator._callback_registry["__delitem__"] == [
            (MyClass.l._before_delitem, MyClass.l._after_delitem)
        ]

    def test_unregister_events(self):
        class my_list(list): pass
        class EventfulElements(Mutable):

            events = {
                "setitem": "__setitem__",
                "delitem": "__delitem__",
            }

            def _before_setitem(self, value, call, notify): pass
            def _after_setitem(self, value, call, notify): pass
            def _before_delitem(self, value, call, notify): pass
            def _after_delitem(self, value, call, notify): pass

        class MyClass(HasTraits):
            l = EventfulElements(my_list,
                eventful=True, castable=list,
                default_value=[])

        mc = MyClass()
        old = mc.l
        mc.l = my_list()
        assert not spectate.watcher(old)._callback_registry

    def test_no_eventful_setattr_for_mutable_builtins(self):
        class MyClass(HasTraits):
            l = Mutable(list, eventful=True, default_value=[])
        with self.assertRaises(TraitError):
            MyClass().l = []

    def test_notify(self):

        validated = []

        class EventfulElements(Mutable):

            events = {
                "append": "append",
            }

            def _before_append(self, value, call, notify):
                notify("before", info=0)
                notify("before", info=1)

            def _after_append(self, value, answer, notify):
                notify("after", info=0)

            def _validate_mutation(self, owner, value):
                validated.append(True)

        before = []
        after = []

        class MyClass(HasTraits):
            l = EventfulElements(list, eventful=True, default_value=[])

            @observe("l", type="before")
            def _before(self, change):
                change.value = change.value[:]
                before.append(change)

            @observe("l", type="after")
            def _after(self, change):
                change.value = change.value[:]
                after.append(change)

        mc = MyClass()
        mc.l.append(1)

        assert validated
        assert len(before) == 1
        assert len(after) == 1

        before = before[0]
        after = after[0]

        assert len(before.events) == 2
        assert len(after.events) == 1

        assert before.events[0] == {"info": 0}
        assert before.events[1] == {"info": 1}
        assert after.events[0] == {"info": 0}

        del before["events"]
        del after["events"]

        assert before == dict(
            name="l",
            value=[],
            depth=0,
            owner=mc,
            type="before",
        )

        assert after == dict(
            name="l",
            value=[1],
            depth=0,
            owner=mc,
            type="after",
        )


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


class TestEventfulSet(TestEventfulBase):

    _s = Set(eventful=True)

    _s_of_i = Set(
        Int(castable=float),
        eventful=True,
    )

    def test_add(self):
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            self.obj.s.add(1)
            t(old=set(), new={1})

    def test_update(self):
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            self.obj.s.update([1, 2, 3])
            t(old=set(), new={1, 2, 3})

    def test_clear(self):
        self.obj.s.update([1, 2, 3])
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            self.obj.s.clear()
            t(new=set(), old={1, 2, 3})

    def test_remove(self):
        self.obj.s.update([1, 2, 3])
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            self.obj.s.remove(1)
            t(new=set(), old={1})

    def test_pop(self):
        self.obj.s.update([1, 2, 3])
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            x = self.obj.s.pop()
            t(new=set(), old={x})

    def test_discard(self):
        self.obj.s.update([1, 2, 3])
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            self.obj.s.discard(1)
            self.obj.s.discard(4)
            t(new=set(), old={1})

    def test_difference_update(self):
        self.obj.s.update([1, 2, 3])
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            self.obj.s.difference_update([1, 2, 4])
            t(new=set(), old={1, 2})

    def test_intersection_update(self):
        self.obj.s.update([1, 2, 3])
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            self.obj.s.intersection_update([2, 4])
            t(new=set(), old={1, 3})

    def test_symmetric_difference_update(self):
        self.obj.s.update([1, 2, 3])
        with self.event_tester("s", self.obj.s, 0, "mutation") as t:
            self.obj.s.symmetric_difference_update([2, 4])
            t(new={4}, old={2})

    def test_coercive_subtrait(self):
        with self.event_tester("s_of_i", self.obj.s_of_i, 0, "mutation") as t:
            self.obj.s_of_i.add(1.5)
            t(new={1.5}, old=set())
            t(new={1}, old={1.5})


class TestEventfulDict(TestEventfulBase):

    _d = Dict(eventful=True)

    def test_setitem(self):
        with self.event_tester("d", self.obj.d, 0, "mutation") as t:
            self.obj.d["a"] = 1
            t(key="a", old=Undefined, new=1)

    def test_setdefault(self):
        with self.event_tester("d", self.obj.d, 0, "mutation") as t:
            self.obj.d.setdefault("a", 1)
            self.obj.d.setdefault("a", 2)
            t(key="a", old=Undefined, new=1)

    def test_delitem(self):
        self.obj.d["a"] = 1
        with self.event_tester("d", self.obj.d, 0, "mutation") as t:
            del self.obj.d["a"]
            t(key="a", old=1, new=Undefined)

    def test_pop(self):
        self.obj.d["a"] = 1
        with self.event_tester("d", self.obj.d, 0, "mutation") as t:
            self.obj.d.pop("a")
            self.obj.d.pop("a", None)
            t(key="a", old=1, new=Undefined)

    def test_update(self):
        self.obj.d["b"] = 0
        with self.event_tester("d", self.obj.d, 0, "mutation") as t:
            self.obj.d.update(a=1, b=2)
            t(key="a", old=Undefined, new=1)
            t(key="b", old=0, new=2)

    def test_clear(self):
        self.obj.d.update(a=1, b=2)
        with self.event_tester("d", self.obj.d, 0, "mutation") as t:
            self.obj.d.clear()
            t(key="a", old=1, new=Undefined)
            t(key="b", old=2, new=Undefined)
