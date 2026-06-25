from genaiscope import GenAIScope

scope = GenAIScope(db_path=".genaiscope/examples_04.db")

scope.memory.add(
    memory_type="profile_memory",
    content="Sapan is a CTO / VP Engineering leader with TravelTech experience.",
    tags=["profile", "cto", "traveltech"],
)

results = scope.memory.search("feature velocity", top_k=5)

report = scope.doctor.diagnose(
    prompt="Write answer for this job",
    response="Feature velocity is important. It depends on many factors.",
    memories_used=results,
    provider="openai",
    model="gpt-4.1",
)

print("Context health score:", report.context_health_score)
print("Detected intent:", report.detected_intent)
print("Missing context:", report.missing_context)
print("Prompt issues:", report.prompt_issues)
print("Recommended prompt:", report.recommended_prompt)
print("Improvement tips:", report.improvement_tips)
scope.close()
