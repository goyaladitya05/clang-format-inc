# Parallel processing

By default `clang-format-inc` processes one file at a time. For large CI jobs with many changed files, the `--workers` flag enables parallel execution.

## `--workers N`

```bash
clang-format-inc --workers 4 file1.cpp file2.cpp file3.cpp file4.cpp
```

```yaml
hooks:
  - id: clang-format-inc
    args: ['--workers', '4']
```

Each worker runs an independent `clang-format` process. The number of workers is capped by your machine's CPU count in practice — setting it higher than that provides no benefit.

---

## Sequential vs parallel behaviour

| | Sequential (default) | Parallel (`--workers N`) |
|---|---|---|
| Stops on first error | ✅ Yes | ❌ No — all files run |
| Output order | Deterministic | Deterministic (submission order) |
| Diff output ordering | In order | In order |

In parallel mode, all files are submitted at once and results are collected in the original file order, so diff output is always consistent regardless of which worker finishes first.

---

## When to use it

For most projects, the default sequential mode is fast enough — pre-commit only passes changed files, and `clang-format` is very quick per file. Consider `--workers` when:

- Your CI job routinely sees tens or hundreds of changed files
- You're running `--all-files` on initial adoption across a large codebase
