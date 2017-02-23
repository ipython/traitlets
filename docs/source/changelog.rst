Changes in Traitlets
====================

4.3
---

4.3.2
*****

`4.3.2 on GitHub`_

4.3.2 is a tiny release, relaxing some of the deprecations introduced in 4.1:

- using :meth:`_traitname_default()` without the ``@default`` decorator is no longer
  deprecated.
- Passing ``config=True`` in traitlets constructors is no longer deprecated.

4.3.1
*****

`4.3.1 on GitHub`_

- Compatibility fix for Python 3.6a1
- Fix bug in Application.classes getting extra entries when multiple Applications are instantiated in the same process.

4.3.0
*****

`4.3.0 on GitHub`_

- Improve the generated config file output.
- Allow TRAITLETS_APPLICATION_RAISE_CONFIG_FILE_ERROR env to override :attr:`Application.raise_config_file_errors`,
  so that config file errors can result in exiting immediately.
- Avoid using root logger. If no application logger is registered,
  the ``'traitlets'`` logger will be used instead of the root logger.
- Change/Validation arguments are now Bunch objects, allowing attribute-access,
  in addition to dictionary access.
- Reduce number of common deprecation messages in certain cases.
- Ensure command-line options always have higher priority than config files.
- Add bounds on numeric traits.
- Improves various error messages.


4.2
---

4.2.2 - 2016-07-01
******************

`4.2.2 on GitHub`_

Partially revert a change in 4.1 that prevented IPython's command-line options from taking priority over config files.


4.2.1 - 2016-03-14
******************

`4.2.1 on GitHub`_

Demotes warning about unused arguments in ``HasTraits.__init__`` introduced in 4.2.0 to DeprecationWarning.

4.2.0 - 2016-03-14
******************

`4.2 on GitHub`_

- :class:`JSONFileConfigLoader` can be used as a context manager for updating configuration.
- If a value in config does not map onto a configurable trait,
  a message is displayed that the value will have no effect.
- Unused arguments are passed to ``super()`` in ``HasTraits.__init__``,
  improving support for multiple inheritance.
- Various bugfixes and improvements in the new API introduced in 4.1.
- Application subclasses may specify ``raise_config_file_errors = True``
  to exit on failure to load config files,
  instead of the default of logging the failures.


4.1 - 2016-01-15
----------------

`4.1 on GitHub`_

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


4.0 - 2015-06-19
----------------

`4.0 on GitHub`_

First release of traitlets as a standalone package.



.. _`4.0 on GitHub`: https://github.com/ipython/traitlets/milestones/4.0
.. _`4.1 on GitHub`: https://github.com/ipython/traitlets/milestones/4.1
.. _`4.2 on GitHub`: https://github.com/ipython/traitlets/milestones/4.2
.. _`4.2.1 on GitHub`: https://github.com/ipython/traitlets/milestones/4.2.1
.. _`4.2.2 on GitHub`: https://github.com/ipython/traitlets/milestones/4.2.2
.. _`4.3.0 on GitHub`: https://github.com/ipython/traitlets/milestones/4.3
.. _`4.3.1 on GitHub`: https://github.com/ipython/traitlets/milestones/4.3.1
.. _`4.3.2 on GitHub`: https://github.com/ipython/traitlets/milestones/4.3.2
