"""Tests for JSON storage (tests/test_storage.py)."""

from __future__ import annotations

import json
import os

import pytest

from qtax.storage import default_data_path, load_entries, save_entries


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "entries.json"
    entries = [
        {"id": 1, "type": "income", "amount": 100.0, "date": "2026-01-05"},
        {"id": 2, "type": "expense", "amount": 25.5, "date": "2026-02-01"},
    ]
    save_entries(str(path), entries)
    loaded = load_entries(str(path))
    assert loaded == entries
    # Verify the file is valid, human-readable JSON.
    with open(path, encoding="utf-8") as handle:
        parsed = json.load(handle)
    assert parsed == entries


def test_load_missing_file_returns_empty(tmp_path):
    assert load_entries(str(tmp_path / "missing.json")) == []


def test_load_empty_file_returns_empty(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("", encoding="utf-8")
    assert load_entries(str(path)) == []


def test_load_corrupt_file_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_entries(str(path))


def test_load_non_list_raises(tmp_path):
    path = tmp_path / "notlist.json"
    path.write_text('{"not": "a list"}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_entries(str(path))


def test_default_data_path_expands_home(tmp_path, monkeypatch):
    monkeypatch.delenv("QTAX_DATA_FILE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    path = default_data_path()
    assert path == os.path.join(str(tmp_path), ".qtax", "entries.json")


def test_env_override_data_path(monkeypatch):
    monkeypatch.setenv("QTAX_DATA_FILE", "/tmp/qtax-override/entries.json")
    assert default_data_path() == "/tmp/qtax-override/entries.json"


def test_save_creates_directories(tmp_path):
    deep = tmp_path / "a" / "b" / "entries.json"
    save_entries(str(deep), [])
    assert deep.exists()
