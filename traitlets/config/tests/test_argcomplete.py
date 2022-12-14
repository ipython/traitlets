"""
Tests for argcomplete handling by traitlets.config.application.Application
"""

import os
import sys
import typing as t
from tempfile import TemporaryFile

import pytest

argcomplete = pytest.importorskip("argcomplete")

from traitlets import Unicode
from traitlets.config.application import Application
from traitlets.config.configurable import Configurable
from traitlets.config.loader import KVArgParseConfigLoader


class ArgcompleteApp(Application):
    argcomplete_kwargs: t.Dict[str, t.Any]

    def _create_loader(self, argv, aliases, flags, classes):
        loader = KVArgParseConfigLoader(argv, aliases, flags, classes=classes, log=self.log)
        loader._argcomplete_kwargs = self.argcomplete_kwargs  # type: ignore[attr-defined]
        return loader


class TestArgcomplete:
    IFS = "\013"
    COMP_WORDBREAKS = " \t\n\"'><=;|&(:"

    @pytest.fixture
    def argcomplete_on(self):
        """Mostly borrowed from argcomplete's unit test fixtures

        Set up environment variables to mimic those passed by argcomplete
        """
        _old_environ = os.environ
        os.environ = os.environ.copy()  # type: ignore[assignment]
        os.environ["_ARGCOMPLETE"] = "1"
        os.environ["_ARC_DEBUG"] = "yes"
        os.environ["IFS"] = self.IFS
        os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = self.COMP_WORDBREAKS
        os.environ["_ARGCOMPLETE"] = "1"
        yield
        os.environ = _old_environ

    def run_completer(
        self,
        app: ArgcompleteApp,
        command: str,
        point: t.Union[str, int, None] = None,
        **kwargs: t.Any,
    ) -> t.List[str]:
        """Mostly borrowed from argcomplete's unit tests

        Modified to take an application instead of an ArgumentParser
        """
        if point is None:
            point = str(len(command))
        with TemporaryFile(mode="wb+") as t:
            os.environ["COMP_LINE"] = command
            os.environ["COMP_POINT"] = str(point)
            with pytest.raises(SystemExit) as cm:
                app.argcomplete_kwargs = dict(output_stream=t, exit_method=sys.exit, **kwargs)
                app.initialize()
            if cm.value.code != 0:
                raise Exception(f"Unexpected exit code {cm.value.code}")
            t.seek(0)
            out: str = t.read().decode()
            return out.split(self.IFS)

    def test_complete_simple_app(self, argcomplete_on):
        app = ArgcompleteApp()
        expected = [
            '--help',
            '--debug',
            '--show-config',
            '--show-config-json',
            '--log-level',
            '--Application.',
            '--ArgcompleteApp.',
        ]
        assert set(self.run_completer(app, "app --")) == set(expected)

        # completing class traits
        assert set(self.run_completer(app, "app --App")) > {
            '--Application.show_config',
            '--Application.log_level',
            '--Application.log_format',
        }

    def test_complete_custom_completers(self, argcomplete_on):
        app = ArgcompleteApp()
        # test pre-defined completers for Bool/Enum
        assert set(self.run_completer(app, "app --Application.log_level=")) > {"DEBUG", "INFO"}
        assert set(self.run_completer(app, "app --ArgcompleteApp.show_config ")) == {
            "0",
            "1",
            "true",
            "false",
        }

        # test custom completer and mid-command completions
        class CustomCls(Configurable):
            val = Unicode().tag(
                config=True, argcompleter=argcomplete.completers.ChoicesCompleter(["foo", "bar"])
            )

        class CustomApp(ArgcompleteApp):
            classes = [CustomCls]
            aliases = {("v", "val"): "CustomApp.val"}

        app = CustomApp()
        assert self.run_completer(app, "app --val ") == ["foo", "bar"]
        assert self.run_completer(app, "app --val=") == ["foo", "bar"]
        assert self.run_completer(app, "app -v ") == ["foo", "bar"]
        assert self.run_completer(app, "app -v=") == ["foo", "bar"]
        assert self.run_completer(app, "app --CustomCls.val  ") == ["foo", "bar"]
        assert self.run_completer(app, "app --CustomCls.val=") == ["foo", "bar"]
        assert self.run_completer(app, "app --val= abc xyz", point=10) == ["--val=foo", "--val=bar"]
        assert self.run_completer(app, "app --val  --log-level=", point=10) == ["foo", "bar"]
