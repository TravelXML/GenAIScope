# GenAIScope Documentation

## Getting Started

Welcome to GenAIScope! This documentation will help you get started with inspecting and optimizing your GenAI applications.

## Documentation Structure

- **Quick Start** - Get up and running in 5 minutes
- **Installation** - Detailed installation instructions
- **Concepts** - Core concepts and architecture
- **CLI Reference** - Command-line interface guide
- **API Reference** - Complete Python API documentation
- **Recipes** - Practical examples and use cases
- **Comparisons** - How GenAIScope compares to alternatives

## Key Features

GenAIScope helps you:

- ✅ Inspect prompts for quality and safety
- ✅ Analyze RAG systems for context relevance
- ✅ Validate structured outputs (JSON, XML, CSV)
- ✅ Detect Personally Identifiable Information (PII)
- ✅ Identify hallucination risks
- ✅ Estimate API costs
- ✅ Assess safety and bias issues
- ✅ Monitor GenAI application readiness

## Quick Example

```python
from genaiscope import Inspector

# Create inspector
inspector = Inspector()

# Inspect a prompt
report = inspector.inspect_prompt("What is AI?")
print(report.summary())
```

## Community

- Report issues on GitHub
- Join discussions
- Contribute code
- Share feedback

Let's make GenAI applications production-ready together! 🚀
