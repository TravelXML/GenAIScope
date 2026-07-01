# GenAIScope

**GenAIScope is a lightweight memory, tracing, and context diagnosis toolkit for LLM and Agent applications.**

It helps developers understand why LLM outputs fail by capturing prompts, responses, token usage, model behavior, memory usage, context gaps, and recommending better prompts for higher-quality AI results.

GenAIScope is also the broader local-first Python toolkit it always was: AI memory, file intelligence, prompt coaching, trace logging, and GenAI production-readiness checks (inspection, PII, hallucination/safety analysis, structured-output validation). It helps developers, Tech Leaders, and AI engineers identify and fix issues in GenAI applications before production. Context Doctor (v0.6.0) is the newest, most opinionated layer on top of that foundation, and v0.7.0 connects it to live LLM providers, MCP, and the wider agent-tooling ecosystem.

## What is Context Doctor?

**GenAIScope Context Doctor is a lightweight memory, tracing, and prompt diagnosis layer for LLM and Agent applications. It captures prompts, responses, token usage, model behavior, memory usage, context gaps, and recommends better prompts for higher-quality AI outputs.**

Every LLM interaction can produce an answer *plus* a health report: memory used, prompt quality, context gaps, token usage, cost, latency, model fit, hallucination risk, and a suggested better prompt — computed locally with rule-based heuristics, no extra LLM call required.

## Why memory + tracing + diagnosis matters

Weak LLM answers are usually a *context* problem, not a model problem: the prompt didn't say who the answer is for, how long it should be, or what background the user already has on file. Context Doctor turns "the answer was mediocre" into a concrete, actionable diagnosis - what's missing, why, and exactly how to rewrite the prompt - by combining three things GenAIScope already does well: local memory, local tracing, and rule-based scoring.

## Key Features

- **Context Doctor (v0.6.0)** - Rule-based health score, missing-context detection, and a recommended prompt rewrite for every LLM interaction
- **One-line APIs for beginners** - Easy to use for quick checks
- **Deep inspection APIs** - Advanced capabilities for engineering teams
- **CLI-first experience** - Interact via command line or Python
- **Local-first** - Run everything locally by default
- **Modular design** - Mix and match what you need
- **Production-ready** - Type-safe, async-capable, fully tested
- **SQLite local memory** - Store user preferences, project facts, prompts, and document chunks
- **Optional Redis backend** - Move production memory and traces to Redis without changing APIs
- **Scoped memory and TTL** - Keep user, project, workspace, agent, and session context tidy
- **Semantic cache foundation** - Reuse responses with deterministic hybrid text similarity
- **Prompt coach** - Get local comments and improvement suggestions for weak prompts
- **Static dashboard** - Generate a local HTML dashboard with memory, file, prompt, trace, and cost insights
- **Live LLM gateway (v0.7.0)** - `genaiscope ask` / `scope.gateway` auto-routes to OpenAI/Anthropic/Google with fallback, logging a health score on every call
- **MCP tools (v0.7.0)** - `doctor_diagnose`, `analytics_*`, `report_generate`, plus the v0.4.0 memory tools, over `genaiscope serve mcp`
- **Cross-encoder reranking (v0.7.0)** - Opt-in `rerank=True` on memory search for higher-precision retrieval
- **Agent evaluation (v0.7.0)** - `genaiscope.evals.run_agent_eval` scores multi-step agent trajectories
- **LangChain / LlamaIndex / OpenTelemetry / Langfuse (v0.7.0)** - Drop-in memory ABCs, OTel span export, and Langfuse batch export

## What Makes GenAIScope Different

- Not another LLM framework (like LangChain)
- Not just another observability platform (like Langfuse)
- Not only an eval framework (like Ragas or DeepEval)
- Not just an LLM gateway (like Helicone)

GenAIScope is a **readiness and manipulation toolkit** - lightweight but comprehensive - designed to help teams operationalize GenAI applications safely and efficiently.

## Installation

```bash
pip install genaiscope
```

### Optional Dependencies

```bash
# All live gateway providers (OpenAI + Anthropic + Google) -- needed for `genaiscope ask`
pip install genaiscope[providers]

# Redis-backed memory/tracing for production
pip install genaiscope[redis]

# Real embeddings + cross-encoder reranking
pip install genaiscope[embeddings]

# MCP server (Context Doctor + memory tools)
pip install genaiscope[mcp]

# REST API server
pip install genaiscope[server]

# OpenTelemetry span export
pip install genaiscope[otel]

# LangChain chat-history integration
pip install genaiscope[langchain]

# LlamaIndex memory integration
pip install genaiscope[llamaindex]

# For development
pip install genaiscope[dev]

# For documentation building
pip install genaiscope[docs]

# Everything (providers, redis, embeddings, mcp, server, otel, langchain, llamaindex)
pip install genaiscope[all]
```

