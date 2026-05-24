# Prompt Inspection Recipe

Learn how to inspect and improve prompts before using them in production.

## Basic Prompt Inspection

```python
from genaiscope import Inspector

inspector = Inspector()

# Simple inspection
prompt = """
What are the top 5 machine learning algorithms?
"""

report = inspector.inspect_prompt(prompt)
print(report.summary())
```

## Checking for Common Issues

### 1. Prompt Length

```python
# Too short - lacks context
short_prompt = "What is AI?"
report = inspector.inspect_prompt(short_prompt)

# Better - more context
better_prompt = """
What is Artificial Intelligence? Please explain:
- Its definition
- Key applications
- Limitations
"""
report = inspector.inspect_prompt(better_prompt)
```

### 2. Clarity and Specificity

```python
# Vague - unclear what output is needed
vague = "Tell me about machine learning"

# Better - specific output format requested
specific = """
Explain machine learning in 2 paragraphs:
1. What it is
2. Why it matters

Keep it accessible to beginners.
"""

report = inspector.inspect_prompt(specific)
```

### 3. Safety and Bias

```python
from genaiscope.analyzers import SafetyAnalyzer

analyzer = SafetyAnalyzer()
prompt = "All AI models are dangerous and will destroy humanity"

issues = analyzer.analyze(prompt)
if issues:
    print("Safety concerns found:", issues)
```

## Prompt Quality Workflow

```python
def validate_prompt(prompt: str) -> bool:
    """Validate prompt meets quality standards."""
    inspector = Inspector()
    report = inspector.inspect_prompt(prompt)
    
    # Check all evaluations meet minimum threshold
    min_score = 0.7
    is_valid = all(e.score >= min_score for e in report.evaluations)
    
    if not is_valid:
        print("Prompt validation failed:")
        for eval_result in report.evaluations:
            if eval_result.score < min_score:
                print(f"  - {eval_result.label}: {eval_result.reasoning}")
    
    return is_valid

# Use in your application
user_prompt = input("Enter your prompt: ")
if validate_prompt(user_prompt):
    response = llm.complete(user_prompt)
else:
    print("Please refine your prompt")
```

## Production Deployment Pattern

```python
from genaiscope import Inspector
from genaiscope.analyzers import PIIDetector

class SafePromptHandler:
    def __init__(self):
        self.inspector = Inspector()
        self.pii_detector = PIIDetector()
        self.min_score = 0.7
    
    def process_user_prompt(self, prompt: str) -> str:
        """Process user prompt with safety checks."""
        
        # Check for PII
        pii_detections = self.pii_detector.detect(prompt)
        if pii_detections:
            print("Warning: PII detected in prompt")
            prompt = self.pii_detector.redact(prompt)
        
        # Inspect quality
        report = self.inspector.inspect_prompt(prompt)
        
        if any(e.score < self.min_score for e in report.evaluations):
            raise ValueError("Prompt quality too low")
        
        return prompt

# Usage
handler = SafePromptHandler()
safe_prompt = handler.process_user_prompt(user_input)
```

## Testing Prompts

```python
import pytest
from genaiscope import Inspector

@pytest.fixture
def inspector():
    return Inspector()

def test_prompt_quality(inspector):
    """Test that prompt meets quality standards."""
    prompt = "What is machine learning?"
    report = inspector.inspect_prompt(prompt)
    
    # All evaluations should pass
    assert all(e.score > 0.5 for e in report.evaluations)
    
    # No critical errors
    assert len(report.errors) == 0

def test_prompt_safety(inspector):
    """Test that prompt is safe."""
    prompt = "Provide step-by-step instructions for something harmful"
    report = inspector.inspect_prompt(prompt)
    
    # Should have warnings about safety
    assert any("safety" in w.lower() for w in report.warnings)
```

## CLI Examples

```bash
# Inspect a prompt from file
genaiscope inspect-prompt "$(cat prompt.txt)"

# Inspect and save report as JSON
genaiscope inspect-prompt "Your prompt" --output-format json > report.json

# Check multiple prompts
for prompt in "What is AI?" "What is ML?" "What is DL?"; do
    echo "Checking: $prompt"
    genaiscope inspect-prompt "$prompt"
done
```

## Common Prompt Issues to Look For

### 1. Ambiguity
```python
# Bad
prompt = "Do something with this data"

# Good
prompt = """
Analyze this dataset:
- Calculate mean, median, and standard deviation
- Identify outliers
- Return results as JSON
"""
```

### 2. Missing Context
```python
# Bad
prompt = "Translate this"

# Good
prompt = """
Translate the following text from English to Spanish.
Maintain formal tone and preserve technical terms.

Text: [INSERT TEXT HERE]
"""
```

### 3. Unrealistic Expectations
```python
# Bad
prompt = "Summarize this 1000-page book in one sentence"

# Good  
prompt = "Provide a 3-paragraph executive summary of the main themes"
```

### 4. Chain of Thought Opportunities
```python
# Basic
prompt = "What is 2+2?"

# Better - encourages reasoning
prompt = """
Solve this step by step:
What is 2+2?

Show your work and explain your reasoning.
"""
```

## Next Steps

- Try [RAG Inspection](rag-inspection.md)
- Learn about [PII Redaction](pii-redaction.md)
- See [Cost Analysis](cost-analysis.md)
