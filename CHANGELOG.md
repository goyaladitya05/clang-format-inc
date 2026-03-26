# Changelog

All notable changes to `clang-format-inc` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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

[Unreleased]: https://github.com/goyaladitya05/clang-format-inc/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/goyaladitya05/clang-format-inc/releases/tag/v0.1.0
