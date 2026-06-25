# Examples

All examples run locally with no API keys. Run any of them with:

```bash
python examples/<name>.py
```

## Context Doctor (v0.6.0)

| File | Demonstrates |
|---|---|
| `01_basic_trace.py` | `GenAIScope.trace()` context manager and `log_interaction()` |
| `02_memory_add_search.py` | `scope.memory.add()` / `search()` / `forget()` |
| `03_context_builder.py` | `scope.context.build()` — retrieved memory + improved prompt |
| `04_context_doctor.py` | `scope.doctor.diagnose()` — health score and recommended prompt |
| `05_usage_analytics.py` | `scope.analytics.usage_summary()` and `prompt_patterns()` |
| `06_html_report.py` | `scope.report.generate_html()` |
| `07_cto_copilot_example.py` | Full walkthrough: profile + project memory → weak prompt → improved context → trace → diagnosis → HTML report |

## Core toolkit

| File | Demonstrates |
|---|---|
| `memory_quickstart.py` | `MemoryStore.add()` / `search()` |
| `local_tracing.py` | `LocalTracer.log()` |
| `dashboard_demo.py` | `generate_dashboard()` (memory/file/trace overview, distinct from the Context Doctor report) |
| `file_memory_quickstart.py` | `FileMemory` for TXT/MD/JSON/CSV |
| `prompt_coach.py` | `memory.add_prompt()` quality coaching |
