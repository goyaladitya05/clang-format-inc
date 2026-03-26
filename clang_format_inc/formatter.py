"""
Run clang-format on specific line ranges within files.

Receives the parsed hunks from diff_parser and invokes clang-format with
``--lines start:end`` for each changed range, leaving all other lines untouched.
"""

from __future__ import annotations

import difflib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def _format_file(
    binary: str,
    filename: str,
    ranges: list[tuple[int, int]],
    style: str,
    fallback_style: str | None,
    sort_includes: bool,
    check: bool,
    diff: bool,
) -> tuple[int, str]:
    """Format (or inspect) a single file for the given line ranges.

    Returns ``(returncode, diff_text)`` where *diff_text* is a non-empty
    unified diff string only when *diff* mode is active and changes exist.
    """
    cmd = [binary]
    for start, end in ranges:
        cmd += ["--lines", f"{start}:{end}"]
    cmd += ["--style", style]
    if fallback_style:
        cmd += ["--fallback-style", fallback_style]
    if sort_includes:
        cmd.append("--sort-includes")

    if check or diff:
        # Read-only modes: run without -i, compare stdout to original.
        try:
            proc = subprocess.run(cmd + [filename], capture_output=True, text=True)
        except FileNotFoundError:
            return 1, ""
        if proc.returncode != 0:
            return proc.returncode, ""
        original = Path(filename).read_text()
        if proc.stdout == original:
            return 0, ""
        if check:
            print(f"clang-format-inc: {filename} would be reformatted", file=sys.stderr)
            return 1, ""
        # diff mode: emit a unified diff to stdout.
        diff_text = "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                proc.stdout.splitlines(keepends=True),
                fromfile=f"a/{filename}",
                tofile=f"b/{filename}",
            )
        )
        return 1, diff_text

    # Default: format in-place.
    try:
        fmt_proc = subprocess.run(cmd + ["-i", filename])
    except FileNotFoundError:
        # Binary not on PATH — on Windows subprocess raises instead of returning non-zero.
        # main() guards against this with shutil.which, but format_hunks is also a
        # public API that callers may invoke directly.
        return 1, ""
    return fmt_proc.returncode, ""


def format_hunks(
    binary: str,
    hunks: dict[str, list[tuple[int, int]]],
    style: str = "file",
    fallback_style: str | None = None,
    sort_includes: bool = False,
    check: bool = False,
    diff: bool = False,
    workers: int = 1,
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
        diff:           If ``True``, do not modify files.  Print a unified diff
                        to stdout and return non-zero if any file would change.
        workers:        Number of parallel clang-format processes (default 1).
                        Values > 1 process all files concurrently; useful for
                        large CI jobs with many changed files.

    Returns:
        0 on success.  In check/diff mode, 1 if any file would be reformatted.
        Otherwise the first non-zero exit code returned by clang-format.
    """
    if not hunks:
        return 0

    items = list(hunks.items())

    if workers == 1:
        # Sequential: stop on first error (preserves existing behaviour).
        for filename, ranges in items:
            rc, diff_text = _format_file(binary, filename, ranges, style, fallback_style, sort_includes, check, diff)
            if diff_text:
                sys.stdout.write(diff_text)
            if rc != 0:
                return rc
        return 0

    # Parallel: submit all, collect in submission order, then report.
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                _format_file,
                binary,
                filename,
                ranges,
                style,
                fallback_style,
                sort_includes,
                check,
                diff,
            )
            for filename, ranges in items
        ]
        results = [f.result() for f in futures]

    first_error = 0
    for rc, diff_text in results:
        if diff_text:
            sys.stdout.write(diff_text)
        if rc != 0 and first_error == 0:
            first_error = rc
    return first_error