## Context Doctor: 5-Minute Quickstart

```python
from genaiscope import GenAIScope

scope = GenAIScope(db_path="genaiscope.db")

# 1. Teach it who you are and what you've worked on (one-time setup)
scope.memory.add(
    memory_type="profile_memory",
    content="Sapan is a CTO / VP Engineering leader with TravelTech experience.",
    tags=["profile", "cto", "traveltech"],
)
scope.memory.add(
    memory_type="project_memory",
    content="Led the TravelTech platform rebuild focused on feature velocity and roadmap execution.",
    tags=["traveltech", "project"],
)

# 2. Ask a deliberately weak prompt
weak_prompt = "Write answer for feature velocity."

# 3. Get an improved prompt built from your own memory
context = scope.context.build(weak_prompt, top_k=5)
print(context.improved_prompt)

# 4. Log the real interaction and get a health report
response = "Feature velocity is how fast a team ships value."
report = scope.doctor.diagnose(prompt=weak_prompt, response=response, memories_used=context.retrieved_memories)
print(report.context_health_score, report.missing_context, report.recommended_prompt)

# 5. Generate an HTML report you can open in a browser
scope.report.generate_html("genaiscope_report.html")
```

### Example output

```text
Context Health Score: 61/100
Missing context: ['Target audience', 'Desired answer length or format', 'Tone preference', 'Business context (impact, outcomes)']
Recommended prompt: Using your background (Sapan is a CTO / VP Engineering leader with
TravelTech experience; ...), write answer for feature velocity. Keep it concise and
well-structured. Use a senior, professional tone. Connect it to business impact and outcomes.
```

### Dashboard / report screenshot

> _Run `genaiscope report --out genaiscope_report.html` and open it in a browser --
> screenshot placeholder, contributions of a real screenshot welcome._

See `examples/07_cto_copilot_example.py` for the full end-to-end walkthrough (memory →
context → trace → diagnosis → HTML report), and [docs/context-doctor.md](docs/context-doctor.md)
for the complete field reference.

## Quick Start

### Local Memory

```python
from genaiscope.memory import MemoryStore

memory = MemoryStore()
memory.add("User prefers short CTO-level answers.", memory_type="preference")
results = memory.search("answer style")
print(results)
```

### Production Memory

```python
from genaiscope.memory import MemoryStore

memory = MemoryStore(backend="redis", redis_url="redis://localhost:6379", namespace="memovo")
memory.remember(
    "User prefers concise CTO-level answers.",
    memory_type="preference",
    user_id="sapan",
    project_id="memovo",
    importance=8,
)
memory.remember("Temporary context", memory_type="temporary", ttl_days=3)
```

### Backup And Dedupe

```bash
genaiscope memory duplicates
genaiscope memory dedupe --apply --strategy keep_newest
genaiscope memory export memories.json
genaiscope memory import memories.json
```

### Semantic Cache

```python
from genaiscope.cache import SemanticCache

cache = SemanticCache(memory_store=memory)
cache.set(prompt="Summarize refund policy", response="Refund policy summary...", user_id="sapan")
hit = cache.get(prompt="Can you summarize the refund policy?", user_id="sapan")
```

## Memovo Integration

Memovo can use GenAIScope as a local SQLite or production Redis backend for user memory,
project memory, file memory, prompt history, conversation context, agent traces, semantic
cache, dashboard analytics, and a future MCP access layer.

### Prompt Coach

```python
from genaiscope.memory import MemoryStore

memory = MemoryStore()
item = memory.add_prompt("Summarize this properly.")
print(item.prompt_score)
print(item.prompt_comments)
print(item.prompt_suggestions)
```

GenAIScope automatically comments on weak prompts and suggests improvements.

### File Memory

```python
from genaiscope.files import FileMemory

files = FileMemory()
files.add_file("README.md")
results = files.search("installation")
print(results)
```

### Local Tracing

```python
from genaiscope.tracing import LocalTracer

tracer = LocalTracer()
tracer.log(
    name="demo-call",
    input_text="hello",
    output_text="hi",
    model="local",
    input_tokens=5,
    output_tokens=2,
    estimated_cost=0.0,
)
```

