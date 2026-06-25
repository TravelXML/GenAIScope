from genaiscope import GenAIScope

scope = GenAIScope(db_path=".genaiscope/examples_01.db")

with scope.trace(provider="openai", model="gpt-4.1", category="cto_interview", tags=["prompt-diagnosis", "traveltech"]) as trace:
    response = "Feature velocity measures how fast a team ships customer value."
    trace.log(prompt="Explain feature velocity", response=response)

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

print(scope.analytics.usage_summary(days=1))
scope.close()
