from genaiscope import GenAIScope

scope = GenAIScope(db_path=".genaiscope/examples_03.db")

scope.memory.add(
    memory_type="profile_memory",
    content="Sapan is a CTO / VP Engineering leader with TravelTech experience.",
    tags=["profile", "cto", "traveltech"],
)
scope.memory.add(
    memory_type="project_memory",
    content="Led the TravelTech platform rebuild focused on feature velocity and roadmap execution.",
    tags=["traveltech", "project"],
)

context = scope.context.build(
    user_prompt="Write answer for CTO interview question about feature velocity",
    top_k=5,
    include_profile=True,
    include_projects=True,
    include_preferences=True,
)

print("Context text:\n", context.context_text)
print("\nImproved prompt:\n", context.improved_prompt)
print("\nContext quality score:", context.context_quality_score)
scope.close()