### Dashboard

```bash
genaiscope dashboard generate
```

### Python API

```python
from genaiscope import Inspector

# Create an inspector
inspector = Inspector()

# Inspect a prompt
report = inspector.inspect_prompt("What is the capital of France?")
print(report.summary())

# Inspect RAG output
rag_report = inspector.inspect_rag(
    query="What is AI?",
    context="Artificial Intelligence is...",
    response="AI is..."
)
print(rag_report.summary())

# Inspect structured output
output_report = inspector.inspect_output(
    '{"name": "test"}',
    expected_format="json"
)
print(output_report.summary())
```

### CLI Usage

```bash
# Show version
genaiscope version

# Show configuration
genaiscope config-show

# Inspect a prompt
genaiscope inspect-prompt "What is AI?"

# Detect PII in text
genaiscope detect-pii "My email is john@example.com"

# Redact PII
genaiscope detect-pii "Email: john@example.com" --redact

# Estimate API costs
genaiscope estimate-cost gpt-4 100 200

# Analyze text for issues
genaiscope analyze-text "Your text here" --analyze-pii --analyze-hallucination --context "background"

# Validate output format
genaiscope validate-output '{"test": "data"}' --format json

# v0.2.91 local memory and dashboard
genaiscope memory add "User prefers concise answers" --type preference --tags user,style
genaiscope memory add-prompt "Summarize this properly."
genaiscope memory search "concise answers"
genaiscope files add README.md
genaiscope trace stats
genaiscope dashboard generate

# v0.6.0 Context Doctor
genaiscope init
genaiscope memory add "User profile" --type profile_memory --tags profile,cto
genaiscope diagnose --prompt "Write answer for this job"
genaiscope analytics
genaiscope report --out genaiscope_report.html
genaiscope export --format json --out genaiscope_export.json

# v0.7.0 -- live gateway, MCP Context Doctor tools, Langfuse export
genaiscope ask "Refactor this function and explain the bug" --provider auto
genaiscope export --format langfuse --out genaiscope_traces.json
genaiscope serve mcp --trace  # exposes doctor_diagnose, analytics_*, report_generate too

# v0.8.0 -- the same live gateway, over REST (used by the browser extension's "Ask" panel)
genaiscope serve api --trace
curl -X POST http://127.0.0.1:8000/v1/gateway/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Refactor this function and explain the bug", "provider": "auto"}'
```

### Context Doctor CLI commands

| Command | Description |
|---|---|
| `genaiscope init` | Initialize a local GenAIScope workspace |
| `genaiscope diagnose --prompt "..."` | Health score, missing context, and a recommended rewrite for a prompt |
| `genaiscope analytics [--days N]` | Token/cost/latency usage summary + repeated prompt patterns |
| `genaiscope report --out FILE` | Generate the Context Doctor HTML report |
| `genaiscope export --format json\|jsonl\|langfuse --out FILE` | Export memories, or traces in Langfuse batch-ingestion format |
| `genaiscope ask "..." [--provider auto\|openai\|anthropic\|google]` | Call a live LLM provider (auto-routed by default), logged with a health score |

### Browser Extension

`browser-extension/` captures your prompts and AI replies from ChatGPT, Claude, and Gemini's
web apps into your local memory store, via the existing `/v1/prompts` and `/v1/memory/remember`
REST endpoints. Manual install only for now (load unpacked in Chrome) — see
`browser-extension/README.md`. Its DOM selectors are unofficial and will need updating whenever
one of those sites changes its markup.

Its popup also has an **"Ask GenAIScope"** panel (v0.8.0) that routes a prompt through the new
`POST /v1/gateway/ask` REST route instead: your own server calls OpenAI/Anthropic/Google
directly with your own API key, so the interaction is captured completely and reliably, rather
than scraped from a chat site's rendered page after the fact.

## v0.3.0 Roadmap Notes

Known limitations:

- Search uses local keyword/hybrid scoring, not real embeddings
- PDF/DOCX ingestion is not included yet
- Dashboard output is static HTML

Planned for a later release:

- Real vector DB support
- Semantic cache
- MCP memory server
- REST API
- Docker Compose

## Core Modules

### Inspector

The main entry point for inspecting GenAI applications:

```python
from genaiscope import Inspector

inspector = Inspector()

# Prompt inspection
report = inspector.inspect_prompt(prompt)

# RAG inspection
report = inspector.inspect_rag(query, context, response)

# Output inspection
report = inspector.inspect_output(output, expected_format="json")
```

