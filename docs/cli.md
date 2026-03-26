# CLI Reference

```
clang-format-inc [OPTIONS] [FILES ...]
```

`FILES` are the C/C++ files to consider. When used as a pre-commit hook, pre-commit passes the staged files automatically.

---

## Options

### `--binary PATH`

Path to the `clang-format` executable.

**Default:** `clang-format` (resolved from `PATH`)

```bash
clang-format-inc --binary /usr/lib/llvm-18/bin/clang-format
```

---

### `--style STYLE`

Formatting style passed to `clang-format`.

**Default:** `file` (reads `.clang-format` from the nearest parent directory)

Common values: `LLVM`, `Google`, `Chromium`, `Mozilla`, `WebKit`, `Microsoft`, `file`.

```bash
clang-format-inc --style Google
```

---

### `--fallback-style STYLE`

Style to use when `--style=file` is active but no `.clang-format` file is found.

**Default:** none (clang-format uses `LLVM` as its own fallback)

```bash
clang-format-inc --fallback-style LLVM
```

---

### `--sort-includes`

Pass `--sort-includes` to `clang-format`, enabling include sorting.

**Default:** off

---

### `-p NUM`

Strip `NUM` leading path components from filenames in the diff. Matches the `-p` flag of `patch`.

**Default:** `1` (strips git's `a/` / `b/` prefixes)

---

### `--include REGEX`

Only process files whose path matches this regular expression.

```bash
clang-format-inc --include '\.cpp$'
```

---

### `--exclude REGEX`

Skip files whose path matches this regular expression.

```bash
clang-format-inc --exclude 'third_party/'
```

---

### `--workers N`

Number of parallel `clang-format` processes.

**Default:** `1` (sequential)

---

## Modes (mutually exclusive)

### `--check`

Do not modify files. Exit non-zero and print a message if any changed line would be reformatted.

### `--diff`

Do not modify files. Print a unified diff of what would change and exit non-zero if any file would be reformatted.

---

## Environment variables

These are set automatically by pre-commit when running with `--from-ref`/`--to-ref`. You can also set them manually.

| Variable | Effect |
|---|---|
| `PRE_COMMIT_FROM_REF` | Base commit SHA for CI diff |
| `PRE_COMMIT_TO_REF` | Head commit SHA for CI diff |

When both are set, `clang-format-inc` uses `git diff FROM TO`. Otherwise it uses `git diff --cached`.

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success — no changes needed (or changes applied) |
| `1` | Binary not found, git error, or (in check/diff mode) file would be reformatted |
| other | `clang-format` returned a non-zero exit code |
