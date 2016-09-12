import sys
import copy
import inspect
import warnings
from contextlib import contextmanager

#-----------------------------------------------------------------------------
# General Utilities
#-----------------------------------------------------------------------------

def _last_module_name():
    if __name__ == "__main__":
        return __name__
    else:
        this = __name__
        module = __name__
        f = inspect.currentframe()
        while module == this:
            f = f.f_back
            module = f.f_globals["__name__"]
        return module

def _filtered_modules_stack(modules):
    out = []
    for frame in [s[0] for s in inspect.stack()]:
        name = frame.f_globals["__name__"]
        if name in modules:
            out.append(name)
        if name == "__main__":
            break
    return out

#-----------------------------------------------------------------------------
# Warning Function and Warning Types
#-----------------------------------------------------------------------------

class LiabilityWarning(UserWarning): pass

class ProvisionalWarning(FutureWarning):
    """A warning for unstable or temporary features"""

    template = "%r is a provisional feature - its use is not recommended"

    def __init__(self, feature, *args):
        """Warn users about the presence an unstable or temporary feature.

        Provisional features are not guaranteed to exist over any period of time in
        the future, whether that be in the same form, or at all. Users are reponcible


        Parameters
        ----------
        feature : str
            A brief, yet informative name for the provisional feature.
        *args : any
            Any other warning arguments.
        """
        super(ProvisionalWarning, self).__init__(self.template % feature, *args)

# all warnings for provisional features raise by default
warnings.simplefilter("error", category=ProvisionalWarning)

def warn(feature, *args):
    with warnings.catch_warnings():
        for m in _filtered_modules_stack(_module_filters):
            for name, warningfilter in _module_filters[m].items():
                if warningfilter['action'] == 'error':
                    block(**{name: warningfilter['priority']})
                elif warningfilter['action'] == 'ignore':
                    allow(**{name: warningfilter['priority']})
                else:
                    raise ValueError("unknown action '%s'"
                        % warningfilter['priority'])
        warnings.warn(ProvisionalWarning(feature, *args), stacklevel=2)

#-----------------------------------------------------------------------------
# Help Utility
#-----------------------------------------------------------------------------

_help = {}

def set_help(docstring, module=None):
    """Set a help docstring for a module with provisional features

    Parameters
    ----------
    docstring : str
        The docstring explaining all the module's provisional features.
    module : str
        The full module name the features are contained in. If no module
        is given, the module of the frame which called this function is
        used instead.
    """
    if module is None:
        module = inspect.currentframe().f_back.f_globals["__name__"]
    _help[module] = docstring

def help(module=None):
    """Get a docstring explaining the provisional features of a module

    Parameters
    ----------
    module : str
        The full module name provisional features are contained in.
        If given as None, then a tuple of the all module names for
        which docstrings have been written, will be returned."""
    if module is None:
        return tuple(_help.keys())
    try:
        return _help[module]
    except:
        raise KeyError("No docstring for '%s'" % module)

#-----------------------------------------------------------------------------
# Warning Filter Utilities
#-----------------------------------------------------------------------------

def allowed_features():
    """Get a list of features which are allowed in the current context"""
    return _public_filter_dict("ignore")

def blocked_features():
    """Get a list of features which are blocked in the current context"""
    return _public_filter_dict("error")

def active_filters():
    """Get a dict defining the active provisional filters in this context"""
    return {n: d.copy() for n, d in _global_filters.items()}

def _public_filter_dict(action):
    return set(n for n, d in
        _global_filters.items()
        if d["action"] == action).union(
        n for m in _filtered_modules_stack(_module_filters)
        for n, d in _module_filters[m] if d["action"] == action)

def _merge_non_priorities(names, priorities):
    """merge feature names into priorities"""
    for n in names:
        if n in priorities:
            raise ValueError("Conflicting feature "
                "'%s' in *names and **priorities")
        else:
            priorities[n] = None

