"""Tests for traitlets.config.manager"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import errno
import json
import os

import pytest

from traitlets.config.manager import BaseJSONConfigManager, recursive_update


def test_recursive_update_merges_nested_dicts():
    target = {"a": {"b": 1, "c": 2}, "d": 3}
    recursive_update(target, {"a": {"c": 20, "e": 5}})
    assert target == {"a": {"b": 1, "c": 20, "e": 5}, "d": 3}


def test_recursive_update_creates_missing_subdict():
    target = {}
    recursive_update(target, {"a": {"b": 1}})
    assert target == {"a": {"b": 1}}


def test_recursive_update_none_removes_key():
    target = {"a": 1, "b": 2}
    recursive_update(target, {"a": None, "never-there": None})
    assert target == {"b": 2}


def test_recursive_update_prunes_emptied_subdicts():
    target = {"a": {"b": 1}}
    recursive_update(target, {"a": {"b": None}})
    assert target == {}


def test_file_name_joins_the_config_dir(tmp_path):
    mgr = BaseJSONConfigManager(config_dir=str(tmp_path))
    assert mgr.file_name("section") == os.path.join(str(tmp_path), "section.json")


def test_get_missing_section_is_empty(tmp_path):
    mgr = BaseJSONConfigManager(config_dir=str(tmp_path))
    assert mgr.get("never-written") == {}


def test_set_then_get_roundtrips(tmp_path):
    mgr = BaseJSONConfigManager(config_dir=str(tmp_path))
    mgr.set("section", {"a": 1, "b": {"c": 2}})
    assert mgr.get("section") == {"a": 1, "b": {"c": 2}}
    on_disk = json.loads((tmp_path / "section.json").read_text(encoding="utf-8"))
    assert on_disk == {"a": 1, "b": {"c": 2}}


def test_set_creates_the_config_dir(tmp_path):
    config_dir = tmp_path / "not-yet-there"
    mgr = BaseJSONConfigManager(config_dir=str(config_dir))
    mgr.set("section", {"a": 1})
    assert config_dir.is_dir()


def test_ensure_config_dir_exists_tolerates_an_existing_dir(tmp_path):
    mgr = BaseJSONConfigManager(config_dir=str(tmp_path))
    mgr.ensure_config_dir_exists()
    mgr.ensure_config_dir_exists()
    assert tmp_path.is_dir()


def test_ensure_config_dir_exists_reraises_other_errors(tmp_path):
    # A file where a parent directory should be: the resulting error is not
    # EEXIST, so it must propagate rather than be swallowed.
    blocker = tmp_path / "a-file"
    blocker.write_text("not a directory", encoding="utf-8")
    mgr = BaseJSONConfigManager(config_dir=str(blocker / "sub"))
    with pytest.raises(OSError, match="sub") as excinfo:
        mgr.ensure_config_dir_exists()
    assert excinfo.value.errno != errno.EEXIST


def test_update_merges_into_the_stored_section(tmp_path):
    mgr = BaseJSONConfigManager(config_dir=str(tmp_path))
    mgr.set("section", {"a": {"b": 1}, "drop-me": True})
    result = mgr.update("section", {"a": {"c": 2}, "drop-me": None})
    assert result == {"a": {"b": 1, "c": 2}}
    assert mgr.get("section") == {"a": {"b": 1, "c": 2}}
