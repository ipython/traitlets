import sys
import inspect
import warnings
from contextlib import contextmanager

#-----------------------------------------------------------------------------
# Warning Types
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
        super(ProvisionalWarning, self).__init__(template % feature, *args)

# all warnings for provisional features raise by default
warnings.simplefilter("error", category=ProvisionalWarning)

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

_active_filters = {}

def allowed_features():
    """Get a list of features which are allowed in the current context"""
    return _public_filter_dict("ignore")

def blocked_features():
    """Get a list of features which are blocked in the current context"""
    return _public_filter_dict("error")

def active_filters():
    """Get a dict defining the active provisional filters in this context"""
    return {n: d.copy() for n, d in _active_filters.items()}

def _public_flter_dict(action):
    return list(n for n, d in
        _active_filters.items()
        if d["action"] == action)

def acknowledge_liability(cls):
    """Acknowledge responcibility to supresses ``LiabilityWarnings``"""
    user_acknowledges = ("Provisional features are subject to change without "
        "warning, and only intended for experimental use. By envoking this "
        "method, the user assumes all responsibility for supporting them until "
        "their provisional status has been revoked.")
    warnings.warn(user_acknowledges, LiabilityWarning)
    warnings.simplefilter("ignore", category=LiabilityWarning)

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
    with warnings.catch_warnings():
        allow(*name, **priorities)
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
    _merge_non_priorities(name, priorities)
    _liability_warning(list(priorities.keys()))
    _filter_features("ignore", **features)

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
    with warnings.catch_warnings():
        block(*name, **priorities)
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
    _merge_non_priorities(name, priorities)
    _filter_features("error", **features)

def _merge_non_priorities(name, priorities):
    """merge feature names into priorities"""
    for n in names:
        if n in priorities:
            raise ValueError("Conflicting feature "
                "'%s' in *names and **priorities")
        else:
            priorities[n] = None

def _filter_features(action, **features):
    if not features or "ALL" in features:
        _add_filter("ALL", features.get("ALL", None),
            action=action, category=ProvisionalWarning)
    else:
        for name in features:
            _add_filter("ALL", features[name], action=action,
                message=("^(?:" + ProvisionalWarning.template
                    % name + "|" + name + ")$"),
                category=ProvisionalWarning)

def _add_filter(name, priority, **kwargs):
    """Add a new feature filter

    If a filter for the feature already exists, the
    new one only overrides it if the new one has a
    higher priority the the preexisting one. If that
    is True, warnings.filterwarnings is called with
    **kwargs and the filter's action and prioritty is
    stored in a global ``_active_filters`` dictionary
    """
    if name in _active_filters:
        fdict = _active_filters[name]
        p = fdict["priority"]
    else:
        fdict = {}
        _active_filters[name] = fdict
        p = None
    if p is None or (p != 0 and p <= priority):
        warnings.filterwarnings(**kwargs)
        fdict.update(action=kwargs["action"],
            priority=priority)

@staticmethod
def _liability_warning(features):
    if len(features) == 0:
        fill = "provisional features"
    elif len(features) == 1:
        fill = ("%r" % features[0],)
    elif len(features) == 2:
        fill = ("%r and %r" % features,)
    else:
        fill = (str(features[:-1])[1:-1] + ", and %r" % features[-1],)
    user_acknowledges = ("By specifying that %s be enabled, the user acknowledges "
        "that they have assumed all responsibility for supporting them until their "
        "provisional status has been revoked." % fill)
    warnings.warn(user_acknowledges, LiabilityWarning)
