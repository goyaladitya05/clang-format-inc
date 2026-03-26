"""
Run clang-format on specific line ranges within files.

Receives the parsed hunks from diff_parser and invokes clang-format with
``--lines start:end`` for each changed range, leaving all other lines untouched.
"""

from __future__ import annotations

import subprocess


def format_hunks(
    binary: str,
    hunks: dict[str, list[tuple[int, int]]],
    style: str = "file",
    fallback_style: str | None = None,
    sort_includes: bool = False,
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

    Returns:
        0 on success, or the first non-zero return code from clang-format.
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
        cmd += ["-i", filename]

        try:
            result = subprocess.run(cmd)
        except FileNotFoundError:
            # Binary not on PATH — on Windows subprocess raises instead of returning non-zero.
            # main() guards against this with shutil.which, but format_hunks is also a
            # public API that callers may invoke directly.
            return 1
        if result.returncode != 0:
            return result.returncode

    return 0
