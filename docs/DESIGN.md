# pycliphist — Design Notes

`pycliphist` is intentionally small: one package, three focused modules, no
runtime dependencies beyond the standard library (`sqlite3`, `tkinter`). This
note explains the data model and the guarantees each module provides.

## Module map

| Module | Responsibility |
| --- | --- |
| `pycliphist.store` | Owns the SQLite connection, schema, deduplication, trimming, and all queries. |
| `pycliphist.clipboard` | Thin clipboard abstraction (`Clipboard` protocol, `TkClipboard`, `MemoryClipboard`). |
| `pycliphist.formatting` | Pure helpers for previews, timestamps, sizes, and table rendering. |
| `pycliphist.cli` | Argument parsing and command dispatch; the only module that prints. |

## Storage schema

```sql
CREATE TABLE IF NOT EXISTS clips (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content    TEXT    NOT NULL,
    hash       TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clips_hash ON clips(hash);
```

- `content` is the raw clipboard text (UTF-8).
- `hash` is the SHA-256 of `content`, used for duplicate suppression.
- `created_at` is an ISO-8601 string with a local timezone offset, produced by
  `datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")`.

## Guarantees

**Duplicate suppression.** `Store.add` compares the new content's hash with the
most recent row only. A background clipboard watcher fires many identical reads
(a copy/screenshot burst), so suppressing *consecutive* duplicates is enough and
keeps the write path cheap (a single indexed lookup).

**Bounded history.** After each insert, `Store._trim` deletes rows outside the
newest `max_entries` (`DELETE ... WHERE id NOT IN (SELECT id ... LIMIT ?)`).
`max_entries` of `None`/`0` disables trimming.

**Portable storage.** A single file at `~/.pycliphist/history.db`, overridable
via `PYCLIPHIST_DB`. `Store.__init__` creates the parent directory if missing.

## Clipboard abstraction

`clipboard.py` defines a minimal protocol so the watcher and the tests do not
depend on a real display:

```python
class Clipboard(Protocol):
    def read(self) -> str | None: ...
    def write(self, text: str) -> None: ...
    def close(self) -> None: ...
```

`TkClipboard` wraps a hidden Tk root; `MemoryClipboard` is an in-memory fake used
by the test-suite. `ClipboardUnavailable` is raised when no display/backend is
present, and the CLI turns it into a clean error instead of a traceback.

## Testing strategy

The suite covers three layers independently:

- `tests/test_store.py` — schema, dedupe, trimming, search (LIKE + regex), stats.
- `tests/test_clipboard.py` — `MemoryClipboard` behaviour and protocol conformance.
- `tests/test_cli.py` — each subcommand through `cli.main([...])` with a
  temporary `PYCLIPHIST_DB`, asserting exit codes and captured stdout/stderr.

No test needs a real clipboard or a GUI.

## Why standard library only

A clipboard-history tool is something you want to `pipx install` and forget. The
dependency footprint is the feature: `sqlite3` and `tkinter` ship with CPython,
so there is nothing to compile and no service to keep alive.
