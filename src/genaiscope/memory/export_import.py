"""Memory backup and migration helpers."""

from __future__ import annotations

import json
from pathlib import Path

from genaiscope.memory.base import BaseMemoryStore


def export_memories(store: BaseMemoryStore, output_path: str | Path, format: str = "json") -> int:
    """Export memories as JSON or JSONL."""

    path = Path(output_path)
    items = [item.model_dump(mode="json") for item in store.list(limit=100000, include_expired=True)]
    if format == "json":
        path.write_text(json.dumps(items, indent=2), encoding="utf-8")
    elif format == "jsonl":
        path.write_text("\n".join(json.dumps(item) for item in items) + ("\n" if items else ""), encoding="utf-8")
    else:
        raise ValueError("format must be 'json' or 'jsonl'")
    return len(items)


def import_memories(store: BaseMemoryStore, input_path: str | Path, merge_strategy: str = "skip_existing") -> int:
    """Import memories into any backend."""

    path = Path(input_path)
    if merge_strategy not in {"skip_existing", "overwrite", "create_new"}:
        raise ValueError("invalid merge strategy")
    text = path.read_text(encoding="utf-8")
    records = json.loads(text) if path.suffix.lower() == ".json" else [json.loads(line) for line in text.splitlines() if line.strip()]
    imported = 0
    for record in records:
        existing = store.get(record["id"], include_expired=True)
        if existing and merge_strategy == "skip_existing":
            continue
        if merge_strategy == "create_new":
            record.pop("id", None)
        else:
            record["memory_id"] = record.pop("id")
        record.pop("expires_at", None)
        store.add(**record)
        imported += 1
    return imported
