Changes in Traitlets
====================

4.1
---

`4.1 on GitHub <https://github.com/ipython/traitlets/milestones/4.1>`__

Traitlets 4.1 introduces a totally new decorator-based API for configuring traitlets.
Highlights:

- Decorators are used, rather than magic method names, for registering trait-related methods. See :doc:`using_traitlets` and :doc:`migration` for more info.
- Deprecate ``Trait(config=True)`` in favor of ``Trait().tag(config=True)``. In general, metadata is added via ``tag`` instead of the constructor.

Other changes:

- Trait attributes initialized with `read_only=True` can only be set with the ``set_trait`` method. Attempts to
directly modify a read-only trait attribute raises a ``TraitError``.
- Various fixes and improvements to config-file generation (fixed ordering, Undefined showing up, etc.)
- Warn on unrecognized traits that aren't configurable, to avoid silently ignoring mistyped config.

4.0
---

`4.0 on GitHub <https://github.com/ipython/traitlets/milestones/4.0>`__

First release of traitlets as a standalone package.
