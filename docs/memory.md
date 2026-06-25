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

## v0.6.0: the `scope.memory` convenience layer

`GenAIScope.memory` adds `title`, `entities`, and `confidence` (stored in the existing
`metadata` dict) plus a 0-1 `importance_score` (mapped onto the existing 1-10 `importance`
field), and conventional memory-type constants in `genaiscope.memory.types`
(`PROFILE_MEMORY`, `PROJECT_MEMORY`, `PREFERENCE_MEMORY`, `CONVERSATION_MEMORY`,
`DOCUMENT_MEMORY`, `ENTITY_MEMORY`, `DECISION_MEMORY`, `LEARNING_MEMORY`,
`PROMPT_PATTERN_MEMORY` — `memory_type` remains a free string, these are typo-safety only):

```python
from genaiscope import GenAIScope

scope = GenAIScope(db_path="genaiscope.db")
scope.memory.add(
    memory_type="profile_memory",
    title="User profile",
    content="Sapan is a CTO / VP Engineering leader with TravelTech experience.",
    tags=["profile", "cto", "traveltech"],
    confidence=0.95,
    importance_score=0.9,
)
results = scope.memory.search("CTO interview feature velocity", top_k=5)
scope.memory.forget(results[0].item.id)
```

See [context-doctor.md](context-doctor.md) for the full Context Doctor layer built on top of
this (`scope.context`, `scope.doctor`, `scope.analytics`, `scope.report`).
