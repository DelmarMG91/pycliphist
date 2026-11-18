# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Nothing yet.

## [0.1.0] - 2025-01-01

### Added

- `start` command that polls the system clipboard and stores distinct changes.
- `list`, `search`, `get`, `delete`, `clear`, and `stats` commands.
- SQLite storage with consecutive-duplicate suppression and automatic trimming
  to a configurable maximum number of entries.
- `PYCLIPHIST_DB` environment variable for overriding the database location.
- Clipboard backend abstraction with tkinter and in-memory implementations.
- Test suite covering storage, formatting, clipboard, and CLI behaviour.

[Unreleased]: https://github.com/DelmarMG91/pycliphist/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DelmarMG91/pycliphist/releases/tag/v0.1.0
