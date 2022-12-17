import os
import sys
from tempfile import TemporaryFile

import pytest

debug_stream = sys.stderr


class TestTempFile:
    IFS = "\013"

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
        print("test", file=debug_stream)
        debug_stream.flush()

        _old_environ = os.environ
        os.environ = os.environ.copy()  # type: ignore[assignment]
        os.environ["IFS"] = self.IFS
        yield
        os.environ = _old_environ

    def test_temp_file1(self, argcomplete_on):
        with TemporaryFile("wt+") as t:
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"

    def test_temp_file2(self, argcomplete_on):
        with pytest.raises(RuntimeError):
            raise RuntimeError("test")
