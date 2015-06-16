Using Traitlets
===============

.. currentmodule:: traitlets

Any class with traitlet attributes must inherit from :class:`HasTraits`.

.. autoclass:: HasTraits

   .. automethod:: has_trait

   .. automethod:: trait_names

   .. automethod:: class_trait_names

   .. automethod:: traits

   .. automethod:: class_traits

   .. automethod:: trait_metadata

   .. automethod:: add_traits

You then declare the traitlets on the class like this::

    from traitlets import HasTraits, Int, Unicode

    class Requester(HasTraits):
        url = Unicode()
        timeout = Int(30)  # 30 will be the default value

For the available traitlet types and the arguments you can give them, see
:doc:`trait_types`.

Dynamic default values
----------------------

To calculate a default value dynamically, give your class a method named
:samp:`_{traitname}_default`. This will be called on the instance,
and should return the default value. For example::

    import getpass

    class Identity(HasTraits):
        username = Unicode()
        def _username_default(self):
            return getpass.getuser()

Callbacks when traitlets change
-------------------------------

To do something when a traitlet is changed, define a method named
:samp:`_{traitname}_changed`. This can have several possible signatures:

.. class:: TraitletsCallbacksExample

   .. method:: _traitlet1_changed()
               _traitlet2_changed(traitlet_name)
               _traitlet3_changed(traitlet_name, new_value)
               _traitlet4_changed(traitlet_name, old_value, new_value)

You can also add callbacks to a trait dynamically:

.. automethod:: HasTraits.on_trait_change

.. note::

   If a traitlet with a dynamic default value has another value set before it is
   used, the default will not be calculated.
   Any callbacks on that trait will will fire, and *old_value* will be ``None``.
