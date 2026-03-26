# Changelog

The full changelog is maintained in [`CHANGELOG.md`](https://github.com/goyaladitya05/clang-format-inc/blob/main/CHANGELOG.md) on GitHub.

---

## [1.0.0] — 2026-03-26

First stable release. No breaking changes from 0.3.0 — marks the API and behaviour as production-ready.

### Changed
- Development status bumped to `Production/Stable`

---

## [0.3.0] — 2026-03-26

### Added
- **`--diff` mode**: print a unified diff of what would change without modifying files
- **`--include REGEX`**: only process files whose path matches the given regex
- **`--exclude REGEX`**: skip files whose path matches the given regex
- **`--workers N`**: parallel clang-format processes (default 1)
- README: document untracked-files behaviour

---

## [0.2.0] — 2026-03-26

### Added
- **`--check` mode**: exit non-zero if any changed line would be reformatted, without modifying files
- **`additional_dependencies: ['clang-format']`** in `.pre-commit-hooks.yaml`: clang-format installs automatically, no system install required

---

## [0.1.0] — 2026-03-26

Initial release.

### Added
- Incremental C/C++ formatting: format only lines changed in a diff
- CI mode via `PRE_COMMIT_FROM_REF` / `PRE_COMMIT_TO_REF`
- Local mode via `git diff --cached`
- `--binary`, `--style`, `--fallback-style`, `--sort-includes`, `-p` options
- `.pre-commit-hooks.yaml` for direct use as a pre-commit hook source
- `py.typed` marker for PEP 561 compatibility
