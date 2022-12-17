import os
import sys

import pytest

debug_stream = sys.stderr


class TestTempFile:
    @pytest.fixture
    def argcomplete_on(self):
        """Mostly borrowed from argcomplete's unit test fixtures

        Set up environment variables to mimic those passed by argcomplete
        """
        # mock_fdopen = mocker.patch("os.fdopen")

        try:
            debug_stream = os.fdopen(9, "w")
            print("using fd9")
        except Exception:
            debug_stream = sys.stderr
            print("using stderr")
        print("test", file=debug_stream)
        debug_stream.flush()

        try:
            yield
        finally:
            if debug_stream is not sys.stderr:
                debug_stream.close()

    def test_temp_file1(self, argcomplete_on):
        assert True

    def test_temp_file2(self, argcomplete_on):
        assert True
