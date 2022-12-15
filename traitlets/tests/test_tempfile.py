from pathlib import Path
from tempfile import TemporaryFile, TemporaryDirectory


class TestTempFile:
    def test_temp_file1(self):
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

    def test_temp_file2(self):
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

        with TemporaryFile("wt+") as t:
            t.write("hello world")
            t.flush()
            t.seek(0)
            assert t.read() == "hello world"

    def test_temp_file3(self):
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

    def test_temp_dir1(self):
        with TemporaryDirectory() as tmpdir:
            with Path(tmpdir).joinpath("tmp").open("wt+") as t:
                t.write("hello world")
                t.flush()
                t.seek(0)
                assert t.read() == "hello world"

    def test_temp_dir2(self):
        with TemporaryDirectory() as tmpdir:
            with Path(tmpdir).joinpath("tmp").open("wt+") as t:
                t.write("hello world")
                t.flush()
                t.seek(0)
                assert t.read() == "hello world"

    def test_temp_dir3(self):
        with TemporaryDirectory() as tmpdir:
            with Path(tmpdir).joinpath("tmp").open("wt+") as t:
                t.write("hello world")
                t.flush()
                t.seek(0)
                assert t.read() == "hello world"
