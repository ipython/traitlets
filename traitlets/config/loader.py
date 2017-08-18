# encoding: utf-8
"""A simple configuration system."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import argparse
from ast import literal_eval
import copy
import functools as fnt
import os
import re
import sys
import json
import warnings

from ipython_genutils.path import filefind
from ipython_genutils import py3compat
from ipython_genutils.encoding import DEFAULT_ENCODING
from six import text_type, string_types, PY3
from traitlets.traitlets import (
    HasTraits, Container, List, Dict, Any,
)

#-----------------------------------------------------------------------------
# Exceptions
#-----------------------------------------------------------------------------


class ConfigError(Exception):
    pass

class ConfigLoaderError(ConfigError):
    pass

class ConfigFileNotFound(ConfigError):
    pass

class ArgumentError(ConfigLoaderError):
    pass

#-----------------------------------------------------------------------------
# Argparse fix
#-----------------------------------------------------------------------------

# Unfortunately argparse by default prints help messages to stderr instead of
# stdout.  This makes it annoying to capture long help screens at the command
# line, since one must know how to pipe stderr, which many users don't know how
# to do.  So we override the print_help method with one that defaults to
# stdout and use our class instead.

class ArgumentParser(argparse.ArgumentParser):
    """Simple argparse subclass that prints help to stdout by default."""

    def print_help(self, file=None):
        if file is None:
            file = sys.stdout
        return super(ArgumentParser, self).print_help(file)

    print_help.__doc__ = argparse.ArgumentParser.print_help.__doc__

#-----------------------------------------------------------------------------
# Config class for holding config information
#-----------------------------------------------------------------------------

class LazyConfigValue(HasTraits):
    """Proxy object for exposing methods on configurable containers

    Exposes:

    - append, extend, insert on lists
    - update on dicts
    - update, add on sets
    """

    _value = None

    # list methods
    _extend = List()
    _prepend = List()

    def append(self, obj):
        self._extend.append(obj)

    def extend(self, other):
        self._extend.extend(other)

    def prepend(self, other):
        """like list.extend, but for the front"""
        self._prepend[:0] = other

    _inserts = List()
    def insert(self, index, other):
        if not isinstance(index, int):
            raise TypeError("An integer is required")
        self._inserts.append((index, other))

    # dict methods
    # update is used for both dict and set
    _update = Any()
    def update(self, other):
        if self._update is None:
            if isinstance(other, dict):
                self._update = {}
            else:
                self._update = set()
        self._update.update(other)

    # set methods
    def add(self, obj):
        self.update({obj})

    def get_value(self, initial):
        """construct the value from the initial one

        after applying any insert / extend / update changes
        """
        if self._value is not None:
            return self._value
        value = copy.deepcopy(initial)
        if isinstance(value, list):
            for idx, obj in self._inserts:
                value.insert(idx, obj)
            value[:0] = self._prepend
            value.extend(self._extend)

        elif isinstance(value, dict):
            if self._update:
                value.update(self._update)
        elif isinstance(value, set):
            if self._update:
                value.update(self._update)
        self._value = value
        return value

    def to_dict(self):
        """return JSONable dict form of my data

        Currently update as dict or set, extend, prepend as lists, and inserts as list of tuples.
        """
        d = {}
        if self._update:
            d['update'] = self._update
        if self._extend:
            d['extend'] = self._extend
        if self._prepend:
            d['prepend'] = self._prepend
        elif self._inserts:
            d['inserts'] = self._inserts
        return d

    def __repr__(self):
        if self._value is not None:
            return "<%s value=%r>" % (self.__class__.__name__, self._value)
        else:
            return "<%s %r>" % (self.__class__.__name__, self.to_dict())


def _is_section_key(key):
    """Is a Config key a section name (does it start with a capital)?"""
    if key and key[0].upper()==key[0] and not key.startswith('_'):
        return True
    else:
        return False


class Config(dict):
    """An attribute based dict that can do smart merges."""

    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self._ensure_subconfig()

    def _ensure_subconfig(self):
        """ensure that sub-dicts that should be Config objects are

        casts dicts that are under section keys to Config objects,
        which is necessary for constructing Config objects from dict literals.
        """
        for key in self:
            obj = self[key]
            if _is_section_key(key) \
                    and isinstance(obj, dict) \
                    and not isinstance(obj, Config):
                setattr(self, key, Config(obj))

    def _merge(self, other):
        """deprecated alias, use Config.merge()"""
        self.merge(other)

    def merge(self, other):
        """merge another config object into this one"""
        to_update = {}
        for k, v in other.items():
            if k not in self:
                to_update[k] = v
            else: # I have this key
                if isinstance(v, Config) and isinstance(self[k], Config):
                    # Recursively merge common sub Configs
                    self[k].merge(v)
                else:
                    # Plain updates for non-Configs
                    to_update[k] = v

        self.update(to_update)

    def collisions(self, other):
        """Check for collisions between two config objects.

        Returns a dict of the form {"Class": {"trait": "collision message"}}`,
        indicating which values have been ignored.

        An empty dict indicates no collisions.
        """
        collisions = {}
        for section in self:
            if section not in other:
                continue
            mine = self[section]
            theirs = other[section]
            for key in mine:
                if key in theirs and mine[key] != theirs[key]:
                    collisions.setdefault(section, {})
                    collisions[section][key] = "%r ignored, using %r" % (mine[key], theirs[key])
        return collisions

    def __contains__(self, key):
        # allow nested contains of the form `"Section.key" in config`
        if '.' in key:
            first, remainder = key.split('.', 1)
            if first not in self:
                return False
            return remainder in self[first]

        return super(Config, self).__contains__(key)

    # .has_key is deprecated for dictionaries.
    has_key = __contains__

    def _has_section(self, key):
        return _is_section_key(key) and key in self

    def copy(self):
        return type(self)(dict.copy(self))

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        new_config = type(self)()
        for key, value in self.items():
            if isinstance(value, (Config, LazyConfigValue)):
                # deep copy config objects
                value = copy.deepcopy(value, memo)
            elif type(value) in {dict, list, set, tuple}:
                # shallow copy plain container traits
                value = copy.copy(value)
            new_config[key] = value
        return new_config

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            if _is_section_key(key):
                c = Config()
                dict.__setitem__(self, key, c)
                return c
            elif not key.startswith('_'):
                # undefined, create lazy value, used for container methods
                v = LazyConfigValue()
                dict.__setitem__(self, key, v)
                return v
            else:
                raise KeyError

    def __setitem__(self, key, value):
        if _is_section_key(key):
            if not isinstance(value, Config):
                raise ValueError('values whose keys begin with an uppercase '
                                 'char must be Config instances: %r, %r' % (key, value))
        dict.__setitem__(self, key, value)

    def __getattr__(self, key):
        if key.startswith('__'):
            return dict.__getattr__(self, key)
        try:
            return self.__getitem__(key)
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, key, value):
        if key.startswith('__'):
            return dict.__setattr__(self, key, value)
        try:
            self.__setitem__(key, value)
        except KeyError as e:
            raise AttributeError(e)

    def __delattr__(self, key):
        if key.startswith('__'):
            return dict.__delattr__(self, key)
        try:
            dict.__delitem__(self, key)
        except KeyError as e:
            raise AttributeError(e)


class DeferredConfigString(text_type):
    """Config value for loading config from a string

    Interpretation is deferred until it is loaded into the trait.

    Subclass of unicode for backward compatibility.

    This class is only used for values that are not listed
    in the configurable classes.

    When config is loaded, `trait.from_string` will be used.
    
    If an error is raised

    .. versionadded:: 5.0
    """
    def get_value(self, trait):
        """Get the value stored in this string"""
        s = text_type(self)
        try:
            return trait.from_string(s)
        except Exception:
            # exception casting from string,
            # let the original string lie.
            # this will raise a more informative error when config is loaded.
            return s

    def __repr__(self):
        super_repr = super(DeferredConfigString, self).__repr__()
        return '%s(%s)' % (self.__class__.__name__, super_repr)


#-----------------------------------------------------------------------------
# Config loading classes
#-----------------------------------------------------------------------------


class ConfigLoader(object):
    """A object for loading configurations from just about anywhere.

    The resulting configuration is packaged as a :class:`Config`.

    Notes
    -----
    A :class:`ConfigLoader` does one thing: load a config from a source
    (file, command line arguments) and returns the data as a :class:`Config` object.
    There are lots of things that :class:`ConfigLoader` does not do.  It does
    not implement complex logic for finding config files.  It does not handle
    default values or merge multiple configs.  These things need to be
    handled elsewhere.
    """

    def _log_default(self):
        from traitlets.log import get_logger
        return get_logger()

    def __init__(self, log=None):
        """A base class for config loaders.

        log : instance of :class:`logging.Logger` to use.
              By default loger of :meth:`traitlets.config.application.Application.instance()`
              will be used

        Examples
        --------

        >>> cl = ConfigLoader()
        >>> config = cl.load_config()
        >>> config
        {}
        """
        self.clear()
        if log is None:
            self.log = self._log_default()
            self.log.debug('Using default logger')
        else:
            self.log = log

    def clear(self):
        self.config = Config()

    def load_config(self):
        """Load a config from somewhere, return a :class:`Config` instance.

        Usually, this will cause self.config to be set and then returned.
        However, in most cases, :meth:`ConfigLoader.clear` should be called
        to erase any previous state.
        """
        self.clear()
        return self.config


class FileConfigLoader(ConfigLoader):
    """A base class for file based configurations.

    As we add more file based config loaders, the common logic should go
    here.
    """

    def __init__(self, filename, path=None, **kw):
        """Build a config loader for a filename and path.

        Parameters
        ----------
        filename : str
            The file name of the config file.
        path : str, list, tuple
            The path to search for the config file on, or a sequence of
            paths to try in order.
        """
        super(FileConfigLoader, self).__init__(**kw)
        self.filename = filename
        self.path = path
        self.full_filename = ''

    def _find_file(self):
        """Try to find the file by searching the paths."""
        self.full_filename = filefind(self.filename, self.path)

class JSONFileConfigLoader(FileConfigLoader):
    """A JSON file loader for config

    Can also act as a context manager that rewrite the configuration file to disk on exit.

    Example::

        with JSONFileConfigLoader('myapp.json','/home/jupyter/configurations/') as c:
            c.MyNewConfigurable.new_value = 'Updated'

    """

    def load_config(self):
        """Load the config from a file and return it as a Config object."""
        self.clear()
        try:
            self._find_file()
        except IOError as e:
            raise ConfigFileNotFound(str(e))
        dct = self._read_file_as_dict()
        self.config = self._convert_to_config(dct)
        return self.config

    def _read_file_as_dict(self):
        with open(self.full_filename) as f:
            return json.load(f)

    def _convert_to_config(self, dictionary):
        if 'version' in dictionary:
            version = dictionary.pop('version')
        else:
            version = 1

        if version == 1:
            return Config(dictionary)
        else:
            raise ValueError('Unknown version of JSON config file: {version}'.format(version=version))

    def __enter__(self):
        self.load_config()
        return self.config

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager but do not handle any errors.

        In case of any error, we do not want to write the potentially broken
        configuration to disk.
        """
        self.config.version = 1
        json_config = json.dumps(self.config, indent=2)
        with open(self.full_filename, 'w') as f:
            f.write(json_config)



class PyFileConfigLoader(FileConfigLoader):
    """A config loader for pure python files.

    This is responsible for locating a Python config file by filename and
    path, then executing it to construct a Config object.
    """

    def load_config(self):
        """Load the config from a file and return it as a Config object."""
        self.clear()
        try:
            self._find_file()
        except IOError as e:
            raise ConfigFileNotFound(str(e))
        self._read_file_as_dict()
        return self.config

    def load_subconfig(self, fname, path=None):
        """Injected into config file namespace as load_subconfig"""
        if path is None:
            path = self.path

        loader = self.__class__(fname, path)
        try:
            sub_config = loader.load_config()
        except ConfigFileNotFound:
            # Pass silently if the sub config is not there,
            # treat it as an empty config file.
            pass
        else:
            self.config.merge(sub_config)

    def _read_file_as_dict(self):
        """Load the config file into self.config, with recursive loading."""
        def get_config():
            """Unnecessary now, but a deprecation warning is more trouble than it's worth."""
            return self.config

        namespace = dict(
            c=self.config,
            load_subconfig=self.load_subconfig,
            get_config=get_config,
            __file__=self.full_filename,
        )
        # encode filename to bytes only on py2 on non-Windows:
        if PY3 or sys.platform.startswith('win'):
            conf_filename = self.full_filename
        else:
            fs_encoding = sys.getfilesystemencoding() or 'ascii'
            conf_filename = self.full_filename.encode(fs_encoding)
        py3compat.execfile(conf_filename, namespace)


class CommandLineConfigLoader(ConfigLoader):
    """A config loader for command line arguments.

    As we add more command line based loaders, the common logic should go
    here.
    """

    def _parse_config_value(self, rhs, trait=None):
        """Python-evaluates any cmd-line argument values."""
        rhs = os.path.expanduser(rhs)
        if len(rhs) > 2:
            # handle deprecated "1"
            for c in "'\"":
                if rhs[0] == rhs[-1] == c:
                    old_rhs = rhs
                    rhs = rhs[1:-1]
                    warnings.warn(
                        "Supporting extra quotes around strings is deprecated in traitlets 5.0. "
                        "Use %r instead of %r" % (rhs, old_rhs),
                        DeprecationWarning)
        if trait:
            try:
                return trait.from_string(rhs)
            except Exception:
                # failed to eval, let later config loading raise,
                # which will be more informative
                return rhs
        else:
            return DeferredConfigString(rhs)

    def _exec_config_str(self, lhs, rhs, trait=None):
        """execute self.config.<lhs> = <rhs>

        * expands ~ with expanduser
        * interprets value with trait if available
        """
        if isinstance(trait, Dict) and not isinstance(rhs, string_types):
            if len(rhs) == 1 and isinstance(rhs[0], string_types):
                # check for deprecated --Class.trait="{'a': 'b'}"
                self.log.warning(
                    "--{0}={1} for dict-traits is deprecated in traitlets 5.0. "
                    "You can pass --{0} <key=value> ... multiple times to add items to a dict.".format(
                        lhs, rhs[0])
                )
                value = literal_eval(rhs[0])
            else:
                # FIXME: get trait for values
                value = {}
                for k, v in rhs:
                    value_trait = (trait._per_key_traits or {}).get(k, trait._value_trait)
                    if value_trait:
                        value[k] = self._parse_config_value(v, value_trait)
                    else:
                        # no trait, use str
                        # non-str values can only be passed this way
                        # if the dict trait defines value traits
                        value[k] = v

        elif isinstance(rhs, (list, tuple)):
            value = None
            if len(rhs) == 1 and len(rhs[0]) > 0:
                # check for deprecated --Class.trait="['a', 'b', 'c']"
                r = rhs[0]
                if (
                    (r[0] == '[' and r[-1] == ']') or
                    (r[0] == '(' and r[-1] == ')')
                ):
                    self.log.warning(
                        "--{0}={1} for containers is deprecated in traitlets 5.0. "
                        "You can pass --{0} item ... multiple times to add items to a list.".format(
                            lhs, rhs)
                    )
                    value = self._parse_config_value(r, trait)

            if value is None:
                if trait:
                    value_trait = getattr(trait, "_trait")
                else:
                    value_trait = None
                if value_trait:
                    value = [self._parse_config_value(r, value_trait) for r in rhs]
                else:
                    # no trait, use strings
                    value = [r for r in rhs]
        else:
            value = self._parse_config_value(rhs, trait)

        exec(u'self.config.%s = value' % lhs, None, locals())

    def _load_flag(self, cfg):
        """update self.config from a flag, which can be a dict or Config"""
        if isinstance(cfg, (dict, Config)):
            # don't clobber whole config sections, update
            # each section from config:
            for sec,c in cfg.items():
                self.config[sec].update(c)
        else:
            raise TypeError("Invalid flag: %r" % cfg)

# raw --identifier=value pattern
# but *also* accept '-' as wordsep, for aliases
# accepts:  --foo=a
#           --Class.trait=value
#           --alias-name=value
# rejects:  -foo=value
#           --foo
#           --Class.trait
kv_pattern = re.compile(r'\-\-[A-Za-z][\w\-]*(\.[\w\-]+)*\=.*')

# just flags, no assignments, with two *or one* leading '-'
# accepts:  --foo
#           -foo-bar-again
# rejects:  --anything=anything
#           --two.word

flag_pattern = re.compile(r'\-\-?\w+[\-\w]*$')

class KeyValueConfigLoader(CommandLineConfigLoader):
    """A config loader that loads key value pairs from the command line.

    This allows command line options to be gives in the following form::

        ipython --profile="foo" --InteractiveShell.autocall=False
    """

    def __init__(self, argv=None, aliases=None, flags=None, classes=None, **kw):
        """Create a key value pair config loader.

        Parameters
        ----------
        argv : list
            A list that has the form of sys.argv[1:] which has unicode
            elements of the form u"key=value". If this is None (default),
            then sys.argv[1:] will be used.
        aliases : dict
            A dict of aliases for configurable traits.
            Keys are the short aliases, Values are the resolved trait.
            Of the form: `{'alias' : 'Configurable.trait'}`
        flags : dict
            A dict of flags, keyed by str name. Values can be Config objects,
            dicts, or "key=value" strings.  If Config or dict, when the flag
            is triggered, The flag is loaded as `self.config.update(m)`.
        classes : sequence
            A list/tuple of classes that are to be configured.
            Classes included in this list

        Returns
        -------
        config : Config
            The resulting Config object.

        Examples
        --------

            >>> from traitlets.config.loader import KeyValueConfigLoader
            >>> cl = KeyValueConfigLoader()
            >>> d = cl.load_config(["--A.name='brian'","--B.number=0"])
            >>> sorted(d.items())
            [('A', {'name': 'brian'}), ('B', {'number': 0})]
        """
        super(KeyValueConfigLoader, self).__init__(**kw)
        if argv is None:
            argv = sys.argv[1:]
        self.argv = argv
        self.aliases = aliases or {}
        self.flags = flags or {}
        self.classes = classes or ()


    def clear(self):
        super(KeyValueConfigLoader, self).clear()
        self.extra_args = []


    def _decode_argv(self, argv, enc=None):
        """decode argv if bytes, using stdin.encoding, falling back on default enc"""
        uargv = []
        if enc is None:
            enc = DEFAULT_ENCODING
        for arg in argv:
            if not isinstance(arg, text_type):
                # only decode if not already decoded
                arg = arg.decode(enc)
            uargv.append(arg)
        return uargv

    def _find_trait(self, lhs):
        """Find the trait for a Class.trait string"""
        
        from .configurable import Configurable
        class_name, trait_name = lhs.split('.')[-2:]
        for cls in self.classes:
            for parent in cls.mro():
                if (
                    issubclass(parent, Configurable) and
                    parent.__name__ == class_name
                ):
                    return parent.class_traits().get(trait_name)
        return None

    def load_config(self, argv=None, aliases=None, flags=None):
        """Parse the configuration and generate the Config object.

        After loading, any arguments that are not key-value or
        flags will be stored in self.extra_args - a list of
        unparsed command-line arguments.  This is used for
        arguments such as input files or subcommands.

        Parameters
        ----------
        argv : list, optional
            A list that has the form of sys.argv[1:] which has unicode
            elements of the form u"key=value". If this is None (default),
            then self.argv will be used.
        aliases : dict
            A dict of aliases for configurable traits.
            Keys are the short aliases, Values are the resolved trait.
            Of the form: `{'alias' : 'Configurable.trait'}`
        flags : dict
            A dict of flags, keyed by str name. Values can be Config objects
            or dicts.  When the flag is triggered, The config is loaded as
            `self.config.update(cfg)`.
        """
        self.clear()
        if argv is None:
            argv = self.argv
        if aliases is None:
            aliases = self.aliases
        if flags is None:
            flags = self.flags

        # ensure argv is a list of unicode strings:
        uargv = self._decode_argv(argv)
        for idx, raw in enumerate(uargv):
            if raw == '--':
                # Don't parse arguments after '--'.
                # This is useful for relaying arguments to scripts, e.g.:
                #     ipython -i foo.py --matplotlib=qt -- args after '--' go-to-foo.py
                self.extra_args.extend(uargv[idx + 1:])
                break

            # strip leading '-'
            item = raw.lstrip('-')

            if not item:
                ## It was either a lone '-' (i.e. denoting STDIN),
                #  or more than 3 '---'; append it as is.
                self.extra_args.append(raw)
                continue

            if kv_pattern.match(raw):
                lhs, rhs = item.split('=', 1)
                # Substitute longnames for aliases.
                if lhs in aliases:
                    lhs = aliases[lhs]
                if '.' not in lhs:
                    # probably a mistyped alias, but not technically illegal
                    self.log.warning("Unrecognized alias: '%s', it will have no effect.", raw)
                    trait = None
                else:
                    trait = self._find_trait(lhs)
                try:
                    self._exec_config_str(lhs, rhs, trait)
                except Exception:
                    raise
                    raise ArgumentError("Invalid argument: '%s'" % raw)

            elif flag_pattern.match(raw):
                if item in flags:
                    cfg, _ = flags[item]
                    self._load_flag(cfg)
                else:
                    raise ArgumentError("Unrecognized flag: '%s'" % raw)
            elif raw.startswith('-'):
                kv = '--' + item
                if kv_pattern.match(kv):
                    raise ArgumentError("Invalid argument: '%s', did you mean '%s'?" % (raw, kv))
                else:
                    raise ArgumentError("Invalid argument: '%s'" % raw)
            else:
                # keep all args that aren't valid in a list,
                # in case our parent knows what to do with them.
                self.extra_args.append(item)
        return self.config


class ArgParseConfigLoader(CommandLineConfigLoader):
    """A loader that uses the argparse module to load from the command line."""

    def __init__(self, argv=None, aliases=None, flags=None, log=None, classes=(),
                 *parser_args, **parser_kw):
        """Create a config loader for use with argparse.

        Parameters
        ----------

        classes : optional, list
          The classes to scan for *container* config-traits and decide
          for their "multiplicity" when adding them as *argparse* arguments.

        argv : optional, list
          If given, used to read command-line arguments from, otherwise
          sys.argv[1:] is used.

        parser_args : tuple
          A tuple of positional arguments that will be passed to the
          constructor of :class:`argparse.ArgumentParser`.

        parser_kw : dict
          A tuple of keyword arguments that will be passed to the
          constructor of :class:`argparse.ArgumentParser`.

        Returns
        -------
        config : Config
            The resulting Config object.
        """
        super(CommandLineConfigLoader, self).__init__(log=log)
        self.clear()
        if argv is None:
            argv = sys.argv[1:]
        self.argv = argv
        self.aliases = aliases or {}
        self.flags = flags or {}
        self.classes = classes

        self.parser_args = parser_args
        self.version = parser_kw.pop("version", None)
        kwargs = dict(argument_default=argparse.SUPPRESS)
        kwargs.update(parser_kw)
        self.parser_kw = kwargs

    def load_config(self, argv=None, aliases=None, flags=None, classes=None):
        """Parse command line arguments and return as a Config object.

        Parameters
        ----------

        args : optional, list
          If given, a list with the structure of sys.argv[1:] to parse
          arguments from. If not given, the instance's self.argv attribute
          (given at construction time) is used."""
        self.clear()
        if argv is None:
            argv = self.argv
        self._create_parser(aliases, flags, classes)
        self._parse_args(argv)
        self._convert_to_config()
        return self.config

    def get_extra_args(self):
        if hasattr(self, 'extra_args'):
            return self.extra_args
        else:
            return []

    def _create_parser(self, aliases=None, flags=None, classes=None):
        self.parser = ArgumentParser(*self.parser_args, **self.parser_kw)
        self._add_arguments(aliases, flags, classes)

    def _add_arguments(self, aliases=None, flags=None, classes=None):
        raise NotImplementedError("subclasses must implement _add_arguments")

    def _parse_args(self, args):
        """self.parser->self.parsed_data"""
        # decode sys.argv to support unicode command-line options
        enc = DEFAULT_ENCODING
        uargs = [py3compat.cast_unicode(a, enc) for a in args]
        self.parsed_data, self.extra_args = self.parser.parse_known_args(uargs)

    def _convert_to_config(self):
        """self.parsed_data->self.config"""
        for k, v in vars(self.parsed_data).items():
            exec("self.config.%s = v"%k, locals(), globals())

## For Dict traits, describes the cmd-line option as `key=value`
_kv_opt_pattern = re.compile(r'^([^=]+)=(.*)$')

def _kv_opt(traitname, opt_value):
    """
    Used as `type` when adding args into :meth:`ArgumentParser.add_argument()`
    corresponding to config Dict-traits.
    """
    if opt_value[0] == '{' and opt_value[-1] == '}' and ':' in opt_value:
        # leave opt_value as a string for parsing later
        return opt_value

    m = _kv_opt_pattern.match(opt_value)
    if not m:
        raise ArgumentError("Expecting <key>=<value> for Dict-trait '%s', got %r!"
                            % (traitname, opt_value))
    return m.groups()


class KVArgParseConfigLoader(ArgParseConfigLoader):
    """A config loader that loads aliases and flags with argparse,
    but will use KVLoader for the rest.  This allows better parsing
    of common args, such as `ipython -c 'print 5'`, but still gets
    arbitrary config with `ipython --InteractiveShell.autoindent=False`"""

    def _add_arguments(self, aliases=None, flags=None, classes=None):
        self.alias_flags = {}
        # print aliases, flags
        if aliases is None:
            aliases = self.aliases
        if flags is None:
            flags = self.flags
        if classes is None:
            classes = self.classes
        paa = self.parser.add_argument

        ## An index of all container traits collected::
        #
        #     { <traitname>: (<trait>, <argparse-kwds>) }
        #
        #  Used to add the correct type into the `config` tree.
        #  Used also for aliases, not to re-collect them.
        self.argparse_traits = argparse_traits = {}
        for cls in classes:
            for traitname, trait in cls.class_traits(config=True).items():
                argname = '%s.%s' % (cls.__name__, traitname)
                argparse_kwds = {'type': text_type}
                if isinstance(trait, (Container, Dict)):
                    multiplicity = trait.metadata.get('multiplicity', 'append')
                    if multiplicity == 'append':
                        argparse_kwds['action'] = multiplicity
                    else:
                        argparse_kwds['nargs'] = multiplicity
                    if isinstance(trait, Dict):
                        argparse_kwds['type'] = fnt.partial(_kv_opt, traitname)
                argparse_traits[argname] = (trait, argparse_kwds)
                paa('--'+argname, **argparse_kwds)

        for keys, traitname in aliases.items():
            if not isinstance(keys, tuple):
                keys = (keys, )
            for key in keys:
                argparse_kwds = {'type': text_type, 'dest': traitname}
                ## Is alias for a sequence-trait?
                #
                if traitname in argparse_traits:
                    argparse_kwds.update(argparse_traits[traitname][1])
                    if 'action' in argparse_kwds:
                        ## A flag+alias should have `nargs='?'` multiplicity,
                        #  but base config-property had 'append' multiplicity!
                        #
                        if key in flags:
                            raise ArgumentError(
                                "The alias `%s` for the 'append' sequence "
                                "config-trait `%s` cannot be also a flag!'"
                                % (key, traitname))
                else:
                    if key in flags:
                        argparse_kwds['nargs'] = '?'
                keys = ('-'+key, '--'+key) if len(key) is 1 else ('--'+key, )
                paa(*keys, **argparse_kwds)

        for keys, (value, _) in flags.items():
            if not isinstance(keys, tuple):
                keys = (keys, )
            for key in keys:
                if key in self.aliases:
                    self.alias_flags[self.aliases[key]] = value
                    continue
                keys = ('-'+key, '--'+key) if len(key) is 1 else ('--'+key, )
                paa(*keys, action='append_const', dest='_flags', const=value)

    def _convert_to_config(self):
        """self.parsed_data->self.config, parse unrecognized extra args via KVLoader."""
        # remove subconfigs list from namespace before transforming the Namespace
        if '_flags' in self.parsed_data:
            subcs = self.parsed_data._flags
            del self.parsed_data._flags
        else:
            subcs = []

        for k, v in vars(self.parsed_data).items():
            if v is None:
                # it was a flag that shares the name of an alias
                subcs.append(self.alias_flags[k])
            else:
                trait = self.argparse_traits.get(k)
                if trait:
                    trait = trait[0]
                # eval the KV assignment
                self._exec_config_str(k, v, trait=trait)

        for subc in subcs:
            self._load_flag(subc)

        if self.extra_args:
            sub_parser = KeyValueConfigLoader(log=self.log, classes=self.classes)
            sub_parser.load_config(self.extra_args)
            self.config.merge(sub_parser.config)
            self.extra_args = sub_parser.extra_args


def load_pyconfig_files(config_files, path):
    """Load multiple Python config files, merging each of them in turn.

    Parameters
    ==========
    config_files : list of str
        List of config files names to load and merge into the config.
    path : unicode
        The full path to the location of the config files.
    """
    config = Config()
    for cf in config_files:
        loader = PyFileConfigLoader(cf, path=path)
        try:
            next_config = loader.load_config()
        except ConfigFileNotFound:
            pass
        except:
            raise
        else:
            config.merge(next_config)
    return config
