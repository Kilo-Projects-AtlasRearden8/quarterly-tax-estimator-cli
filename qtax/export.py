"""CSV export for entries."""

from __future__ import annotations

import csv
from typing import Any

FIELDNAMES = ("id", "type", "amount", "date", "note", "source", "category", "created_at")


def export_csv(path: str, entries: list[dict[str, Any]]) -> None:
    """Write entries to a CSV file with stable column order."""
    ordered = sorted(entries, key=lambda e: (e.get("date", ""), e.get("id", 0)))
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for entry in ordered:
            writer.writerow({field: entry.get(field, "") for field in FIELDNAMES})
