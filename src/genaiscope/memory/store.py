"""Backward-compatible import for the default SQLite store."""

from genaiscope.memory.store_sqlite import SQLiteMemoryStore

MemoryStore = SQLiteMemoryStore

__all__ = ["MemoryStore", "SQLiteMemoryStore"]
