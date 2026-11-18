"""Tests for :mod:`pycliphist.clipboard`."""

import pytest

import pycliphist.clipboard as clipboard_module
from pycliphist.clipboard import (
    ClipboardBackend,
    ClipboardUnavailable,
    MemoryClipboard,
    TkClipboard,
)


def test_memory_clipboard_starts_empty():
    backend = MemoryClipboard()
    assert backend.read() is None


def test_memory_clipboard_read_write():
    backend = MemoryClipboard()
    backend.write("hello")
    assert backend.read() == "hello"


def test_memory_clipboard_initial_value_and_overwrite():
    backend = MemoryClipboard("seed")
    assert backend.read() == "seed"
    backend.write("next")
    backend.write("last")
    assert backend.read() == "last"


def test_memory_clipboard_satisfies_protocol():
    assert isinstance(MemoryClipboard(), ClipboardBackend)


def test_tk_clipboard_reports_missing_tkinter(monkeypatch):
    monkeypatch.setattr(clipboard_module, "_tk", None)
    monkeypatch.setattr(clipboard_module, "_TK_IMPORT_ERROR", ImportError("missing"))
    backend = TkClipboard()
    with pytest.raises(ClipboardUnavailable):
        backend.read()
