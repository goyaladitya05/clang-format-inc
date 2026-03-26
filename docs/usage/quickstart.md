# Quick start

## 1. Add a `.clang-format` file

Put a style config in your repo root so clang-format knows your project's style:

```yaml
# .clang-format
BasedOnStyle: LLVM
IndentWidth: 4
ColumnLimit: 120
```

Common bases: `LLVM`, `Google`, `Chromium`, `Mozilla`, `WebKit`, `Microsoft`.

Without this file, clang-format falls back to `LLVM` style.

---

## 2. Add the hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/goyaladitya05/clang-format-inc
    rev: v0.3.0
    hooks:
      - id: clang-format-inc
```

---

## 3. Install

```bash
pip install pre-commit
pre-commit install
```

---

## 4. Try it

Stage a badly-formatted C++ file and commit:

```bash
echo 'int main(){int x=1;return x;}' > foo.cpp
git add foo.cpp
git commit -m "test"
```

The hook runs, formats only the changed lines in-place, and pre-commit detects the modification — the commit is blocked and you see:

```
clang-format-inc...........................................................Failed
- hook id: clang-format-inc
- files were modified by this hook
```

Run `git add foo.cpp` and commit again — this time it passes because the file is now formatted.

---

## 5. Run manually

```bash
# Format staged changes right now
pre-commit run clang-format-inc

# Format all files (useful for initial setup)
pre-commit run clang-format-inc --all-files
```
