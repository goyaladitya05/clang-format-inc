# clang-format-inc

**Incremental C/C++ formatting as a pre-commit hook — format only the lines you changed.**

[![CI](https://github.com/goyaladitya05/clang-format-inc/actions/workflows/ci.yml/badge.svg)](https://github.com/goyaladitya05/clang-format-inc/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/clang-format-inc.svg)](https://pypi.org/project/clang-format-inc/)
[![Python versions](https://img.shields.io/pypi/pyversions/clang-format-inc.svg)](https://pypi.org/project/clang-format-inc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/goyaladitya05/clang-format-inc/blob/main/LICENSE)

---

## The problem

| Tool | Issue |
|---|---|
| `mirrors-clang-format` | Reformats **entire files** — pollutes diffs in large codebases |
| `git clang-format --staged` | Works locally, but **staging area is empty in CI** when pre-commit uses `--from-ref`/`--to-ref` |

`clang-format-inc` solves both. It reads the `PRE_COMMIT_FROM_REF` / `PRE_COMMIT_TO_REF` environment variables that pre-commit sets in CI mode and falls back to `git diff --cached` locally.

Inspired by [`darker`](https://github.com/akaihola/darker), which does the same thing for Python/Black.

---

## Quick start

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/goyaladitya05/clang-format-inc
    rev: v0.3.0
    hooks:
      - id: clang-format-inc
```

`clang-format` is installed automatically — no system-wide install needed.

Then:

```bash
pip install pre-commit
pre-commit install
```

That's it. Every `git commit` now formats only the lines you changed.

---

## Why incremental?

Imagine you're working on a large legacy codebase where half the files aren't yet formatted. Running `clang-format` on whole files every commit would:

- Reformat thousands of untouched lines
- Make every PR unreadable — formatting noise drowns real changes
- Trigger conflicts with teammates working on the same files

Incremental formatting enforces style **only on new code** — the code you actually wrote. Legacy lines stay untouched until someone deliberately reformats them.
