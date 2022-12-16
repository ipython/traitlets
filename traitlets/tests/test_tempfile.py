import contextlib
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory, TemporaryFile

import pytest

_DEBUG = True


@contextlib.contextmanager
def mute_stdout():
    stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stdout = stdout


@contextlib.contextmanager
def mute_stderr():
    stderr = sys.stderr
    sys.stderr = open(os.devnull, "w")
    try:
        yield
    finally:
        sys.stderr.close()
        sys.stderr = stderr


debug_stream = sys.stderr


def debug(*args):
    if _DEBUG:
        print(file=debug_stream, *args)


class TestTempFile:
    IFS = "\013"
    COMP_WORDBREAKS = " \t\n\"'><=;|&(:"

    @pytest.fixture
    def argcomplete_on(self):
        """Mostly borrowed from argcomplete's unit test fixtures

        Set up environment variables to mimic those passed by argcomplete
        """
        global debug_stream
        try:
            debug_stream = os.fdopen(9, "w")
        except Exception:
            debug_stream = sys.stderr
        debug("test")
        debug_stream.flush()

        # with mute_stdout():
        #     print("abc")

        # with mute_stderr():
        #     print("def", file=sys.stderr)

        _old_environ = os.environ
        os.environ = os.environ.copy()  # type: ignore[assignment]
        os.environ["_ARGCOMPLETE"] = "1"
        os.environ["_ARC_DEBUG"] = "yes"
        os.environ["IFS"] = self.IFS
        os.environ["_ARGCOMPLETE_COMP_WORDBREAKS"] = self.COMP_WORDBREAKS
        os.environ["_ARGCOMPLETE"] = "1"
        yield
        os.environ = _old_environ

    def test_temp_file1(self, argcomplete_on):
        with TemporaryFile("wt+") as t:
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"
        with TemporaryFile("wt+") as t:
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"

    def test_temp_file2(self, argcomplete_on):
        with TemporaryFile("wt+") as t:
            with pytest.raises(SystemExit):
                sys.exit(0)
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"

        with TemporaryFile("wt+") as t:
            with pytest.raises(SystemExit):
                sys.exit(0)
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"

        with TemporaryFile("wt+") as t:
            with pytest.raises(SystemExit):
                sys.exit(0)
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"

    def test_temp_file3(self, argcomplete_on):
        with TemporaryFile("wt+") as t:
            with pytest.raises(SystemExit):
                sys.exit(0)
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"

        with TemporaryFile("wt+") as t:
            with pytest.raises(SystemExit):
                sys.exit(0)
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"

    def test_temp_dir1(self, argcomplete_on):
        with TemporaryDirectory() as tmpdir:
            with Path(tmpdir).joinpath("tmp").open("wt+") as t:
                t.write("hello world")
                t.flush()
                t.seek(0)
                assert t.read() == "hello world"

    def test_temp_dir2(self, argcomplete_on):
        with TemporaryDirectory() as tmpdir:
            with Path(tmpdir).joinpath("tmp").open("wt+") as t:
                t.write("hello world")
                t.flush()
                t.seek(0)
                assert t.read() == "hello world"

    def test_temp_dir3(self, argcomplete_on):
        with TemporaryDirectory() as tmpdir:
            with Path(tmpdir).joinpath("tmp").open("wt+") as t:
                t.write("hello world")
                t.flush()
                t.seek(0)
                assert t.read() == "hello world"
