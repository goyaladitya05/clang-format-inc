"""
Integration tests for clang_format_inc.main.

These tests use real git repositories (via the git_repo fixture) and real
clang-format invocations. No mocking anywhere.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from clang_format_inc.main import main, parse_args
from tests.conftest import commit_file, requires_clang_format

# A minimal style config so tests are not sensitive to the user's repo config.
CLANG_FORMAT_CONFIG = "BasedOnStyle: LLVM\nIndentWidth: 4\nColumnLimit: 120\n"

BADLY_FORMATTED = "int main(){int x=1;return x;}\n"
WELL_FORMATTED = "int main() {\n    int x = 1;\n    return x;\n}\n"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_pre_commit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure CI env vars are absent unless a test sets them explicitly."""
    monkeypatch.delenv("PRE_COMMIT_FROM_REF", raising=False)
    monkeypatch.delenv("PRE_COMMIT_TO_REF", raising=False)


@pytest.fixture
def repo(git_repo: Path) -> Path:
    """git_repo with a .clang-format config committed."""
    (git_repo / ".clang-format").write_text(CLANG_FORMAT_CONFIG)
    subprocess.run(["git", "add", ".clang-format"], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "add clang-format config"], check=True, capture_output=True)
    return git_repo


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    def test_defaults(self):
        args = parse_args([])
        assert args.binary == "clang-format"
        assert args.style == "file"
        assert args.fallback_style is None
        assert args.sort_includes is False
        assert args.p == 1
        assert args.files == []
        assert args.check is False
        assert args.diff is False
        assert args.include is None
        assert args.exclude is None
        assert args.workers == 1

    def test_all_options(self):
        args = parse_args(
            [
                "--binary",
                "/usr/bin/clang-format-17",
                "--style",
                "Google",
                "--fallback-style",
                "LLVM",
                "--sort-includes",
                "-p",
                "2",
                "--include",
                r".*\.cpp$",
                "--exclude",
                r"third_party/",
                "--workers",
                "4",
                "a.cpp",
                "b.cpp",
            ]
        )
        assert args.binary == "/usr/bin/clang-format-17"
        assert args.style == "Google"
        assert args.fallback_style == "LLVM"
        assert args.sort_includes is True
        assert args.p == 2
        assert args.include == r".*\.cpp$"
        assert args.exclude == r"third_party/"
        assert args.workers == 4
        assert args.files == ["a.cpp", "b.cpp"]

    def test_check_and_diff_are_mutually_exclusive(self):
        import pytest

        with pytest.raises(SystemExit):
            parse_args(["--check", "--diff"])


# ---------------------------------------------------------------------------
# Binary validation (no git repo needed)
# ---------------------------------------------------------------------------


