# Local Memory

GenAIScope v0.2.90 includes a SQLite-backed local memory store.

```python
from genaiscope.memory import MemoryStore

memory = MemoryStore()
memory.add("User prefers concise answers.", memory_type="preference")
print(memory.search("concise answers"))
```

The default database path is `.genaiscope/memory.db`.
