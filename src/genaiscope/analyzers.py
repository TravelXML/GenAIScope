"""Analyzers module."""

import json
import re
from typing import Any

from genaiscope.core.logging import get_logger

logger = get_logger(__name__)


class CostAnalyzer:
    """Analyzer for calculating API costs."""

    def __init__(self) -> None:
        """Initialize cost analyzer."""
        # Pricing per 1K tokens (in USD)
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
        }

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> dict[str, float]:
        """Estimate API cost."""
        if model not in self.pricing:
            logger.warning(f"Unknown model {model}, returning zero cost")
            return {"input_cost": 0.0, "output_cost": 0.0, "total_cost": 0.0}

        pricing = self.pricing[model]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]

        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": input_cost + output_cost,
        }


class PIIDetector:
    """Detector for Personally Identifiable Information (PII)."""

    def __init__(self) -> None:
        """Initialize PII detector."""
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
            "ipv4": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
        }

    def detect(self, text: str) -> dict[str, list[str]]:
        """Detect PII in text."""
        results = {}

        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                results[pii_type] = matches

        return results

    def redact(self, text: str) -> str:
        """Redact PII from text."""
        redacted = text
        for pii_type, pattern in self.patterns.items():
            redacted = re.sub(pattern, f"[{pii_type.upper()}]", redacted)
        return redacted


class HallucinationDetector:
    """Detector for potential hallucinations."""

    def __init__(self) -> None:
        """Initialize hallucination detector."""

    def detect(self, context: str, response: str) -> dict[str, Any]:
        """Detect potential hallucinations."""
        # Simple heuristic: check for contradictions
        context_lower = context.lower()
        response_lower = response.lower()

        # Check for "I don't know" or "cannot" statements not in context
        unreliability_indicators = ["i don't know", "cannot", "unclear", "uncertain"]
        contains_uncertainty = any(
            indicator in response_lower for indicator in unreliability_indicators
        )

        response_sentences = response_lower.split(".")

        unsupported_count = 0
        for sentence in response_sentences:
            if sentence.strip() and sentence.strip() not in context_lower:
                unsupported_count += 1

        hallucination_score = min(1.0, unsupported_count / max(1, len(response_sentences)))

        return {
            "hallucination_risk": hallucination_score,
            "contains_uncertainty": contains_uncertainty,
            "unsupported_statements": unsupported_count,
        }


class SafetyAnalyzer:
    """Analyzer for safety issues."""

    def __init__(self) -> None:
        """Initialize safety analyzer."""
        self.harmful_patterns = {
            "toxic": r"(hate|kill|destroy|harmful)",
            "bias": r"(always|never|all|none)",
            "misinformation": r"(definitely|certainly|absolutely) (?!correct)",
        }

    def analyze(self, text: str) -> dict[str, list[str]]:
        """Analyze text for safety issues."""
        issues = {}

        for issue_type, pattern in self.harmful_patterns.items():
            matches = re.findall(pattern, text.lower())
            if matches:
                issues[issue_type] = matches

        return issues


class StructuredOutputValidator:
    """Validator for structured outputs."""

    @staticmethod
    def validate_json(text: str) -> dict[str, Any]:
        """Validate JSON output."""
        try:
            data = json.loads(text)
            return {"valid": True, "data": data}
        except (json.JSONDecodeError, ValueError) as e:
            return {"valid": False, "error": str(e)}

    @staticmethod
    def validate_xml(text: str) -> dict[str, Any]:
        """Validate XML output."""
        try:
            import xml.etree.ElementTree as ET

            ET.fromstring(text)
            return {"valid": True}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    @staticmethod
    def validate_csv(text: str) -> dict[str, Any]:
        """Validate CSV output."""
        try:
            import csv
            import io

            csv.reader(io.StringIO(text))
            return {"valid": True}
        except Exception as e:
            return {"valid": False, "error": str(e)}
