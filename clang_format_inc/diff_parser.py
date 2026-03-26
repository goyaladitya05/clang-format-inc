"""
Parse unified diff output to extract per-file added-line ranges.

This replaces the vendored clang-format-diff.py from LLVM.  We only need the
diff-parsing half; the clang-format invocation lives in formatter.py.
"""

from __future__ import annotations

import re
from collections import defaultdict

# Matches the +++ header line produced by git diff.
# Group 1: the filename after stripping p leading path components.
# Example with p=1:  "+++ b/src/foo.cpp"  →  "src/foo.cpp"
_PLUS_HEADER = re.compile(r"^\+\+\+[ \t]+(?:.*?/){{{p}}}(.+)")

# Matches a hunk header and captures the start line and optional count.
# Example:  "@@ -1,3 +5,4 @@"  →  start=5, count=4
_HUNK_HEADER = re.compile(r"^@@.*\+(\d+)(?:,(\d+))?")


def parse_diff_hunks(diff: str, p: int = 1) -> dict[str, list[tuple[int, int]]]:
    """Return a mapping of filename → added line ranges from a unified diff.

    Args:
        diff: Unified diff string, e.g. from ``git diff -U0 --no-color``.
        p:    Number of leading path components to strip from filenames
              (matches the ``-p`` flag of ``patch``).  Default 1 matches
              git's ``a/`` / ``b/`` prefixes.

    Returns:
        ``{filename: [(start, end), ...]}`` where *start* and *end* are
        1-indexed line numbers (inclusive) of added hunks.  Deleted-only
        hunks (``+N,0``) and deleted files (``+++ /dev/null``) are excluded.
    """
    hunks: dict[str, list[tuple[int, int]]] = defaultdict(list)
    filename: str | None = None
    plus_re = re.compile(_PLUS_HEADER.pattern.format(p=p))

    for line in diff.splitlines():
        m = plus_re.match(line)
        if m:
            candidate = m.group(1).strip()
            # Deleted files produce "+++ /dev/null"; after prefix-stripping
            # this becomes "dev/null".  Skip them — their hunks have count=0
            # anyway, but being explicit is safer.
            if candidate in ("/dev/null", "dev/null"):
                filename = None
            else:
                filename = candidate
            continue

        if filename is None:
            continue

        m = _HUNK_HEADER.match(line)
        if m:
            start = int(m.group(1))
            count = 1 if m.group(2) is None else int(m.group(2))
            if count == 0:
                # Pure deletion — no lines were added, nothing to format.
                continue
            hunks[filename].append((start, start + count - 1))

    return dict(hunks)
