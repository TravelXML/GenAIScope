from genaiscope import GenAIScope

scope = GenAIScope(db_path=".genaiscope/examples_02.db")

scope.memory.add(
    memory_type="profile_memory",
    title="User profile",
    content="Sapan is a CTO / VP Engineering leader with TravelTech experience.",
    tags=["profile", "cto", "traveltech"],
    confidence=0.95,
    importance_score=0.9,
)
scope.memory.add(
    memory_type="project_memory",
    title="TravelTech rebuild",
    content="Led the TravelTech platform rebuild focused on feature velocity and roadmap execution.",
    tags=["traveltech", "project"],
    importance_score=0.8,
)

results = scope.memory.search("CTO interview feature velocity", top_k=5)
for result in results:
    print(f"[{result.score:.2f}] {result.item.memory_type}: {result.item.content}")

if results:
    scope.memory.forget(results[0].item.id)
scope.close()
