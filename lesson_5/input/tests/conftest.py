import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_repo():
    """Temporary git repo with 3 known commits.

    Structure:
      commit 1 (initial) — README.md  (no parent, skipped by get_changed_files)
      commit 2           — foo.py, bar.py added
      commit 3           — foo.py updated
    Result: foo.py has 2 changes, bar.py has 1.
    """
    path = tempfile.mkdtemp()

    def git(*args):
        subprocess.run(["git", "-C", path, *args], check=True, capture_output=True)

    git("init")
    git("config", "user.email", "alice@example.com")
    git("config", "user.name", "Alice")

    (Path(path) / "README.md").write_text("# test repo")
    git("add", ".")
    git("commit", "-m", "init")

    (Path(path) / "foo.py").write_text("x = 1")
    (Path(path) / "bar.py").write_text("y = 2")
    git("add", ".")
    git("commit", "-m", "add foo and bar")

    (Path(path) / "foo.py").write_text("x = 2")
    git("add", ".")
    git("commit", "-m", "update foo")

    yield path
    shutil.rmtree(path, ignore_errors=True)
