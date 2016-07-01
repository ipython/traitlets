Changes in Traitlets
====================

4.2
---

4.2.2
*****

`4.2.2 on GitHub <https://github.com/ipython/traitlets/milestones/4.2.2>`__

Partially revert a change in 4.1 that prevented IPython's command-line options from taking priority over config files.


4.2.1
*****

`4.2.1 on GitHub <https://github.com/ipython/traitlets/milestones/4.2.1>`__

Demotes warning about unused arguments in ``HasTraits.__init__`` introduced in 4.2.0 to DeprecationWarning.

4.2.0
*****

`4.2 on GitHub <https://github.com/ipython/traitlets/milestones/4.2>`__

- :class:`JSONFileConfigLoader` can be used as a context manager for updating configuration.
- If a value in config does not map onto a configurable trait,
  a message is displayed that the value will have no effect.
- Unused arguments are passed to ``super()`` in ``HasTraits.__init__``,
  improving support for multiple inheritance.
- Various bugfixes and improvements in the new API introduced in 4.1.
- Application subclasses may specify ``raise_config_file_errors = True``
  to exit on failure to load config files,
  instead of the default of logging the failures.


4.1
---

`4.1 on GitHub <https://github.com/ipython/traitlets/milestones/4.1>`__

Traitlets 4.1 introduces a totally new decorator-based API for configuring traitlets.
Highlights:

- Decorators are used, rather than magic method names, for registering trait-related methods. See :doc:`using_traitlets` and :doc:`migration` for more info.
- Deprecate ``Trait(config=True)`` in favor of ``Trait().tag(config=True)``. In general, metadata is added via ``tag`` instead of the constructor.

Other changes:

- Trait attributes initialized with ``read_only=True`` can only be set with the ``set_trait`` method.
  Attempts to directly modify a read-only trait attribute raises a ``TraitError``.
- The directional link now takes an optional `transform` attribute allowing the modification of the value.
- Various fixes and improvements to config-file generation (fixed ordering, Undefined showing up, etc.)
- Warn on unrecognized traits that aren't configurable, to avoid silently ignoring mistyped config.


4.0
---

`4.0 on GitHub <https://github.com/ipython/traitlets/milestones/4.0>`__

First release of traitlets as a standalone package.
