Traitlets API reference
=======================

.. currentmodule:: traitlets

Any class with trait attributes must inherit from :class:`HasTraits`.

.. autoclass:: HasTraits

   .. automethod:: has_trait

   .. automethod:: trait_has_value

   .. automethod:: trait_names

   .. automethod:: class_trait_names

   .. automethod:: traits

   .. automethod:: class_traits

   .. automethod:: trait_metadata

   .. automethod:: add_traits

You then declare the trait attributes on the class like this::

    from traitlets import HasTraits, Int, Unicode

    class Requester(HasTraits):
        url = Unicode()
        timeout = Int(30)  # 30 will be the default value

For the available trait types and the arguments you can give them, see
:doc:`trait_types`.


Dynamic default values
----------------------

.. autofunction:: default

To calculate a default value dynamically, decorate a method of your class with
``@default({traitname})``. This method will be called on the instance, and should
return the default value. For example::

    import getpass

    class Identity(HasTraits):
        username = Unicode()

        @default('username')
        def _username_default(self):
            return getpass.getuser()


Callbacks when trait attributes change
--------------------------------------

.. autofunction:: observe

To do something when a trait attribute is changed, decorate a method with :func:`traitlets.observe`.
The method will be called with a single argument, a dictionary of the form::

    {
      'owner': object, # The HasTraits instance
      'new': 6, # The new value
      'old': 5, # The old value
      'name': "foo", # The name of the changed trait
      'type': 'change', # The event type of the notification, usually 'change'
    }

For example::

    from traitlets import HasTraits, Integer, observe

    class TraitletsExample(HasTraits):
        num = Integer(5, help="a number").tag(config=True)

        @observe('num')
        def _num_changed(self, change):
            print("{name} changed from {old} to {new}".format(**change))


.. versionchanged:: 4.1

    The ``_{trait}_changed`` magic method-name approach is deprecated.

You can also add callbacks to a trait dynamically:

.. automethod:: HasTraits.observe

.. note::

    If a trait attribute with a dynamic default value has another value set
    before it is used, the default will not be calculated.
    Any callbacks on that trait will will fire, and *old_value* will be ``None``.

Validating proposed changes
---------------------------

.. autofunction:: validate

Validator methods can be used to enforce certain aspects of a property.
These are called on proposed changes,
and can raise a TraitError if the change should be rejected,
or coerce the value if it should be accepted with some modification.
This can be useful for things such as ensuring a path string is always absolute,
or check if it points to an existing directory.

For example::

    from traitlets import HasTraits, Unicode, validate, TraitError

    class TraitletsExample(HasTraits):
        path = Unicode('', help="a path")

        @validate('path')
        def _check_prime(self, proposal):
            path = proposal['value']
            if not path.endswith('/'):
                # ensure path always has trailing /
                path = path + '/'
            if not os.path.exists(path):
                raise TraitError("path %r does not exist" % path)
            return path
