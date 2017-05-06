import six
import types
import inspect

def getargspec(func):
    if isinstance(func, types.FunctionType) or isinstance(func, types.MethodType):
        return inspect.getargspec(func)
    else:
        # no signature introspection is available for this type
        return inspect.ArgSpec(None, 'args', 'kwargs', None)

class WatchedType(object):
    """An eventful base class purely for introspection"""
    pass


class Bunch(dict):
    # Copyright (c) Jupyter Development Team.
    # Distributed under the terms of the Modified BSD License.

    """A dict with attribute-access"""
    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            raise AttributeError(key)
    
    def __setattr__(self, key, value):
        self.__setitem__(key, value)
    
    def __dir__(self):
        # py2-compat: can't use super because dict doesn't have __dir__
        names = dir({})
        names.extend(self.keys())
        return names

    def copy(self):
        return Bunch(self)


class Spectator(object):

    def __init__(self, base, subclass):
        self.base = base
        self.subclass = subclass
        self._callback_registry = {}

    def callback(self, name, before=None, after=None):
        for name in (name if isinstance(name, (list, tuple)) else (name,)):
            if not isinstance(getattr(self.subclass, name), MethodSpectator):
                raise ValueError("No method specator for '%s'" % name)
            if before is None and after is None:
                raise ValueError("No pre or post '%s' callbacks were given" % name)
            elif ((before is not None and not callable(before))
                or (after is not None and not callable(after))):
                raise ValueError("Expected a callables")

            if name in self._callback_registry:
                l = self._callback_registry[name]
            else:
                l = []
                self._callback_registry[name] = l
            l.append((before, after))

    def remove_callback(self, name, before=None, after=None):
        if name in self._callback_registry:
            l = self._callback_registry[name]
        else:
            l = []
            self._callback_registry[name] = l
        l.remove((before, after))

    def wrapper(self, name, args, kwargs):
        """A callback made prior to calling the given base method

        Parameters
        ----------
        name: str
            The name of the method that will be called
        args: tuple
            The arguments that will be passed to the base method
        kwargs: dict
            The keyword args that will be passed to the base method
        """
        if name in self._callback_registry:
            beforebacks, afterbacks = zip(*self._callback_registry.get(name, []))

            hold = []
            for b in beforebacks:
                if b is not None:
                    call = Bunch(name=name,
                        kwargs=kwargs.copy(),
                        args=args[1:])
                    v = b(args[0], call)
                else:
                    v = None
                hold.append(v)

            out = getattr(self.base, name)(*args, **kwargs)

            for a, bval in zip(afterbacks, hold):
                if a is not None:
                    a(args[0], Bunch(before=bval,
                        name=name, value=out))
                elif callable(bval):
                    # the beforeback's return value was an
                    # afterback that expects to be called
                    bval(out)
            return out
        else:
            return getattr(self.base, name)(*args, **kwargs)


class MethodSpectator(object):

    _compile_count = 0
    _src_str = """def {name}({signature}):
    args, varargs, kwargs = [{args}], {varargs}, {keywords}
    args.extend(varargs)
    return args[0].instance_spectator.wrapper(
        '{name}', tuple(args), kwargs.copy())"""

    def __init__(self, base, name):
        self.base, self.name = base, name
        aspec = getargspec(self.basemethod)
        self.defaults = aspec.defaults
        self.code = self._code(aspec)

    @property
    def basemethod(self):
        return getattr(self.base, self.name)

    def _code(self, aspec):
        # list values were repred - remove quotes
        args = str(aspec.args)[1:-1].replace("'", "")
        signature = args + (", " if args else "")
        if aspec.varargs is not None:
            signature += '*' + aspec.varargs + ', '
        if aspec.keywords is not None:
            signature += '**' + aspec.keywords
        if signature.endswith(', '):
            signature = signature[:-2]
        src = self._src_str.format(name=self.name,
            signature=signature, args=args,
            varargs=aspec.varargs or (),
            keywords=aspec.keywords or {})
        filename = "watched-method-gen-%d" % self._compile_count
        code = compile(src, filename, 'single')
        MethodSpectator._compile_count += 1
        return code

    def new_wrapper(self, inst):
        evaldict = {}
        eval(self.code, evaldict)
        # extract wrapper by name
        new = evaldict[self.name]
        # assign docstring and defaults
        new.__doc__ = self.basemethod.__doc__
        new.__defaults__ = self.defaults
        return types.MethodType(new, inst)

    def __call__(self, *args, **kwargs):
        return self.new_wrapper(None, self.base)(*args, **kwargs)

    def __get__(self, inst, cls):
        if inst is None:
            return self
        elif inst.instance_spectator is None:
            return types.MethodType(self.basemethod, inst)
        else:
            return self.new_wrapper(inst)


def watched_type(name, base, *notify_on):
    classdict = base.__dict__.copy()

    def __new__(cls, *args, **kwargs):
        inst = base.__new__(cls, *args, **kwargs)
        object.__setattr__(inst, 'instance_spectator', Spectator(base, cls))
        return inst

    classdict['__new__'] = __new__

    for method in notify_on:
        if not hasattr(base, method):
            raise ValueError("Cannot notify on '%s', because '%s' "
                "instances lack this method" % (method, base.__name__))
        else:
            classdict[method] = MethodSpectator(base, method)

    return type(name, (base, WatchedType), classdict)
