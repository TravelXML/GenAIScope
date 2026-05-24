# Concepts

## Core Concepts

### Inspector

The main entry point for analyzing GenAI applications. Provides unified interface for inspecting different aspects:

- **Prompt Inspection** - Analyze prompts for quality and potential issues
- **RAG Inspection** - Evaluate Retrieval Augmented Generation systems
- **Output Inspection** - Validate model outputs and structured formats

### InspectionReport

Result of an inspection containing:

- **Evaluations** - Scored assessments of different aspects
- **Metrics** - Quantitative measurements
- **Warnings** - Potential issues identified
- **Errors** - Critical problems found
- **Summary** - Human-readable report

### Analyzers

Specialized tools for specific inspection tasks:

- **CostAnalyzer** - Estimate API costs
- **PIIDetector** - Find Personally Identifiable Information
- **HallucinationDetector** - Identify hallucination risks
- **SafetyAnalyzer** - Assess safety and bias issues
- **StructuredOutputValidator** - Validate JSON/XML/CSV formats

### ScoringEngine

Flexible system for evaluating and scoring text:

- Default scorers for common checks
- Pluggable custom scorer registration
- Threshold-based pass/fail evaluation

### Result Type

Generic wrapper for operation results with:

- **Status** - SUCCESS, FAILURE, PARTIAL, SKIPPED
- **Data** - Result data
- **Error** - Error message if failed
- **Message** - Optional additional message

## Architecture

GenAIScope follows a modular, layered architecture:

```
┌─────────────────────────────────────┐
│      CLI / Python API               │
├─────────────────────────────────────┤
│      Inspector (Main Interface)     │
├─────────────────────────────────────┤
│  Specialized Analyzers              │
│  ├─ PromptInspector                │
│  ├─ RAGInspector                   │
│  ├─ OutputInspector                │
│  ├─ PII/Hallucination/Safety...    │
└─────────────────────────────────────┘
│      Scoring Engine                 │
├─────────────────────────────────────┤
│      Core Models & Providers        │
│      ├─ Config                     │
│      ├─ Models                     │
│      ├─ Providers                  │
│      └─ Logging                    │
└─────────────────────────────────────┘
```

## Design Principles

### 1. Simplicity First
One-line APIs for common tasks, deeper APIs for advanced use.

### 2. Local by Default
All analysis runs locally. No mandatory cloud dependencies.

### 3. Modularity
Pick what you need. Mix and match different tools.

### 4. Production Ready
Type hints, error handling, comprehensive testing.

### 5. No Vendor Lock-in
Works with any provider. Easy to extend.

### 6. Local-First Cloud-Ready
Start local, scale to cloud later if needed.

## Workflow Example

```
1. Initialize Inspector
   inspector = Inspector()

2. Run Inspection
   report = inspector.inspect_prompt(prompt)

3. Get Results
   report.evaluations    # Scored assessments
   report.metrics        # Quantitative data
   report.warnings       # Potential issues
   report.summary()      # Human-readable report

4. Take Action
   - Fix issues identified
   - Store report
   - Integrate into pipeline
```

## Integration Points

### Within Your Application
```python
# Validate before API call
report = inspector.inspect_prompt(user_prompt)
if any(e.score < 0.5 for e in report.evaluations):
    raise ValueError("Unsafe prompt detected")
```

### In CI/CD Pipeline
```bash
# CLI-based validation
genaiscope inspect-prompt "$PROMPT" || exit 1
```

### In Testing Framework
```python
def test_response_quality():
    response = llm.complete(prompt)
    report = inspector.inspect_output(response)
    assert all(e.score > 0.7 for e in report.evaluations)
```

## Performance Considerations

- Analysis is synchronous by default (async support coming)
- Local analyzers are fast (<1ms per check)
- PII detection uses regex (fast) not ML
- Hallucination detection uses heuristics (not ML-based)

## Extensibility

Extend GenAIScope with custom scorers and analyzers:

```python
# Custom scorer
def my_scorer(text: str) -> float:
    return 0.9 if "good" in text else 0.3

engine = ScoringEngine()
engine.register("my_check", my_scorer)

# Custom analyzer
from genaiscope.analyzers import SafetyAnalyzer
class MyAnalyzer(SafetyAnalyzer):
    def analyze(self, text):
        # Custom logic
        return super().analyze(text)
```

## Roadmap & Future

- Agent safety analysis
- Multi-modal inspection
- Distributed evaluation
- ML-based hallucination detection
- Web dashboard
- Enterprise governance platform
- Advanced RAG analysis
- Prompt optimization suggestions