class TestBinaryValidation:
    def test_nonexistent_binary_returns_1(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.chdir(tmp_path)
        result = main(["--binary", "clang-format-does-not-exist-xyz"])
        assert result == 1

    def test_nonexistent_binary_prints_error(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture,  # type: ignore[type-arg]
    ):
        monkeypatch.chdir(tmp_path)
        main(["--binary", "clang-format-xyz-missing"])
        err = capsys.readouterr().err
        assert "clang-format-xyz-missing" in err
        assert "not found" in err


# ---------------------------------------------------------------------------
# Local mode (git diff --cached)
# ---------------------------------------------------------------------------


@requires_clang_format
class TestLocalMode:
    def test_formats_staged_file(self, repo: Path):
        f = repo / "foo.cpp"
        f.write_text(BADLY_FORMATTED)
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        result = main(["foo.cpp"])

        assert result == 0
        content = f.read_text()
        assert "int x = 1;" in content

    def test_only_changed_lines_formatted(self, repo: Path):
        """Lines outside the diff hunk must not be touched."""
        f = repo / "foo.cpp"
        commit_file(f, WELL_FORMATTED, "add foo.cpp")

        # Stage a new badly-formatted line appended at the end
        f.write_text(WELL_FORMATTED + "int y=2;\n")
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        result = main(["foo.cpp"])

        assert result == 0
        lines = f.read_text().splitlines()
        assert lines[0] == "int main() {"  # original line untouched
        assert "int y = 2;" in lines  # appended bad line fixed

    def test_unstaged_changes_not_formatted(self, repo: Path):
        """Only staged changes should be picked up."""
        f = repo / "foo.cpp"
        commit_file(f, WELL_FORMATTED, "add foo.cpp")

        # Modify but do NOT stage
        f.write_text(BADLY_FORMATTED)

        result = main(["foo.cpp"])

        assert result == 0
        assert f.read_text() == BADLY_FORMATTED  # untouched — not staged

    def test_nothing_staged_returns_0(self, repo: Path):
        result = main([])
        assert result == 0

    def test_formats_multiple_staged_files(self, repo: Path):
        a = repo / "a.cpp"
        b = repo / "b.cpp"
        a.write_text("int x=1;\n")
        b.write_text("int y=2;\n")
        subprocess.run(["git", "add", "a.cpp", "b.cpp"], check=True, capture_output=True)

        result = main(["a.cpp", "b.cpp"])

        assert result == 0
        assert "int x = 1;" in a.read_text()
        assert "int y = 2;" in b.read_text()


# ---------------------------------------------------------------------------
# CI mode (PRE_COMMIT_FROM_REF / PRE_COMMIT_TO_REF)
# ---------------------------------------------------------------------------


@requires_clang_format
class TestCIMode:
    def test_formats_changed_lines_between_refs(self, repo: Path, monkeypatch: pytest.MonkeyPatch):
        f = repo / "foo.cpp"
        from_sha = commit_file(f, WELL_FORMATTED, "add foo.cpp")
        to_sha = commit_file(f, WELL_FORMATTED + "int y=2;\n", "append bad line")

        monkeypatch.setenv("PRE_COMMIT_FROM_REF", from_sha)
        monkeypatch.setenv("PRE_COMMIT_TO_REF", to_sha)

        result = main(["foo.cpp"])

        assert result == 0
        content = f.read_text()
        assert "int y = 2;" in content  # changed line formatted
        assert "int main() {" in content  # unchanged line untouched

    def test_does_not_format_lines_outside_diff(self, repo: Path, monkeypatch: pytest.MonkeyPatch):
        """Pre-existing badly-formatted lines not in the diff must not be touched."""
        f = repo / "foo.cpp"
        from_sha = commit_file(f, "int a=99;\n", "initial bad line 1")
        to_sha = commit_file(f, "int a=99;\nint b=2;\n", "append bad line 2")

        monkeypatch.setenv("PRE_COMMIT_FROM_REF", from_sha)
        monkeypatch.setenv("PRE_COMMIT_TO_REF", to_sha)

        result = main(["foo.cpp"])

        assert result == 0
        lines = f.read_text().splitlines()
        assert lines[0] == "int a=99;"  # NOT in the diff — untouched
        assert lines[1] == "int b = 2;"  # in the diff — formatted

    def test_only_from_ref_set_falls_back_to_local(self, repo: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PRE_COMMIT_FROM_REF", "abc123")
        # PRE_COMMIT_TO_REF absent — should fall back to local mode (nothing staged → 0)
        result = main([])
        assert result == 0

    def test_only_to_ref_set_falls_back_to_local(self, repo: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PRE_COMMIT_TO_REF", "abc123")
        result = main([])
        assert result == 0


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


@requires_clang_format
class TestErrors:
    def test_invalid_git_ref_returns_nonzero(self, repo: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("PRE_COMMIT_FROM_REF", "deadbeefdeadbeef")
        monkeypatch.setenv("PRE_COMMIT_TO_REF", "cafecafecafecafe")

        result = main([])
        assert result != 0


# ---------------------------------------------------------------------------
# --check mode
# ---------------------------------------------------------------------------


@requires_clang_format
class TestCheckMode:
    def test_check_fails_when_staged_bad_code(self, repo: Path):
        f = repo / "foo.cpp"
        f.write_text(BADLY_FORMATTED)
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        result = main(["--check", "foo.cpp"])

        assert result != 0

    def test_check_does_not_modify_staged_file(self, repo: Path):
        f = repo / "foo.cpp"
        f.write_text(BADLY_FORMATTED)
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        main(["--check", "foo.cpp"])

        assert f.read_text() == BADLY_FORMATTED

    def test_check_passes_when_staged_good_code(self, repo: Path):
        f = repo / "foo.cpp"
        f.write_text(WELL_FORMATTED)
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        result = main(["--check", "foo.cpp"])

        assert result == 0

    def test_check_nothing_staged_returns_zero(self, repo: Path):
        result = main(["--check"])
        assert result == 0


# ---------------------------------------------------------------------------
# --diff mode
# ---------------------------------------------------------------------------


@requires_clang_format
class TestDiffMode:
    def test_diff_fails_when_staged_bad_code(self, repo: Path):
        f = repo / "foo.cpp"
        f.write_text(BADLY_FORMATTED)
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        result = main(["--diff", "foo.cpp"])

        assert result != 0

    def test_diff_does_not_modify_file(self, repo: Path):
        f = repo / "foo.cpp"
        f.write_text(BADLY_FORMATTED)
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        main(["--diff", "foo.cpp"])

        assert f.read_text() == BADLY_FORMATTED

    def test_diff_outputs_unified_diff(self, repo: Path, capsys: pytest.CaptureFixture):  # type: ignore[type-arg]
        f = repo / "foo.cpp"
        f.write_text(BADLY_FORMATTED)
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        main(["--diff", "foo.cpp"])

        out = capsys.readouterr().out
        assert "---" in out
        assert "+++" in out

    def test_diff_passes_when_staged_good_code(self, repo: Path):
        f = repo / "foo.cpp"
        f.write_text(WELL_FORMATTED)
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        result = main(["--diff", "foo.cpp"])

        assert result == 0


# ---------------------------------------------------------------------------
# --include / --exclude file filtering
# ---------------------------------------------------------------------------


@requires_clang_format
class TestFileFiltering:
    def test_include_processes_matching_files(self, repo: Path):
        a = repo / "a.cpp"
        b = repo / "b.cpp"
        a.write_text("int x=1;\n")
        b.write_text("int y=2;\n")
        subprocess.run(["git", "add", "a.cpp", "b.cpp"], check=True, capture_output=True)

        result = main(["--include", r"a\.cpp$", "a.cpp", "b.cpp"])

        assert result == 0
        assert "int x = 1;" in a.read_text()  # matched — formatted
        assert b.read_text() == "int y=2;\n"  # not matched — untouched

    def test_exclude_skips_matching_files(self, repo: Path):
        a = repo / "a.cpp"
        b = repo / "b.cpp"
        a.write_text("int x=1;\n")
        b.write_text("int y=2;\n")
        subprocess.run(["git", "add", "a.cpp", "b.cpp"], check=True, capture_output=True)

        result = main(["--exclude", r"b\.cpp$", "a.cpp", "b.cpp"])

        assert result == 0
        assert "int x = 1;" in a.read_text()  # not excluded — formatted
        assert b.read_text() == "int y=2;\n"  # excluded — untouched

    def test_exclude_all_files_returns_zero(self, repo: Path):
        f = repo / "foo.cpp"
        f.write_text("int x=1;\n")
        subprocess.run(["git", "add", "foo.cpp"], check=True, capture_output=True)

        result = main(["--exclude", r".*", "foo.cpp"])

        assert result == 0
        assert f.read_text() == "int x=1;\n"  # excluded — untouched


# ---------------------------------------------------------------------------
# --workers (parallel processing)
# ---------------------------------------------------------------------------


@requires_clang_format
class TestParallelProcessing:
    def test_workers_formats_all_staged_files(self, repo: Path):
        a = repo / "a.cpp"
        b = repo / "b.cpp"
        c = repo / "c.cpp"
        a.write_text("int x=1;\n")
        b.write_text("int y=2;\n")
        c.write_text("int z=3;\n")
        subprocess.run(["git", "add", "a.cpp", "b.cpp", "c.cpp"], check=True, capture_output=True)

        result = main(["--workers", "2", "a.cpp", "b.cpp", "c.cpp"])

        assert result == 0
        assert "int x = 1;" in a.read_text()
        assert "int y = 2;" in b.read_text()
        assert "int z = 3;" in c.read_text()
