# Semantic Cache

GenAIScope v0.3.0 includes a lightweight semantic cache foundation. It uses deterministic hybrid
text similarity and stores entries as `cache` memories, so SQLite and Redis backends both work.

```python
from genaiscope.cache import SemanticCache

cache = SemanticCache(memory_store=memory)
cache.set(prompt="Summarize refund policy", response="Refund policy summary...", user_id="sapan")
hit = cache.get(prompt="Can you summarize the refund policy?", user_id="sapan")
```
