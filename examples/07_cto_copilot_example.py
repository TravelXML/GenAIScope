"""End-to-end Context Doctor walkthrough: a CTO's personal AI copilot.

Seeds profile + project memory, asks a deliberately weak prompt, builds
improved context from memory, logs the interaction, diagnoses it, and
generates an HTML report -- all locally, no API keys required.
"""

from genaiscope import GenAIScope
from genaiscope.embeddings import LocalHashEmbedder
from genaiscope.vector import LocalVectorStore

embedder = LocalHashEmbedder()
vector_store = LocalVectorStore(db_path=".genaiscope/examples_07_vectors.db")
scope = GenAIScope(db_path=".genaiscope/examples_07.db", embedder=embedder, vector_store=vector_store)

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
    title="TravelTech project",
    content="Led the TravelTech platform rebuild focused on feature velocity, roadmap execution, and customer impact.",
    tags=["traveltech", "project"],
    importance_score=0.85,
)

weak_prompt = "Write answer for feature velocity."
print("Weak prompt:", weak_prompt)

context = scope.context.build(weak_prompt, top_k=5)
print("\nRetrieved memories:", [m["memory_type"] for m in context.retrieved_memories])
print("\nImproved prompt:\n", context.improved_prompt)

response = "Feature velocity is how fast a team ships value. It depends on many factors."

with scope.trace(provider="openai", model="gpt-4.1", category="cto_interview", tags=["traveltech", "feature-velocity"]) as trace:
    trace.log(prompt=weak_prompt, response=response)

report = scope.doctor.diagnose(
    prompt=weak_prompt,
    response=response,
    memories_used=context.retrieved_memories,
    provider="openai",
    model="gpt-4.1",
)

print("\n=== Context Doctor Report ===")
print("Context health score:", report.context_health_score, "/100")
print("Missing context:", report.missing_context)
print("Prompt issues:", report.prompt_issues)
print("\nRecommended prompt:\n", report.recommended_prompt)
print("\nImprovement tips:", report.improvement_tips)

report_path = scope.report.generate_html(".genaiscope/reports/cto_copilot_report.html")
print("\nHTML report generated at:", report_path)

scope.close()
