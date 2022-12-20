import pytest
from typing_extensions import reveal_type

from traitlets import Bool, HasTraits, TCPAddress


@pytest.mark.mypy_testing
def mypy_bool_typing():
    class T(HasTraits):
        b = Bool().tag(sync=True)

    t = T()
    reveal_type(t.b)  # R: Union[builtins.bool, None]
    # we would expect this to be Optional[Union[bool, int]], but...
    t.b = "foo"  # E: Incompatible types in assignment (expression has type "str", variable has type "Optional[int]")  [assignment]
    T.b.tag(foo=True)


@pytest.mark.mypy_testing
def mypy_tcp_typing():
    class T(HasTraits):
        tcp = TCPAddress()

    t = T()
    reveal_type(t.tcp)  # R: Union[Tuple[builtins.str, builtins.int], None]
    t.tcp = "foo"  # E: Incompatible types in assignment (expression has type "str", variable has type "Optional[Tuple[str, int]]")  [assignment]
