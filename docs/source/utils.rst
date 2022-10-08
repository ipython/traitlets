Utils
=====

.. module:: traitlets
   :noindex:

A simple utility to import something by its string name.

.. autofunction:: import_item

.. autofunction:: signature_has_traits

This is a way to expand the signature of the ``HasTraits`` class constructor. This
enables auto-completion of trait-names in IPython and xeus-python when having
Jedi>=0.15 by adding trait names with their default values in the constructor
signature.

Example:

.. code:: Python

    from inspect import signature

    from traitlets import HasTraits, Int, Unicode, signature_has_traits

    @signature_has_traits
    class Foo(HasTraits):
        number1 = Int()
        number2 = Int()
        value = Unicode('Hello')

        def __init__(self, arg1, **kwargs):
            self.arg1 = arg1

            super(Foo, self).__init__(**kwargs)

    print(signature(Foo))  # <Signature (arg1, *, number1=0, number2=0, value='Hello', **kwargs)>


Links
-----

.. autoclass:: link

.. autoclass:: directional_link
