"""Manager to read and modify config data in JSON files.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import errno
import io
import json
import os

from six import PY3
from traitlets.config import LoggingConfigurable
from traitlets.traitlets import Unicode, Bool


def recursive_update(target, new):
    """Recursively update one dictionary using another.

    None values will delete their keys.
    """
    for k, v in new.items():
        if isinstance(v, dict):
            if k not in target:
                target[k] = {}
            recursive_update(target[k], v)
            if not target[k]:
                # Prune empty subdicts
                del target[k]

        elif v is None:
            target.pop(k, None)

        else:
            target[k] = v


class BaseJSONConfigManager(LoggingConfigurable):
    """General JSON config manager
    
    Deals with persisting/storing config in a json file with optionally
    default values in a {section_name}.d directory.
    """

    config_dir = Unicode('.')
    read_directory = Bool(True)

    def ensure_config_dir_exists(self):
        try:
            os.makedirs(self.config_dir, 0o755)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    def file_name(self, section_name):
        return os.path.join(self.config_dir, section_name+'.json')

    def directory(self, section_name):
        return os.path.join(self.config_dir, section_name+'.d')

    def get(self, section_name):
        """Retrieve the config data for the specified section.

        Returns the data as a dictionary, or an empty dictionary if the file
        doesn't exist.
        """
        filename = self.file_name(section_name)
        data = {}
        if self.read_directory:
            directory = self.directory(section_name)
            if os.path.isdir(directory):
                paths = os.listdir(directory)
                for path in sorted(paths):
                    name, ext = os.path.splitext(path)
                    abspath = os.path.join(directory, path)
                    if ext == ".json" and name not in data:
                        with io.open(abspath, encoding='utf-8') as f:
                            more_defaults = json.load(f)
                        recursive_update(data, more_defaults)
        if os.path.isfile(filename):
            with io.open(filename, encoding='utf-8') as f:
                new_data = json.load(f)
            recursive_update(data, new_data)
        return data

    def set(self, section_name, data):
        """Store the given config data.
        """
        filename = self.file_name(section_name)
        self.ensure_config_dir_exists()

        if PY3:
            f = io.open(filename, 'w', encoding='utf-8')
        else:
            f = open(filename, 'wb')
        with f:
            json.dump(data, f, indent=2)

    def update(self, section_name, new_data):
        """Modify the config section by recursively updating it with new_data.

        Returns the modified config data as a dictionary.
        """
        data = self.get(section_name)
        recursive_update(data, new_data)
        self.set(section_name, data)
        return data
