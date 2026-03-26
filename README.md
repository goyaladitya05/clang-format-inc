# clang-format-inc

[![CI](https://github.com/goyaladitya05/clang-format-inc/actions/workflows/ci.yml/badge.svg)](https://github.com/goyaladitya05/clang-format-inc/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/clang-format-inc.svg)](https://pypi.org/project/clang-format-inc/)
[![Python versions](https://img.shields.io/pypi/pyversions/clang-format-inc.svg)](https://pypi.org/project/clang-format-inc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Incremental C/C++ formatting as a pre-commit hook — format only the lines you changed.**

---

## The problem

| Tool | Issue |
|---|---|
| `mirrors-clang-format` | Reformats **entire files** — breaks diffs in large codebases |
| `git clang-format --staged` | Works locally, but **staging area is empty in CI** when pre-commit uses `--from-ref`/`--to-ref` |

`clang-format-inc` solves both: it reads the `PRE_COMMIT_FROM_REF` / `PRE_COMMIT_TO_REF` environment variables that pre-commit sets in CI mode and falls back to `--cached` (staged changes) locally.

Inspired by [`darker`](https://github.com/akaihola/darker), which does the same for Python/Black.

---

## How it works

```
pre-commit (CI, --from-ref/--to-ref)
  └─ sets PRE_COMMIT_FROM_REF, PRE_COMMIT_TO_REF
      └─ clang-format-inc
          └─ git diff -U0 $FROM_REF $TO_REF -- <files>
              └─ clang-format-diff.py -i -p1  ← formats only changed lines

pre-commit (local)
  └─ clang-format-inc
      └─ git diff -U0 --cached -- <files>
          └─ clang-format-diff.py -i -p1
```

The diff is piped to [clang-format-diff.py](https://github.com/llvm/llvm-project/blob/main/clang/tools/clang-format/clang-format-diff.py) (bundled from LLVM), which calls `clang-format --lines=<start>:<end>` for each changed hunk. **Only touched lines are reformatted.**

---

## Requirements

- Python 3.8+
- `clang-format` on `PATH` (or specify with `--binary`)

---

## Usage as a pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/goyaladitya05/clang-format-inc
    rev: v0.1.0
    hooks:
      - id: clang-format-inc
        # Optional overrides:
        # args: [--binary=clang-format-17, --style=Google]
```

Run locally:

```bash
pre-commit run clang-format-inc --all-files
```

Run in CI (GitHub Actions example):

```yaml
- name: Run pre-commit
  run: |
    pre-commit run clang-format-inc \
      --from-ref ${{ github.event.pull_request.base.sha }} \
      --to-ref   ${{ github.event.pull_request.head.sha }}
```

---

## CLI reference

```
clang-format-inc [options] [files ...]

Options:
  --binary PATH          Path to clang-format binary (default: clang-format)
  --style STYLE          Formatting style: file, LLVM, Google, etc. (default: file)
  --fallback-style STYLE Style to use when --style=file but no .clang-format found
  -p NUM                 Strip NUM leading path components from diff filenames (default: 1)
```

---

## Install from PyPI

```bash
pip install clang-format-inc
```

---

## Environment variables (set automatically by pre-commit)

| Variable | When set | Value |
|---|---|---|
| `PRE_COMMIT_FROM_REF` | CI mode (`--from-ref`) | Base commit SHA |
| `PRE_COMMIT_TO_REF` | CI mode (`--to-ref`) | Head commit SHA |

When both are set, `clang-format-inc` diffs those two commits. Otherwise it diffs the index (`--cached`).

---

## License

- `clang-format-inc` itself: **MIT** © Aditya Goyal
- Bundled `clang_format_diff.py`: **Apache-2.0 WITH LLVM-exception** (from the LLVM Project)
