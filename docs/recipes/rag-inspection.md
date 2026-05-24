# RAG Inspection Recipe

Learn how to inspect and optimize Retrieval Augmented Generation (RAG) systems.

## What is RAG Inspection?

RAG systems combine three components:
1. **Query** - User question
2. **Context** - Retrieved documents
3. **Response** - Generated answer

RAG inspection evaluates how well these components work together.

## Basic RAG Inspection

```python
from genaiscope import Inspector

inspector = Inspector()

# Inspect a RAG interaction
report = inspector.inspect_rag(
    query="What is machine learning?",
    context="Machine learning is a subset of artificial intelligence that enables computers to learn from data.",
    response="Machine learning allows computers to learn patterns from data without explicit programming."
)

print(report.summary())
```

## Checking Context Relevance

```python
from genaiscope import Inspector

inspector = Inspector()

# Good RAG - context matches response
good_rag = inspect_rag(
    query="What year was Python created?",
    context="Python was created by Guido van Rossum and first released in 1991.",
    response="Python was created in 1991 by Guido van Rossum."
)

# Poor RAG - context doesn't match
poor_rag = inspect_rag(
    query="What year was Python created?",
    context="Java is an object-oriented programming language created in 1995.",
    response="Python was created in 1991."
)

print("Good RAG score:", good_rag.evaluations[0].score)
print("Poor RAG score:", poor_rag.evaluations[0].score)
```

## Hallucination Detection in RAG

```python
from genaiscope.analyzers import HallucinationDetector

detector = HallucinationDetector()

# Response matches context
context = "The Eiffel Tower is located in Paris, France."
response = "The Eiffel Tower is in Paris."
results = detector.detect(context, response)
print(f"Hallucination risk: {results['hallucination_risk']}")  # Low

# Response contradicts context
context = "The capital of France is Paris."
response = "The capital of France is London."
results = detector.detect(context, response)
print(f"Hallucination risk: {results['hallucination_risk']}")  # High
```

## RAG Quality Workflow

```python
from genaiscope import Inspector
from genaiscope.analyzers import HallucinationDetector

class RAGValidator:
    def __init__(self):
        self.inspector = Inspector()
        self.hallucination_detector = HallucinationDetector()
        self.min_context_score = 0.6
        self.max_hallucination_risk = 0.4
    
    def validate_rag_output(self, query: str, context: str, response: str) -> bool:
        """Validate RAG output quality."""
        
        # Check context relevance
        rag_report = self.inspector.inspect_rag(query, context, response)
        context_score = rag_report.evaluations[0].score if rag_report.evaluations else 0
        
        if context_score < self.min_context_score:
            print(f"Context relevance too low: {context_score}")
            return False
        
        # Check for hallucinations
        hallucination_results = self.hallucination_detector.detect(context, response)
        hallucination_risk = hallucination_results['hallucination_risk']
        
        if hallucination_risk > self.max_hallucination_risk:
            print(f"Hallucination risk too high: {hallucination_risk}")
            return False
        
        return True

# Usage in RAG pipeline
validator = RAGValidator()
if validator.validate_rag_output(user_query, retrieved_context, generated_response):
    return generated_response
else:
    return "Unable to generate reliable answer with available context"
```

## Production RAG Pipeline

```python
from genaiscope import Inspector
from genaiscope.analyzers import HallucinationDetector, PIIDetector

class ProductionRAG:
    def __init__(self):
        self.inspector = Inspector()
        self.hallucination_detector = HallucinationDetector()
        self.pii_detector = PIIDetector()
    
    def retrieve_and_generate(self, query: str, knowledge_base):
        # 1. Retrieve context
        context = knowledge_base.search(query)
        
        # 2. Generate response
        response = self.llm.generate(query, context)
        
        # 3. Quality checks
        rag_report = self.inspector.inspect_rag(query, context, response)
        
        # 4. Hallucination check
        hallucination_results = self.hallucination_detector.detect(context, response)
        
        # 5. PII check
        pii_detections = self.pii_detector.detect(response)
        
        # 6. Validation
        if hallucination_results['hallucination_risk'] > 0.3:
            raise ValueError("High hallucination risk detected")
        
        if pii_detections:
            response = self.pii_detector.redact(response)
        
        # 7. Return with metadata
        return {
            "response": response,
            "context_quality": rag_report.evaluations[0].score if rag_report.evaluations else 0,
            "hallucination_risk": hallucination_results['hallucination_risk'],
            "pii_redacted": bool(pii_detections),
        }

# Usage
rag = ProductionRAG()
result = rag.retrieve_and_generate("What is AI?", knowledge_base)
print(f"Response: {result['response']}")
print(f"Quality score: {result['context_quality']}")
```

## Testing RAG Systems

```python
import pytest
from genaiscope import Inspector
from genaiscope.analyzers import HallucinationDetector

def test_rag_with_matching_context():
    """Test RAG when context matches response."""
    inspector = Inspector()
    
    report = inspector.inspect_rag(
        query="What is Python?",
        context="Python is a programming language.",
        response="Python is a programming language."
    )
    
    # Context score should be high
    assert report.evaluations[0].score > 0.7

def test_rag_with_mismatched_context():
    """Test RAG when context doesn't match response."""
    inspector = Inspector()
    
    report = inspector.inspect_rag(
        query="What year was Python created?",
        context="Java was created in 1995.",
        response="Python was created in 1991."
    )
    
    # Context score should be low
    assert report.evaluations[0].score < 0.5

def test_hallucination_detection():
    """Test hallucination detection."""
    detector = HallucinationDetector()
    
    results = detector.detect(
        context="The Earth is round.",
        response="The Earth is flat."
    )
    
    assert results['hallucination_risk'] > 0.5
```

## CLI Examples

```bash
# Analyze a complete RAG interaction
# First, save query, context, response to separate files

# Then create a Python script to analyze:
python -c """
from genaiscope import Inspector

inspector = Inspector()
with open('query.txt') as f:
    query = f.read()
with open('context.txt') as f:
    context = f.read()
with open('response.txt') as f:
    response = f.read()

report = inspector.inspect_rag(query, context, response)
print(report.summary())
"""
```

## Common RAG Issues

### 1. Poor Context Retrieval
```python
# Problem: Retrieved context is irrelevant
query = "How to bake a cake?"
context = "The best pizza restaurants in New York..."
response = "I'm not sure about baking cakes..."

# Solution: Improve retrieval with better embeddings
# or expand knowledge base
```

### 2. Context Not Used
```python
# Problem: Response ignores retrieved context
query = "What is machine learning?"
context = "ML is a subset of AI that enables learning from data..."
response = "I don't know about machine learning."

# Solution: Improve prompt to encourage context usage
```

### 3. Hallucinations
```python
# Problem: Response adds information not in context
context = "Paris is the capital of France."
response = "Paris is the capital of France and is located on Mars."

# Solution: Use HallucinationDetector to catch this
```

## Optimization Tips

1. **Better Retrieval**: Improve embeddings and search algorithms
2. **Context Window**: Balance between detail and token limits
3. **Prompt Engineering**: Encourage use of context in instructions
4. **Evaluation**: Continuously monitor hallucination and context scores
5. **Feedback Loop**: Use validation results to improve retrieval

## Next Steps

- Try [PII Redaction](pii-redaction.md)
- Learn [Cost Analysis](cost-analysis.md)
- See [Structured Output](structured-output.md)
