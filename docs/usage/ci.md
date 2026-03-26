# CI mode

When pre-commit is invoked with `--from-ref` and `--to-ref`, it sets `PRE_COMMIT_FROM_REF` and `PRE_COMMIT_TO_REF` in the environment. `clang-format-inc` detects these and diffs between the two refs instead of using the staging area.

This solves the classic CI problem: **the staging area is empty when pre-commit runs in CI**, so `git diff --cached` would always return nothing.

## GitHub Actions

### Using the pre-commit action (simplest)

```yaml
# .github/workflows/pre-commit.yml
name: pre-commit

on:
  pull_request:

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # needed so git can access the base ref

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - uses: pre-commit/action@v3.0.1
        with:
          extra_args: >-
            --from-ref ${{ github.event.pull_request.base.sha }}
            --to-ref   ${{ github.event.pull_request.head.sha }}
```

### Manual invocation

```yaml
- name: Run clang-format-inc
  run: |
    pip install pre-commit
    pre-commit run clang-format-inc \
      --from-ref ${{ github.event.pull_request.base.sha }} \
      --to-ref   ${{ github.event.pull_request.head.sha }}
```

## How the env vars are used

```
PRE_COMMIT_FROM_REF=abc123   (base commit SHA)
PRE_COMMIT_TO_REF=def456     (head commit SHA)
  └─ git diff -U0 --no-color abc123 def456 -- <files>
      └─ parse changed lines
          └─ clang-format --lines=N:M -i <file>
```

## Partial env var guard

If only one of `PRE_COMMIT_FROM_REF` / `PRE_COMMIT_TO_REF` is set (misconfiguration), `clang-format-inc` falls back to local mode rather than crashing.

## Check-only in CI

If you want CI to **report** formatting issues without auto-applying fixes (common in open-source workflows), use `--check`:

```yaml
hooks:
  - id: clang-format-inc
    args: [--check]
```

The hook will exit non-zero and print which files would be reformatted, without modifying them.
