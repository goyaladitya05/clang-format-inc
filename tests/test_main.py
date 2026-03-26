"""Tests for clang_format_inc.main"""

import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, call, patch

from clang_format_inc.main import main, parse_args


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


class TestParseArgs(unittest.TestCase):
    def test_defaults(self):
        args = parse_args([])
        self.assertEqual(args.binary, "clang-format")
        self.assertEqual(args.style, "file")
        self.assertEqual(args.p, 1)
        self.assertEqual(args.files, [])

    def test_custom_options(self):
        args = parse_args(["--binary", "/usr/bin/clang-format-17", "--style", "Google", "-p", "2", "a.cpp"])
        self.assertEqual(args.binary, "/usr/bin/clang-format-17")
        self.assertEqual(args.style, "Google")
        self.assertEqual(args.p, 2)
        self.assertEqual(args.files, ["a.cpp"])


class TestCIMode(unittest.TestCase):
    """When PRE_COMMIT_FROM_REF and PRE_COMMIT_TO_REF are set, use git diff <from> <to>."""

    def _make_diff_run(self, stdout=""):
        mock = MagicMock()
        mock.stdout = stdout
        mock.returncode = 0
        return mock

    def test_ci_mode_calls_git_diff_with_refs(self):
        env = {"PRE_COMMIT_FROM_REF": "abc123", "PRE_COMMIT_TO_REF": "def456"}
        diff_run = self._make_diff_run(stdout=SAMPLE_DIFF)
        format_run = self._make_diff_run()

        with patch.dict(os.environ, env, clear=False):
            with patch("subprocess.run", side_effect=[diff_run, format_run]) as mock_run:
                result = main(["foo.cpp"])

        first_call_args = mock_run.call_args_list[0][0][0]
        self.assertIn("abc123", first_call_args)
        self.assertIn("def456", first_call_args)
        self.assertNotIn("--cached", first_call_args)
        self.assertEqual(result, 0)

    def test_ci_mode_passes_files_to_diff(self):
        env = {"PRE_COMMIT_FROM_REF": "aaa", "PRE_COMMIT_TO_REF": "bbb"}
        diff_run = self._make_diff_run(stdout=SAMPLE_DIFF)
        format_run = self._make_diff_run()

        with patch.dict(os.environ, env, clear=False):
            with patch("subprocess.run", side_effect=[diff_run, format_run]) as mock_run:
                main(["src/foo.cpp", "src/bar.cpp"])

        first_call_args = mock_run.call_args_list[0][0][0]
        self.assertIn("src/foo.cpp", first_call_args)
        self.assertIn("src/bar.cpp", first_call_args)


class TestLocalMode(unittest.TestCase):
    """When PRE_COMMIT_FROM_REF/PRE_COMMIT_TO_REF are absent, use git diff --cached."""

    def setUp(self):
        # Ensure CI env vars are not set
        self._orig = {}
        for key in ("PRE_COMMIT_FROM_REF", "PRE_COMMIT_TO_REF"):
            self._orig[key] = os.environ.pop(key, None)

    def tearDown(self):
        for key, val in self._orig.items():
            if val is not None:
                os.environ[key] = val

    def _make_run(self, stdout=""):
        mock = MagicMock()
        mock.stdout = stdout
        mock.returncode = 0
        return mock

    def test_local_mode_uses_cached(self):
        diff_run = self._make_run(stdout=SAMPLE_DIFF)
        format_run = self._make_run()

        with patch("subprocess.run", side_effect=[diff_run, format_run]) as mock_run:
            result = main(["foo.cpp"])

        first_call_args = mock_run.call_args_list[0][0][0]
        self.assertIn("--cached", first_call_args)
        self.assertEqual(result, 0)

    def test_local_mode_no_ci_refs_in_command(self):
        diff_run = self._make_run(stdout=SAMPLE_DIFF)
        format_run = self._make_run()

        with patch("subprocess.run", side_effect=[diff_run, format_run]) as mock_run:
            main([])

        first_call_args = mock_run.call_args_list[0][0][0]
        # No commit SHAs from CI env vars should appear
        self.assertNotIn("PRE_COMMIT_FROM_REF", " ".join(first_call_args))


class TestEmptyDiff(unittest.TestCase):
    """When there are no changed lines, clang-format-diff should not be invoked."""

    def setUp(self):
        for key in ("PRE_COMMIT_FROM_REF", "PRE_COMMIT_TO_REF"):
            os.environ.pop(key, None)

    def test_skips_formatting_when_diff_empty(self):
        diff_run = MagicMock()
        diff_run.stdout = ""
        diff_run.returncode = 0

        with patch("subprocess.run", return_value=diff_run) as mock_run:
            result = main([])

        # subprocess.run should be called exactly once (for git diff), not again for clang-format-diff
        self.assertEqual(mock_run.call_count, 1)
        self.assertEqual(result, 0)

    def test_skips_formatting_when_diff_whitespace_only(self):
        diff_run = MagicMock()
        diff_run.stdout = "   \n  \n"
        diff_run.returncode = 0

        with patch("subprocess.run", return_value=diff_run) as mock_run:
            result = main([])

        self.assertEqual(mock_run.call_count, 1)
        self.assertEqual(result, 0)


class TestFormatCommand(unittest.TestCase):
    """Verify the clang-format-diff invocation uses correct flags."""

    def setUp(self):
        for key in ("PRE_COMMIT_FROM_REF", "PRE_COMMIT_TO_REF"):
            os.environ.pop(key, None)

    def _make_run(self, stdout=""):
        mock = MagicMock()
        mock.stdout = stdout
        mock.returncode = 0
        return mock

    def test_format_command_includes_inplace_flag(self):
        diff_run = self._make_run(stdout=SAMPLE_DIFF)
        format_run = self._make_run()

        with patch("subprocess.run", side_effect=[diff_run, format_run]) as mock_run:
            main([])

        second_call_args = mock_run.call_args_list[1][0][0]
        self.assertIn("-i", second_call_args)

    def test_custom_binary_passed_to_format_script(self):
        diff_run = self._make_run(stdout=SAMPLE_DIFF)
        format_run = self._make_run()

        with patch("subprocess.run", side_effect=[diff_run, format_run]) as mock_run:
            main(["--binary", "/usr/local/bin/clang-format-17"])

        second_call_args = mock_run.call_args_list[1][0][0]
        self.assertTrue(any("-binary=/usr/local/bin/clang-format-17" in a for a in second_call_args))

    def test_custom_style_passed_to_format_script(self):
        diff_run = self._make_run(stdout=SAMPLE_DIFF)
        format_run = self._make_run()

        with patch("subprocess.run", side_effect=[diff_run, format_run]) as mock_run:
            main(["--style", "Google"])

        second_call_args = mock_run.call_args_list[1][0][0]
        self.assertTrue(any("-style=Google" in a for a in second_call_args))

    def test_format_script_receives_diff_on_stdin(self):
        diff_run = self._make_run(stdout=SAMPLE_DIFF)
        format_run = self._make_run()

        with patch("subprocess.run", side_effect=[diff_run, format_run]) as mock_run:
            main([])

        second_call_kwargs = mock_run.call_args_list[1][1]
        self.assertEqual(second_call_kwargs.get("input"), SAMPLE_DIFF)


if __name__ == "__main__":
    unittest.main()
