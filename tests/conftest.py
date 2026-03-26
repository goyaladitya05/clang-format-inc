"""Shared fixtures and marks for the test suite."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Skip marker — use on any test that actually invokes clang-format
# ---------------------------------------------------------------------------

requires_clang_format = pytest.mark.skipif(
    shutil.which("clang-format") is None,
    reason="clang-format not installed",
)


# ---------------------------------------------------------------------------
# git_repo fixture
# ---------------------------------------------------------------------------


def _git(args: list[str], **kwargs) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    """Run a git command, raise on failure."""
    return subprocess.run(["git"] + args, check=True, capture_output=True, text=True, **kwargs)


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return a temporary git repo with one initial commit.

    The fixture also changes the process cwd to the repo root so that
    ``git diff`` and ``clang-format`` resolve paths correctly without
    needing explicit ``-C`` flags or path manipulation in every test.
    """
    _git(["init", str(tmp_path)])
    _git(["-C", str(tmp_path), "config", "user.email", "test@example.com"])
    _git(["-C", str(tmp_path), "config", "user.name", "Test User"])

    # Switch cwd before making the initial commit so subsequent git calls
    # in tests can omit -C.
    monkeypatch.chdir(tmp_path)

    (tmp_path / "README").write_text("initial\n")
    _git(["add", "."])
    _git(["commit", "-m", "initial"])

    return tmp_path


# ---------------------------------------------------------------------------
# Helpers exported for tests
# ---------------------------------------------------------------------------


def commit_file(path: Path, content: str, message: str = "update") -> str:
    """Write *content* to *path*, stage and commit it. Returns the new SHA."""
    path.write_text(content)
    _git(["add", path.name])
    _git(["commit", "-m", message])
    return _git(["rev-parse", "HEAD"]).stdout.strip()
