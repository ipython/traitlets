We closed 5 issues and merged 115 pull requests.
The full list can be seen `on GitHub <https://github.com/ipython/traitlets/issues?q=milestone%3A5.0>`__

The following 34 authors contributed 465 commits.

* Adam Chainz
* Albert Zeyer
* Aliaksei Urbanski
* Benjamin Ragan-Kelley
* Carol Willing
* Christian Clauss
* Conner Cowling
* Dan Allan
* David Brochart
* Francisco de la Peña
* Frédéric Chapoton
* Hans Moritz Günther
* Jake VanderPlas
* Jason Grout
* Jeroen Demeyer
* Kevin Bates
* Kostis Anagnostopoulos
* Kyle Kelley
* Leo Gallucci
* Leonardo Uieda
* Lumir Balhar
* maartenbreddels
* martinRenou
* Matthias Bussonnier
* Ryan Morshead
* Sylvain Corlay
* Thomas Aarholt
* Thomas Kluyver
* Tim Paine
* Todd
* Travis DePrato
* Vidar Tonaas Fauske
* William Krinsman
* Yves Delley

GitHub issues and pull requests:

Pull Requests (115):

* :ghpull:`576`: more removal of Python 2 specificity
* :ghpull:`575`: finish first pass on whats new
* :ghpull:`574`: more version_info removal
* :ghpull:`573`: Some removal of Python 2 compatibility (in particular six)
* :ghpull:`572`: review a few more PRs.
* :ghpull:`570`: review more PRs changelog and reorder
* :ghpull:`571`: remove PY2 compat + isort + pyupgrade + darker
* :ghpull:`567`: fixup changelog
* :ghpull:`566`: Changelog part 1
* :ghpull:`565`: Fix doc formatting.
* :ghpull:`563`: Stop testing traittypes which fails.
* :ghpull:`562`: Travis CI: Fix Travis build configuration validation issues
* :ghpull:`561`: Travis CI: Run tests on Python 3.8, not 3.7
* :ghpull:`543`: Travis CI: Test the current versions of Python
* :ghpull:`531`: Update myapp.py
* :ghpull:`546`: Export Bunch
* :ghpull:`547`: Unpin Python 3.5 for docs
* :ghpull:`559`: Start testing on current Python versions.
* :ghpull:`556`: add callable test for master
* :ghpull:`542`: typo
* :ghpull:`515`: Add trait-names autocompletion support
* :ghpull:`529`: Minor addition to docs
* :ghpull:`528`: Fix formatting.
* :ghpull:`526`: Fix tests for ipywidgets
* :ghpull:`525`: Fix backward compatibility and tests
* :ghpull:`522`: Expose loaded config files, make load idempotent
* :ghpull:`524`: Fix SyntaxWarning: "is" with a literal.
* :ghpull:`523`: DOC: Add Callable to docs.
* :ghpull:`509`: do not catch system exceptions like KeyboardInterrupt
* :ghpull:`501`: Preserve Class Repr After ``add_traits``
* :ghpull:`517`: Use log from parent in LoggingConfigurable.
* :ghpull:`516`: Fix CI
* :ghpull:`510`: remove one useless return line
* :ghpull:`493`: Include LICENSE file in wheels
* :ghpull:`491`: Add missing ``default`` import to run the example
* :ghpull:`489`: Update link to enthought trait library
* :ghpull:`484`: Add imports to "Using Traitlets" docs
* :ghpull:`482`: Fix copy(HasTraits) by copying ``_trait_values`` dict
* :ghpull:`483`: Appveyor has started failing when upgrading ``pip``
* :ghpull:`473`: test some downstream projects
* :ghpull:`464`: Drop dependency on decorator package
* :ghpull:`462`: drop Python 3.3, update to use 3.6
* :ghpull:`458`: Add Sphinx extension and autogen function for documenting config options
* :ghpull:`453`: Remove extra backtics from class link
* :ghpull:`407`: fix flags & aliases with the same name
* :ghpull:`438`: fix(help): finish #381 for RsT to print enum-choices
* :ghpull:`393`: Link tranform
* :ghpull:`440`: Fix getting class for deprecation warning
* :ghpull:`436`: Fix overriding ``_trait_default`` method
* :ghpull:`437`: Don't call notify_change with non-change events
* :ghpull:`434`: disable cross-validation of defaults
* :ghpull:`413`: Has Trait Value Method
* :ghpull:`416`: whitelist traitlets exports
* :ghpull:`426`: Explain the casing/substring matching of Enums on help-msgs and errors
* :ghpull:`424`: refact(log): consolidate some duplicate log statements
* :ghpull:`430`: Fix parsing of deprecated list options failing with empty strings
* :ghpull:`433`: fix(help): a yield had been forgotten from #405
* :ghpull:`422`: fix(help): minor typo in print_examples()
* :ghpull:`420`: BUG: remove redundant call to List.validate_elements
* :ghpull:`418`: remove incorrect version arg from json config doc
* :ghpull:`415`: follow mro for trait default generators
* :ghpull:`414`: fix instance error message
* :ghpull:`402`: Better Errors for Nested Traits
* :ghpull:`405`: feat(app): provide help-functions also as generators of text-lines
* :ghpull:`406`: update pip before install
* :ghpull:`404`: Tell about help-all last.
* :ghpull:`371`: New FuzzyEnum trait that matches case-insensitive prefixes/substrings
* :ghpull:`392`: style(cfg): apply review items in #385 for gen-config
* :ghpull:`384`: add ``trait_values`` method
* :ghpull:`399`: test on appveyor
* :ghpull:`391`: Suppress Redundant Configurable Validation
* :ghpull:`341`: add Application.show_config[_json]
* :ghpull:`396`: Ensure config loader tests include unicode
* :ghpull:`394`: Add link method to link and dlink
* :ghpull:`398`: explain which singleton is already instanciated
* :ghpull:`385`: generate all config, not just new traits on each class
* :ghpull:`383`: notify on default creation
* :ghpull:`381`: feat(cfg): write also enum choices when generating config.py files
* :ghpull:`257`: [WIP] make This inherit from Instance and add ThisType
* :ghpull:`380`: feat(app): iterate Configurable base-classes for non ``app.classes`` lists
* :ghpull:`368`: README: Addd links-table from index, improve opening
* :ghpull:`365`: FIX: KVConfigLoader could not handle lone dashes('-') as extra arguments
* :ghpull:`364`: Re-enable TC-code for subcmds forgotten by #362
* :ghpull:`367`: Fix a bug in TraitType.default
* :ghpull:`362`: Support callable subcommands
* :ghpull:`361`: help: Alias overriding help-text (like flags), options list human-help before automated infos
* :ghpull:`360`: Add factory method on Application for customizing the Loader parsing cmd-line args
* :ghpull:`354`: Improve generated help and config messages
* :ghpull:`359`: Pin docs build to Python 3.5
* :ghpull:`356`: Allow "cls" and "self" as keyword argument in __new__
* :ghpull:`346`: invert class/instance initialize priority in union "subtraits"
* :ghpull:`347`: test union valdiation priority
* :ghpull:`353`: Don't warn about correctly decorated default-value generators
* :ghpull:`355`: Merge class config dicts when flattening flags
* :ghpull:`350`: further clarify Dict docstring
* :ghpull:`306`: added a key_trait argument to Dict
* :ghpull:`340`: reintroduce deprecated support for old-style container args
* :ghpull:`338`: [proposal] Make new argparse container CLI opt-in
* :ghpull:`349`: Consolidated TraitType Defaults Into One Generator
* :ghpull:`343`: Any should allow None by default
* :ghpull:`332`: Create All Default Values With Generators
* :ghpull:`337`: Enable deprecation warnings during test-suite.
* :ghpull:`339`: nicer repr of LazyConfigValues
* :ghpull:`333`: Add a Callable Trait
* :ghpull:`322`: Use argparse to configure container-traits from command-line
* :ghpull:`331`: Update examples to use an IPython config option which still exists
* :ghpull:`330`: Convert readthedocs links for their .org -> .io migration for hosted projects
* :ghpull:`329`: setup.py - set url to github repo
* :ghpull:`319`: app: support flags/aliases given as (--long, -short) tuple
* :ghpull:`320`: docs: Move changelog as /CHANGES.rst
* :ghpull:`324`: Add more cross-validation examples
* :ghpull:`323`: use simpler callable check for meta_eval
* :ghpull:`316`: Test on nightly and allow_failure.
* :ghpull:`299`: casting traits inherit from mixin
* :ghpull:`311`: use pip_install in readthedocs.yml

Issues (5):

* :ghissue:`287`: Default values are not cross-validated with ``@validation``
* :ghissue:`363`: Traitlets master breaks ipywidgets
* :ghissue:`417`: buggy recommendation for version param in json config traitlets/docs/source/config.rst
* :ghissue:`342`: Test failures in jack-of-none
* :ghissue:`256`: how to extend dynamic defaults with super
