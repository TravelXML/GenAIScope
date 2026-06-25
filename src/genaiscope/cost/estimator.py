"""CostEstimator -- provider-aware cost estimation.

Looks up a per-1K-token price from cost.pricing, then reuses
genaiscope.analyzers.CostAnalyzer for the actual cost arithmetic instead of
reimplementing it.
"""

from __future__ import annotations

from genaiscope.analyzers import CostAnalyzer
from genaiscope.cost.models import CostEstimate
from genaiscope.cost.pricing import lookup_price


class CostEstimator:
    """Estimate API cost for a provider/model/token-count combination."""

    def estimate(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> CostEstimate:
        price = lookup_price(provider, model)
        if price is None:
            return CostEstimate(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
                priced=False,
            )

        # Reuse CostAnalyzer's per-1K-token math against a single-entry table
        # scoped to this lookup. A fresh instance per call avoids sharing
        # mutable pricing state across concurrent/threaded callers.
        analyzer = CostAnalyzer()
        analyzer.pricing = {model: price}
        result = analyzer.estimate_cost(model, input_tokens, output_tokens)

        return CostEstimate(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=result["input_cost"],
            output_cost=result["output_cost"],
            total_cost=result["total_cost"],
            priced=True,
        )
