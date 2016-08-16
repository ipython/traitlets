Using Traitlets
===============

In short, traitlets let the user define classes that have

1. Attributes (traits) with type checking and dynamically computed
   default values
2. Traits emit change events when attributes are modified
3. Traitlets perform some validation and allow coercion of new trait
   values on assignment. They also allow the user to define custom
   validation logic for attributes based on the value of other
   attributes.

Default values, and checking type and value
-------------------------------------------

At its most basic, traitlets provides type checking, and dynamic default
value generation of attributes on :class:``traitlets.HasTraits``
subclasses:

.. code:: python

    import getpass

    class Identity(HasTraits):
        username = Unicode()

        @default('username')
        def _default_username(self):
            return getpass.getuser()

.. code:: python

    class Foo(HasTraits):
        bar = Int()

    foo = Foo(bar='3')  # raises a TraitError

::

    TraitError: The 'bar' trait of a Foo instance must be an int,
    but a value of '3' <class 'str'> was specified

observe
-------

Traitlets implement the observer pattern

.. code:: python

    class Foo(HasTraits):
        bar = Int()
        baz = Unicode()

    foo = Foo()

    def func(change):
        print(change['old'])
        print(change['new'])   # as of traitlets 4.3, one should be able to
                               # write print(change.new) instead

    foo.observe(func, names=['bar'])
    foo.bar = 1  # prints '0\n 1'
    foo.baz = 'abc'  # prints nothing

When observers are methods of the class, a decorator syntax can be used.

.. code:: python

    class Foo(HasTraits):
        bar = Int()
        baz = Unicode()

        @observe('bar')
        def _observe_bar(self, change):
            print(change['old'])
            print(change['new'])

Validation
----------

Custom validation logic on trait classes

.. code:: python

    from traitlets import HasTraits, TraitError, Int, Bool, validate

    class Parity(HasTraits):
        value = Int()
        parity = Int()

        @validate('value')
        def _valid_value(self, proposal):
            if proposal['value'] % 2 != self.parity:
                raise TraitError('value and parity should be consistent')
            return proposal['value']

        @validate('parity')
        def _valid_parity(self, proposal):
            parity = proposal['value']
            if parity not in [0, 1]:
                raise TraitError('parity should be 0 or 1')
            if self.value % 2 != parity:
                raise TraitError('value and parity should be consistent')
            return proposal['value']

    parity_check = Parity(value=2)

    # Changing required parity and value together while holding cross validation
    with parity_check.hold_trait_notifications():
        parity_check.value = 1
        parity_check.parity = 1

In the case where the a validation error occurs when
``hold_trait_notifications`` context manager is released, changes are
rolled back to the initial state.

-  Finally, trait type can have other events than trait changes. This
   capability was added so as to enable notifications on change of
   values in container classes. The items available in the dictionary
   passed to the observer registered with ``observe`` depends on the
   event type.
