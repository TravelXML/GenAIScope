# Structured Output Recipe

Learn how to validate and work with structured outputs (JSON, XML, CSV) in GenAI applications.

## Basic Validation

```python
from genaiscope.analyzers import StructuredOutputValidator

validator = StructuredOutputValidator()

# Validate JSON
json_output = '{"name": "John", "age": 30}'
result = validator.validate_json(json_output)
print(f"Valid JSON: {result['valid']}")

# Validate XML
xml_output = "<user><name>John</name><age>30</age></user>"
result = validator.validate_xml(xml_output)
print(f"Valid XML: {result['valid']}")

# Validate CSV
csv_output = "name,age\nJohn,30\nJane,25"
result = validator.validate_csv(csv_output)
print(f"Valid CSV: {result['valid']}")
```

## Output Inspection with Format Validation

```python
from genaiscope import Inspector

inspector = Inspector()

# Inspect with expected format
prompt = "Return user data as JSON"
output = '{"id": 123, "name": "John", "email": "john@example.com"}'

report = inspector.inspect_output(output, expected_format="json")
print(report.summary())

# Check if format validation passed
format_checks = [e for e in report.evaluations if "format" in e.reasoning.lower()]
if format_checks:
    print(f"Format validation: {format_checks[0].label}")
```

## Production JSON Output Validation

```python
from genaiscope.analyzers import StructuredOutputValidator
import json
import logging

logger = logging.getLogger(__name__)

class JSONOutputValidator:
    def __init__(self, schema=None):
        self.validator = StructuredOutputValidator()
        self.schema = schema
    
    def validate_and_parse(self, output: str):
        """
        Validate JSON output and parse to dict.
        
        Args:
            output: Raw string output from LLM
        
        Returns:
            Parsed dict if valid, None otherwise
        """
        # First validate the JSON format
        result = self.validator.validate_json(output)
        
        if not result["valid"]:
            logger.error(f"Invalid JSON output: {result.get('error')}")
            return None
        
        try:
            data = result.get("data", json.loads(output))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return None
        
        # Optional: Validate against schema
        if self.schema:
            is_valid = self._validate_schema(data)
            if not is_valid:
                logger.error("JSON does not match schema")
                return None
        
        return data
    
    def _validate_schema(self, data: dict) -> bool:
        """Validate data against schema."""
        required_fields = self.schema.get("required", [])
        for field in required_fields:
            if field not in data:
                return False
        return True

# Usage
validator = JSONOutputValidator(schema={
    "required": ["id", "name", "email"]
})

json_output = '{"id": 123, "name": "John", "email": "john@example.com"}'
parsed = validator.validate_and_parse(json_output)

if parsed:
    print(f"Valid: {parsed}")
else:
    print("Invalid output")
```

## Handling Invalid Output

```python
from genaiscope import Inspector
from genaiscope.analyzers import StructuredOutputValidator

class RobustOutputHandler:
    def __init__(self):
        self.inspector = Inspector()
        self.validator = StructuredOutputValidator()
    
    def generate_structured_output(self, prompt: str, expected_format: str):
        """
        Generate structured output with retries.
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            # Generate output
            raw_output = self.llm.generate(prompt)
            
            # Validate format
            report = self.inspector.inspect_output(raw_output, expected_format=expected_format)
            
            # Check validation results
            format_valid = any(
                e.score > 0.7 and "format" in e.reasoning.lower()
                for e in report.evaluations
            )
            
            if format_valid:
                return raw_output
            
            # Retry with improved prompt
            prompt = self._improve_prompt(prompt, report, attempt)
        
        raise ValueError(f"Failed to generate valid {expected_format} after {max_retries} attempts")
    
    def _improve_prompt(self, prompt: str, report, attempt: int) -> str:
        """Improve prompt based on validation failures."""
        if attempt == 0:
            return prompt + "\n\nEnsure output is valid " + expected_format.upper()
        elif attempt == 1:
            return prompt + "\n\nOutput MUST be valid " + expected_format.upper() + ". No preamble."
        else:
            return prompt + "\n\nRespond with ONLY a valid " + expected_format.upper() + " object."
```

## Batch Processing with Validation

