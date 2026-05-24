"""Tests for scoring engine."""

import pytest
from genaiscope.core.scoring import ScoringEngine


def test_scoring_engine_initialization():
    """Test scoring engine initialization."""
    engine = ScoringEngine()
    assert "length" in engine.scorers
    assert "null_safety" in engine.scorers


def test_score_length():
    """Test length scoring."""
    engine = ScoringEngine()
    score = engine.score("Hello world", "length")
    assert 0 <= score <= 1


def test_score_null_safety():
    """Test null safety scoring."""
    engine = ScoringEngine()
    
    score_valid = engine.score("Some text", "null_safety")
    assert score_valid == 1.0
    
    score_empty = engine.score("", "null_safety")
    assert score_empty == 0.0


def test_register_custom_scorer():
    """Test registering a custom scorer."""
    engine = ScoringEngine()
    
    def custom_scorer(text: str) -> float:
        return 0.5
    
    engine.register("custom", custom_scorer)
    assert "custom" in engine.scorers
    
    score = engine.score("test", "custom")
    assert score == 0.5


def test_evaluate():
    """Test evaluation."""
    engine = ScoringEngine()
    result = engine.evaluate("Some text", "length", threshold=0.5)
    
    assert hasattr(result, "score")
    assert hasattr(result, "label")
    assert result.label in ["pass", "fail"]
