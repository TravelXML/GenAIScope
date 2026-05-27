"""Tests for core models."""

from genaiscope.core.models import EvaluationResult, InspectionReport, Provider, ScopeConfig


def test_scope_config_default():
    """Test default ScopeConfig."""
    config = ScopeConfig()
    assert config.provider == Provider.OPENAI
    assert config.model == "gpt-4"
    assert config.temperature == 0.7


def test_evaluation_result():
    """Test EvaluationResult creation."""
    result = EvaluationResult(
        score=0.85,
        label="pass",
        reasoning="Test reasoning",
    )
    assert result.score == 0.85
    assert result.label == "pass"


def test_inspection_report():
    """Test InspectionReport creation."""
    report = InspectionReport(
        id="test-1",
        title="Test Report",
        description="A test report",
    )
    assert report.id == "test-1"
    assert report.title == "Test Report"

    summary = report.summary()
    assert "Test Report" in summary
    assert "A test report" in summary