```python
from genaiscope.analyzers import StructuredOutputValidator
from concurrent.futures import ThreadPoolExecutor
import json

class BatchProcessor:
    def __init__(self, format_type: str):
        self.validator = StructuredOutputValidator()
        self.format_type = format_type
    
    def process_batch(self, items: list) -> list:
        """Process batch of items with output validation."""
        results = []
        failed = []
        
        for item in items:
            output = self._process_item(item)
            
            # Validate output
            if self.format_type == "json":
                validation = self.validator.validate_json(output)
            elif self.format_type == "xml":
                validation = self.validator.validate_xml(output)
            else:
                validation = self.validator.validate_csv(output)
            
            if validation["valid"]:
                results.append(validation.get("data", output))
            else:
                failed.append({
                    "item": item,
                    "error": validation.get("error"),
                    "output": output,
                })
        
        return {
            "success": results,
            "failed": failed,
            "total": len(items),
            "success_rate": len(results) / len(items) if items else 0,
        }
    
    def _process_item(self, item):
        """Process single item through LLM."""
        # Your LLM processing logic here
        pass
```

## Testing Structured Output

```python
import pytest
from genaiscope import Inspector
from genaiscope.analyzers import StructuredOutputValidator

def test_json_validation():
    """Test JSON validation."""
    validator = StructuredOutputValidator()
    
    valid_json = '{"name": "John", "age": 30}'
    result = validator.validate_json(valid_json)
    assert result["valid"] is True
    
    invalid_json = '{invalid json}'
    result = validator.validate_json(invalid_json)
    assert result["valid"] is False

def test_xml_validation():
    """Test XML validation."""
    validator = StructuredOutputValidator()
    
    valid_xml = "<root><item>test</item></root>"
    result = validator.validate_xml(valid_xml)
    assert result["valid"] is True
    
    invalid_xml = "<root><item>test</item>"
    result = validator.validate_xml(invalid_xml)
    assert result["valid"] is False

def test_output_inspection_with_format():
    """Test output inspection with format checking."""
    inspector = Inspector()
    
    json_output = '{"status": "success"}'
    report = inspector.inspect_output(json_output, expected_format="json")
    
    # Should have format-related evaluations
    assert len(report.evaluations) > 0
    assert report.output_text == json_output

@pytest.mark.parametrize("format_type,valid_output,invalid_output", [
    ("json", '{"test": "data"}', "{invalid}"),
    ("xml", "<root></root>", "<root>"),
   ("csv", "a,b\n1,2", "a,,b\n1,2"),
])
def test_multiple_formats(format_type, valid_output, invalid_output):
    """Test validation for multiple formats."""
    validator = StructuredOutputValidator()
    
    method = getattr(validator, f"validate_{format_type}")
    
    valid_result = method(valid_output)
    assert valid_result["valid"] is True
    
    invalid_result = method(invalid_output)
    # Invalid may not always be detected, but shouldn't crash
    assert "valid" in invalid_result
```

## CLI Usage

```bash
# Validate JSON from string
genaiscope validate-output '{"name":"John"}' --format json

# Validate from file
genaiscope validate-output "$(cat output.json)" --format json

# Validate XML
genaiscope validate-output '<?xml version="1.0"?><root></root>' --format xml

# Validate CSV
genaiscope validate-output "name,age\nJohn,30" --format csv
```

## Common Issues and Solutions

### 1. Incomplete JSON

```python
# Problem: LLM returns partial JSON
output = '{"name": "John", "age": 30'

# Solution: Ask for complete output
prompt = "Return complete JSON object with no explanations:\n{...}"
```

### 2. Escaped Quotes

```python
# Problem: JSON with escaped quotes  
output = '{\\"name\\": \\"John\\"}'

# Solution: Unescaping before validation
import json
unescaped = json.loads(output)
```

### 3. Extra Whitespace/Newlines

```python
# Problem: Output has preamble
output = '''
Here's the JSON:
{"name": "John"}
'''

# Solution: Strip and extract
output = output.strip()
# Extract JSON if needed
import re
json_match = re.search(r'\{.*\}', output, re.DOTALL)
```

## Performance Optimization

```python
from genaiscope.analyzers import StructuredOutputValidator
import json

class FastValidator:
    """Optimized validator with caching."""
    
    def __init__(self):
        self.validator = StructuredOutputValidator()
        self.cache = {}
    
    def validate_with_cache(self, output: str, format_type: str):
        """Validate with result caching."""
        cache_key = hash(output)
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        method = getattr(self.validator, f"validate_{format_type}")
        result = method(output)
        
        self.cache[cache_key] = result
        return result
```

## Next Steps

- Try [Agent Safety](agent-safety.md)
- Learn [Cost Analysis](cost-analysis.md)
- See [RAG Inspection](rag-inspection.md)
