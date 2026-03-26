# Changelog

All notable changes to `clang-format-inc` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [1.0.0] — 2026-03-26

First stable release. No breaking changes from 0.3.0 — this marks the API
and behaviour as production-ready.

### Changed

- Development status bumped to `Production/Stable`
- Version references in docs updated to `v1.0.0`

## [0.3.0] — 2026-03-26

### Added

- **`--diff` mode**: print a unified diff of what would change without modifying
  files; exits non-zero if any changed line would be reformatted — useful for PR
  comment bots and debugging. Mutually exclusive with `--check`.
- **`--include REGEX`**: only process files whose path matches the given regular
  expression; useful when running standalone (outside pre-commit).
- **`--exclude REGEX`**: skip files whose path matches the given regular expression.
- **`--workers N`**: process files in parallel using N clang-format processes
  (default 1); useful for large CI jobs with many changed files.
- README: document untracked-files behaviour (new files are formatted in full
  since there is no prior revision to diff against).

## [0.2.0] — 2026-03-26

### Added

- **`--check` mode**: run without modifying files; exits non-zero and prints a message
  if any changed line would be reformatted — suitable for CI pipelines that want to
  report formatting issues without auto-applying fixes
- **`additional_dependencies: ['clang-format']`** in `.pre-commit-hooks.yaml`: pre-commit
  now installs the `clang-format` PyPI package automatically into the hook virtualenv,
  removing the requirement for a system-installed `clang-format`; users can pin a
  specific version via `additional_dependencies: ['clang-format==18.1.0']` in their
  own `.pre-commit-config.yaml`

## [0.1.0] — 2026-03-26

Initial release.

### Added

- Incremental C/C++ formatting: format only lines changed in a diff, not whole files
- **CI mode**: reads `PRE_COMMIT_FROM_REF` / `PRE_COMMIT_TO_REF` environment variables
  set by pre-commit when running with `--from-ref`/`--to-ref`; diffs those two refs
- **Local mode**: falls back to `git diff --cached` (staged changes) when env vars are absent
- **Partial env var guard**: if only one of the two CI env vars is set, falls back to local
  mode rather than crashing
- `--binary` option to specify a custom `clang-format` executable path
- `--style` option (default: `file`, reads `.clang-format` from the repo)
- `--fallback-style` option for repos without a `.clang-format` file
- `-p` option to control path-prefix stripping in the diff (default: `1`)
- Early exit when no diff output — skips `clang-format-diff.py` entirely
- Friendly error message when `clang-format` binary is not found on `PATH`
- Bundled `clang-format-diff.py` from LLVM (Apache-2.0 WITH LLVM-exception) — zero
  runtime dependencies beyond Python and a `clang-format` binary
- `.pre-commit-hooks.yaml` so this repo can be used directly as a pre-commit hook source
- `py.typed` marker for PEP 561 compatibility

[Unreleased]: https://github.com/goyaladitya05/clang-format-inc/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/goyaladitya05/clang-format-inc/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/goyaladitya05/clang-format-inc/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/goyaladitya05/clang-format-inc/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/goyaladitya05/clang-format-inc/releases/tag/v0.1.0
