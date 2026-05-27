"""Tests for analyzers."""

from genaiscope.analyzers import (
    CostAnalyzer,
    HallucinationDetector,
    PIIDetector,
    SafetyAnalyzer,
    StructuredOutputValidator,
)


def test_cost_analyzer():
    """Test cost analyzer."""
    analyzer = CostAnalyzer()
    costs = analyzer.estimate_cost("gpt-4", 100, 200)

    assert "input_cost" in costs
    assert "output_cost" in costs
    assert "total_cost" in costs
    assert costs["total_cost"] > 0


def test_pii_detector():
    """Test PII detection."""
    detector = PIIDetector()

    # Test email detection
    detections = detector.detect("Contact me at john@example.com")
    assert "email" in detections
    assert "john@example.com" in detections["email"]

    # Test redaction
    redacted = detector.redact("Email: john@example.com Phone: 555-123-4567")
    assert "[EMAIL]" in redacted
    assert "[PHONE]" in redacted


def test_hallucination_detector():
    """Test hallucination detection."""
    detector = HallucinationDetector()

    context = "The sky is blue. Water is wet."
    response = "The sky is green. Water is wet. The earth is flat."

    results = detector.detect(context, response)
    assert "hallucination_risk" in results
    assert results["hallucination_risk"] > 0


def test_safety_analyzer():
    """Test safety analyzer."""
    analyzer = SafetyAnalyzer()

    issues = analyzer.analyze("This is always bad and will never improve")
    assert len(issues) > 0


def test_structured_output_validator():
    """Test structured output validation."""
    validator = StructuredOutputValidator()

    # Test JSON validation
    json_result = validator.validate_json('{"name": "test"}')
    assert json_result["valid"] is True

    json_invalid = validator.validate_json("invalid json")
    assert json_invalid["valid"] is False

    # Test XML validation
    xml_result = validator.validate_xml("<root></root>")
    assert xml_result["valid"] is True
