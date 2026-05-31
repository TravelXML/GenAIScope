# Production Memory

GenAIScope v0.3.0 uses SQLite by default and offers an optional Redis production backend.

```python
from genaiscope.memory import MemoryStore

memory = MemoryStore()
memory.add("User prefers concise answers.", memory_type="preference", user_id="sapan", project_id="memovo")
print(memory.search("concise answers"))
```

The default database path is `.genaiscope/memory.db`.

```python
memory = MemoryStore(backend="redis", redis_url="redis://localhost:6379", namespace="memovo")
memory.remember("Temporary context", memory_type="temporary", ttl_days=3)
```

Memory supports user, workspace, project, agent, and session scopes, TTL cleanup, deterministic
hybrid search, duplicate cleanup, and JSON or JSONL export/import for SQLite-to-Redis migrations.
