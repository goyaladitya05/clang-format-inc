"""
Unit tests for clang_format_inc.diff_parser.parse_diff_hunks.

These are pure unit tests — no mocks, no subprocesses, no filesystem access.
parse_diff_hunks is a pure function; we feed it diff strings and check the output.
"""

from __future__ import annotations

from clang_format_inc.diff_parser import parse_diff_hunks

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_diff(filename: str, hunk_header: str, body: str = "") -> str:
    """Build a minimal unified diff for a single file and hunk."""
    return (
        f"diff --git a/{filename} b/{filename}\n"
        f"index 0000000..1111111 100644\n"
        f"--- a/{filename}\n"
        f"+++ b/{filename}\n"
        f"{hunk_header}\n"
        f"{body}"
    )


# ---------------------------------------------------------------------------
# Basic cases
# ---------------------------------------------------------------------------


class TestSingleFileHunks:
    def test_single_added_line(self):
        diff = make_diff("foo.cpp", "@@ -1,0 +2,1 @@", "+int x = 1;\n")
        assert parse_diff_hunks(diff) == {"foo.cpp": [(2, 2)]}

    def test_multiple_added_lines(self):
        diff = make_diff("foo.cpp", "@@ -1,0 +3,4 @@", "+a\n+b\n+c\n+d\n")
        assert parse_diff_hunks(diff) == {"foo.cpp": [(3, 6)]}

    def test_multiple_hunks_in_one_file(self):
        diff = (
            "diff --git a/foo.cpp b/foo.cpp\n"
            "--- a/foo.cpp\n"
            "+++ b/foo.cpp\n"
            "@@ -1,0 +2,2 @@\n"
            "+line a\n"
            "+line b\n"
            "@@ -10,0 +20,3 @@\n"
            "+line x\n"
            "+line y\n"
            "+line z\n"
        )
        assert parse_diff_hunks(diff) == {"foo.cpp": [(2, 3), (20, 22)]}

    def test_count_omitted_means_one_line(self):
        # "@@ -1 +5 @@" — no comma, count defaults to 1
        diff = make_diff("bar.cpp", "@@ -1 +5 @@", "+single\n")
        assert parse_diff_hunks(diff) == {"bar.cpp": [(5, 5)]}


# ---------------------------------------------------------------------------
# Deletion and deletion-only cases
# ---------------------------------------------------------------------------


class TestDeletions:
    def test_deletion_only_hunk_is_skipped(self):
        """A hunk with +N,0 has count=0 — no lines added, nothing to format."""
        diff = make_diff("foo.cpp", "@@ -5,3 +5,0 @@", "-a\n-b\n-c\n")
        assert parse_diff_hunks(diff) == {}

    def test_deleted_file_is_skipped(self):
        """+++ /dev/null should never produce hunks."""
        diff = (
            "diff --git a/old.cpp b/old.cpp\n"
            "deleted file mode 100644\n"
            "--- a/old.cpp\n"
            "+++ /dev/null\n"
            "@@ -1,3 +0,0 @@\n"
            "-line1\n"
            "-line2\n"
            "-line3\n"
        )
        assert parse_diff_hunks(diff) == {}

    def test_mixed_hunks_keeps_additions_skips_deletions(self):
        diff = (
            "--- a/foo.cpp\n"
            "+++ b/foo.cpp\n"
            "@@ -1,2 +1,0 @@\n"  # deletion-only
            "-gone\n"
            "@@ -10,0 +8,2 @@\n"  # addition
            "+new1\n"
            "+new2\n"
        )
        assert parse_diff_hunks(diff) == {"foo.cpp": [(8, 9)]}


# ---------------------------------------------------------------------------
# New files
# ---------------------------------------------------------------------------


class TestNewFiles:
    def test_new_file_all_lines_are_added(self):
        diff = (
            "diff --git a/new.cpp b/new.cpp\n"
            "new file mode 100644\n"
            "--- /dev/null\n"
            "+++ b/new.cpp\n"
            "@@ -0,0 +1,3 @@\n"
            "+int a;\n"
            "+int b;\n"
            "+int c;\n"
        )
        assert parse_diff_hunks(diff) == {"new.cpp": [(1, 3)]}


# ---------------------------------------------------------------------------
# Multi-file diffs
# ---------------------------------------------------------------------------


class TestMultiFile:
    def test_two_files(self):
        diff = (
            "--- a/a.cpp\n"
            "+++ b/a.cpp\n"
            "@@ -1,0 +1,1 @@\n"
            "+int a;\n"
            "--- a/b.cpp\n"
            "+++ b/b.cpp\n"
            "@@ -1,0 +5,2 @@\n"
            "+int x;\n"
            "+int y;\n"
        )
        result = parse_diff_hunks(diff)
        assert result == {"a.cpp": [(1, 1)], "b.cpp": [(5, 6)]}

    def test_three_files_with_subdirs(self):
        diff = (
            "+++ b/src/a.cpp\n"
            "@@ -0,0 +1,2 @@\n"
            "+x\n+y\n"
            "+++ b/include/b.h\n"
            "@@ -0,0 +3,1 @@\n"
            "+z\n"
            "+++ b/main.cpp\n"
            "@@ -0,0 +10,3 @@\n"
            "+p\n+q\n+r\n"
        )
        result = parse_diff_hunks(diff)
        assert result == {
            "src/a.cpp": [(1, 2)],
            "include/b.h": [(3, 3)],
            "main.cpp": [(10, 12)],
        }


# ---------------------------------------------------------------------------
# p flag (prefix stripping)
# ---------------------------------------------------------------------------


class TestPrefixStripping:
    def test_p0_keeps_full_path(self):
        diff = "+++ b/src/foo.cpp\n@@ -0,0 +1,1 @@\n+x\n"
        result = parse_diff_hunks(diff, p=0)
        # With p=0, no components stripped — full path after +++ including b/
        assert "b/src/foo.cpp" in result

    def test_p1_strips_one_component(self):
        diff = "+++ b/src/foo.cpp\n@@ -0,0 +1,1 @@\n+x\n"
        assert parse_diff_hunks(diff, p=1) == {"src/foo.cpp": [(1, 1)]}

    def test_p2_strips_two_components(self):
        diff = "+++ b/src/foo.cpp\n@@ -0,0 +1,1 @@\n+x\n"
        assert parse_diff_hunks(diff, p=2) == {"foo.cpp": [(1, 1)]}


# ---------------------------------------------------------------------------
# Empty and no-op diffs
# ---------------------------------------------------------------------------


class TestEmptyDiff:
    def test_empty_string(self):
        assert parse_diff_hunks("") == {}

    def test_whitespace_only(self):
        assert parse_diff_hunks("  \n\n  ") == {}

    def test_diff_header_only_no_hunks(self):
        diff = "diff --git a/foo.cpp b/foo.cpp\nindex 0..1 100644\n"
        assert parse_diff_hunks(diff) == {}
