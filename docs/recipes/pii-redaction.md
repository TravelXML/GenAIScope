# PII Redaction Recipe

Learn how to detect and redact Personally Identifiable Information (PII) in GenAI applications.

## Basic PII Detection

```python
from genaiscope.analyzers import PIIDetector

detector = PIIDetector()

# Detect PII
text = "Contact John at john@example.com or call 555-123-4567"
detections = detector.detect(text)

print("PII Found:")
for pii_type, matches in detections.items():
    print(f"  {pii_type}: {matches}")

# Output:
# PII Found:
#   email: ['john@example.com']
#   phone: ['555-123-4567']
```

## Redacting PII

```python
from genaiscope.analyzers import PIIDetector

detector = PIIDetector()

# Original text with PII
text = """
Customer: John Smith
Email: john@example.com
Phone: (555) 123-4567
SSN: 123-45-6789
"""

# Redact PII
redacted = detector.redact(text)
print("Redacted:")
print(redacted)

# Output:
# Customer: John Smith
# Email: [EMAIL]
# Phone: [PHONE]
# SSN: [SSN]
```

## Production PII Pipeline

```python
from genaiscope.analyzers import PIIDetector
import logging

class PIPipeline:
    def __init__(self, redact_by_default=True):
        self.detector = PIIDetector()
        self.redact_by_default = redact_by_default
        self.logger = logging.getLogger(__name__)
    
    def process_user_input(self, text: str, redact: bool = None) -> str:
        """
        Process user input and handle PII detection.
        
        Args:
            text: User input text
            redact: Whether to redact PII (defaults to self.redact_by_default)
        
        Returns:
            Processed text (possibly redacted)
        """
        if redact is None:
            redact = self.redact_by_default
        
        # Detect PII
        detections = self.detector.detect(text)
        
        if detections:
            self.logger.warning(f"PII detected: {list(detections.keys())}")
            
            if redact:
                self.logger.info("Redacting PII from user input")
                return self.detector.redact(text)
            else:
                self.logger.warning("PII not redacted - ensure proper permissions")
                return text
        
        return text
    
    def process_model_output(self, text: str) -> str:
        """
        Process model output and redact any PII that may have leaked.
        """
        detections = self.detector.detect(text)
        
        if detections:
            self.logger.error(f"PII leaked in model output: {list(detections.keys())}")
            # Always redact model output
            return self.detector.redact(text)
        
        return text

# Usage
pipeline = PIPipeline(redact_by_default=True)

# Process user input
user_input = "Please call me at 555-123-4567"
safe_input = pipeline.process_user_input(user_input)

# Process model output  
model_output = "As discussed, we can reach you at 555-123-4567"
safe_output = pipeline.process_model_output(model_output)
```

## PII Types Detected

GenAIScope detects the following PII:

```python
from genaiscope.analyzers import PIIDetector

detector = PIIDetector()

# Email addresses
emails = detector.detect("Contact john@example.com")

# Phone numbers
phones = detector.detect("Call 555-123-4567 or (555) 123-4567")

# Social Security Numbers
ssns = detector.detect("SSN: 123-45-6789")

# Credit Card Numbers
credit_cards = detector.detect("Card: 4532-1234-5678-9010")

# IPv4 addresses
ips = detector.detect("Server at 192.168.1.1")
```

## Data Privacy Workflow

```python
from genaiscope.analyzers import PIIDetector
from genaiscope import Inspector
import json

class PrivacyCompliantRAG:
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.inspector = Inspector()
    
    def generate_response(self, user_query: str, context: str) -> str:
        """
        Generate response with privacy controls.
        """
        # 1. Check user query for PII
        query_pii = self.pii_detector.detect(user_query)
        if query_pii:
            print(f"Warning: User query contains PII: {list(query_pii.keys())}")
            user_query = self.pii_detector.redact(user_query)
        
        # 2. Check context for PII
        context_pii = self.pii_detector.detect(context)
        if context_pii:
            print(f"Warning: Context contains PII: {list(context_pii.keys())}")
            # Don't redact context if it's needed for retrieval
            # But log it for compliance
        
        # 3. Generate response
        response = self.llm.generate(user_query, context)
        
        # 4. Check response for PII leakage
        response_pii = self.pii_detector.detect(response)
        if response_pii:
            print(f"Error: Response contains PII leakage: {list(response_pii.keys())}")
            response = self.pii_detector.redact(response)
        
        # 5. Return safe response
        return response
    
    def get_compliance_report(self, interaction_id: str, query: str, context: str, response: str):
        """Generate compliance report for an interaction."""
        query_pii = self.pii_detector.detect(query)
        context_pii = self.pii_detector.detect(context)
        response_pii = self.pii_detector.detect(response)
        
        report = {
            "interaction_id": interaction_id,
            "user_query_pii": dict(query_pii),
            "context_pii": dict(context_pii),
            "response_pii": dict(response_pii),
            "response_redacted": bool(response_pii),
            "compliant": not bool(response_pii),
        }
        
        return report
```

