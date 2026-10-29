"""JSON storage for income and expense entries.

Local-first: entries live in a single JSON file on your machine (default
``~/.qtax/entries.json``). Set ``QTAX_DATA_FILE`` to use a different path,
or pass ``--data-file`` on any command.
"""

from __future__ import annotations

import json
import os
from typing import Any

DEFAULT_DIR_NAME = ".qtax"
DEFAULT_FILE_NAME = "entries.json"


def default_data_path() -> str:
    """Resolve the storage file path (env override wins)."""
    override = os.environ.get("QTAX_DATA_FILE")
    if override:
        return os.path.expanduser(override)
    home = os.path.expanduser("~")
    return os.path.join(home, DEFAULT_DIR_NAME, DEFAULT_FILE_NAME)


def load_entries(path: str) -> list[dict[str, Any]]:
    """Load entries from the JSON storage file.

    Returns an empty list if the file is missing or empty. A corrupt file
    raises ValueError with a plain-language message.
    """
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        raw = handle.read().strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"storage file {path!r} is not valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"storage file {path!r} must contain a JSON list of entries")
    return [entry for entry in data if isinstance(entry, dict)]


def save_entries(path: str, entries: list[dict[str, Any]]) -> None:
    """Atomically write entries to the JSON storage file."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(tmp_path, path)
