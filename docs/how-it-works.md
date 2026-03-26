# How it works

`clang-format-inc` is a thin orchestrator — it connects three standard tools (`git`, `clang-format`, and Python's `difflib`) to produce incremental formatting.

---

## The pipeline

```
1. Determine diff source
      ├── CI:    git diff -U0 FROM_REF TO_REF -- <files>
      └── Local: git diff -U0 --cached -- <files>

2. Parse the unified diff
      └── extract { filename → [(start, end), ...] }
              (added-line ranges only; deletions and unchanged lines ignored)

3. For each file, invoke clang-format on its ranges only
      └── clang-format --lines=start:end [--lines=...] --style=... -i <file>
```

---

## Step 1 — Determining the diff source

`main.py` checks the environment:

- **CI mode**: `PRE_COMMIT_FROM_REF` and `PRE_COMMIT_TO_REF` are both set → `git diff -U0 FROM TO`
- **Local mode**: env vars absent (or only one is set) → `git diff -U0 --cached`

Using `-U0` (zero context lines) ensures the diff contains only the exact lines that changed, with no surrounding context to confuse the range parser.

---

## Step 2 — Parsing the diff

`diff_parser.py` is a pure function with no I/O. It reads the unified diff string and walks it line by line:

- `+++ b/src/foo.cpp` → sets the current filename (stripping the `b/` prefix via `-p1`)
- `@@ -old +new,count @@` → records `(new, new + count - 1)` as an added-line range
- Skips deletion-only hunks (`+N,0`) and deleted files (`+++ /dev/null`)

The result is a dict: `{"src/foo.cpp": [(5, 8), (20, 22)], ...}`.

---

## Step 3 — Formatting the ranges

`formatter.py` calls clang-format once per file with all its changed ranges:

```bash
clang-format --lines=5:8 --lines=20:22 --style=file -i src/foo.cpp
```

The `--lines` flag tells clang-format to reformat only those line ranges. Lines outside the ranges are output verbatim — the file structure is preserved, only the changed hunks get reformatted.

### Check mode

In `--check` mode, `-i` is omitted. clang-format writes the formatted content to stdout. `formatter.py` compares stdout to the original file — if they differ, the file would have been changed and the hook returns non-zero.

### Diff mode

Same as check mode, but instead of just returning non-zero, `formatter.py` generates a unified diff using Python's `difflib.unified_diff` and writes it to stdout.

---

## Why not use `clang-format-diff.py`?

The LLVM project ships a script (`clang-format-diff.py`) that does something similar — it reads a unified diff and calls `clang-format --lines`. We deliberately don't use it:

1. **License** — it's Apache-2.0; bundling it into an MIT package adds complexity
2. **Dependency maintenance** — vendored files need tracking against upstream LLVM releases
3. **Scope** — we only need the diff-parsing half, which is ~30 lines of Python

`clang_format_inc/diff_parser.py` reimplements that half cleanly, with full test coverage and no external dependency.
