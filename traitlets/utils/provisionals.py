import warnings
from contextlib import contextmanager

class ProvisionalWarning(FutureWarning):
    
    template = "%r is a provisional feature - its use is not recommended"
    
    def __init__(self, feature, *args):
        """Warn users about the presence an unstable or temporary feature.

        Provisional features are not guaranteed to exist over any period of time in
        the future, whether that be in the same form, or at all. To avoid provisional
        warnings, users must envoke the ``without_provisional_warnings`` context
        manager and specify the names of all unstable features they wish to enable.

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

@contextmanager
def silenced_provisional_warnings(*features):
    """Specify which provisional features to enable

    By enabling provisional features, the user acknowledges that they are not
    guaranteed to exist over any period of time in the futures, whether that be
    in the same form, or at all.

    Parameters
    ----------
    *features : str
        The names of the provisional features which may be encountered.
    """
    if len(features) == 0:
        raise ValueError("Specify the provisional features that should be enabled")
    elif len(features) == 1:
        fill = ("%r" % features[0],)
    elif len(features) == 2:
        fill = ("%r and %r" % features,)
    else:
        fill = (str(list(features[:-1]))[1:-1] + ", and %r" % features[-1],)

    warnings.warn("By specifying that %s be enabled, the user acknowledges that "
        "provisional features are not guaranteed to exist over any period of time "
        "in the future, whether that be in the same form, or at all." % fill)
    with warnings.catch_warnings(record=True) as w:
        for name in features:
            warnings.filterwarnings("always", message=(
                ".*" + ProvisionalWarning.template % name + ".*"),
                category=ProvisionalWarning)
        yield w