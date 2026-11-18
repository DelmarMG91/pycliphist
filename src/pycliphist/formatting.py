"""Human-readable formatting helpers for CLI output."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def preview(text: str, width: int = 60) -> str:
    """Collapse whitespace and truncate ``text`` to at most ``width`` characters."""
    flat = " ".join(text.split())
    if len(flat) <= width:
        return flat
    if width <= 1:
        return flat[:width]
    return flat[: width - 1] + "…"


def format_time(iso: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format an ISO-8601 timestamp; fall back to the raw string on failure."""
    try:
        return datetime.fromisoformat(iso).strftime(fmt)
    except (ValueError, TypeError):
        return str(iso)


def format_list(rows: List[Dict[str, Any]], width: int = 60) -> str:
    """Render a list of clip rows as an aligned, reverse-chronological table."""
    if not rows:
        return "No clips found."
    lines = []
    for row in rows:
        lines.append(
            f"{row['id']:>4}  {format_time(row['created_at'])}  "
            f"{preview(row['content'], width)}"
        )
    return "\n".join(lines)


def human_size(num: int) -> str:
    """Render a byte count using binary (1024-based) units."""
    size = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