### Analyzers

Specialized analyzers for different types of issues:

```python
from genaiscope.analyzers import (
    CostAnalyzer,
    PIIDetector,
    HallucinationDetector,
    SafetyAnalyzer,
    StructuredOutputValidator,
)

# Cost analysis
cost_analyzer = CostAnalyzer()
costs = cost_analyzer.estimate_cost("gpt-4", input_tokens, output_tokens)

# PII detection
pii_detector = PIIDetector()
detections = pii_detector.detect(text)
redacted = pii_detector.redact(text)

# Hallucination detection
detector = HallucinationDetector()
results = detector.detect(context, response)

# Safety analysis
analyzer = SafetyAnalyzer()
issues = analyzer.analyze(text)

# Structured output validation
validator = StructuredOutputValidator()
result = validator.validate_json(text)
```

### Scoring Engine

Evaluate and score text:

```python
from genaiscope import ScoringEngine

engine = ScoringEngine()

# Use built-in scorers
score = engine.score(text, "length")
result = engine.evaluate(text, "null_safety", threshold=0.5)

# Register custom scorers
def my_scorer(text):
    return 0.8

engine.register("custom", my_scorer)
score = engine.score(text, "custom")
```

## Configuration

Set configuration via environment variables:

```bash
# Provider settings
export GENAISCOPE_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export GENAISCOPE_MODEL=gpt-4

# Execution settings
export GENAISCOPE_MAX_TOKENS=2048
export GENAISCOPE_TEMPERATURE=0.7
export GENAISCOPE_TIMEOUT=30
export GENAISCOPE_RETRIES=3

# Logging
export GENAISCOPE_LOG_LEVEL=INFO
export GENAISCOPE_LOG_FILE=genaiscope.log
```

Or use the Python API:

```python
from genaiscope.core.config import set_config, Config

config = Config(
    provider="openai",
    openai_api_key="sk-...",
    model="gpt-4",
    temperature=0.7,
)
set_config(config)
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=src/genaiscope
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/genaiscope/genaiscope.git
cd genaiscope

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode with all dependencies
pip install -e ".[dev,docs]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Run Linting

```bash
ruff check src/
black --check src/
mypy src/
```

### Format Code

```bash
black src/ tests/
ruff check --fix src/
```

### Build Documentation

```bash
mkdocs serve
```

## Project Structure

```
genaiscope/
├── pyproject.toml           # Project configuration
├── README.md                # This file
├── LICENSE                  # MIT License
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # Contribution guidelines
├── CODE_OF_CONDUCT.md      # Community guidelines
├── .gitignore              # Git ignore rules
├── .env.example            # Environment template
├── mkdocs.yml              # Documentation config
├── docs/                   # Documentation
│   ├── index.md
│   ├── quickstart.md
│   ├── installation.md
│   ├── concepts.md
│   ├── cli.md
│   ├── api-reference.md
│   ├── recipes/
│   └── comparisons/
├── src/genaiscope/         # Package source
│   ├── __init__.py
│   ├── version.py
│   ├── inspect.py          # Main inspector
│   ├── analyzers.py        # Specialized analyzers
│   ├── scoring.py          # Scoring engine
│   ├── cli/                # Typer CLI (entry point: cli/main.py)
│   ├── core/                # Config, errors, models, GenAIScope facade (scope.py)
│   ├── memory/              # Scoped SQLite/Redis memory, dedupe, export/import
│   ├── tracing/              # Local trace logging
│   ├── embeddings/, vector/  # Pluggable embeddings + vector search
│   ├── cache/                # Semantic cache
│   ├── mcp/, server/, adapters/  # MCP memory + Context Doctor tools, REST API, provider adapters
│   ├── evals/                # Memory retrieval eval harness + v0.7.0 agent-trajectory eval
│   ├── dashboard/             # Static memory/file/trace HTML dashboard
│   ├── context/, doctor/      # v0.6.0: ContextBuilder, ContextDoctor
│   ├── cost/, router/         # v0.6.0: CostEstimator, model-type recommender
│   ├── analytics/, report/    # v0.6.0: usage/pattern analytics, Context Doctor HTML report
│   ├── gateway/                # v0.7.0: multi-provider live LLM gateway (`scope.gateway`, `genaiscope ask`)
│   ├── integrations/           # v0.7.0: LangChain, LlamaIndex, OpenTelemetry integrations
│   ├── export/                 # v0.7.0: Langfuse batch export (`genaiscope export --format langfuse`)
│   └── files/                 # File memory (TXT/MD/JSON/CSV)
└── tests/                  # Test suite (one file per module, see tests/)
```
## ALL Scripts

https://colab.research.google.com/drive/14mBCI4k1QO_yvZpUMwBgIwNwHwhgP_bE?usp=sharing

## API Reference

### Inspector

- `inspect_prompt(prompt: str) -> InspectionReport` - Analyze prompt quality
- `inspect_rag(query: str, context: str, response: str) -> InspectionReport` - Analyze RAG system
- `inspect_output(output: str, expected_format: Optional[str]) -> InspectionReport` - Validate output

### Analyzers

- `CostAnalyzer.estimate_cost(model: str, input_tokens: int, output_tokens: int)` - Calculate costs
- `PIIDetector.detect(text: str)` - Detect PII
- `PIIDetector.redact(text: str)` - Redact PII
- `HallucinationDetector.detect(context: str, response: str)` - Detect hallucinations
- `SafetyAnalyzer.analyze(text: str)` - Analyze for safety issues
- `StructuredOutputValidator.validate_json(text: str)` - Validate JSON

### ScoringEngine

- `score(text: str, scorer_name: str) -> float` - Score text
- `evaluate(text: str, scorer_name: str, threshold: float) -> EvaluationResult` - Evaluate text
- `register(name: str, scorer: Callable)` - Register custom scorer

## Testing

GenAIScope includes comprehensive tests for all components. See [TESTING.md](TESTING.md) for:

- ✅ Setup instructions
- ✅ Running unit tests with pytest
- ✅ Code quality checks (ruff, black, mypy)
- ✅ Coverage reports
- ✅ Manual testing procedures
- ✅ CI/CD validation with GitHub Actions
- ✅ Performance profiling
- ✅ Troubleshooting guide

Quick test command:
```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Roadmap

