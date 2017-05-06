from .utils.bunch import Bunch
from contextlib import contextmanager
from .utils.spectate import watched_type
from .traitlets import (TraitType, Dict, List,
    Undefined, equivalent, Set, TraitError)


class Callback(object):

    def __init__(self, owner, trait, etype, callback):
        self.owner = owner
        self.trait = trait
        self.etype = etype
        self.func = callback


class Beforeback(Callback):

    def __call__(self, inst, call):
        call = call.copy()
        call.update(
            trait=self.trait,
            owner=self.owner,
            type=self.etype)
        return self.func(inst, call)


class Afterback(Callback):

    def __call__(self, inst, answer):
        if self.func is None:
            result = answer['before']
            if (isinstance(result, Redirect)
                and result.origin is not None):
                origin = result.origin
            else:
                origin = self.etype

            event = (result(answer.value) if
                callable(result) else result)
        else:
            origin = self.etype
            event = self.func(inst, answer)
        if None not in (origin, event):
            self.owner.notify_change(Bunch(
                type=origin, event=event,
                name=self.trait.name,
                owner=self.owner))
        return event


class Redirect(object):

    def __init__(self, origin, target, inst, args, kwargs):
        self.origin = origin
        registry = inst.instance_spectator._callback_registry
        # Eventful._setup_events registers first
        b, a = registry.get(target, [(None, None)])[0]

        if b is not None:
            call = Bunch(name=target,
                kwargs=kwargs.copy(),
                args=args[:])
            bval = b(inst, call)
        else:
            bval = None

        if a is not None:
            self.trigger = lambda value: a(inst, Bunch(
                before=bval, name=target, value=value))
        elif callable(bval):
            self.trigger = bval

    def __call__(self, value):
        # trigger afterbacks
        return self.trigger(value)

    @staticmethod
    def trigger(value):
        pass


class Eventful(TraitType):

    read_only = True
    event_map = {}
    type_name = 'WatchedType'

    def __new__(cls, default_value, *args, **kwargs):
        new = super(Eventful, cls).__new__
        if new is object.__new__:
            self = new(cls)
        else:
            self = new(cls, default_value, *args, **kwargs)
        if getattr(self, 'klass', None) is None:
            self.klass = type(default_value)
        self._active_events = []
        # register builtin events before
        # returning object to the user
        self._setup_events()
        return self

    def _setup_events(self):
        for name, on in self.event_map.items():
            for method in (on if isinstance(on, (tuple, list)) else (on,)):
                before = getattr(self, "_before_"+name, None)
                after = getattr(self, "_after_"+name, None)
                if not (before is None and after is None):
                    self.event(type=name, on=method,
                        before=before, after=after)

    def event(self, type, on, before=None, after=None):
        if before is None and after is None:
            raise ValueError("No callbacks were provided for the event")
        for method in (on if isinstance(on, (list, tuple)) else (on,)):
            self._active_events.append((type, method, before, after))
        return self

    def class_init(self, cls, name):
        super(Eventful, self).class_init(cls, name)
        if self.klass is None:
            raise TypeError("Eventful types must have a 'klass' attribute")
        self.watched_type = watched_type(self.type_name,
            self.klass, *(e[1] for e in self._active_events))

    def _validate(self, owner, value):
        try:
            owner._trait_values[self.name].instance_spectator = None
        except KeyError:
            pass
        value = super(Eventful, self)._validate(owner, value)
        if value is not None:
            value = self.watched_type(value)
            self._register_defined_events(owner, value)
        return value

    def _register_defined_events(self, owner, value):
        for e in self._active_events:
            etype, on, before, after = e
            value.instance_spectator.callback(on,
                before=Beforeback(owner, self, etype, before),
                after=Afterback(owner, self, etype, after))

    def redirect_once(self, origin, target, inst, args=(), kwargs={}):
        value = self.event_map[target]
        target = value[0] if isinstance(value, (list, tuple)) else value
        return Redirect(origin, target, inst, args, kwargs)

    def redirect(self, origin, target, inst, args=None, kwargs=None):
        value = self.event_map[target]
        target = value[0] if isinstance(value, (list, tuple)) else value

        if args is None and kwargs is not None:
            args = [() for i in range(len(kwargs))]
        elif kwargs is None and args is not None:
            kwargs = [{} for i in range(len(args))]
        if len(args) != len(kwargs):
            raise ValueError("Uneven args (%s) and kwargs (%s) lists")

        redirects = [Redirect(origin, target, inst, a, kw)
            for a, kw in zip(args, kwargs)]
        def redirect(value):
            events = []
            for r in redirects:
                events.append(r(value))
            return events
        return redirect


class EDict(Eventful, Dict):

    event_map = {
        'setitem': ('__setitem__', 'setdefault'),
        'delitem': ('__delitem__', 'pop'),
        'update': 'update',
        'clear': 'clear',
    }
    type_name = 'edict'

    def _before_update(self, inst, call):
        new = call.args[0]
        new.update(call.kwargs)
        call_list = []
        return self.redirect(
            None, 'setitem', inst,
            args=new.items())

    def _before_clear(self, inst, call):
        return self.redirect(
            None, 'delitem', inst,
            args=inst.keys())

    @staticmethod
    def before_setitem(inst, call):
        """Expect call.args[0] = key"""
        key, old = call.args[0], inst.get(call.args[0], Undefined)
        def after_setitem(returned):
            new = inst.get(key, Undefined)
            if not equivalent(old, new):
                return Bunch(key=key, old=old, new=new)
        return after_setitem

    _before_setitem = before_setitem
    _before_delitem = before_setitem


class EList(Eventful, List):

    event_map = {
        'append': 'append',
        'extend': 'extend',
        'setitem': '__setitem__',
        'reverse': 'reverse',
        'sort': 'sort',
    }
    type_name = 'elist'

    def before_setitem(self, inst, index):
        try:
            old = inst[index]
        except:
            old = Undefined
        def after_setitem(returned):
            try:
                new = inst[index]
            except:
                new = Undefined
            if not equivalent(old, new):
                return Bunch(index=index, old=old, new=new)
        return after_setitem

    def _before_setitem(self, inst, call):
        return self.before_setitem(inst, call.args[0])

    def rearrangement(self, origin, inst):
        return self.redirect(origin, 'setitem', inst,
            args=[(i,) for i in range(len(inst))])

    def _before_reverse(self, inst, call):
        return self.rearrangement(inst, 'reverse')

    def _before_sort(self, inst, call):
        return self.rearrangement(inst, 'sort')

    def _before_extend(self, inst, call):
        size = len(call.args[0])
        return self.redirect('append', 'setitem', inst,
            args=[(i+len(inst),) for i in range(size)])

    def _before_append(self, inst, call):
        return self.redirect_once('append',
            'setitem', inst, (len(inst),))
