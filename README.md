# pycliphist

> A cross-platform clipboard history manager for the terminal — SQLite-backed, dependency-free, and scriptable.

[![CI](https://github.com/DelmarMG91/pycliphist/actions/workflows/ci.yml/badge.svg)](https://github.com/DelmarMG91/pycliphist/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/pypi-v0.1.0-informational.svg)](https://pypi.org/project/pycliphist/)

`pycliphist` watches your system clipboard in the background, records every
distinct change in a local SQLite database, and gives you a fast command-line
interface to list, search, retrieve, and prune that history. It uses only the
Python standard library, so there is nothing to compile and no services to run.

## Features

- **Background capture** — poll the clipboard at a configurable interval and
  store each new value with a timestamp.
- **Duplicate suppression** — consecutive identical copies are stored once, so
  repeated <kbd>Ctrl</kbd>+<kbd>C</kbd> presses do not flood the history.
- **Automatic pruning** — keep the newest *N* entries (default 1000) and drop
  the rest as new clips arrive.
- **Fast search** — case-insensitive substring search via SQL `LIKE`, or full
  Python regular expressions with `--regex`.
- **Script-friendly output** — `list --json` emits machine-readable JSON, and
  `get --raw` writes the exact stored bytes with no added newline.
- **Portable storage** — a single SQLite file at `~/.pycliphist/history.db`,
  overridable with the `PYCLIPHIST_DB` environment variable.
- **Tiny footprint** — standard library only (`sqlite3` + `tkinter`).

## Install

With [pipx](https://pipx.pypa.io/) (recommended for command-line tools):

```console
$ pipx install pycliphist
```

With pip, from a checkout:

```console
$ git clone https://github.com/DelmarMG91/pycliphist.git
$ cd pycliphist
$ pip install -e .
```

The `tkinter` module ships with the official CPython installers on Windows and
macOS. On Debian/Ubuntu it is a separate package: `sudo apt install python3-tk`.

## Quick Start

Start the watcher and copy a few things in any application:

```console
$ pycliphist start
Captured 3 clip(s).
```

Press <kbd>Ctrl</kbd>+<kbd>C</kbd> to stop; the watcher prints how many clips it
captured during the session. Then inspect the history:

```console
$ pycliphist list --limit 5
   4  2025-01-15 09:42:11  git commit -m "fix: handle empty clipboard"
   3  2025-01-15 09:41:03  https://docs.python.org/3/library/sqlite3.html
   2  2025-01-15 09:40:47  pip install -e ".[dev]"
   1  2025-01-15 09:39:12  pycliphist --version
```

## Usage

### `pycliphist start`

Poll the system clipboard and record changes until interrupted.

```console
$ pycliphist start --interval 0.25 --max-entries 500
Captured 7 clip(s).
```

| Option | Default | Description |
| --- | --- | --- |
| `--interval SECONDS` | `0.5` | Polling interval in seconds. |
| `--max-entries N` | `1000` | Maximum number of clips to retain. |

If `tkinter` is missing or a display is unavailable, the command prints a clear
error and exits with status `1`.

### `pycliphist list`

List recent clips newest-first, with a single-line preview of each.

```console
$ pycliphist list --limit 3
   4  2025-01-15 09:42:11  git commit -m "fix: handle empty clipboard"
   3  2025-01-15 09:41:03  https://docs.python.org/3/library/sqlite3.html
   2  2025-01-15 09:40:47  pip install -e ".[dev]"
```

JSON output includes the full stored content:

```console
$ pycliphist list --limit 1 --json
[
  {
    "id": 4,
    "created_at": "2025-01-15T09:42:11+08:00",
    "content": "git commit -m \"fix: handle empty clipboard\""
  }
]
```

| Option | Default | Description |
| --- | --- | --- |
| `--limit N` | `20` | Maximum number of rows to display. |
| `--json` | off | Emit a JSON array instead of a table. |

### `pycliphist search`

Search stored contents. The default mode is a case-insensitive substring match.

```console
$ pycliphist search sqlite
   3  2025-01-15 09:41:03  https://docs.python.org/3/library/sqlite3.html
```

Use `--regex` for a Python regular expression:

```console
$ pycliphist search "\bgit commit\b" --regex --limit 5
   4  2025-01-15 09:42:11  git commit -m "fix: handle empty clipboard"
```

| Option | Default | Description |
| --- | --- | --- |
| `QUERY` | — | Required substring or regular expression. |
| `--limit N` | `20` | Maximum number of results. |
| `--regex` | off | Interpret `QUERY` as a Python regex. |

### `pycliphist get`

Print the complete content of one clip.

```console
$ pycliphist get 4
git commit -m "fix: handle empty clipboard"
```

With `--raw`, the content is written verbatim without a trailing newline, which
makes it safe to pipe into other tools:

```console
$ pycliphist get 4 --raw | wc -c
43
```

If the ID does not exist, the command prints an error to stderr and exits with
status `2`.

| Option | Default | Description |
| --- | --- | --- |
| `ID` | — | Required numeric clip ID. |
| `--raw` | off | Write content exactly, with no trailing newline. |

### `pycliphist delete`

Delete a single clip by ID.

```console
$ pycliphist delete 2
Deleted clip 2.
```

A missing ID exits with status `2`.

### `pycliphist clear`

Delete the entire history. Prompts for confirmation unless `--yes` is given.

```console
$ pycliphist clear
Delete all clips? [y/N] y
Cleared 12 clip(s).
```

| Option | Default | Description |
| --- | --- | --- |
| `--yes` | off | Skip the interactive confirmation prompt. |

### `pycliphist stats`

Show the number of clips, database location and size, and the oldest/newest
timestamps.

```console
$ pycliphist stats
Total clips: 4
Database: /home/you/.pycliphist/history.db
Size: 16.0 KB
Oldest: 2025-01-15 09:39:12
Newest: 2025-01-15 09:42:11
```

### Global options

```console
$ pycliphist --version
pycliphist 0.1.0
$ pycliphist --help
usage: pycliphist [-h] [--version] command ...
```

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `PYCLIPHIST_DB` | `~/.pycliphist/history.db` | Path to the SQLite database file. Parent directories are created automatically. |

Example:

```console
$ export PYCLIPHIST_DB="$HOME/tmp/clips.db"
$ pycliphist stats
Total clips: 0
Database: /home/you/tmp/clips.db
Size: 12.0 KB
Oldest: -
Newest: -
```

On Windows (PowerShell):

```powershell
$env:PYCLIPHIST_DB = "$HOME\clips.db"
```

## Development

Clone the repository and install the development extras:

```console
$ git clone https://github.com/DelmarMG91/pycliphist.git
$ cd pycliphist
$ python -m pip install -e ".[dev]"
```

Run the test suite:

```console
$ python -m pytest -q
................................
32 passed in 0.39s
```

The package targets Python 3.9+ and uses only the standard library at runtime.
`pytest` is the sole development dependency.

## Contributing

Contributions are welcome. Fork the repository, create a feature branch, add
tests for any behaviour you change, and open a pull request once
`python -m pytest -q` passes. Keep the runtime dependency list empty and follow
the existing code style (4-space indentation, type hints on public functions).

## License

Released under the [MIT License](LICENSE).

Copyright (c) 2025 DelmarMG91