**v0.6.0** — Context Doctor: memory + tracing + rule-based health scoring, prompt
improvement, usage analytics, prompt-pattern analysis, model-type recommendation, and a local
HTML report.

**v0.7.0**:
- MCP tools for Context Doctor (`doctor_diagnose`, `analytics_usage_summary`,
  `analytics_prompt_patterns`, `report_generate`), alongside the v0.4.0 memory tools
- Multi-provider live LLM gateway (`scope.gateway` / `genaiscope ask`) — auto-routes to a real
  OpenAI/Anthropic/Google call using `genaiscope.router.recommend()`, with fallback across
  candidates and an attached Context Doctor health score
- Cross-encoder reranking for hybrid memory search (`rerank=True`)
- Agent evaluation workflows (`genaiscope.evals.run_agent_eval`)
- LangChain (`GenAIScopeChatMessageHistory`) and LlamaIndex (`GenAIScopeMemory`) integrations
- Langfuse batch export (`genaiscope export --format langfuse`)
- OpenTelemetry exporter hook on `LocalTracer` (`genaiscope.integrations.otel.OTelExporter`)
- Browser extension capture (`browser-extension/`, manual install — see its README)

**v0.8.0 (current)**:
- `POST /v1/gateway/ask` REST route — the v0.7.0 live gateway (auto-routing, fallback, health
  score), now reachable over HTTP, not just from Python
- "Ask GenAIScope" panel in the browser extension popup, wired to the new route — captures
  complete, structured interactions via your own gateway instead of only DOM-scraping a chat
  site's rendered page (additive to the existing capture)
- Sample dashboard committed at `examples/dashboard_sample/dashboard.html`, browsable without
  running anything
- CLI tests hardened against environments that force ANSI color (Jupyter, some CI runners);
  `genaiscope.__version__` de-duplicated

**v0.8.1 (planned)** — dashboard visual redesign (raised as feedback: current cards/tables read
as dense rather than an at-a-glance health check), broader browser-extension site coverage.

## Contributing

We welcome contributions! Please see the [contribution guidelines](https://github.com/TravelXML/genaiscope/blob/main/CONTRIBUTING.md).

## License

MIT License - see the [license file](https://github.com/TravelXML/genaiscope/blob/main/LICENSE) for details.

## Support

- 📖 [Documentation](https://travelxml.github.io/genaiscope)
- 🐛 [Issue Tracker](https://github.com/TravelXML/genaiscope/issues)
- 💬 [Discussions](https://github.com/TravelXML/genaiscope/discussions)