def acknowledge_liability(cls):
    """Acknowledge responcibility to supresses ``LiabilityWarnings``"""
    user_acknowledges = ("Provisional features are subject to change without "
        "warning, and only intended for experimental use. By envoking this "
        "method, the user assumes all responsibility for supporting them until "
        "their provisional status has been revoked.")
    warnings.warn(user_acknowledges, LiabilityWarning)
    warnings.simplefilter("ignore", category=LiabilityWarning)

def _liability_warning(features):
    if len(features) == 0 or "ALL" in features:
        fill = ("provisional features", "them", "their")
    elif len(features) == 1:
        fill = ("%r" % features[0], "it", "its")
    elif len(features) == 2:
        fill = ("%r and %r" % features, "them", "their")
    else:
        fill = (str(features[:-1])[1:-1] + ", and %r" % features[-1],)
    user_acknowledges = ("By specifying that %s be enabled, the user acknowledges "
        "that they have assumed all responsibility for supporting %s until %s "
        "provisional status has been revoked." % fill)
    warnings.warn(user_acknowledges, LiabilityWarning)

#-----------------------------------------------------------------------------
# Module Warning Filter Functions
#-----------------------------------------------------------------------------

_module_filters = {}

def this_module_allows(*names, **priorities):
    _merge_non_priorities(names, priorities)
    _liability_warning(list(priorities.keys()))
    _filter_module_features("ignore", priorities)

def this_module_blocks(*names, **priorities):
    _merge_non_priorities(names, priorities)
    _liability_warning(list(priorities.keys()))
    _filter_module_features("error", priorities)

def _filter_module_features(action, features):
    if not features or "ALL" in features:
        _add_module_filter("ALL", features.get("ALL", None),
            action=action, category=ProvisionalWarning)
    else:
        for name in features:
            _add_module_filter(name, features[name], action=action,
                message=("^(?:" + ProvisionalWarning.template
                    % name + "|" + name + ")$"),
                category=ProvisionalWarning)

def _add_module_filter(name, priority, **kwargs):
    """Add a new feature filter

    If a filter for the feature already exists, the
    new one only overrides it if the new one has a
    higher priority the the preexisting one. If that
    is True, warnings.filterwarnings is called with
    **kwargs and the filter's action and prioritty is
    stored in a global ``_module_filters`` dictionary
    """
    f = _last_module_name()
    if f in _module_filters:
        cache = _module_filters[f]
    else:
        cache = {}
        _module_filters[f] = cache
    if name in cache:
        fdict = cache[name]
        p = fdict["priority"]
    else:
        fdict = {}
        cache[name] = fdict
        p = None
    if p is None or (p != 0 and p <= priority):
        fdict.update(action=kwargs["action"],
            priority=priority)

#-----------------------------------------------------------------------------
# Global / Contextual Warning Filter Functions
#-----------------------------------------------------------------------------

_global_filters = {}

@contextmanager
def _restore_global_filters():
    global _global_filters
    hold = copy.deepcopy(_global_filters)
    yield
    _global_filters = hold

@contextmanager
def allowed_context(*names, **priorities):
    """Create a context where the given provisional features are allowed

    Each allowed feature cause a warning filter to be inserted in
    ``warnings.filters`` that ignores all ProvisionalWarnings for
    that specific feature. Alternatively, the string ``"ALL"``
    can be specified in which case a blanket filter for all
    ProvisionalWarnings is inserted.

    Parameters
    ----------
    *names : str
        A seris of feature names which will be allowed with
        no priority (i.e. any subsiquent filter can override
        the allowances made here).
    **priorities : int or None
        A series of priority values keyed on feature names.
        Each feature will be allowed with its given priority.

    Priority Values
    ---------------
    ``0`` : The highest priority value
        A filter with a priority of ``0`` cannot be overriden,
        even by another ``0`` priority filter.
    ``int`` : Meduim priority values
        Filters with integer priorities (not ``0``) can override
        any filter with a value less-than or equal to its value.
    ``None`` : The lowest priority value
        A filter with a priority of ``None`` can always be
        overriden, even by another ``None`` priority filter
    """
    with _restore_global_filters():
        with warnings.catch_warnings():
            allow(*names, **priorities)
            yield

