# vs Ragas

## Quick Comparison

### GenAIScope

- **Focus**: Holistic GenAI readiness
- **Scope**: Prompts, RAG, outputs, safety, cost
- **Interface**: CLI-first, simple API
- **Dependencies**: Minimal

### Ragas

- **Focus**: RAG evaluation & testing
- **Scope**: Retrieval & generation quality
- **Interface**: Python API, integrations
- **Dependencies**: LangChain, heavy

## Feature Comparison

| Feature | GenAIScope | Ragas |
|---------|-----------|-------|
| RAG Evaluation | ✓ | ✓ (Advanced) |
| Prompt Inspection | ✓ | ✗ |
| Cost Analysis | ✓ | ✗ |
| PII Detection | ✓ | ✗ |
| Hallucination Detection | ✓ | ✓ |
| LLM-based Metrics | ✗ | ✓ |
| Online Metrics | Basic | ✓ (Advanced) |
| No Dependencies | ✓ | ✗ |
| Local-first | ✓ | ✗ |
| CLI Interface | ✓ | ✗ |
| Easy Setup | ✓ | Moderate |

## When to Use GenAIScope

- Quick RAG quality checks
- Broader GenAI application validation
- Cost-conscious projects
- Minimalist setup
- Pre-production checks
- CLI-based workflows

## When to Use Ragas

- Advanced RAG evaluation
- LLM-based quality metrics
- Complex evaluation scenarios
- Integration with LangChain
- Deep RAG optimization
- Academic/research level analysis

## Example Comparison

### GenAIScope Approach

```python
from genaiscope import Inspector

inspector = Inspector()
report = inspector.inspect_rag(
    query="What is AI?",
    context="AI is...",
    response="AI is artificial intelligence..."
)
print(report.summary())
```

### Ragas Approach

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

results = evaluate(
    dataset,
    metrics=[faithfulness, answer_relevancy],
)
```

## Cost Comparison

- **GenAIScope**: Free
- **Ragas**: Free (requires LLM calls for metrics)

## Integration Possibilities

### Use Both

```python
# Quick check with GenAIScope
from genaiscope import Inspector

inspector = Inspector()
quick_check = inspector.inspect_rag(query, context, response)

if quick_check.metrics['context_quality'] > 0.7:
    # Detailed evaluation with Ragas
    from ragas import evaluate
    detailed_results = evaluate(dataset, metrics=[...])
```

## Verdict

- **GenAIScope** = Fast, lightweight RAG inspection
- **Ragas** = Comprehensive RAG evaluation framework

Choose GenAIScope for quick checks, Ragas for detailed research.
