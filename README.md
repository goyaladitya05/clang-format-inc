# clang-format-inc

[![CI](https://github.com/goyaladitya05/clang-format-inc/actions/workflows/ci.yml/badge.svg)](https://github.com/goyaladitya05/clang-format-inc/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/clang-format-inc.svg)](https://pypi.org/project/clang-format-inc/)
[![Python versions](https://img.shields.io/pypi/pyversions/clang-format-inc.svg)](https://pypi.org/project/clang-format-inc/)
[![Docs](https://img.shields.io/badge/docs-online-blue.svg)](https://goyaladitya05.github.io/clang-format-inc/)
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
              └─ clang-format --lines=<start>:<end> -i <file>  ← only changed lines
pre-commit (local)
  └─ clang-format-inc
      └─ git diff -U0 --cached -- <files>
          └─ clang-format --lines=<start>:<end> -i <file>
```

The diff is parsed to extract added-line ranges per file. `clang-format` is called with `--lines=start:end` for each changed hunk — **only touched lines are reformatted.**

---

## Requirements

- Python 3.8+
- `clang-format` — installed automatically by pre-commit via `additional_dependencies` (see below), or specify a custom binary with `--binary`

---

## Usage as a pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/goyaladitya05/clang-format-inc
    rev: v0.2.0
    hooks:
      - id: clang-format-inc
```

`clang-format` is installed automatically into the hook's virtualenv — no system-wide install needed.

### Pin a specific clang-format version

```yaml
hooks:
  - id: clang-format-inc
    additional_dependencies: ['clang-format==18.1.0']
```

### Check mode (report without fixing)

```yaml
hooks:
  - id: clang-format-inc
    args: [--check]
```

With `--check`, the hook exits non-zero if any changed line would be reformatted, but **never modifies files**. Useful in CI pipelines where you want to report issues without auto-applying fixes.

### Diff mode (show what would change)

```yaml
hooks:
  - id: clang-format-inc
    args: [--diff]
```

Like `--check`, but also prints a unified diff of every change that would be applied. Useful for PR comment bots or debugging. `--check` and `--diff` are mutually exclusive.

### Run locally

```bash
pre-commit run clang-format-inc --all-files
```

### Run in CI (GitHub Actions example)

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
  --sort-includes        Pass --sort-includes to clang-format
  -p NUM                 Strip NUM leading path components from diff filenames (default: 1)
  --include REGEX        Only process files whose path matches this regex
  --exclude REGEX        Skip files whose path matches this regex
  --workers N            Number of parallel clang-format processes (default: 1)

Modes (mutually exclusive):
  --check                Don't modify files; exit non-zero if any file would be reformatted
  --diff                 Don't modify files; print a unified diff of what would change
```

## Notes

**Untracked files** (not yet added to git) have no history to diff against, so they are formatted in their entirety rather than incrementally. Stage the file with `git add` first for incremental behaviour.

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

MIT © Aditya Goyal
