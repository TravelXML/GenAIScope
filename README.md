# GenAIScope

**Inspect, test, secure, optimize, and operationalize GenAI applications before production.**

GenAIScope is a production-quality Python library that helps developers, CTOs, and AI engineers identify and fix issues in GenAI applications. It provides lightweight, powerful tooling for detecting gaps in prompts, RAG quality, hallucination risks, structured output failures, unsafe agent tools, PII leakage, cost inefficiency, weak testing, missing observability, and poor production readiness.

## Key Features

- **One-line APIs for beginners** - Easy to use for quick checks
- **Deep inspection APIs** - Advanced capabilities for engineering teams
- **CLI-first experience** - Interact via command line or Python
- **Local-first** - Run everything locally by default
- **Modular design** - Mix and match what you need
- **Production-ready** - Type-safe, async-capable, fully tested

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
# For OpenAI support
pip install genaiscope[openai]

# For Anthropic support
pip install genaiscope[anthropic]

# For Google Gemini support
pip install genaiscope[google]

# For development
pip install genaiscope[dev]

# For documentation building
pip install genaiscope[docs]

# Everything
pip install genaiscope[all]
```

## Quick Start

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
```

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
│   ├── cli.py              # CLI interface
│   ├── inspect.py          # Main inspector
│   ├── analyzers.py        # Specialized analyzers
│   ├── scoring.py          # Scoring engine
│   └── core/               # Core modules
│       ├── config.py
│       ├── models.py
│       ├── errors.py
│       ├── providers.py
│       ├── logging.py
│       ├── result.py
│       └── core_inspect.py
└── tests/                  # Test suite
    ├── test_models.py
    ├── test_analyzers.py
    ├── test_inspect.py
    └── test_scoring.py
```

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

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 📖 [Documentation](https://genaiscope.dev)
- 🐛 [Issue Tracker](https://github.com/genaiscope/genaiscope/issues)
- 💬 [Discussions](https://github.com/genaiscope/genaiscope/discussions)

## Roadmap

- [ ] Agent safety analysis
- [ ] Cost optimization recommendations
- [ ] CI/CD integration
- [ ] Web dashboard
- [ ] Enterprise observability
- [ ] More provider integrations
- [ ] Advanced RAG analysis
- [ ] Prompt optimization suggestions

---

**GenAIScope: Making GenAI applications production-ready.**
