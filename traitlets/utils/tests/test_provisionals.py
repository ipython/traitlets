import warnings
from ..provisionals import ProvisionalWarning, silenced_provisional_warnings

def assert_raises(exception, callable, *args, **kwargs):
    try:
        callable(*args, **kwargs)
    except exception:
        pass
    else:
        assert False

def test_provisional_warning():
    assert_raises(ProvisionalWarning, warnings.warn,
                    ProvisionalWarning("this"))

    # specify the features to enable by name
    with warnings.catch_warnings(record=True) as user_warn:
        with silenced_provisional_warnings("feature 1") as prov_warn:
            warnings.warn(ProvisionalWarning("feature 1"))
            assert_raises(ProvisionalWarning, warnings.warn,
                        ProvisionalWarning("feature 2"))

    assert len(user_warn) == 1
    assert len(prov_warn) == 1