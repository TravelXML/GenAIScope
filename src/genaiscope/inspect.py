"""Main inspection module."""

import uuid
from datetime import datetime
from typing import Any

from genaiscope.core.core_inspect import OutputInspector, PromptInspector, RAGInspector
from genaiscope.core.logging import get_logger
from genaiscope.core.models import InspectionReport

logger = get_logger(__name__)


class Inspector:
    """Main inspector for GenAI applications."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize inspector."""
        self.config = kwargs
        self.prompt_inspector = PromptInspector()
        self.rag_inspector = RAGInspector()
        self.output_inspector = OutputInspector()

    def inspect_prompt(self, prompt: str, **kwargs: Any) -> InspectionReport:
        """Inspect a prompt for quality and safety."""
        logger.info(f"Inspecting prompt: {prompt[:50]}...")

        report = InspectionReport(
            id=str(uuid.uuid4()),
            title="Prompt Inspection",
            description="Analysis of prompt quality and potential issues",
            input_text=prompt,
            timestamp=datetime.utcnow(),
        )

        # Run inspections
        report.evaluations.extend(self.prompt_inspector.inspect(prompt))

        # Add metrics
        report.metrics.update(self._calculate_prompt_metrics(prompt))

        return report

    def inspect_rag(
        self, query: str, context: str, response: str, **kwargs: Any
    ) -> InspectionReport:
        """Inspect RAG system quality."""
        logger.info("Inspecting RAG system...")

        report = InspectionReport(
            id=str(uuid.uuid4()),
            title="RAG Inspection",
            description="Analysis of RAG system quality and context relevance",
            input_text=f"Query: {query}\nContext: {context}",
            output_text=response,
            timestamp=datetime.utcnow(),
        )

        # Run RAG inspections
        report.evaluations.extend(self.rag_inspector.inspect(query, context, response))

        # Add metrics
        report.metrics.update(self._calculate_rag_metrics(query, context, response))

        return report

    def inspect_output(
        self, output: str, expected_format: str | None = None, **kwargs: Any
    ) -> InspectionReport:
        """Inspect model output for structured format and safety."""
        logger.info("Inspecting output...")

        report = InspectionReport(
            id=str(uuid.uuid4()),
            title="Output Inspection",
            description="Analysis of output format, safety, and completeness",
            output_text=output,
            timestamp=datetime.utcnow(),
        )

        # Run output inspections
        report.evaluations.extend(
            self.output_inspector.inspect(output, expected_format=expected_format)
        )

        # Add metrics
        report.metrics.update(self._calculate_output_metrics(output))

        return report

    @staticmethod
    def _calculate_prompt_metrics(prompt: str) -> dict[str, float]:
        """Calculate prompt quality metrics."""
        return {
            "length": len(prompt),
            "word_count": len(prompt.split()),
            "avg_word_length": sum(len(w) for w in prompt.split()) / max(1, len(prompt.split())),
        }

    @staticmethod
    def _calculate_rag_metrics(query: str, context: str, response: str) -> dict[str, float]:
        """Calculate RAG metrics."""
        return {
            "query_length": len(query),
            "context_length": len(context),
            "response_length": len(response),
        }

    @staticmethod
    def _calculate_output_metrics(output: str) -> dict[str, float]:
        """Calculate output metrics."""
        return {
            "length": len(output),
            "word_count": len(output.split()),
        }
