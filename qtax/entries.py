"""Entry model and year-to-date aggregation."""

from __future__ import annotations

import datetime as _dt
from typing import Any

from .storage import load_entries, save_entries

ENTRY_TYPES = ("income", "expense")


def new_entry_id(entries: list[dict[str, Any]]) -> int:
    """Return the next integer entry id."""
    if not entries:
        return 1
    return max(int(entry.get("id", 0)) for entry in entries) + 1


def _today_iso() -> str:
    return _dt.date.today().isoformat()


def _now_iso() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def make_entry(
    entry_type: str,
    amount: float,
    date: str | None = None,
    note: str = "",
    source: str = "",
    category: str = "",
    entry_id: int | None = None,
) -> dict[str, Any]:
    """Build a validated entry dict."""
    if entry_type not in ENTRY_TYPES:
        raise ValueError(f"entry type must be one of {ENTRY_TYPES}")
    if date is None:
        date = _today_iso()
    # Validate the date format without importing heavy machinery.
    _dt.date.fromisoformat(date)
    amount = round(float(amount), 2)
    return {
        "id": entry_id if entry_id is not None else new_entry_id([]),
        "type": entry_type,
        "amount": amount,
        "date": date,
        "note": str(note).strip(),
        "source": str(source).strip(),
        "category": str(category).strip(),
        "created_at": _now_iso(),
    }


def add_entry(path: str, entry: dict[str, Any]) -> dict[str, Any]:
    """Append an entry to storage and return it with its assigned id."""
    entries = load_entries(path)
    entry = dict(entry)
    entry["id"] = new_entry_id(entries)
    entries.append(entry)
    save_entries(path, entries)
    return entry


def list_entries(path: str, entry_type: str | None = None) -> list[dict[str, Any]]:
    """Return all entries, newest first, optionally filtered by type."""
    entries = load_entries(path)
    if entry_type is not None:
        entries = [e for e in entries if e.get("type") == entry_type]
    return sorted(entries, key=lambda e: (e.get("date", ""), e.get("id", 0)), reverse=True)


def totals(entries: list[dict[str, Any]]) -> dict[str, float]:
    """Sum income, expense, and net for a list of entries."""
    income = 0.0
    expense = 0.0
    for entry in entries:
        amount = float(entry.get("amount", 0) or 0)
        if entry.get("type") == "income":
            income += amount
        elif entry.get("type") == "expense":
            expense += amount
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net": round(income - expense, 2),
    }


def ytd_totals(path: str, year: int | None = None) -> dict[str, Any]:
    """Year-to-date totals for all entries (or one year), plus by-month."""
    entries = load_entries(path)
    if year is None:
        year = _dt.date.today().year
    year_entries = [
        e for e in entries if e.get("date", "").startswith(f"{year:04d}-")
    ]
    summary = totals(year_entries)
    months: dict[str, dict[str, float]] = {}
    for entry in year_entries:
        month = entry.get("date", "")[:7]
        bucket = months.setdefault(month, {"income": 0.0, "expense": 0.0})
        amount = float(entry.get("amount", 0) or 0)
        if entry.get("type") == "income":
            bucket["income"] += amount
        elif entry.get("type") == "expense":
            bucket["expense"] += amount
    summary["by_month"] = {
        month: {
            "income": round(bucket["income"], 2),
            "expense": round(bucket["expense"], 2),
            "net": round(bucket["income"] - bucket["expense"], 2),
        }
        for month, bucket in sorted(months.items())
    }
    summary["year"] = year
    summary["entry_count"] = len(year_entries)
    return summary
