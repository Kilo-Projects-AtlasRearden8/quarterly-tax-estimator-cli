"""Tests for entries and aggregation (tests/test_entries.py)."""

from __future__ import annotations

import pytest

from qtax.entries import (
    ENTRY_TYPES,
    add_entry,
    list_entries,
    make_entry,
    totals,
    ytd_totals,
)
from qtax.storage import save_entries


def test_make_entry_defaults(tmp_path):
    entry = make_entry("income", 100.0, date="2026-03-10", note="book royalties")
    assert entry["type"] == "income"
    assert entry["amount"] == 100.0
    assert entry["date"] == "2026-03-10"
    assert entry["note"] == "book royalties"
    assert entry["source"] == ""
    assert entry["category"] == ""
    assert "id" in entry
    assert "created_at" in entry


def test_make_entry_invalid_type():
    with pytest.raises(ValueError):
        make_entry("donation", 10.0)


def test_make_entry_invalid_date():
    with pytest.raises(ValueError):
        make_entry("income", 10.0, date="not-a-date")


def test_add_entry_assigns_ids(tmp_path):
    path = str(tmp_path / "entries.json")
    save_entries(path, [])
    first = add_entry(path, make_entry("income", 50.0, date="2026-01-01"))
    second = add_entry(path, make_entry("expense", 12.5, date="2026-01-02"))
    assert first["id"] == 1
    assert second["id"] == 2
    saved = load(path)
    assert len(saved) == 2


def test_list_entries_sorted_newest_first(tmp_path):
    path = str(tmp_path / "entries.json")
    save_entries(
        path,
        [
            make_entry("income", 10.0, date="2026-01-01", entry_id=1),
            make_entry("income", 20.0, date="2026-01-03", entry_id=2),
            make_entry("expense", 5.0, date="2026-01-02", entry_id=3),
        ],
    )
    ordered = list_entries(path)
    assert [e["id"] for e in ordered] == [2, 3, 1]


def test_list_entries_filter_by_type(tmp_path):
    path = str(tmp_path / "entries.json")
    save_entries(
        path,
        [
            make_entry("income", 10.0, date="2026-01-01", entry_id=1),
            make_entry("expense", 5.0, date="2026-01-02", entry_id=2),
        ],
    )
    expenses = list_entries(path, entry_type="expense")
    assert len(expenses) == 1
    assert expenses[0]["type"] == "expense"


def test_totals():
    entries = [
        {"type": "income", "amount": 100.0},
        {"type": "income", "amount": 50.25},
        {"type": "expense", "amount": 30.0},
    ]
    result = totals(entries)
    assert result == {"income": 150.25, "expense": 30.0, "net": 120.25}


def test_ytd_totals_filters_by_year(tmp_path):
    path = str(tmp_path / "entries.json")
    save_entries(
        path,
        [
            make_entry("income", 100.0, date="2026-06-01", entry_id=1),
            make_entry("expense", 40.0, date="2026-07-01", entry_id=2),
            make_entry("income", 999.0, date="2025-12-31", entry_id=3),
        ],
    )
    summary = ytd_totals(path, year=2026)
    assert summary["year"] == 2026
    assert summary["income"] == 100.0
    assert summary["expense"] == 40.0
    assert summary["net"] == 60.0
    assert summary["entry_count"] == 2


def test_ytd_totals_by_month(tmp_path):
    path = str(tmp_path / "entries.json")
    save_entries(
        path,
        [
            make_entry("income", 100.0, date="2026-01-10", entry_id=1),
            make_entry("income", 50.0, date="2026-01-20", entry_id=2),
            make_entry("expense", 30.0, date="2026-02-05", entry_id=3),
        ],
    )
    summary = ytd_totals(path, year=2026)
    assert summary["by_month"]["2026-01"] == {
        "income": 150.0,
        "expense": 0.0,
        "net": 150.0,
    }
    assert summary["by_month"]["2026-02"] == {
        "income": 0.0,
        "expense": 30.0,
        "net": -30.0,
    }


def test_entry_types_constants():
    assert ENTRY_TYPES == ("income", "expense")


def load(path):
    import json

    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
