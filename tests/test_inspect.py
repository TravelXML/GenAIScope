"""Tests for inspection."""

from genaiscope.inspect import Inspector


def test_inspector_initialization():
    """Test inspector initialization."""
    inspector = Inspector()
    assert inspector.prompt_inspector is not None
    assert inspector.rag_inspector is not None
    assert inspector.output_inspector is not None


def test_inspect_prompt():
    """Test prompt inspection."""
    inspector = Inspector()
    report = inspector.inspect_prompt("What is the capital of France?")

    assert report.title == "Prompt Inspection"
    assert report.input_text == "What is the capital of France?"
    assert len(report.evaluations) > 0
    assert "metrics" in report.model_dump()


def test_inspect_output():
    """Test output inspection."""
    inspector = Inspector()
    report = inspector.inspect_output('{"name": "test"}', expected_format="json")

    assert report.title == "Output Inspection"
    assert len(report.evaluations) > 0


def test_inspect_rag():
    """Test RAG inspection."""
    inspector = Inspector()
    report = inspector.inspect_rag(
        query="What is AI?",
        context="Artificial Intelligence is...",
        response="AI is Artificial Intelligence.",
    )

    assert report.title == "RAG Inspection"
    assert len(report.evaluations) > 0
