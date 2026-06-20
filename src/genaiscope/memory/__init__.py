"""Local memory APIs."""

from genaiscope.memory.base import BaseMemoryStore
from genaiscope.memory.compaction import (
    CompactionReport,
    compact_memories,
    find_semantic_duplicates,
)
from genaiscope.memory.context import ContextResult
from genaiscope.memory.dedupe import dedupe_memories, find_duplicates
from genaiscope.memory.export_import import export_memories, import_memories
from genaiscope.memory.factory import MemoryStore
from genaiscope.memory.models import (
    MemoryItem,
    MemorySearchResult,
    MemoryStats,
    PromptQualityReport,
)
from genaiscope.memory.prompt_quality import analyze_prompt_quality
from genaiscope.memory.store_redis import RedisMemoryStore
from genaiscope.memory.store_sqlite import SQLiteMemoryStore

__all__ = [
    "BaseMemoryStore",
    "CompactionReport",
    "ContextResult",
    "MemoryItem",
    "MemorySearchResult",
    "MemoryStats",
    "MemoryStore",
    "PromptQualityReport",
    "RedisMemoryStore",
    "SQLiteMemoryStore",
    "analyze_prompt_quality",
    "compact_memories",
    "dedupe_memories",
    "export_memories",
    "find_duplicates",
    "find_semantic_duplicates",
    "import_memories",
]
