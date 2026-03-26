"""
Integration tests for clang_format_inc.formatter.format_hunks.

These tests invoke the real clang-format binary on real temporary files.
They are skipped when clang-format is not installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from clang_format_inc.formatter import format_hunks
from tests.conftest import requires_clang_format

# A minimal .clang-format so tests are not sensitive to the user's project config.
CLANG_FORMAT_CONFIG = "BasedOnStyle: LLVM\nIndentWidth: 4\nColumnLimit: 120\n"


@pytest.fixture
def cpp_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A tmp dir with a .clang-format file; cwd set to it."""
    (tmp_path / ".clang-format").write_text(CLANG_FORMAT_CONFIG)
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Core formatting behaviour
# ---------------------------------------------------------------------------


@requires_clang_format
class TestFormatHunks:
    def test_formats_specified_line_range(self, cpp_workspace: Path):
        """Only the lines in the given range are reformatted."""
        f = cpp_workspace / "test.cpp"
        f.write_text(
            "int a=1;\n"  # line 1 — bad, but NOT in range
            "int b=2;\n"  # line 2 — bad, IN range
            "int c=3;\n"  # line 3 — bad, but NOT in range
        )

        result = format_hunks("clang-format", {"test.cpp": [(2, 2)]})

        assert result == 0
        lines = f.read_text().splitlines()
        assert lines[0] == "int a=1;"  # line 1 untouched
        assert lines[1] == "int b = 2;"  # line 2 reformatted
        assert lines[2] == "int c=3;"  # line 3 untouched

    def test_formats_multiple_ranges_in_one_file(self, cpp_workspace: Path):
        f = cpp_workspace / "test.cpp"
        f.write_text(
            "int a=1;\n"  # line 1 — in range
            "int b=2;\n"  # line 2 — NOT in range
            "int c=3;\n"  # line 3 — in range
        )

        result = format_hunks("clang-format", {"test.cpp": [(1, 1), (3, 3)]})

        assert result == 0
        lines = f.read_text().splitlines()
        assert lines[0] == "int a = 1;"
        assert lines[1] == "int b=2;"  # untouched
        assert lines[2] == "int c = 3;"

    def test_formats_multiple_files(self, cpp_workspace: Path):
        a = cpp_workspace / "a.cpp"
        b = cpp_workspace / "b.cpp"
        a.write_text("int x=1;\n")
        b.write_text("int y=2;\n")

        result = format_hunks("clang-format", {"a.cpp": [(1, 1)], "b.cpp": [(1, 1)]})

        assert result == 0
        assert a.read_text().strip() == "int x = 1;"
        assert b.read_text().strip() == "int y = 2;"

    def test_already_formatted_file_is_unchanged(self, cpp_workspace: Path):
        f = cpp_workspace / "test.cpp"
        original = "int x = 1;\n"
        f.write_text(original)

        result = format_hunks("clang-format", {"test.cpp": [(1, 1)]})

        assert result == 0
        assert f.read_text() == original

    def test_style_flag_is_applied(self, cpp_workspace: Path):
        """LLVM style uses 4-space indent; Google uses 2-space.
        Use a multi-statement body so clang-format does not collapse it to one line."""
        f = cpp_workspace / "test.cpp"
        f.write_text("void f() {\nint x = 1;\nint y = 2;\nint z = 3;\n}\n")

        format_hunks("clang-format", {"test.cpp": [(1, 5)]}, style="Google")

        content = f.read_text()
        # Google style indents with 2 spaces
        assert "  int x = 1;" in content

    def test_fallback_style_used_when_no_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        """With no .clang-format file, --fallback-style determines the style."""
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "test.cpp"
        f.write_text("void f() {\nint x=1;\n}\n")

        result = format_hunks("clang-format", {"test.cpp": [(2, 2)]}, style="file", fallback_style="LLVM")

        assert result == 0
        assert "int x = 1;" in f.read_text()

    def test_empty_hunks_dict_is_noop(self, cpp_workspace: Path):
        f = cpp_workspace / "test.cpp"
        original = "int x=1;\n"
        f.write_text(original)

        result = format_hunks("clang-format", {})

        assert result == 0
        assert f.read_text() == original  # untouched


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


@requires_clang_format
class TestFormatHunksErrors:
    def test_nonexistent_binary_returns_nonzero(self, cpp_workspace: Path):
        f = cpp_workspace / "test.cpp"
        f.write_text("int x=1;\n")

        result = format_hunks("clang-format-does-not-exist-xyz", {"test.cpp": [(1, 1)]})

        assert result != 0

    def test_nonexistent_file_returns_nonzero(self, cpp_workspace: Path):
        result = format_hunks("clang-format", {"does_not_exist.cpp": [(1, 1)]})
        assert result != 0

    def test_stops_on_first_failure(self, cpp_workspace: Path):
        """When the first file fails, the second file is not touched."""
        good = cpp_workspace / "good.cpp"
        good.write_text("int x=1;\n")

        result = format_hunks(
            "clang-format",
            {
                "does_not_exist.cpp": [(1, 1)],  # will fail
                "good.cpp": [(1, 1)],  # should not be reached
            },
        )
        assert result != 0
        # good.cpp was not reformatted because we stopped after the first error
        assert good.read_text() == "int x=1;\n"
