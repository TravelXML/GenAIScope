"""Seeds a small, realistic local dataset and regenerates the committed dashboard sample.

Run this from the repo root to reproduce examples/dashboard_sample/dashboard.html:

    python examples/dashboard_sample/populate_demo_data.py

It writes a throwaway db to examples/dashboard_sample/demo.db (gitignored) and the
static dashboard HTML to examples/dashboard_sample/dashboard.html (committed, so the
dashboard is browsable straight from the repo without running anything).
"""

from pathlib import Path

from genaiscope import GenAIScope
from genaiscope.dashboard import generate_dashboard
from genaiscope.files import FileMemory
from genaiscope.memory import MemoryStore

SAMPLE_DIR = Path(__file__).parent
DB_PATH = SAMPLE_DIR / "demo.db"
OUTPUT_PATH = SAMPLE_DIR / "dashboard.html"

DB_PATH.unlink(missing_ok=True)

scope = GenAIScope(db_path=str(DB_PATH))

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
scope.memory.add(
    memory_type="preference",
    content="User prefers concise, senior-level answers with concrete business impact.",
    tags=["preference", "style"],
)
# scope.memory is a thin add()-only wrapper -- add_prompt() lives on the raw MemoryStore.
raw_memory = MemoryStore(db_path=str(DB_PATH))
raw_memory.add_prompt("Summarize this properly.")
raw_memory.add_prompt("Write answer for feature velocity.")

sample_doc = SAMPLE_DIR / "sample_policy.md"
sample_doc.write_text(
    "# Refund Policy\n\nCustomers may request refunds within 30 days of purchase, "
    "subject to supplier cancellation rules and payment status.\n",
    encoding="utf-8",
)
files = FileMemory(db_path=str(DB_PATH))
files.add_file(str(sample_doc))
sample_doc.unlink()

interactions = [
    dict(provider="openai", model="gpt-4o-mini", category="support", tags=["refund"],
         prompt="Summarize the refund policy.", response="Refunds are available within 30 days.",
         input_tokens=42, output_tokens=18, estimated_cost=0.0009),
    dict(provider="anthropic", model="claude-sonnet-5", category="cto_interview", tags=["traveltech", "feature-velocity"],
         prompt="Write answer for feature velocity.",
         response="Feature velocity is how fast a team ships value, tied to roadmap execution and business impact.",
         input_tokens=64, output_tokens=51, estimated_cost=0.0031),
    dict(provider="google", model="gemini-2.0-flash", category="analysis", tags=["cost"],
         prompt="Estimate the cost of this feature.", response="Estimated cost: $1,200/month at current usage.",
         input_tokens=30, output_tokens=22, estimated_cost=0.0004),
]

for interaction in interactions:
    with scope.trace(
        provider=interaction["provider"],
        model=interaction["model"],
        category=interaction["category"],
        tags=interaction["tags"],
    ) as trace:
        trace.log(prompt=interaction["prompt"], response=interaction["response"])
        trace.log_tokens(interaction["input_tokens"], interaction["output_tokens"])
        trace.log_cost(interaction["estimated_cost"])

scope.close()

path = generate_dashboard(output_path=str(OUTPUT_PATH), db_path=str(DB_PATH))
print("Dashboard written to:", path)
