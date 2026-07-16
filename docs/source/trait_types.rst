Trait Types
===========

.. module:: traitlets

.. class:: TraitType

   The base class for all trait types.

   .. automethod:: __init__

   .. automethod:: from_string

Numbers
-------

.. autoclass:: Int

   An integer trait.


.. class:: Integer

   An alias for :class:`Int`

.. class:: Long

   .. deprecated:: 5.16
      Use :class:`Integer` instead.

   This (with Int) were values where the Python 2 ``int`` and ``long``
   types were not interchangeable. Now Long is a deprecated aliases for
   :class:`Int` and emit a :exc:`DeprecationWarning` when used.

.. autoclass:: Float

.. autoclass:: Complex

.. class:: CInt
           CFloat
           CComplex

   Casting variants of the above. When a value is assigned to the attribute,
   these will attempt to convert it by calling e.g. ``value = int(value)``.

.. class:: CLong

   .. deprecated:: 5.16
      Use :class:`CInt` instead.

   A deprecated alias for :class:`CInt`; emits a :exc:`DeprecationWarning`
   when used.

Strings
-------

.. autoclass:: Unicode

.. autoclass:: Bytes

.. class:: CUnicode
           CBytes

   Casting variants. When a value is assigned to the attribute, these will
   attempt to convert it to their type. They will not automatically encode/decode
   between unicode and bytes, however.

.. autoclass:: ObjectName

.. autoclass:: DottedObjectName

Containers
----------

.. autoclass:: List
   :members: __init__, from_string_list, item_from_string

.. autoclass:: Set
   :members: __init__

.. autoclass:: Tuple
   :members: __init__

.. autoclass:: Dict
   :members: __init__, from_string_list, item_from_string

Classes and instances
---------------------

.. autoclass:: Instance
   :members: __init__

.. autoclass:: Type
   :members: __init__

.. autoclass:: This

.. autoclass:: ForwardDeclaredInstance

.. autoclass:: ForwardDeclaredType


Miscellaneous
-------------

.. autoclass:: Bool

.. class:: CBool

   Casting variant. When a value is assigned to the attribute, this will
   attempt to convert it by calling ``value = bool(value)``.

.. autoclass:: Enum

.. autoclass:: CaselessStrEnum

.. autoclass:: UseEnum

.. autoclass:: TCPAddress

.. autoclass:: CRegExp

.. autoclass:: Path

.. autoclass:: Union
   :members: __init__

.. autoclass:: Callable

.. autoclass:: Any
