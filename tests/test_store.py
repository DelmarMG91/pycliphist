"""Tests for :mod:`pycliphist.store`."""

import pytest

from pycliphist.store import Store


@pytest.fixture()
def store(tmp_path):
    instance = Store(str(tmp_path / "history.db"), max_entries=5)
    yield instance
    instance.close()


def test_add_and_get(store):
    clip_id = store.add("hello world")
    assert clip_id is not None
    row = store.get(clip_id)
    assert row is not None
    assert row["content"] == "hello world"
    assert row["created_at"]


def test_consecutive_duplicates_are_skipped(store):
    assert store.add("duplicate") is not None
    assert store.add("duplicate") is None
    assert store.stats()["total"] == 1


def test_non_consecutive_duplicates_are_kept(store):
    store.add("a")
    store.add("b")
    assert store.add("a") is not None
    assert store.stats()["total"] == 3


def test_trim_keeps_only_newest_entries(store):
    for index in range(8):
        store.add(f"item{index}")
    rows = store.list(limit=100)
    assert len(rows) == 5
    assert rows[0]["content"] == "item7"
    assert rows[-1]["content"] == "item3"


def test_list_returns_newest_first_with_limit(store):
    for index in range(4):
        store.add(f"row{index}")
    rows = store.list(limit=2)
    assert [row["content"] for row in rows] == ["row3", "row2"]


def test_search_like_matches_substring(store):
    store.add("hello world")
    store.add("goodbye world")
    results = store.search("hello")
    assert len(results) == 1
    assert results[0]["content"] == "hello world"


def test_search_treats_percent_as_literal(store):
    store.add("100% done")
    store.add("100 done")
    results = store.search("100%")
    assert [row["content"] for row in results] == ["100% done"]


def test_search_regex(store):
    store.add("abc123")
    store.add("xyz")
    results = store.search(r"\d+", regex=True)
    assert [row["content"] for row in results] == ["abc123"]


def test_search_invalid_regex_raises(store):
    with pytest.raises(ValueError):
        store.search("(", regex=True)


def test_get_missing_returns_none(store):
    assert store.get(999) is None


def test_delete_removes_row(store):
    clip_id = store.add("temporary")
    assert store.delete(clip_id) is True
    assert store.get(clip_id) is None
    assert store.delete(clip_id) is False


def test_clear_removes_everything(store):
    store.add("a")
    store.add("b")
    assert store.clear() == 2
    assert store.stats()["total"] == 0
    assert store.list() == []


def test_stats_reports_totals_and_database_size(store):
    store.add("x")
    stats = store.stats()
    assert stats["total"] == 1
    assert stats["db_size"] > 0
    assert stats["oldest"] is not None
    assert stats["newest"] is not None
    assert stats["db_path"].endswith("history.db")
