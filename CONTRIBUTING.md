# Contributing to clang-format-inc

Thanks for taking the time to contribute!

---

## Reporting bugs

Open an issue and include:

- OS and Python version (`python --version`)
- `clang-format` version (`clang-format --version`)
- pre-commit version (`pre-commit --version`)
- Your `.pre-commit-config.yaml` snippet
- The full error output
- A minimal reproduction (ideally a diff or a small C++ file)

## Requesting features

Open an issue describing:

- The problem you're trying to solve
- The proposed behaviour with a usage example
- Why the existing `--binary`, `--style`, `-p`, `--fallback-style` flags don't cover it

---

## Development setup

```bash
git clone https://github.com/goyaladitya05/clang-format-inc
cd clang-format-inc
pip install -e ".[dev]"
pre-commit install
```

## Running tests

```bash
pytest                          # all tests
pytest -v tests/test_main.py   # verbose
pytest --cov=clang_format_inc  # with coverage
```

## Running linters

```bash
ruff check .          # lint
ruff format --check . # formatting check
mypy clang_format_inc/
```

Or let pre-commit run everything before each commit:

```bash
pre-commit run --all-files
```

---

## Submitting a pull request

1. Fork the repo and create a branch from `main`
2. Make your changes, add tests for new behaviour
3. Ensure `pytest`, `ruff check`, and `mypy` all pass
4. Update `CHANGELOG.md` under `[Unreleased]`
5. Open a PR — describe what it does and why

---

## Bundled file

`clang_format_inc/clang_format_diff.py` is vendored from the LLVM project
(Apache-2.0 WITH LLVM-exception). **Do not modify it** — update by fetching
the latest version from:

```
https://github.com/llvm/llvm-project/blob/main/clang/tools/clang-format/clang-format-diff.py
```
