# pycliphist — Command-Line Reference

`pycliphist` records clipboard changes into a local SQLite database and gives
you a fast interface to list, search, retrieve, and prune that history. This
page documents every command; see [DESIGN.md](DESIGN.md) for the internals and
[EXAMPLES.md](EXAMPLES.md) for recipes.

## Synopsis

```
pycliphist [--version] <command> [options]
```

Run `pycliphist <command> --help` for command-specific options.

## Global

| Option | Description |
| --- | --- |
| `--version` | Print `pycliphist <version>` and exit `0`. |
| `--help` | Show help. |

The database location is controlled by the `PYCLIPHIST_DB` environment variable
and defaults to `~/.pycliphist/history.db`.

## Commands

### `add [TEXT]`

Store a clip. With `TEXT` it stores the argument; without it, it reads standard
input (handy for pipelines). Consecutive duplicates of the most recent clip are
ignored.

```console
$ pycliphist add "SELECT * FROM users;"
Added clip 1.

$ echo "piped text" | pycliphist add
Added clip 2.
```

### `start [--interval SECONDS] [--max-entries N]`

Watch the clipboard and record each distinct change. Press Ctrl+C to stop.
`--interval` sets the polling period (default `0.5`s); `--max-entries` caps the
stored history (default `1000`).

```console
$ pycliphist start --interval 0.25 --max-entries 500
Captured 12 clip(s).
```

### `list [--limit N] [--json]`

List recent clips, newest first (default limit `20`). `--json` emits a JSON
array of `{id, created_at, content}` objects.

```console
$ pycliphist list --limit 3
   3  2026-11-18 21:05:19  https://example.com/docs
   2  2026-11-18 21:05:15  pip install pycliphist
   1  2026-11-18 21:05:12  SELECT * FROM users;
```

### `search QUERY [--limit N] [--regex]`

Case-insensitive substring search by default; `--regex` treats `QUERY` as a
Python regular expression.

```console
$ pycliphist search users
   1  2026-11-18 21:05:12  SELECT * FROM users;

$ pycliphist search 'https?://' --regex
   3  2026-11-18 21:05:19  https://example.com/docs
```

### `get ID [--raw]`

Print the full content of one clip. `--raw` writes the exact stored bytes with
no trailing newline, so you can pipe it into a file or another command.

```console
$ pycliphist get 3 --raw
https://example.com/docs
```

### `delete ID`

Delete a single clip.

```console
$ pycliphist delete 2
Deleted clip 2.
```

### `clear [--yes]`

Delete every clip. Prompts for confirmation unless `--yes` is given.

```console
$ pycliphist clear --yes
Cleared 3 clip(s).
```

### `stats`

Show totals, database path, on-disk size, and the oldest/newest timestamps.

```console
$ pycliphist stats
Total clips: 3
Database: /home/ada/.pycliphist/history.db
Size: 12.0 KB
Oldest: 2026-11-18 21:05:12
Newest: 2026-11-18 21:05:19
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success. |
| `1` | Aborted (declined confirmation) or clipboard unavailable. |
| `2` | Bad argument, missing clip id, or invalid regular expression. |
