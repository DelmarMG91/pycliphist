"""Command-line interface for pycliphist."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from . import __version__
from . import formatting
from .clipboard import ClipboardUnavailable, TkClipboard
from .store import Store

DEFAULT_DB = "~/.pycliphist/history.db"


def resolve_db_path() -> str:
    """Return the database path from ``PYCLIPHIST_DB`` or the default location."""
    override = os.environ.get("PYCLIPHIST_DB")
    if override:
        return os.path.expanduser(override)
    return os.path.expanduser(DEFAULT_DB)


def _print_rows(rows: List[Dict[str, Any]], as_json: bool) -> None:
    """Print clip rows either as JSON or as a formatted table."""
    if as_json:
        payload = [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "content": row["content"],
            }
            for row in rows
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(formatting.format_list(rows))


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="pycliphist",
        description="Cross-platform clipboard history manager backed by SQLite.",
        epilog="Run 'pycliphist <command> --help' for command-specific options.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pycliphist {__version__}",
    )
    sub = parser.add_subparsers(dest="command", metavar="command")

    p_add = sub.add_parser("add", help="Add a clip from an argument or stdin.")
    p_add.add_argument(
        "text",
        nargs="?",
        default=None,
        metavar="TEXT",
        help="Clip text to store; omit to read from stdin.",
    )
    p_add.set_defaults(func=cmd_add)

    p_start = sub.add_parser("start", help="Watch the clipboard and record changes.")
    p_start.add_argument(
        "--interval",
        type=float,
        default=0.5,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 0.5).",
    )
    p_start.add_argument(
        "--max-entries",
        type=int,
        default=1000,
        metavar="N",
        help="Maximum number of clips to retain (default: 1000).",
    )
    p_start.set_defaults(func=cmd_start)

    p_list = sub.add_parser("list", help="List recent clips (newest first).")
    p_list.add_argument("--limit", type=int, default=20, metavar="N")
    p_list.add_argument("--json", action="store_true", help="Emit JSON output.")
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", help="Search clip contents.")
    p_search.add_argument("query", metavar="QUERY")
    p_search.add_argument("--limit", type=int, default=20, metavar="N")
    p_search.add_argument(
        "--regex", action="store_true", help="Treat QUERY as a Python regex."
    )
    p_search.set_defaults(func=cmd_search)

    p_get = sub.add_parser("get", help="Print the full content of one clip.")
    p_get.add_argument("clip_id", type=int, metavar="ID")
    p_get.add_argument(
        "--raw",
        action="store_true",
        help="Write content verbatim with no trailing newline.",
    )
    p_get.set_defaults(func=cmd_get)

    p_delete = sub.add_parser("delete", help="Delete a single clip.")
    p_delete.add_argument("clip_id", type=int, metavar="ID")
    p_delete.set_defaults(func=cmd_delete)

    p_clear = sub.add_parser("clear", help="Delete all clips.")
    p_clear.add_argument(
        "--yes", action="store_true", help="Skip the confirmation prompt."
    )
    p_clear.set_defaults(func=cmd_clear)

    p_stats = sub.add_parser("stats", help="Show history statistics.")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def cmd_add(args: argparse.Namespace) -> int:
    """Store a clip passed as an argument or read from standard input."""
    if args.text is not None:
        content = args.text
    else:
        if sys.stdin is None or sys.stdin.isatty():
            print(
                "pycliphist: no text given and stdin is a terminal", file=sys.stderr
            )
            return 2
        content = sys.stdin.read()
    with Store(resolve_db_path()) as store:
        new_id = store.add(content)
    if new_id is None:
        print("Not added: duplicate of the most recent clip.")
        return 0
    print(f"Added clip {new_id}.")
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    """Poll the clipboard, persist distinct changes, and report the count."""
    store = Store(resolve_db_path(), max_entries=args.max_entries)
    backend = TkClipboard()
    try:
        last = backend.read()
    except ClipboardUnavailable as exc:
        print(f"pycliphist: clipboard unavailable: {exc}", file=sys.stderr)
        store.close()
        return 1

    count = 0
    if last:
        if store.add(last) is not None:
            count += 1

    try:
        while True:
            time.sleep(args.interval)
            current = backend.read()
            if current is None or current == last:
                continue
            last = current
            if current == "":
                continue
            if store.add(current) is not None:
                count += 1
    except KeyboardInterrupt:
        print(f"Captured {count} clip(s).")
        return 0
    finally:
        store.close()
        backend.close()


def cmd_list(args: argparse.Namespace) -> int:
    """List recent clips."""
    with Store(resolve_db_path()) as store:
        rows = store.list(limit=args.limit)
    _print_rows(rows, args.json)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Search clips by substring or regular expression."""
    with Store(resolve_db_path()) as store:
        try:
            rows = store.search(args.query, limit=args.limit, regex=args.regex)
        except ValueError as exc:
            print(f"pycliphist: {exc}", file=sys.stderr)
            return 2
    _print_rows(rows, False)
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    """Print the full content of one clip."""
    with Store(resolve_db_path()) as store:
        row = store.get(args.clip_id)
    if row is None:
        print(f"pycliphist: no clip with id {args.clip_id}", file=sys.stderr)
        return 2
    if args.raw:
        sys.stdout.write(row["content"])
    else:
        print(row["content"])
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a single clip."""
    with Store(resolve_db_path()) as store:
        removed = store.delete(args.clip_id)
    if not removed:
        print(f"pycliphist: no clip with id {args.clip_id}", file=sys.stderr)
        return 2
    print(f"Deleted clip {args.clip_id}.")
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    """Delete all clips, optionally without prompting."""
    if not args.yes:
        try:
            answer = input("Delete all clips? [y/N] ")
        except EOFError:
            answer = ""
        if answer.strip().lower() not in ("y", "yes"):
            print("Aborted.")
            return 1
    with Store(resolve_db_path()) as store:
        removed = store.clear()
    print(f"Cleared {removed} clip(s).")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show summary statistics for the history database."""
    with Store(resolve_db_path()) as store:
        stats = store.stats()
    print(f"Total clips: {stats['total']}")
    print(f"Database: {stats['db_path']}")
    print(f"Size: {formatting.human_size(stats['db_size'])}")
    print(
        "Oldest: "
        + (formatting.format_time(stats["oldest"]) if stats["oldest"] else "-")
    )
    print(
        "Newest: "
        + (formatting.format_time(stats["newest"]) if stats["newest"] else "-")
    )
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Program entry point. Return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "func", None) is None:
        parser.print_help()
        return 0
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
