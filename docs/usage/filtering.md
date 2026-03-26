# File filtering

By default, `clang-format-inc` processes every file that appears in the diff. Two flags let you narrow that down by matching file paths against regular expressions.

---

## `--include REGEX`

Only process files whose path **matches** the regex. Files that don't match are silently skipped.

```bash
# Only format .cpp files, skip headers
clang-format-inc --include '\.cpp$'
```

```yaml
hooks:
  - id: clang-format-inc
    args: ['--include', '\.cpp$']
```

---

## `--exclude REGEX`

Skip files whose path **matches** the regex.

```bash
# Skip anything under third_party/ or generated/
clang-format-inc --exclude 'third_party/|generated/'
```

```yaml
hooks:
  - id: clang-format-inc
    args: ['--exclude', 'third_party/|generated/']
```

---

## Using both together

`--include` is applied first, then `--exclude`. A file must pass both filters to be processed.

```yaml
hooks:
  - id: clang-format-inc
    args:
      - '--include'
      - 'src/'       # only files under src/
      - '--exclude'
      - 'src/gen/'   # but not generated files inside src/
```

---

## Note on pre-commit's `types_or`

When used as a pre-commit hook, pre-commit already filters files by type (`c`, `c++`, `cuda`, `objective-c`) before passing them to `clang-format-inc`. The `--include`/`--exclude` flags are most useful when running `clang-format-inc` **standalone** from the CLI, or when you need finer-grained control than type detection provides.
