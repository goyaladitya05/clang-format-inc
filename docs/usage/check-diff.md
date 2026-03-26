# Check & diff modes

Both modes are **read-only** — they never modify files. They are mutually exclusive.

---

## `--check`

Exits non-zero if any changed line would be reformatted. Prints a message identifying the file.

```bash
clang-format-inc --check foo.cpp
# clang-format-inc: foo.cpp would be reformatted
# exit code: 1
```

**Use case:** enforce formatting in CI without auto-fixing. Developers must fix formatting themselves before the PR can merge.

```yaml
hooks:
  - id: clang-format-inc
    args: [--check]
```

---

## `--diff`

Exits non-zero if any changed line would be reformatted, and prints a **unified diff** of exactly what would change.

```bash
clang-format-inc --diff foo.cpp
```

```diff
--- a/foo.cpp
+++ b/foo.cpp
@@ -1 +1 @@
-int x=1;
+int x = 1;
```

**Use cases:**

- Debugging — see exactly what clang-format wants to change
- PR comment bots — parse the diff and post inline comments
- Pre-flight check before auto-formatting

```yaml
hooks:
  - id: clang-format-inc
    args: [--diff]
```

---

## Comparison

| | Default | `--check` | `--diff` |
|---|---|---|---|
| Modifies files | ✅ | ❌ | ❌ |
| Exit non-zero on changes | ❌ | ✅ | ✅ |
| Shows what would change | ❌ | message only | full unified diff |
