Changes in Traitlets
====================

Traitlets 5.0
-------------

(This is an in-progress changelog, please let us know if something is missing/or could be phrased better)

Traitlets 5.0 is a new version of traitlets that accumulate changes over a period of more close to four years; A number of
internal refactoring made the internal code structure cleaner and simpler, and greatly improved the diagnostic error
messages as well has help and documentation generation.

We expect no code change needed for any consumer of the Python API (ipywidgets, and alike), though CLI argument parsing
have seen a complete rewrite, so if you have an application that does use the parsing logic of traitlets you may see
changes in behavior, and have now access to more features.

We also want to thanks in particular a number of regular contributor through the years that have patiently waited for
their often large contribution to be available, if **rough** order of number of contribution:

  - Ryan Morshead - @rmorshea - For serving as a maintainer of the 4.x branch and providing a number of bug fix through
    the years.
  - Kostis Anagnostopoulos - @ankostis - Who push a major refactor of the CLI paring, as well as many help-generating
    function.
  - Benjamin Ragan-Kelley – @minrk – for reviewing and help fixing edge case in most of the above
  - Matthias Bussonnier – @carreau
  - Sylvain Corlay
  - Francisco de la Peña
  - Martin Renou
  - Yves Delley
  - Thomas Kluyver
  - hristian Clauss
  - maartenbreddels
  - Aliaksei Urbanski
  - Kevin Bates
  - David Brochart

As well as many of the passer-by, and less frequent contributors:

  - Tim Paine
  - Jake VanderPlas
  - Frédéric Chapoton
  - Dan Allan
  - Adam Chainz
  - William Krinsman
  - Travis DePrato
  - Todd
  - Thomas Aarholt
  - Lumir Balhar
  - Leonardo Uieda
  - Leo Gallucci
  - Kyle Kelley
  - Jeroen Demeyer
  - Jason Grout
  - Hans Moritz Günther
  - FredInChina
  - Conner Cowling
  - Carol Willing
  - Albert Zeyer


Major changes are:

 - Removal of Python 2 support,
 - Removal of Python 3.0-3.6 support
 - we now follow NEP 29, and are thus Python 3.7+ only.
 - remove ``six`` as a dependency
 - remove ``funcsig`` as a dependency.



- :ghpull:`362` , :ghpull:`361` introduces:
  - help for aliases , aliases dict values can now be a tuple with ('target', 'help string')
  - subcommands can now be arbitrary callable and do not need to be subclass of :any:`Application`
- :ghpull:`306` Add compatibility with the ``trait`` package for Dictionaries and add the ``key_trait`` parameters
  allowing to restrict the type of the key of a mapping. The constructor parameters ``trait`` and ``traits`` are renamed
  to ``value_trait`` and ``per_key_traits``.
- :ghpull:`319` adds ability to introduce both shot and long version of aliases, allowing for short and long options ``-`` and ``--``.
- :ghpull:`322` rewrite command line argument parsing to use argparse, and allow more flexibility in assigning literals without quoting.
- :ghpull:`332` Make it easier to redefined default values of parents classes.
- :ghpull:`333` introduces a :any:`Callable` trait.
- :ghpull:`340` Old way of passing containers in the command line is now deprecated, and will emit warning on the command line.
- :ghpull:`341` introduces ``--Application.show_config=True``  which will make by default any application show it configuration, all the files it loaded configuration from, and exit.
- :ghpull:`349` unify ability to declare default values across traitlets with a singular method ``default`` method, and :ghpull:`525` adds a warning that `Undefined` is deprecated.
- :ghpull:`355` fix a random ordering issues in command lines flags.
- :ghpull:`356` allow both ``self`` and ``cls`` in ``__new__`` method for genericity.
- :ghpull:`360` Simplify overwriting and extending the command line argument parser.
- :ghpull:`371` introduces a :any:`FuzzyEnum` trait that allow case insensitive and unique prefix matching.
- :ghpull:`384` Ass a `trait_values` method to extra a mapping of trait and their values.
- :ghpull:`393` `Link` now have a transform attribute (taking two functions inverse of each other), that affect how a
  value is mapped between a source and a target.
- :ghpull:`394` `Link` now have a `link` method to re-link object after `unlink` has been called.
- :ghpull:`402` rewrite handling of error messages for nested traits.
- :ghpull:`405` all function that use to print help now have an equivalent that yields the help lines.
- :ghpull:`413` traits now have a method `trait_has_value`, returning a boolean to know if a value has been assigned to
  a trait (excluding the default), in order to help avoiding circular validation at initialisation.
- :ghpull:`416` Explicitly export traitlets  in ``__all__`` to avoid exposing implementation details.
- :ghpull:`438` introduces ``.info_rst()`` to let traitlets overwrite the automatically generated rst documentation.
- :ghpull:`458` Add a sphinx extension to automatically document options of `Application` instance in projects using traitlets.
- :ghpull:`509` remove all base ``except:`` meaning traitlets will not catch a number of :any:`BaseException` s anymore.
- :ghpull:`515` Add a class decorator to enable tab completion of keyword arguments in signature.
- :ghpull:`516` a ``Sentinel`` Traitlets was made public by mistake and is now deprecated.
- :ghpull:`517` use parent Logger within logggin configurable when possible.
- :ghpull:`522` Make loading config files idempotent and expose the list of loaded config files for long running services.

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
