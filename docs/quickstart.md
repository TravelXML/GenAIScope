# Quick Start

Get started with GenAIScope in 5 minutes!

## Installation

```bash
pip install genaiscope
```

## Basic Usage

### Python API

```python
from genaiscope import Inspector

# Create an inspector
inspector = Inspector()

# Inspect a prompt
report = inspector.inspect_prompt("What is the capital of France?")
print(report.summary())
```

### CLI Usage

```bash
# Inspect a prompt
genaiscope inspect-prompt "What is AI?"

# Detect PII
genaiscope detect-pii "Contact john@example.com"

# Estimate costs
genaiscope estimate-cost gpt-4 100 200

# Show configuration
genaiscope config-show
```

## Common Patterns

### Inspect RAG Output

```python
inspector = Inspector()
report = inspector.inspect_rag(
    query="What is machine learning?",
    context="ML is a subset of AI that...",
    response="Machine learning is..."
)
print(report.summary())
```

### Validate Structured Output

```python
report = inspector.inspect_output(
    '{"name": "John", "age": 30}',
    expected_format="json"
)
```

### Detect and Redact PII

```python
from genaiscope.analyzers import PIIDetector

detector = PIIDetector()

# Detect PII
text = "Email me at john@example.com or call 555-123-4567"
detections = detector.detect(text)
print(detections)  # {'email': ['john@example.com'], 'phone': ['555-123-4567']}

# Redact PII
redacted = detector.redact(text)
print(redacted)  # "Email me at [EMAIL] or call [PHONE]"
```

### Estimate Costs

```python
from genaiscope.analyzers import CostAnalyzer

analyzer = CostAnalyzer()
costs = analyzer.estimate_cost("gpt-4", input_tokens=100, output_tokens=150)
print(f"Total cost: ${costs['total_cost']:.4f}")
```

## Next Steps

- Read the full [Installation Guide](installation.md)
- Learn core [Concepts](concepts.md)
- Explore [API Reference](api-reference.md)
- Try [Recipes](recipes/prompt-inspection.md)
- Check [CLI Reference](cli.md)

## Getting Help

- 📖 Read the [documentation](https://genaiscope.dev)
- 🐛 Report [issues on GitHub](https://github.com/genaiscope/genaiscope/issues)
- 💬 Join [discussions](https://github.com/genaiscope/genaiscope/discussions)
