"""
Run clang-format on specific line ranges within files.

Receives the parsed hunks from diff_parser and invokes clang-format with
``--lines start:end`` for each changed range, leaving all other lines untouched.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def format_hunks(
    binary: str,
    hunks: dict[str, list[tuple[int, int]]],
    style: str = "file",
    fallback_style: str | None = None,
    sort_includes: bool = False,
    check: bool = False,
) -> int:
    """Invoke clang-format on the given line ranges for each file.

    Args:
        binary:         Path or name of the clang-format executable.
        hunks:          ``{filename: [(start, end), ...]}`` as returned by
                        :func:`~clang_format_inc.diff_parser.parse_diff_hunks`.
                        Filenames are resolved relative to the current working
                        directory.
        style:          Value for ``--style`` (default ``"file"``).
        fallback_style: Value for ``--fallback-style`` when no ``.clang-format``
                        file is found.  ``None`` omits the flag.
        sort_includes:  Pass ``--sort-includes`` to clang-format.
        check:          If ``True``, do not modify files.  Return non-zero and
                        print a message if any file *would* be reformatted.

    Returns:
        0 on success, or the first non-zero return code from clang-format.
        In check mode, returns 1 if any file would be reformatted.
    """
    for filename, ranges in hunks.items():
        cmd = [binary]
        for start, end in ranges:
            cmd += ["--lines", f"{start}:{end}"]
        cmd += ["--style", style]
        if fallback_style:
            cmd += ["--fallback-style", fallback_style]
        if sort_includes:
            cmd.append("--sort-includes")

        if check:
            # No -i: clang-format writes the fully-formatted file to stdout.
            # Compare to the original; report and fail if they differ.
            try:
                result = subprocess.run(cmd + [filename], capture_output=True, text=True)
            except FileNotFoundError:
                return 1
            if result.returncode != 0:
                return result.returncode
            original = Path(filename).read_text()
            if result.stdout != original:
                print(f"clang-format-inc: {filename} would be reformatted", file=sys.stderr)
                return 1
        else:
            # Format in-place.
            try:
                result = subprocess.run(cmd + ["-i", filename])
            except FileNotFoundError:
                # Binary not on PATH — on Windows subprocess raises instead of returning non-zero.
                # main() guards against this with shutil.which, but format_hunks is also a
                # public API that callers may invoke directly.
                return 1
            if result.returncode != 0:
                return result.returncode

    return 0
