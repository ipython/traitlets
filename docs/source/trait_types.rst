Trait Types
===========

.. module:: traitlets

.. class:: TraitType

   The base class for all trait types.

   .. automethod:: __init__

   .. automethod:: from_string

Numbers
-------

.. autoclass:: Integer

   An integer trait. On Python 2, this automatically uses the ``int`` or
   ``long`` types as necessary.

.. class:: Int
.. class:: Long

   On Python 2, these are traitlets for values where the ``int`` and ``long``
   types are not interchangeable. On Python 3, they are both aliases for
   :class:`Integer`.

   In almost all situations, you should use :class:`Integer` instead of these.

.. autoclass:: Float

.. autoclass:: Complex

.. class:: CInt
           CLong
           CFloat
           CComplex

   Casting variants of the above. When a value is assigned to the attribute,
   these will attempt to convert it by calling e.g. ``value = int(value)``.

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

.. autoclass:: Union
   :members: __init__

.. autoclass:: Callable

.. autoclass:: Any
