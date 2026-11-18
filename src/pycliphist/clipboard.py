"""Clipboard backend abstraction.

Two backends are shipped:

* :class:`TkClipboard` reads and writes the real system clipboard through
  ``tkinter`` (which is standard library on CPython). The underlying Tk root is
  created lazily and hidden, so importing this module never opens a window.
* :class:`MemoryClipboard` is a pure in-memory backend used by the test suite.

Both satisfy the :class:`ClipboardBackend` protocol.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

try:  # pragma: no cover - depends on the host Python build
    import tkinter as _tk

    _TK_IMPORT_ERROR: Optional[BaseException] = None
except Exception as exc:  # pragma: no cover - tkinter missing entirely
    _tk = None  # type: ignore[assignment]
    _TK_IMPORT_ERROR = exc


class ClipboardUnavailable(RuntimeError):
    """Raised when no usable clipboard backend can be initialised."""


@runtime_checkable
class ClipboardBackend(Protocol):
    """Minimal protocol implemented by every clipboard backend."""

    def read(self) -> Optional[str]:
        """Return the current clipboard text, or ``None`` when empty/unavailable."""
        ...

    def write(self, text: str) -> None:
        """Replace the clipboard contents with ``text``."""
        ...


class MemoryClipboard:
    """An in-memory clipboard backend for tests and headless use."""

    def __init__(self, initial: Optional[str] = None) -> None:
        self._value: Optional[str] = initial

    def read(self) -> Optional[str]:
        return self._value

    def write(self, text: str) -> None:
        self._value = text


class TkClipboard:
    """A tkinter-backed clipboard backend that lazily creates a hidden root."""

    def __init__(self) -> None:
        self._root: Optional["_tk.Tk"] = None  # type: ignore[name-defined]

    def _ensure_root(self):
        """Create the hidden Tk root on first use and return it."""
        if _tk is None:
            raise ClipboardUnavailable(
                f"tkinter is not available on this Python: {_TK_IMPORT_ERROR}"
            )
        if self._root is None:
            try:
                root = _tk.Tk()
            except Exception as exc:  # pragma: no cover - no display / bad tk
                raise ClipboardUnavailable(
                    f"could not initialise a Tk clipboard: {exc}"
                ) from exc
            root.withdraw()
            self._root = root
        return self._root

    def read(self) -> Optional[str]:
        root = self._ensure_root()
        try:
            return root.clipboard_get()
        except _tk.TclError:
            # An empty clipboard raises TclError; treat it as "no content".
            return None

    def write(self, text: str) -> None:
        root = self._ensure_root()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()

    def close(self) -> None:
        """Destroy the hidden Tk root, if one was created."""
        if self._root is not None:
            try:
                self._root.destroy()
            finally:
                self._root = None
