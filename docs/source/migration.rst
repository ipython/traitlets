Migration from Traitlets 4.0 to Traitlets 4.1
=============================================

Traitlets 4.1 introduces a totally new decorator-based API for
configuring traitlets and a couple of other changes.

However, it is a backward-compatible release and the deprecated APIs
will be supported for some time.

Separation of metadata and keyword arguments in ``TraitType`` constructors
--------------------------------------------------------------------------

In traitlets 4.0, trait types constructors used all unrecognized keyword
arguments passed to the constructor (like ``sync`` or ``config``) to
populate the ``metadata`` dictionary.

In trailets 4.1, we deprecated this behavior. The preferred method to
populate the metadata for a trait type instance is to use the new
``tag`` method.

.. code:: python

    x = Int(allow_none=True, sync=True)  # deprecated
    x = Int(allow_none=True).tag(sync=True)  # ok

We also deprecated the ``get_metadata`` method. The metadata of a trait
type instance can directly be accessed via the ``metadata`` attribute.

Deprecation of ``on_trait_change``
----------------------------------

The most important change in this release is the deprecation of the
``on_trait_change`` method.

Instead, we introduced two methods, ``observe`` and ``unobserve`` to
register and unregister handlers (instead of passing ``remove=True`` to
``on_trait_change`` for the removal).

-  The ``observe`` method takes one positional argument (the handler),
   and two keyword arguments, ``names`` and ``type``, which are used to
   filter by notification type or by the names of the observed trait
   attribute. The special value ``All`` corresponds to listening to all
   the notification types or all notifications from the trait
   attributes. The ``names`` argument can be a list of string, a string,
   or ``All`` and ``type`` can be a string or ``All``.

-  The observe handler's signature is different from the signature of
   on\_trait\_change. It takes a single change dictionary argument,
   containing

.. code:: python

    {"type": "<The type of notification.>"}

In the case where ``type`` is the string ``'change'``, the following
additional attributes are provided:

.. code:: python

    {
        "owner": "<the HasTraits instance>",
        "old": "<the old trait attribute value>",
        "new": "<the new trait attribute value>",
        "name": "<the name of the changing attribute>",
    }

The ``type`` key in the change dictionary is meant to enable protocols
for other notification types. By default, its value is equal to the
``'change'`` string which corresponds to the change of a trait value.

**Example:**

.. code:: python

    from traitlets import HasTraits, Int, Unicode


    class Foo(HasTraits):
        bar = Int()
        baz = Unicode()


    def handle_change(change):
        print("{name} changed from {old} to {new}".format(**change))


    foo = Foo()
    foo.observe(handle_change, names="bar")

The new ``@observe`` decorator
------------------------------

The use of the magic methods ``_{trait}_changed`` as change handlers is
deprecated, in favor of a new ``@observe`` method decorator.

The ``@observe`` method decorator takes the names of traits to be observed as positional arguments and
has a ``type`` keyword-only argument (defaulting to ``'change'``) to filter
by notification type.

**Example:**

.. code:: python

    class Foo(HasTraits):
        bar = Int()
        baz = EnventfulContainer()  # hypothetical trait type emitting
        # other notifications types

        @observe("bar")  # 'change' notifications for `bar`
        def handler_bar(self, change):
            pass

        @observe("baz ", type="element_change")  # 'element_change' notifications for `baz`
        def handler_baz(self, change):
            pass

        @observe("bar", "baz", type=All)  # all notifications for `bar` and `baz`
        def handler_all(self, change):
            pass

dynamic defaults generation with decorators
-------------------------------------------

The use of the magic methods ``_{trait}_default`` for dynamic default
generation is not deprecated, but a new ``@default`` method decorator
is added.

**Example:**

Default generators should only be called if they are registered in
subclasses of ``trait.this_type``.

.. code:: python

    from traitlets import HasTraits, Int, Float, default


    class A(HasTraits):
        bar = Int()

        @default("bar")
        def get_bar_default(self):
            return 11


    class B(A):
        bar = Float()  # This ignores the default generator
        # defined in the base class A


    class C(B):
        @default("bar")
        def some_other_default(self):  # This should not be ignored since
            return 3.0  # it is defined in a class derived
            # from B.a.this_class.

Deprecation of magic method for cross-validation
------------------------------------------------

``traitlets`` enables custom cross validation between the different
attributes of a ``HasTraits`` instance. For example, a slider value
should remain bounded by the ``min`` and ``max`` attribute. This
validation occurs before the trait notification fires.

The use of the magic methods ``_{name}_validate`` for custom
cross-validation is deprecated, in favor of a new ``@validate`` method
decorator.

The method decorated with the ``@validate`` decorator take a single
``proposal`` dictionary

.. code:: python

    {
        "trait": "<the trait type instance being validated>",
        "value": "<the proposed value>",
        "owner": "<the underlying HasTraits instance>",
    }

Custom validators may raise ``TraitError`` exceptions in case of invalid
proposal, and should return the value that will be eventually assigned.

**Example:**

.. code:: python

    from traitlets import HasTraits, TraitError, Int, Bool, validate


    class Parity(HasTraits):
        value = Int()
        parity = Int()

        @validate("value")
        def _valid_value(self, proposal):
            if proposal["value"] % 2 != self.parity:
                raise TraitError("value and parity should be consistent")
            return proposal["value"]

        @validate("parity")
        def _valid_parity(self, proposal):
            parity = proposal["value"]
            if parity not in [0, 1]:
                raise TraitError("parity should be 0 or 1")
            if self.value % 2 != parity:
                raise TraitError("value and parity should be consistent")
            return proposal["value"]


    parity_check = Parity(value=2)

    # Changing required parity and value together while holding cross validation
    with parity_check.hold_trait_notifications():
        parity_check.value = 1
        parity_check.parity = 1

The presence of the ``owner`` key in the proposal dictionary enable the
use of other attributes of the object in the cross validation logic.
However, we recommend that the custom cross validator don't modify the
other attributes of the object but only coerce the proposed value.

Backward-compatible upgrades
----------------------------

One challenge in adoption of a changing API is how to adopt the new API
while maintaining backward compatibility for subclasses,
as event listeners methods are *de facto* public APIs.

Take for instance the following class:

.. code:: python

    from traitlets import HasTraits, Unicode


    class Parent(HasTraits):
        prefix = Unicode()
        path = Unicode()

        def _path_changed(self, name, old, new):
            self.prefix = os.path.dirname(new)

And you know another package has the subclass:

.. code:: python

    from parent import Parent


    class Child(Parent):
        def _path_changed(self, name, old, new):
            super()._path_changed(name, old, new)
            if not os.path.exists(new):
                os.makedirs(new)

If the parent package wants to upgrade without breaking Child,
it needs to preserve the signature of ``_path_changed``.
For this, we have provided an ``@observe_compat`` decorator,
which automatically shims the deprecated signature into the new signature:

.. code:: python

    from traitlets import HasTraits, Unicode, observe, observe_compat


    class Parent(HasTraits):
        prefix = Unicode()
        path = Unicode()

        @observe("path")
        @observe_compat  # <- this allows super()._path_changed in subclasses to work with the old signature.
        def _path_changed(self, change):
            self.prefix = os.path.dirname(change["value"])
