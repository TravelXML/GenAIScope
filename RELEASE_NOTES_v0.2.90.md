# GenAIScope v0.2.90 Release Notes

GenAIScope v0.2.90 adds a local-first memory, file intelligence, prompt coaching,
trace logging, and dashboard layer on top of the existing readiness toolkit.

## Install

```bash
pip install genaiscope
```

## New Features

- SQLite-backed local memory store
- Local keyword/hybrid memory search
- Prompt quality coach
- File memory for TXT, MD, JSON, and CSV
- Local trace logging
- Static HTML dashboard

## CLI

```bash
genaiscope memory add "User prefers concise answers" --type preference
genaiscope memory add-prompt "Summarize this properly."
genaiscope memory search "concise answers"
genaiscope files add README.md
genaiscope trace stats
genaiscope dashboard generate
```

## Python

```python
from genaiscope.memory import MemoryStore

memory = MemoryStore()
memory.add("User prefers short CTO-level answers.", memory_type="preference")
print(memory.search("answer style"))
```

## Known Limitations

- SQLite only in this release
- Local keyword/hybrid scoring only; no embeddings yet
- PDF and DOCX ingestion are not included
- Dashboard is static HTML

## Roadmap

- Redis backend
- Vector search
- Semantic cache
- MCP memory server
- REST API
