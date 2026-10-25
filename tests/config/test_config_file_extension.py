from __future__ import annotations

from unittest import TestCase

import pytest

from traitlets import Integer
from traitlets.config import Application


class ExampleApp(Application):
    value = Integer(0).tag(config=True)


@pytest.fixture
def config_paths(tmp_path):
    py_path = tmp_path / "foo.py"
    json_path = tmp_path / "foo.json"
    py_path.write_text("c.ExampleApp.value = 10\n", encoding="utf-8")
    json_path.write_text('{"ExampleApp": {"value": 11}}', encoding="utf-8")
    return py_path, json_path


@pytest.mark.parametrize("suffix,value", [(".py", 10), (".json", 11)])
def test_explicit_absolute_path_only_loads_requested_file(config_paths, suffix, value):
    py_path, json_path = config_paths
    requested = py_path if suffix == ".py" else json_path
    app = ExampleApp(raise_config_file_errors=True)
    app.load_config_file(requested)
    assert app.value == value
    assert app.loaded_config_files == [str(requested)]


@pytest.mark.parametrize("suffix,value", [(".py", 10), (".json", 11)])
def test_explicit_relative_path_only_loads_requested_file(config_paths, suffix, value):
    py_path, json_path = config_paths
    requested = py_path if suffix == ".py" else json_path
    app = ExampleApp(raise_config_file_errors=True)
    app.load_config_file(requested.name, path=str(requested.parent))
    assert app.value == value
    assert app.loaded_config_files == [str(requested)]


def test_explicit_python_ignores_broken_json(config_paths):
    py_path, json_path = config_paths
    json_path.write_text("Invalid JSON", encoding="utf-8")
    app = ExampleApp(raise_config_file_errors=True)
    app.load_config_file(py_path)
    assert app.value == 10
    assert app.loaded_config_files == [str(py_path)]


def test_explicit_json_never_executes_python(config_paths):
    py_path, json_path = config_paths
    py_path.write_text("raise RuntimeError('unexpected Python execution')", encoding="utf-8")
    app = ExampleApp(raise_config_file_errors=True)
    app.load_config_file(json_path)
    assert app.value == 11
    assert app.loaded_config_files == [str(json_path)]


def test_basename_loads_both_in_legacy_order(config_paths):
    py_path, json_path = config_paths
    app = ExampleApp(raise_config_file_errors=True)
    app.load_config_file(str(py_path.with_suffix("")))
    assert app.value == 11
    assert app.loaded_config_files == [str(py_path), str(json_path)]


def test_dotted_basename_explicit_file(tmp_path):
    py_path = tmp_path / "app.v1.py"
    json_path = tmp_path / "app.v1.json"
    py_path.write_text("c.ExampleApp.value = 10", encoding="utf-8")
    json_path.write_text('{"ExampleApp": {"value": 11}}', encoding="utf-8")
    app = ExampleApp(raise_config_file_errors=True)
    app.load_config_file(py_path)
    assert app.value == 10
    assert app.loaded_config_files == [str(py_path)]


def test_path_priority_not_changed(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    (left / "foo.py").write_text("c.ExampleApp.value = 10", encoding="utf-8")
    (right / "foo.py").write_text("c.ExampleApp.value = 20", encoding="utf-8")
    (left / "foo.json").write_text('{"ExampleApp": {"value": 11}}', encoding="utf-8")
    (right / "foo.json").write_text('{"ExampleApp": {"value": 21}}', encoding="utf-8")
    app = ExampleApp(raise_config_file_errors=True)
    app.load_config_file("foo.py", path=[str(left), str(right)])
    assert app.value == 10
    assert app.loaded_config_files == [str(right / "foo.py"), str(left / "foo.py")]


def test_legacy_unknown_extension_behavior(tmp_path):
    # Before #850, unknown suffixes were stripped in load_config_file().
    py_path = tmp_path / "foo.py"
    py_path.write_text("c.ExampleApp.value = 10", encoding="utf-8")
    app = ExampleApp(raise_config_file_errors=True)
    app.load_config_file(tmp_path / "foo.unknown")
    assert app.value == 10
    assert app.loaded_config_files == [str(py_path)]


def test_basename_collision_warning(config_paths):
    py_path, _ = config_paths
    app = ExampleApp(raise_config_file_errors=True)
    with TestCase().assertLogs(app.log, level="WARNING") as captured:
        app.load_config_file("foo", path=str(py_path.parent))
    assert app.value == 11
    assert any("Collisions detected" in line for line in captured.output)


def test_explicit_bad_python_still_raises(tmp_path):
    bad_py = tmp_path / "broken.py"
    bad_py.write_text("syntax error()", encoding="utf-8")
    app = ExampleApp(raise_config_file_errors=True)
    with pytest.raises(SyntaxError):
        app.load_config_file(bad_py)
