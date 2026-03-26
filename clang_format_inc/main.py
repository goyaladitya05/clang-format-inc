"""
clang-format-inc: Incrementally format only changed C/C++ lines with clang-format.

In CI mode  (PRE_COMMIT_FROM_REF + PRE_COMMIT_TO_REF are set by pre-commit when
running with --from-ref/--to-ref): diffs the two refs and formats only those lines.

In local mode (no env vars): diffs the staging area (--cached) and formats those lines.

The actual line-range formatting is delegated to clang-format-diff.py (bundled from LLVM,
Apache-2.0 license), which reads a unified diff on stdin and applies clang-format only to
the changed hunks.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _diff_script_path() -> Path:
    return Path(__file__).parent / "clang_format_diff.py"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Incrementally format changed C/C++ lines with clang-format."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to consider (passed automatically by pre-commit).",
    )
    parser.add_argument(
        "--binary",
        default="clang-format",
        help="Path to clang-format binary (default: clang-format).",
    )
    parser.add_argument(
        "--style",
        default="file",
        help="Formatting style passed to clang-format (default: file).",
    )
    parser.add_argument(
        "-p",
        type=int,
        default=1,
        metavar="NUM",
        help="Strip NUM leading path components from filenames in the diff "
             "(default: 1, matching git's a/ b/ prefixes).",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    from_ref = os.environ.get("PRE_COMMIT_FROM_REF")
    to_ref = os.environ.get("PRE_COMMIT_TO_REF")

    if from_ref and to_ref:
        # CI mode: pre-commit was invoked with --from-ref/--to-ref
        diff_cmd = [
            "git", "diff", "-U0", "--no-color",
            from_ref, to_ref, "--",
        ] + args.files
    else:
        # Local mode: compare staged (index) vs HEAD
        diff_cmd = [
            "git", "diff", "-U0", "--no-color",
            "--cached", "--",
        ] + args.files

    try:
        diff_result = subprocess.run(
            diff_cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"clang-format-inc: git diff failed:\n{exc.stderr}", file=sys.stderr)
        return exc.returncode

    diff_output = diff_result.stdout
    if not diff_output.strip():
        # Nothing changed — skip formatting entirely
        return 0

    diff_script = _diff_script_path()
    format_cmd = [
        sys.executable,
        str(diff_script),
        "-i",
        f"-p{args.p}",
        f"-style={args.style}",
        f"-binary={args.binary}",
    ]

    try:
        result = subprocess.run(
            format_cmd,
            input=diff_output,
            text=True,
        )
    except FileNotFoundError:
        print(
            f"clang-format-inc: could not find clang-format binary '{args.binary}'. "
            "Make sure it is installed and on PATH.",
            file=sys.stderr,
        )
        return 1

    return result.returncode
