# Semantic Memory Compaction

Text-based dedupe (`genaiscope memory dedupe`) only catches near-identical wording. Compaction
reuses the embeddings already stored by `memory.add()` to catch paraphrased duplicates too, then
merges each cluster into one memory — shrinking what `memory.context()` injects into every
future prompt, on any provider.

```python
from genaiscope.memory import MemoryStore, compact_memories

memory = MemoryStore(embedder="local")
memory.add("User prefers concise CTO-level answers", memory_type="preference")
memory.add("Keep replies short and exec-level", memory_type="preference")

report = compact_memories(memory, strategy="keep_best", dry_run=True)
print(report.clusters_found, report.tokens_saved, report.dollar_savings)
```

Pass a `summarizer` to merge clusters with an LLM instead of just keeping the best item — works
identically with OpenAI, Anthropic, or Gemini:

```python
from genaiscope.adapters import openai_summarizer

report = compact_memories(
    memory, strategy="synthesize", summarizer=openai_summarizer(), dry_run=False
)
```

With no embedder/vector store configured, compaction falls back to text-based dedupe
(`report.semantic` is `False`) instead of erroring. `dry_run=True` still calls a configured
`summarizer` to preview real savings — that is not free if the summarizer hits a paid API.

```bash
genaiscope memory compact --embedder local --threshold 0.92
genaiscope memory compact --embedder local --summarizer openai --apply
```
