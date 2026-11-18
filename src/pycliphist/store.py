"""SQLite-backed storage for clipboard history.

The store keeps a single ``clips`` table and enforces three behaviours:

* consecutive identical content is never inserted twice (deduplicated by the
  SHA-256 hash of the newest row);
* the table is trimmed to ``max_entries`` rows, dropping the oldest records;
* all timestamps are stored as ISO-8601 strings with a local timezone offset.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_clips_hash ON clips(hash);
"""

_SELECT_COLUMNS = "id, content, created_at"


def _hash(content: str) -> str:
    """Return the SHA-256 hex digest of ``content`` (UTF-8 encoded)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _now() -> str:
    """Return the current local time as an ISO-8601 string with offset."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class Store:
    """A thin, well-typed wrapper around a SQLite database of clipboard clips."""

    def __init__(self, db_path: str, max_entries: Optional[int] = 1000) -> None:
        """Open (creating if needed) the database at ``db_path``.

        Args:
            db_path: Filesystem path to the SQLite database file.
            max_entries: Keep at most this many rows; ``None`` or ``0`` means
                unlimited. The newest rows are always retained.
        """
        self.db_path = db_path
        self.max_entries = max_entries
        directory = os.path.dirname(os.path.abspath(db_path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # -- lifecycle -----------------------------------------------------------
    def close(self) -> None:
        """Close the underlying database connection."""
        self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    # -- writes --------------------------------------------------------------
    def add(self, content: Optional[str]) -> Optional[int]:
        """Insert ``content`` unless it matches the most recent row.

        Args:
            content: The clipboard text to persist.

        Returns:
            The new row id, or ``None`` when the content was a duplicate of the
            newest entry (or when ``content`` is ``None``).
        """
        if content is None:
            return None
        digest = _hash(content)
        last = self._conn.execute(
            "SELECT hash FROM clips ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if last is not None and last["hash"] == digest:
            return None
        cursor = self._conn.execute(
            "INSERT INTO clips (content, hash, created_at) VALUES (?, ?, ?)",
            (content, digest, _now()),
        )
        self._conn.commit()
        new_id = cursor.lastrowid
        self._trim()
        return new_id

    def delete(self, clip_id: int) -> bool:
        """Delete the row with ``clip_id``. Return ``True`` if a row was removed."""
        cursor = self._conn.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def clear(self) -> int:
        """Delete every row and return the number of clips removed."""
        cursor = self._conn.execute("DELETE FROM clips")
        self._conn.commit()
        return max(cursor.rowcount, 0)

    # -- reads ---------------------------------------------------------------
    def list(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return up to ``limit`` clips in reverse-chronological order."""
        cursor = self._conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM clips ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def search(
        self, query: str, limit: int = 20, regex: bool = False
    ) -> List[Dict[str, Any]]:
        """Search clip content.

        Args:
            query: The substring (or regular expression) to look for.
            limit: Maximum number of results to return.
            regex: When ``True`` treat ``query`` as a Python regular expression;
                otherwise perform a case-insensitive SQL ``LIKE`` search.

        Raises:
            ValueError: If ``regex`` is ``True`` and ``query`` is invalid.
        """
        if regex:
            try:
                pattern = re.compile(query)
            except re.error as exc:  # pragma: no cover - defensive
                raise ValueError(f"invalid regular expression: {exc}") from exc
            rows = self._conn.execute(
                f"SELECT {_SELECT_COLUMNS} FROM clips ORDER BY id DESC"
            ).fetchall()
            matches = [dict(r) for r in rows if pattern.search(r["content"] or "")]
            return matches[:limit]

        escaped = (
            query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        like = f"%{escaped}%"
        cursor = self._conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM clips "
            "WHERE content LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT ?",
            (like, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get(self, clip_id: int) -> Optional[Dict[str, Any]]:
        """Return the clip with ``clip_id``, or ``None`` when it does not exist."""
        cursor = self._conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM clips WHERE id = ?", (clip_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row is not None else None

    def stats(self) -> Dict[str, Any]:
        """Return aggregate statistics about the stored history."""
        total = self._conn.execute("SELECT COUNT(*) FROM clips").fetchone()[0]
        oldest = self._conn.execute(
            "SELECT created_at FROM clips ORDER BY id ASC LIMIT 1"
        ).fetchone()
        newest = self._conn.execute(
            "SELECT created_at FROM clips ORDER BY id DESC LIMIT 1"
        ).fetchone()
        size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
        return {
            "total": total,
            "db_size": size,
            "oldest": oldest[0] if oldest is not None else None,
            "newest": newest[0] if newest is not None else None,
            "db_path": self.db_path,
        }

    # -- internals -----------------------------------------------------------
    def _trim(self) -> None:
        """Drop the oldest rows so the table holds at most ``max_entries``."""
        if not self.max_entries or self.max_entries <= 0:
            return
        self._conn.execute(
            "DELETE FROM clips WHERE id NOT IN "
            "(SELECT id FROM clips ORDER BY id DESC LIMIT ?)",
            (self.max_entries,),
        )
        self._conn.commit()
