from genaiscope import GenAIScope

scope = GenAIScope(db_path=".genaiscope/examples_05.db")

scope.log_interaction(
    prompt="Explain feature velocity",
    response="Feature velocity means shipping customer value faster.",
    provider="openai",
    model="gpt-4.1",
    input_tokens=120,
    output_tokens=240,
    latency_ms=1800,
    category="cto_learning",
    tags=["metrics", "cto"],
)
scope.log_interaction(
    prompt="Write answer for this job",
    response="It depends.",
    provider="openai",
    model="gpt-4.1",
    input_tokens=50,
    output_tokens=20,
    latency_ms=900,
    category="cto_interview",
    tags=["traveltech"],
)

summary = scope.analytics.usage_summary(days=7)
print("Usage summary:", summary)

patterns = scope.analytics.prompt_patterns(days=30)
print("\nTop categories:", patterns.top_topics)
print("Repeated weak patterns:", patterns.repeated_weak_patterns)
print("Best prompt templates:", patterns.best_prompt_templates)
scope.close()
