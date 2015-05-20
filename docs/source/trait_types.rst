Trait Types
===========

.. module:: traitlets

.. class:: TraitType

   The base class for all trait types.

   .. automethod:: __init__

Numbers
-------
.. autoclass:: Int

.. class:: Long

   Integers ``> sys.maxsize`` on Python 2. Alias for :class:`Int` on Python 3.

.. class:: Integer

   Uses the int or long types as appropriate on Python 2. Alias for :class:`Int`
   on Python 3.

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
   :members: __init__

.. autoclass:: Set
   :members: __init__

.. autoclass:: Tuple
   :members: __init__

.. autoclass:: Dict
   :members: __init__

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

.. autoclass:: TCPAddress

.. autoclass:: CRegExp

.. autoclass:: Union
   :members: __init__

.. autoclass:: Any