## Testing PII Detection

```python
import pytest
from genaiscope.analyzers import PIIDetector

@pytest.fixture
def detector():
    return PIIDetector()

def test_email_detection(detector):
    """Test email PII detection."""
    result = detector.detect("Email me at john@example.com")
    assert "email" in result
    assert "john@example.com" in result["email"]

def test_phone_detection(detector):
    """Test phone number detection."""
    result = detector.detect("Call 555-123-4567")
    assert "phone" in result

def test_multiple_pii_types(detector):
    """Test detection of multiple PII types."""
    text = "Email john@example.com, call 555-123-4567, SSN 123-45-6789"
    result = detector.detect(text)
    
    assert "email" in result
    assert "phone" in result
    assert "ssn" in result

def test_pii_redaction(detector):
    """Test that redaction replaces PII."""
    original = "Email: john@example.com Phone: 555-123-4567"
    redacted = detector.redact(original)
    
    assert "john@example.com" not in redacted
    assert "555-123-4567" not in redacted
    assert "[EMAIL]" in redacted
    assert "[PHONE]" in redacted

def test_false_positives(detector):
    """Test that legitimate content isn't flagged as PII."""
    # IP addresses in documentation
    result = detector.detect("The default gateway is 192.168.1.1")
    
    # This might detect the IP, which may be acceptable depending on context
    # You may want to add filtering for private IP ranges
```

## CLI Usage

```bash
# Detect PII in text
genaiscope detect-pii "My email is john@example.com"

# Redact PII
genaiscope detect-pii "Email john@example.com call 555-123-4567" --redact

# Process file
cat sensitive_file.txt | xargs genaiscope detect-pii

# Detect specific types (advanced - create custom script)
python -c """
from genaiscope.analyzers import PIIDetector

detector = PIIDetector()
with open('data.txt') as f:
    text = f.read()

detections = detector.detect(text)
for pii_type, matches in detections.items():
    print(f'{pii_type}: {len(matches)} occurrences')
"""
```

## Privacy Best Practices

### 1. Always Redact Model Outputs
```python
# ✓ Good - redact model output before showing to user
response = llm.generate(prompt)
response = detector.redact(response)
return response

# ✗ Bad - leaking PII from model
response = llm.generate(prompt)
return response  # May contain PII
```

### 2. Log PII Detection Events
```python
import logging

logger = logging.getLogger(__name__)

detections = detector.detect(text)
if detections:
    logger.warning(f"PII detected in input: {list(detections.keys())}")
    # This logs the detection for compliance auditing
```

### 3. Use Different Strategies for Different Contexts
```python
# For user input - redact and log
user_input = detector.redact(user_input)
logger.info("User input redacted")

# For internal processing - preserve but log
internal_data = detective(internal_data)
if detections:
    logger.warning("PII in internal data")

# For output to users - always redact
user_output = detector.redact(user_output)
```

### 4. Comply with Regulations
```python
class RegulatoryCompliantSystem:
    """Example showing GDPR/CCPA compliance."""
    
    def __init__(self):
        self.detector = PIIDetector()
    
    def process_user_data(self, data: str) -> str:
        """Process with privacy compliance."""
        # Under GDPR, must minimize PII processing
        pii = self.detector.detect(data)
        if pii:
            # Log for privacy policy compliance
            self.log_pii_processing(pii)
            # Redact or anonymize
            data = self.detector.redact(data)
        return data
    
    def log_pii_processing(self, pii: dict):
        """Log PII processing for compliance."""
        # Store in audit log for GDPR Article 30 compliance
        pass
```

## Advanced: Custom PII Patterns

```python
from genaiscope.analyzers import PIIDetector
import re

class ExtendedPIIDetector(PIIDetector):
    """Extended detector with custom patterns."""
    
    def __init__(self):
        super().__init__()
        # Add custom patterns
        self.patterns["passport"] = r"\b[A-Z]{1,2}\d{6,9}\b"
        self.patterns["driver_license"] = r"\b[A-Z]{2}\d{5,8}\b"

# Usage
detector = ExtendedPIIDetector()
detections = detector.detect(text)
```

## Next Steps

- Try [Structured Output Validation](structured-output.md)
- Learn [RAG Inspection](rag-inspection.md)
- See [Safety Analysis](agent-safety.md)
