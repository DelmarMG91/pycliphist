"""Tests for the pycliphist command-line interface."""

import io
import json

import pytest

from pycliphist import cli
from pycliphist import __version__
from pycliphist.formatting import preview
from pycliphist.store import Store


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "cli-history.db"
    monkeypatch.setenv("PYCLIPHIST_DB", str(db_path))
    return db_path


def seed(db_path, *contents):
    store = Store(str(db_path))
    ids = [store.add(content) for content in contents]
    store.close()
    return ids


def test_version_prints_version(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--version"])
    assert excinfo.value.code == 0
    assert "pycliphist {0}".format(__version__) in capsys.readouterr().out


def test_help_lists_commands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
    output = capsys.readouterr().out
    for command in ("start", "list", "search", "get", "delete", "clear", "stats"):
        assert command in output


def test_list_json_on_empty_database(capsys):
    assert cli.main(["list", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_list_shows_newest_first(capsys, temp_db):
    seed(temp_db, "alpha", "beta")
    assert cli.main(["list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["content"] for item in payload] == ["beta", "alpha"]
    assert payload[0]["id"] > payload[1]["id"]


def test_get_missing_id_exits_2(capsys):
    assert cli.main(["get", "42"]) == 2
    assert "no clip with id 42" in capsys.readouterr().err


def test_get_raw_preserves_content(capsys, temp_db):
    ids = seed(temp_db, "line1\nline2")
    assert cli.main(["get", str(ids[0]), "--raw"]) == 0
    assert capsys.readouterr().out == "line1\nline2"


def test_delete_cli(capsys, temp_db):
    ids = seed(temp_db, "temporary")
    assert cli.main(["delete", str(ids[0])]) == 0
    assert "Deleted clip" in capsys.readouterr().out


def test_delete_missing_id_exits_2(capsys):
    assert cli.main(["delete", "123"]) == 2
    assert "no clip" in capsys.readouterr().err


def test_clear_with_yes(capsys, temp_db):
    seed(temp_db, "a", "b")
    assert cli.main(["clear", "--yes"]) == 0
    assert "Cleared 2 clip(s)." in capsys.readouterr().out


def test_clear_aborts_without_confirmation(capsys, temp_db, monkeypatch):
    seed(temp_db, "keep me")
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert cli.main(["clear"]) == 1
    assert "Aborted." in capsys.readouterr().out
    assert cli.main(["list", "--json"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 1


def test_stats_cli(capsys, temp_db):
    seed(temp_db, "one", "two")
    assert cli.main(["stats"]) == 0
    output = capsys.readouterr().out
    assert "Total clips: 2" in output
    assert "Size:" in output


def test_search_cli(capsys, temp_db):
    seed(temp_db, "hello world", "goodbye")
    assert cli.main(["search", "hello"]) == 0
    output = capsys.readouterr().out
    assert "hello world" in output
    assert "goodbye" not in output


def test_search_regex_cli(capsys, temp_db):
    seed(temp_db, "abc123", "xyz")
    assert cli.main(["search", r"\d+", "--regex"]) == 0
    assert "abc123" in capsys.readouterr().out


def test_preview_truncation():
    assert preview("x" * 100, width=10) == "x" * 9 + "…"
    assert len(preview("x" * 100, width=10)) == 10
    assert preview("  a \n b  ") == "a b"


def test_add_from_argument(capsys, temp_db):
    assert cli.main(["add", "hello clipboard"]) == 0
    assert "Added clip 1." in capsys.readouterr().out
    assert cli.main(["list", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["content"] == "hello clipboard"


def test_add_from_stdin(capsys, temp_db, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("piped text"))
    assert cli.main(["add"]) == 0
    assert "Added clip 1." in capsys.readouterr().out
    assert cli.main(["get", "1", "--raw"]) == 0
    assert capsys.readouterr().out == "piped text"


def test_add_duplicate_of_latest_is_skipped(capsys, temp_db):
    assert cli.main(["add", "dup"]) == 0
    capsys.readouterr()
    assert cli.main(["add", "dup"]) == 0
    assert "duplicate" in capsys.readouterr().out.lower()
    assert cli.main(["stats"]) == 0
    assert "Total clips: 1" in capsys.readouterr().out


def test_add_without_text_and_tty_errors(capsys, temp_db, monkeypatch):
    class _TTY(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.setattr("sys.stdin", _TTY(""))
    assert cli.main(["add"]) == 2
    assert "stdin is a terminal" in capsys.readouterr().err
