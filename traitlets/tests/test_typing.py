from typing import Optional

import pytest
from typing_extensions import reveal_type

from traitlets import Bool, CInt, HasTraits, Int, TCPAddress


@pytest.mark.mypy_testing
def mypy_bool_typing():
    class T(HasTraits):
        b = Bool(True).tag(sync=True)
        ob = Bool(None, allow_none=True).tag(sync=True)

    t = T()
    reveal_type(
        Bool(True)  # R: traitlets.traitlets.Bool[builtins.bool, Union[builtins.bool, builtins.int]]
    )
    reveal_type(
        Bool(  # R: traitlets.traitlets.Bool[builtins.bool, Union[builtins.bool, builtins.int]]
            True
        ).tag(sync=True)
    )
    reveal_type(
        Bool(  # R: traitlets.traitlets.Bool[Union[builtins.bool, None], Union[builtins.bool, builtins.int, None]]
            None, allow_none=True
        )
    )
    reveal_type(
        Bool(  # R: traitlets.traitlets.Bool[Union[builtins.bool, None], Union[builtins.bool, builtins.int, None]]
            None, allow_none=True
        ).tag(
            sync=True
        )
    )
    reveal_type(
        T.b  # R: traitlets.traitlets.Bool[builtins.bool, Union[builtins.bool, builtins.int]]
    )
    reveal_type(t.b)  # R: builtins.bool
    reveal_type(t.ob)  # R: Union[builtins.bool, None]
    reveal_type(
        T.b  # R: traitlets.traitlets.Bool[builtins.bool, Union[builtins.bool, builtins.int]]
    )
    reveal_type(
        T.ob  # R: traitlets.traitlets.Bool[Union[builtins.bool, None], Union[builtins.bool, builtins.int, None]]
    )
    # we would expect this to be Optional[Union[bool, int]], but...
    t.b = "foo"  # E: Incompatible types in assignment (expression has type "str", variable has type "Union[bool, int]")  [assignment]
    t.b = None  # E: Incompatible types in assignment (expression has type "None", variable has type "Union[bool, int]")  [assignment]


@pytest.mark.mypy_testing
def mypy_int_typing():
    class T(HasTraits):
        i: Int[int, int] = Int(42).tag(sync=True)
        oi: Int[Optional[int], Optional[int]] = Int(42, allow_none=True).tag(sync=True)

    t = T()
    reveal_type(Int(True))  # R: traitlets.traitlets.Int[builtins.int, builtins.int]
    reveal_type(Int(True).tag(sync=True))  # R: traitlets.traitlets.Int[builtins.int, builtins.int]
    reveal_type(
        Int(  # R: traitlets.traitlets.Int[Union[builtins.int, None], Union[builtins.int, None]]
            None, allow_none=True
        )
    )
    reveal_type(
        Int(  # R: traitlets.traitlets.Int[Union[builtins.int, None], Union[builtins.int, None]]
            None, allow_none=True
        ).tag(sync=True)
    )
    reveal_type(T.i)  # R: traitlets.traitlets.Int[builtins.int, builtins.int]
    reveal_type(t.i)  # R: builtins.int
    reveal_type(t.oi)  # R: Union[builtins.int, None]
    reveal_type(T.i)  # R: traitlets.traitlets.Int[builtins.int, builtins.int]
    reveal_type(
        T.oi  # R: traitlets.traitlets.Int[Union[builtins.int, None], Union[builtins.int, None]]
    )
    t.i = "foo"  # E: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]
    t.i = None  # E: Incompatible types in assignment (expression has type "None", variable has type "int")  [assignment]
    t.i = 1.2  # E: Incompatible types in assignment (expression has type "float", variable has type "int")  [assignment]


@pytest.mark.mypy_testing
def mypy_cint_typing():
    class T(HasTraits):
        i = CInt(42).tag(sync=True)
        oi = CInt(42, allow_none=True).tag(sync=True)

    t = T()
    reveal_type(CInt(True))  # R: traitlets.traitlets.CInt[builtins.int, Union[builtins.int, Any]]
    reveal_type(
        CInt(True).tag(  # R: traitlets.traitlets.CInt[builtins.int, Union[builtins.int, Any]]
            sync=True
        )
    )
    reveal_type(
        CInt(  # R: traitlets.traitlets.CInt[Union[builtins.int, None], Union[builtins.int, Any, None]]
            None, allow_none=True
        )
    )
    reveal_type(
        CInt(  # R: traitlets.traitlets.CInt[Union[builtins.int, None], Union[builtins.int, Any, None]]
            None, allow_none=True
        ).tag(
            sync=True
        )
    )
    reveal_type(T.i)  # R: traitlets.traitlets.CInt[builtins.int, Union[builtins.int, Any]]
    reveal_type(t.i)  # R: builtins.int
    reveal_type(t.oi)  # R: Union[builtins.int, None]
    reveal_type(T.i)  # R: traitlets.traitlets.CInt[builtins.int, Union[builtins.int, Any]]
    reveal_type(
        T.oi  # R: traitlets.traitlets.CInt[Union[builtins.int, None], Union[builtins.int, Any, None]]
    )


@pytest.mark.mypy_testing
def mypy_tcp_typing():
    class T(HasTraits):
        tcp = TCPAddress()
        otcp = TCPAddress(None, allow_none=True)

    t = T()
    reveal_type(t.tcp)  # R: Tuple[builtins.str, builtins.int]
    reveal_type(
        T.tcp  # R: traitlets.traitlets.TCPAddress[Tuple[builtins.str, builtins.int], Tuple[builtins.str, builtins.int]]
    )
    reveal_type(
        T.tcp.tag(  # R:traitlets.traitlets.TCPAddress[Tuple[builtins.str, builtins.int], Tuple[builtins.str, builtins.int]]
            sync=True
        )
    )
    reveal_type(t.otcp)  # R: Union[Tuple[builtins.str, builtins.int], None]
    reveal_type(
        T.otcp  # R: traitlets.traitlets.TCPAddress[Union[Tuple[builtins.str, builtins.int], None], Union[Tuple[builtins.str, builtins.int], None]]
    )
    reveal_type(
        T.otcp.tag(  # R: traitlets.traitlets.TCPAddress[Union[Tuple[builtins.str, builtins.int], None], Union[Tuple[builtins.str, builtins.int], None]]
            sync=True
        )
    )
    t.tcp = "foo"  # E: Incompatible types in assignment (expression has type "str", variable has type "Tuple[str, int]")  [assignment]
    t.otcp = "foo"  # E: Incompatible types in assignment (expression has type "str", variable has type "Optional[Tuple[str, int]]")  [assignment]
    t.tcp = None  # E: Incompatible types in assignment (expression has type "None", variable has type "Tuple[str, int]")  [assignment]
