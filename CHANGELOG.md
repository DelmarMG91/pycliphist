# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No unreleased changes yet._

## [0.2.0] - 2026-11-18

### Added

- `add` command: store a clip from an argument or from standard input, so
  history can be fed from scripts and pipelines. Consecutive duplicates are
  reported and skipped.
- Animated terminal demo (`docs/demo.gif`) and a runnable `examples/demo.sh`.
- `docs/USAGE.md` (command reference), `docs/DESIGN.md` (internals) and
  `docs/EXAMPLES.md` (recipes).
- A PyPI publish workflow (`.github/workflows/publish.yml`) using Trusted
  Publishing, plus a `pipx install pycliphist` quick path in the README.

### Changed

- Test suite extended to cover the new `add` command (argument, stdin,
  duplicate, and terminal-without-input paths).

## [0.1.0] - 2025-01-01

### Added

- `start` command that polls the system clipboard and stores distinct changes.
- `list`, `search`, `get`, `delete`, `clear`, and `stats` commands.
- SQLite storage with consecutive-duplicate suppression and automatic trimming
  to a configurable maximum number of entries.
- `PYCLIPHIST_DB` environment variable for overriding the database location.
- Clipboard backend abstraction with tkinter and in-memory implementations.
- Test suite covering storage, formatting, clipboard, and CLI behaviour.

[Unreleased]: https://github.com/DelmarMG91/pycliphist/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/DelmarMG91/pycliphist/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/DelmarMG91/pycliphist/releases/tag/v0.1.0
