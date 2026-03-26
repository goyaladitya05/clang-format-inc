# Installation

## As a pre-commit hook (recommended)

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/goyaladitya05/clang-format-inc
    rev: v1.0.0
    hooks:
      - id: clang-format-inc
```

Then install the hooks:

```bash
pip install pre-commit
pre-commit install
```

`clang-format` is automatically installed into the hook's isolated virtualenv via `additional_dependencies`. No system-wide `clang-format` install is needed.

### Pin a specific clang-format version

```yaml
hooks:
  - id: clang-format-inc
    additional_dependencies: ['clang-format==18.1.0']
```

Any version available on PyPI as the [`clang-format`](https://pypi.org/project/clang-format/) package can be pinned this way.

---

## As a standalone CLI tool

```bash
pip install clang-format-inc
```

You will also need `clang-format` available on your `PATH`, or pass `--binary` to specify its location:

```bash
clang-format-inc --binary /usr/lib/llvm-18/bin/clang-format foo.cpp
```

---

## Requirements

- Python 3.9+
- Git (must be on `PATH`)
- `clang-format` — installed automatically by pre-commit, or manually for standalone use
