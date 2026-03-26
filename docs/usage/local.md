# Local mode

When no CI environment variables are set, `clang-format-inc` operates in **local mode**: it diffs the staging area against `HEAD` using `git diff --cached`.

## How it works

```
git commit
  └─ pre-commit runs clang-format-inc
      └─ git diff -U0 --cached -- <staged files>
          └─ parse added-line ranges per file
              └─ clang-format --lines=N:M -i <file>
```

Only lines that exist in the staged diff are formatted. Unstaged changes are never touched.

## Example

```bash
# Commit well-formatted code alongside a bad new line
git add good_file.cpp          # already formatted — safe
git add new_feature.cpp        # badly formatted new code
git commit -m "add feature"
# → only the changed lines in new_feature.cpp are formatted
# → good_file.cpp is untouched
```

## Unstaged changes

If you modify a file but don't stage it, the hook will not touch it — even if those lines are badly formatted. Only staged changes are in scope.

## Untracked files

New files that have never been committed have no prior revision to diff against. They are formatted **in their entirety** rather than incrementally. Stage the file with `git add` and the hook picks up all lines as "added".
