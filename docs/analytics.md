# Usage Analytics & Prompt Patterns

`genaiscope.analytics` summarizes token/cost/latency usage and repeated prompt patterns over
traces recorded via `GenAIScope.trace()` / `log_interaction()`.

## Usage summary

```python
summary = scope.analytics.usage_summary(days=7)

summary.total_requests
summary.total_input_tokens
summary.total_output_tokens
summary.total_tokens
summary.total_estimated_cost
summary.average_latency_ms
summary.cost_by_provider     # {"openai": 0.012, ...}
summary.cost_by_model        # {"gpt-4.1": 0.012, ...}
summary.tokens_by_category   # {"cto_interview": 360, ...}
```

## Prompt patterns

```python
patterns = scope.analytics.prompt_patterns(days=30)

patterns.top_topics                       # most common categories
patterns.repeated_weak_patterns           # e.g. "Prompts missing: Target audience"
patterns.best_prompt_templates            # categories with consistently high health scores
patterns.most_used_entities
patterns.most_used_tags
patterns.most_frequent_categories
patterns.average_health_score_by_category
patterns.token_usage_by_category
patterns.model_performance_by_category
```

`prompt_patterns()` reads the `category`, `tags`, `context_health_score`, `missing_context`,
and `detected_entities` keys that `GenAIScope.trace()`/`log_interaction()` write into each
trace's `metadata` (see [context-doctor.md](context-doctor.md)) — there is no separate
pattern-storage table.

## CLI

```bash
genaiscope analytics --days 7 --pattern-days 30
```

## Design note

Aggregation happens in Python over `tracer.list()` results, not via SQL `GROUP BY`. This is a
deliberate trade-off for a local, single-developer tool: it avoids any database schema/migration
work, at the cost of being less efficient at very large trace volumes than a real analytics
warehouse would be.
