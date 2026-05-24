# vs DeepEval

## Quick Comparison

### GenAIScope

- **Focus**: GenAI readiness & quality toolkit
- **Scope**: Broad coverage (prompts, RAG, safety, cost)
- **API**: Simple, one-line APIs
- **Learning Curve**: Minimal

### DeepEval

- **Focus**: LLM evaluation framework
- **Scope**: Detailed evaluation metrics
- **API**: Comprehensive, test-based
- **Learning Curve**: Moderate

## Feature Comparison

| Feature | GenAIScope | DeepEval |
|---------|-----------|----------|
| Simple One-Liners | ✓ | ✗ |
| Prompt Inspection | ✓ | ✗ |
| RAG Quality | ✓ | ✓ |
| Cost Analysis | ✓ | ✗ |
| PII Detection | ✓ | ✗ |
| hallucination | ✓ | ✓ (Advanced) |
| Test Framework | Basic | ✓ (Advanced) |
| Custom Metrics | ✓ | ✓ |
| LLM Integration | ✓ | ✓ |
| Local-first | ✓ | ✗ |
| Minimal Setup | ✓ | Moderate |
| Dashboard | ✗ | ✓ (Optional) |

## When to Use GenAIScope

- Quick quality checks
- Holistic GenAI validation
- Cost-conscious projects
- Beginners/simple use cases
- Local development
- CI/CD integration
- Ad-hoc analysis

## When to Use DeepEval

- Comprehensive test suites
- Advanced evaluation scenarios
- Custom metric definition
- Team-based testing
- Integration with testing frameworks
- Production evaluation pipeline
- Complex validation logic

## Example Comparison

### GenAIScope

```python
from genaiscope import Inspector

# Simple, one-liner quality check
inspector = Inspector()
report = inspector.inspect_prompt("What is AI?")
print(f"Quality: {report.evaluations[0].score}")
```

### DeepEval

```python
from deepeval import evaluate
from deepeval.metrics import Faithfulness

# Comprehensive evaluation
metric = Faithfulness()
test_case = LLMTestCase(
    input="What is AI?",
    actual_output=model_response,
    context=context
)
result = evaluate([test_case], [metric])
```

## Setup Complexity

- **GenAIScope**: 1 command (`pip install genaiscope`)
- **DeepEval**: Multiple integrations and configuration

## Customization

### GenAIScope

```python
engine = ScoringEngine()

def custom_scorer(text: str) -> float:
    return 0.8 if len(text) > 100 else 0.2

engine.register("custom", custom_scorer)
```

### DeepEval

```python
class CustomMetric(BaseMetric):
    def __init__(self):
        super().__init__(name="custom")
    
    def measure(self, test_case: LLMTestCase):
        # Complex implementation
        pass
```

## Integration

### With Testing Frameworks

**GenAIScope:**
```python
def test_prompt_quality():
    inspector = Inspector()
    report = inspector.inspect_prompt(prompt)
    assert report.evaluations[0].score > 0.7
```

**DeepEval:**
```python
@pytest.mark.parametrize('test_case', test_cases)
def test_faithfulness(test_case):
    metric = Faithfulness()
    evaluate([test_case], [metric])
```

## Cost

- **GenAIScope**: Free
- **DeepEval**: Free (optional paid analytics)

## Use Cases

### GenAIScope Ideal For

- MVP validation
- Pre-deployment checks
- Fast iteration
- Budget-conscious teams
- Beginners

### DeepEval Ideal For

- Production verification
- Complex requirements
- Advanced teams
- Enterprise setups
- Academic research

## Verdict

- **GenAIScope** = Quick & easy GenAI quality checks
- **DeepEval** = Comprehensive evaluation framework

Choose GenAIScope for simplicity, DeepEval for power.
