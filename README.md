# Traitlets

[![Build Status](https://travis-ci.org/ipython/traitlets.svg?branch=master)](https://travis-ci.org/ipython/traitlets)
[![Documentation Status](https://readthedocs.org/projects/traitlets/badge/?version=latest)](http://traitlets.readthedocs.org/en/latest/?badge=latest)

Traitlets are a pure Python library enabling

 - the enforcement of strong typing for attributes of Python objects
(typed attributes are called "traits"),
 - notifications on changes of trait attributes,
 - automatic validation and coercion of trait attributes when attempting a
change.

The implementation relies on the [descriptor](https://docs.python.org/howto/descriptor.html)
pattern. This package powers the configuration system of IPython and Jupyter,
and the declarative API of IPython interactive widgets.

## Installation

For a local installation, make sure you have
[pip installed](https://pip.readthedocs.org/en/stable/installing/) and run:

```
pip install traitlets
```

For a development installation:

* Clone this repository and `cd` into it
* `pip install -e .`

## Running the tests

* `nosetests traitlets`.

## Usage

Any class with trait attributes must inherit from `HasTraits`.
For the list of available trait types and ther properties, see the
[Trait Types](http://traitlets.readthedocs.org/en/latest/trait_types.html)
section of the documentation.

### Dynamic default values

To calculate a default value dynamically, decorate a method of your class with
@default({traitname})`. This method will be called on the instance, and should
return the default value. For example:

```Python
import getpass
from traitlets import HasTraits, Unicode, observe

class Identity(HasTraits):
    username = Unicode()

    @default('username')
    def _username_default(self):
        return getpass.getuser()
```

### Callbacks when trait attributes change

To do something when a trait attribute is changed, decorate a method with
`traitlets.observe()`. The method will be called with a single argument, a
dictionary of the form:

```Python
{
  'owner': object, # The HasTraits instance
  'new': 6, # The new value
  'old': 5, # The old value
  'name': "foo", # The name of the changed trait
  'type': 'change', # The event type of the notification, usually 'change'
}
```
For example:

```Python
from traitlets import HasTraits, Integer, observe

class TraitletsExample(HasTraits):
    num = Integer(5, help="a number").tag(config=True)

    @observe('num')
    def _num_changed(self, change):
        print("{name} changed from {old} to {new}".format(**change))
```

### Validation and coercion

Each trait type (`Int`, `Unicode`, `Dict` etc.) may have its own validation or
coercion logic, in addition to which we can register custom cross-validators
that may depend on the state of other attributes.

```Python
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
```

However, we recommend that custom cross-validators don't modify the state of
the HasTraits instance.
