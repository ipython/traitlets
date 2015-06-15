Defining new trait types
========================

.. py:currentmodule:: traitlets

To define a new trait type, subclass from :class:`TraitType`. You can define the
following things:

.. class:: MyTrait

   .. attribute:: info_text

      A short string describing what this trait should hold.

   .. attribute:: default_value

      A default value, if one makes sense for this trait type. If there is no
      obvious default, don't provide this.

   .. method:: validate(obj, value)

      Check whether a given value is valid. If it is, it should return the value
      (coerced to the desired type, if necessary). If not, it should raise
      :exc:`TraitError`. :meth:`TraitType.error` is a convenient way to raise an
      descriptive error saying that the given value is not of the required type.

      ``obj`` is the object to which the trait belongs.

For instance, here's the definition of the :class:`TCPAddress` trait:

.. literalinclude:: /../../traitlets/traitlets.py
   :pyobject: TCPAddress
