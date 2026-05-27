"""Core inspection modules."""

from genaiscope.core.models import EvaluationResult


class PromptInspector:
    """Inspector for prompts."""

    def inspect(self, prompt: str) -> list[EvaluationResult]:
        """Inspect a prompt."""
        results = []

        # Check if prompt is too short
        if len(prompt.strip()) < 10:
            results.append(
                EvaluationResult(
                    score=0.3,
                    label="warn",
                    reasoning="Prompt is very short and may lack context",
                )
            )

        # Check for common issues
        if "???" in prompt:
            results.append(
                EvaluationResult(
                    score=0.5,
                    label="warn",
                    reasoning="Prompt contains unclear placeholders",
                )
            )

        # Positive evaluation
        results.append(
            EvaluationResult(
                score=0.8,
                label="pass",
                reasoning="Prompt structure looks reasonable",
            )
        )

        return results


class RAGInspector:
    """Inspector for RAG systems."""

    def inspect(self, query: str, context: str, response: str) -> list[EvaluationResult]:
        """Inspect RAG output."""
        results = []

        # Check if context is being used
        context_words = set(context.lower().split())
        response_words = set(response.lower().split())
        overlap = len(context_words & response_words) / max(1, len(context_words))

        results.append(
            EvaluationResult(
                score=overlap,
                label="pass" if overlap > 0.2 else "fail",
                reasoning=f"Context usage ratio: {overlap:.2f}",
            )
        )

        # Check if context is empty
        if not context or len(context.strip()) == 0:
            results.append(
                EvaluationResult(
                    score=0.0,
                    label="fail",
                    reasoning="No context provided for RAG",
                )
            )

        return results


class OutputInspector:
    """Inspector for model outputs."""

    def inspect(self, output: str, expected_format: str | None = None) -> list[EvaluationResult]:
        """Inspect model output."""
        results = []

        # Check for empty output
        if not output or len(output.strip()) == 0:
            results.append(
                EvaluationResult(
                    score=0.0,
                    label="fail",
                    reasoning="Output is empty",
                )
            )
        else:
            results.append(
                EvaluationResult(
                    score=1.0,
                    label="pass",
                    reasoning="Output is not empty",
                )
            )

        # Check for format if specified
        if expected_format:
            if self._matches_format(output, expected_format):
                results.append(
                    EvaluationResult(
                        score=1.0,
                        label="pass",
                        reasoning=f"Output matches {expected_format} format",
                    )
                )
            else:
                results.append(
                    EvaluationResult(
                        score=0.5,
                        label="warn",
                        reasoning=f"Output may not match {expected_format} format",
                    )
                )

        return results

    @staticmethod
    def _matches_format(output: str, expected_format: str) -> bool:
        """Check if output matches expected format."""
        if expected_format.lower() == "json":
            try:
                import json

                json.loads(output)
                return True
            except (ValueError, TypeError):
                return False
        elif expected_format.lower() == "xml":
            return output.strip().startswith("<") and output.strip().endswith(">")
        elif expected_format.lower() == "csv":
            return "," in output
        return True
