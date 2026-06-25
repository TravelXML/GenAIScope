# GenAIScope Documentation

## Getting Started

Welcome to GenAIScope! This documentation will help you get started with inspecting and optimizing your GenAI applications.

## Documentation Structure

- **Quick Start** - Get up and running in 5 minutes
- **Installation** - Detailed installation instructions
- **Concepts** - Core concepts and architecture
- **[Context Doctor](context-doctor.md)** - Memory + tracing + rule-based prompt/context diagnosis (v0.6.0)
- **[Analytics](analytics.md)** - Usage summaries and prompt-pattern analysis (v0.6.0)
- **[Memory](memory.md)** / **[Tracing](tracing.md)** - Local-first memory and trace logging
- **CLI Reference** - Command-line interface guide
- **API Reference** - Complete Python API documentation
- **[Examples](examples.md)** - Runnable example scripts
- **Recipes** - Practical examples and use cases
- **Comparisons** - How GenAIScope compares to alternatives

## Key Features

GenAIScope helps you:

- ✅ Diagnose why an LLM answer was weak and get a recommended prompt rewrite (Context Doctor)
- ✅ Capture prompts, responses, token usage, and cost locally (tracing)
- ✅ Store and retrieve user/project memory with keyword or vector search
- ✅ Inspect prompts for quality and safety
- ✅ Analyze RAG systems for context relevance
- ✅ Validate structured outputs (JSON, XML, CSV)
- ✅ Detect Personally Identifiable Information (PII)
- ✅ Identify hallucination risks
- ✅ Estimate API costs across OpenAI, Anthropic, Google, Groq, and local models
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
