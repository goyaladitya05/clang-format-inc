"""
clang-format-inc: Incrementally format only changed C/C++ lines with clang-format.

In CI mode  (PRE_COMMIT_FROM_REF + PRE_COMMIT_TO_REF are set by pre-commit when
running with --from-ref/--to-ref): diffs the two refs and formats only those lines.

In local mode (no env vars): diffs the staging area (--cached) and formats those lines.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from clang_format_inc.diff_parser import parse_diff_hunks
from clang_format_inc.formatter import format_hunks


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Incrementally format changed C/C++ lines with clang-format.")
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
        "--fallback-style",
        default=None,
        metavar="STYLE",
        help="Style to use when --style=file but no .clang-format file is found "
        "(e.g. LLVM, Google). Passed through to clang-format.",
    )
    parser.add_argument(
        "--sort-includes",
        action="store_true",
        default=False,
        help="Pass --sort-includes to clang-format.",
    )
    parser.add_argument(
        "-p",
        type=int,
        default=1,
        metavar="NUM",
        help="Strip NUM leading path components from filenames in the diff "
        "(default: 1, matching git's a/ b/ prefixes).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help="Don't modify files; exit non-zero if any file would be reformatted.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Validate the clang-format binary up front for a clear error message.
    if shutil.which(args.binary) is None:
        print(
            f"clang-format-inc: '{args.binary}' not found. "
            "Install clang-format and make sure it is on PATH, "
            "or pass --binary=/path/to/clang-format.",
            file=sys.stderr,
        )
        return 1

    from_ref = os.environ.get("PRE_COMMIT_FROM_REF")
    to_ref = os.environ.get("PRE_COMMIT_TO_REF")

    if from_ref and to_ref:
        # CI mode: pre-commit was invoked with --from-ref/--to-ref
        diff_cmd = ["git", "diff", "-U0", "--no-color", from_ref, to_ref, "--"] + args.files
    else:
        # Local mode: compare staged (index) vs HEAD.
        # Also used when only one of the two env vars is set (misconfiguration).
        diff_cmd = ["git", "diff", "-U0", "--no-color", "--cached", "--"] + args.files

    try:
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"clang-format-inc: git diff failed:\n{exc.stderr}", file=sys.stderr)
        return exc.returncode

    diff_output = diff_result.stdout
    if not diff_output.strip():
        return 0

    hunks = parse_diff_hunks(diff_output, p=args.p)
    if not hunks:
        return 0

    return format_hunks(
        binary=args.binary,
        hunks=hunks,
        style=args.style,
        fallback_style=args.fallback_style,
        sort_includes=args.sort_includes,
        check=args.check,
    )
