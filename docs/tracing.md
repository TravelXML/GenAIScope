# Local Tracing

Local tracing records model calls, latency, token counts, cost estimates, and errors.

```python
from genaiscope.tracing import LocalTracer

tracer = LocalTracer()
tracer.log(name="demo", input_text="hello", output_text="hi", model="local")
```

For production Redis traces:

```python
tracer = LocalTracer(backend="redis", redis_url="redis://localhost:6379", namespace="memovo")
```

## v0.6.0: `GenAIScope.trace()` and `log_interaction()`

The `GenAIScope` facade wraps `LocalTracer` with `category`/`tags`/`user_id`/`project_id`/
`session_id`/`rating` (stored in the trace's `metadata`) and automatically attaches a Context
Doctor health score:

```python
from genaiscope import GenAIScope

scope = GenAIScope(db_path="genaiscope.db")

with scope.trace(provider="openai", model="gpt-4.1", category="cto_interview", tags=["traveltech"]) as trace:
    response = llm_call(prompt)
    trace.log(prompt=prompt, response=response)

scope.log_interaction(
    prompt="Explain feature velocity",
    response="Feature velocity means shipping value to customers faster.",
    provider="openai", model="gpt-4.1",
    input_tokens=120, output_tokens=240, latency_ms=1800,
    category="cto_learning", tags=["metrics", "cto"],
)
```

See [context-doctor.md](context-doctor.md) and [analytics.md](analytics.md) for how this
feeds `scope.doctor.diagnose()` and `scope.analytics.prompt_patterns()`.
