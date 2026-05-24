"""Scoring engine for evaluations."""

from typing import Any, Callable, Dict, List, Optional

from genaiscope.core.models import EvaluationResult


class ScoringEngine:
    """Engine for scoring and evaluation."""

    def __init__(self) -> None:
        """Initialize the scoring engine."""
        self.scorers: Dict[str, Callable[[str], float]] = {}
        self._register_default_scorers()

    def _register_default_scorers(self) -> None:
        """Register default scoring functions."""
        self.register("length", self._score_length)
        self.register("null_safety", self._score_null_safety)

    def register(self, name: str, scorer: Callable[[str], float]) -> None:
        """Register a custom scorer."""
        self.scorers[name] = scorer

    def score(self, text: str, scorer_name: str, **kwargs: Any) -> float:
        """Score text using a registered scorer."""
        if scorer_name not in self.scorers:
            raise ValueError(f"Unknown scorer: {scorer_name}")
        return self.scorers[scorer_name](text, **kwargs)

    def evaluate(
        self, text: str, scorer_name: str, threshold: float = 0.5, **kwargs: Any
    ) -> EvaluationResult:
        """Evaluate text and return an evaluation result."""
        score = self.score(text, scorer_name, **kwargs)
        label = "pass" if score >= threshold else "fail"
        reasoning = f"Score {score:.2f} vs threshold {threshold}"

        return EvaluationResult(score=score, label=label, reasoning=reasoning)

    @staticmethod
    def _score_length(text: str, min_length: int = 1, max_length: int = 10000) -> float:
        """Score based on text length."""
        length = len(text)
        if length < min_length or length > max_length:
            return 0.0
        normalized = (length - min_length) / (max_length - min_length)
        return min(1.0, max(0.0, normalized))

    @staticmethod
    def _score_null_safety(text: str) -> float:
        """Score if text is not null or empty."""
        return 1.0 if text and len(text.strip()) > 0 else 0.0