def allow(*names, **priorities):
    """Allow the given prosivional features
    
    Parameters
    ----------
    *names : str
        A seris of feature names which will be allowed with
        no priority (i.e. any subsiquent filter can override
        the allowances made here).
    **priorities : int or None
        A series of priority values keyed on feature names.
        Each feature will be allowed with its given priority.

    Priority Values
    ---------------
    ``0`` : The highest priority value
        A filter with a priority of ``0`` cannot be overriden,
        even by another ``0`` priority filter.
    ``int`` : Meduim priority values
        Filters with integer priorities (not ``0``) can override
        any filter with a value less-than or equal to its value.
    ``None`` : The lowest priority value
        A filter with a priority of ``None`` can always be
        overriden, even by another ``None`` priority filter
    """
    _merge_non_priorities(names, priorities)
    _liability_warning(list(priorities.keys()))
    _filter_global_features("ignore", priorities)

@contextmanager
def blocked_context(*names, **priorities):
    """Create a context where the given features are blocked

    Each blocked feature cause a warning filter to be inserted in
    ``warnings.filters`` that raises all ProvisionalWarnings for
    that specific feature. Alternatively, the string ``"ALL"``
    can be specified in which case a blanket filter for all
    ProvisionalWarnings is inserted.

    Parameters
    ----------
    *names : str, "ALL"
        A seris of feature names which will be blocked with
        no priority (i.e. any subsiquent context can override
        the bloackages made here).
    **priorities : int, None, "ALL"
        A series of priority values keyed on feature names.
        Each feature will be blocked with its given priority.

    Priority Values
    ---------------
    ``0`` : The highest priority value
        A filter with a priority of ``0`` cannot be overriden,
        even by another ``0`` priority filter.
    ``int`` : Meduim priority values
        Filters with integer priorities (not ``0``) can override
        any filter with a value less-than or equal to its value.
    ``None`` : The lowest priority value
        A filter with a priority of ``None`` can always be
        overriden, even by another ``None`` priority filter
    """
    with _restore_global_filters():
        with warnings.catch_warnings():
            block(*names, **priorities)
            yield

def block(*names, **priorities):
    """Block the given prosivional features
    
    Parameters
    ----------
    *names : str
        A seris of feature names which will be blocked with
        no priority (i.e. any subsiquent filter can override
        the blockages made here).
    **priorities : int or None
        A series of priority values keyed on feature names.
        Each feature will be blocked with its given priority.

    Priority Values
    ---------------
    ``0`` : The highest priority value
        A filter with a priority of ``0`` cannot be overriden,
        even by another ``0`` priority filter.
    ``int`` : Meduim priority values
        Filters with integer priorities (not ``0``) can override
        any filter with a value less-than or equal to its value.
    ``None`` : The lowest priority value
        A filter with a priority of ``None`` can always be
        overriden, even by another ``None`` priority filter
    """
    _merge_non_priorities(names, priorities)
    _liability_warning(list(priorities.keys()))
    _filter_global_features("error", priorities)

def _filter_global_features(action, features):
    if not features or "ALL" in features:
        _add_global_filter("ALL", features.get("ALL", None),
            action=action, category=ProvisionalWarning)
    else:
        for name in features:
            _add_global_filter(name, features[name], action=action,
                message=("^(?:" + ProvisionalWarning.template
                    % name + "|" + name + ")$"),
                category=ProvisionalWarning)

def _add_global_filter(name, priority, **kwargs):
    """Add a new feature filter

    If a filter for the feature already exists, the
    new one only overrides it if the new one has a
    higher priority the the preexisting one. If that
    is True, warnings.filterwarnings is called with
    **kwargs and the filter's action and prioritty is
    stored in a global ``_global_filters`` dictionary
    """
    if name in _global_filters:
        fdict = _global_filters[name]
        p = fdict["priority"]
    else:
        fdict = {}
        _global_filters[name] = fdict
        p = None
    if p is None or (p != 0 and p <= priority):
        warnings.filterwarnings(**kwargs)
        fdict.update(action=kwargs["action"],
            priority=priority)
