"""Tests for clang_format_inc.main"""

import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

from clang_format_inc.main import main, parse_args


# ---------------------------------------------------------------------------
# Diff fixtures
# ---------------------------------------------------------------------------

SAMPLE_DIFF = """\
diff --git a/foo.cpp b/foo.cpp
index 0000000..1111111 100644
--- a/foo.cpp
+++ b/foo.cpp
@@ -1,3 +1,4 @@
 #include <iostream>
+int x=1;
 int main() { return 0; }
"""

# Only lines deleted — no added lines.  clang-format-diff skips +N,0 hunks.
DELETIONS_ONLY_DIFF = """\
diff --git a/foo.cpp b/foo.cpp
index 1111111..0000000 100644
--- a/foo.cpp
+++ b/foo.cpp
@@ -2,3 +2,0 @@
-int x = 1;
-int y = 2;
-int z = 3;
"""

# Entire file deleted — +++ /dev/null won't match any C++ filename regex.
DELETED_FILE_DIFF = """\
diff --git a/old.cpp b/old.cpp
deleted file mode 100644
index 1111111..0000000
--- a/old.cpp
+++ /dev/null
@@ -1,3 +0,0 @@
-#include <iostream>
-int main() { return 0; }
"""

# Multiple files changed in one diff.
MULTI_FILE_DIFF = """\
diff --git a/src/a.cpp b/src/a.cpp
index 0000000..1111111 100644
--- a/src/a.cpp
+++ b/src/a.cpp
@@ -1,2 +1,3 @@
 #include <iostream>
+int a=1;
 int main(){}
diff --git a/src/b.cpp b/src/b.cpp
index 0000000..2222222 100644
--- a/src/b.cpp
+++ b/src/b.cpp
@@ -1,2 +1,3 @@
 #include <string>
+std::string s="hello";
 int foo(){}
diff --git a/include/c.h b/include/c.h
index 0000000..3333333 100644
--- a/include/c.h
+++ b/include/c.h
@@ -1,1 +1,2 @@
 #pragma once
+int x=42;
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_run(stdout="", returncode=0):
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    return mock


def _clear_ci_env():
    for key in ("PRE_COMMIT_FROM_REF", "PRE_COMMIT_TO_REF"):
        os.environ.pop(key, None)


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs(unittest.TestCase):
    def test_defaults(self):
        args = parse_args([])
        self.assertEqual(args.binary, "clang-format")
        self.assertEqual(args.style, "file")
        self.assertIsNone(args.fallback_style)
        self.assertEqual(args.p, 1)
        self.assertEqual(args.files, [])

    def test_custom_options(self):
        args = parse_args([
            "--binary", "/usr/bin/clang-format-17",
            "--style", "Google",
            "--fallback-style", "LLVM",
            "-p", "2",
            "a.cpp",
        ])
        self.assertEqual(args.binary, "/usr/bin/clang-format-17")
        self.assertEqual(args.style, "Google")
        self.assertEqual(args.fallback_style, "LLVM")
        self.assertEqual(args.p, 2)
        self.assertEqual(args.files, ["a.cpp"])


# ---------------------------------------------------------------------------
# CI mode
# ---------------------------------------------------------------------------

class TestCIMode(unittest.TestCase):
    """Both FROM_REF and TO_REF set → git diff <from> <to>."""

    def setUp(self):
        _clear_ci_env()

    def test_uses_both_refs(self):
        with patch.dict(os.environ, {"PRE_COMMIT_FROM_REF": "abc123", "PRE_COMMIT_TO_REF": "def456"}):
            with patch("shutil.which", return_value="/usr/bin/clang-format"):
                with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                    result = main(["foo.cpp"])

        args = mock_run.call_args_list[0][0][0]
        self.assertIn("abc123", args)
        self.assertIn("def456", args)
        self.assertNotIn("--cached", args)
        self.assertEqual(result, 0)

    def test_passes_files_to_diff(self):
        with patch.dict(os.environ, {"PRE_COMMIT_FROM_REF": "aaa", "PRE_COMMIT_TO_REF": "bbb"}):
            with patch("shutil.which", return_value="/usr/bin/clang-format"):
                with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                    main(["src/foo.cpp", "src/bar.cpp"])

        args = mock_run.call_args_list[0][0][0]
        self.assertIn("src/foo.cpp", args)
        self.assertIn("src/bar.cpp", args)

    def test_only_from_ref_set_falls_back_to_local(self):
        """Only one env var set → fall back to --cached (misconfiguration guard)."""
        with patch.dict(os.environ, {"PRE_COMMIT_FROM_REF": "abc"}, clear=False):
            os.environ.pop("PRE_COMMIT_TO_REF", None)
            with patch("shutil.which", return_value="/usr/bin/clang-format"):
                with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                    main([])

        args = mock_run.call_args_list[0][0][0]
        self.assertIn("--cached", args)

    def test_only_to_ref_set_falls_back_to_local(self):
        """Only one env var set → fall back to --cached (misconfiguration guard)."""
        os.environ.pop("PRE_COMMIT_FROM_REF", None)
        with patch.dict(os.environ, {"PRE_COMMIT_TO_REF": "def"}, clear=False):
            with patch("shutil.which", return_value="/usr/bin/clang-format"):
                with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                    main([])

        args = mock_run.call_args_list[0][0][0]
        self.assertIn("--cached", args)


# ---------------------------------------------------------------------------
# Local mode
# ---------------------------------------------------------------------------

class TestLocalMode(unittest.TestCase):
    """No env vars → git diff --cached."""

    def setUp(self):
        _clear_ci_env()

    def test_uses_cached(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                result = main(["foo.cpp"])

        args = mock_run.call_args_list[0][0][0]
        self.assertIn("--cached", args)
        self.assertEqual(result, 0)

    def test_no_ci_refs_in_command(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main([])

        args = mock_run.call_args_list[0][0][0]
        self.assertFalse(any("PRE_COMMIT" in a for a in args))


# ---------------------------------------------------------------------------
# Empty / no-op diffs
# ---------------------------------------------------------------------------

class TestEmptyDiff(unittest.TestCase):
    """When there are no changed lines, clang-format-diff should not be invoked."""

    def setUp(self):
        _clear_ci_env()

    def test_skips_formatting_when_diff_empty(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", return_value=_make_run("")) as mock_run:
                result = main([])

        self.assertEqual(mock_run.call_count, 1)
        self.assertEqual(result, 0)

    def test_skips_formatting_when_diff_whitespace_only(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", return_value=_make_run("   \n  \n")) as mock_run:
                result = main([])

        self.assertEqual(mock_run.call_count, 1)
        self.assertEqual(result, 0)

    def test_deletions_only_diff_is_passed_through(self):
        """A diff with only deletions is non-empty so we pass it to clang-format-diff,
        which internally skips +N,0 hunks. We must not short-circuit here."""
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(DELETIONS_ONLY_DIFF), _make_run()]) as mock_run:
                result = main([])

        # Both git diff AND clang-format-diff were called
        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(result, 0)

    def test_deleted_file_diff_is_passed_through(self):
        """A deleted-file diff (+++ /dev/null) is non-empty; clang-format-diff
        won't match /dev/null against its C++ regex so it's a no-op — but we
        must still pipe it through rather than silently skip."""
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(DELETED_FILE_DIFF), _make_run()]) as mock_run:
                result = main([])

        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(result, 0)


# ---------------------------------------------------------------------------
# Multi-file diffs
# ---------------------------------------------------------------------------

class TestMultiFileDiff(unittest.TestCase):
    def setUp(self):
        _clear_ci_env()

    def test_multi_file_diff_is_passed_through_intact(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(MULTI_FILE_DIFF), _make_run()]) as mock_run:
                result = main([])

        self.assertEqual(mock_run.call_count, 2)
        # The entire diff is sent as stdin to clang-format-diff
        stdin_input = mock_run.call_args_list[1][1].get("input")
        self.assertEqual(stdin_input, MULTI_FILE_DIFF)
        self.assertEqual(result, 0)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        _clear_ci_env()

    def test_git_diff_failure_returns_nonzero(self):
        exc = subprocess.CalledProcessError(returncode=128, cmd=["git", "diff"], stderr="not a git repo")
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=exc):
                result = main([])

        self.assertEqual(result, 128)

    def test_git_diff_failure_prints_stderr(self):
        exc = subprocess.CalledProcessError(returncode=128, cmd=["git", "diff"], stderr="fatal: not a repo")
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=exc):
                with patch("sys.stderr") as mock_stderr:
                    main([])
                    output = "".join(str(c) for c in mock_stderr.write.call_args_list)
                    self.assertIn("git diff failed", output)

    def test_clang_format_not_on_path_returns_1(self):
        with patch("shutil.which", return_value=None):
            result = main([])

        self.assertEqual(result, 1)

    def test_clang_format_not_on_path_prints_message(self):
        with patch("shutil.which", return_value=None):
            with patch("sys.stderr") as mock_stderr:
                main(["--binary", "clang-format-99"])
                output = "".join(str(c) for c in mock_stderr.write.call_args_list)
                self.assertIn("clang-format-99", output)
                self.assertIn("not found", output)

    def test_clang_format_not_found_skips_git_diff(self):
        """When the binary is missing we bail before even calling git."""
        with patch("shutil.which", return_value=None):
            with patch("subprocess.run") as mock_run:
                main([])

        mock_run.assert_not_called()

    def test_format_script_nonzero_returncode_propagated(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run(returncode=1)]):
                result = main([])

        self.assertEqual(result, 1)


# ---------------------------------------------------------------------------
# Format command flags
# ---------------------------------------------------------------------------

class TestFormatCommand(unittest.TestCase):
    def setUp(self):
        _clear_ci_env()

    def test_inplace_flag(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main([])

        args = mock_run.call_args_list[1][0][0]
        self.assertIn("-i", args)

    def test_custom_binary(self):
        with patch("shutil.which", return_value="/opt/llvm/bin/clang-format-17"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main(["--binary", "/opt/llvm/bin/clang-format-17"])

        args = mock_run.call_args_list[1][0][0]
        self.assertTrue(any("-binary=/opt/llvm/bin/clang-format-17" in a for a in args))

    def test_custom_style(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main(["--style", "Google"])

        args = mock_run.call_args_list[1][0][0]
        self.assertTrue(any("-style=Google" in a for a in args))

    def test_fallback_style_included_when_set(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main(["--fallback-style", "LLVM"])

        args = mock_run.call_args_list[1][0][0]
        self.assertTrue(any("-fallback-style=LLVM" in a for a in args))

    def test_fallback_style_absent_when_not_set(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main([])

        args = mock_run.call_args_list[1][0][0]
        self.assertFalse(any("-fallback-style" in a for a in args))

    def test_p_flag_default(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main([])

        args = mock_run.call_args_list[1][0][0]
        self.assertIn("-p1", args)

    def test_p_flag_custom(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main(["-p", "2"])

        args = mock_run.call_args_list[1][0][0]
        self.assertIn("-p2", args)
        self.assertNotIn("-p1", args)

    def test_diff_piped_as_stdin(self):
        with patch("shutil.which", return_value="/usr/bin/clang-format"):
            with patch("subprocess.run", side_effect=[_make_run(SAMPLE_DIFF), _make_run()]) as mock_run:
                main([])

        kwargs = mock_run.call_args_list[1][1]
        self.assertEqual(kwargs.get("input"), SAMPLE_DIFF)


if __name__ == "__main__":
    unittest.main()
