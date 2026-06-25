from genaiscope import GenAIScope

scope = GenAIScope(db_path=".genaiscope/examples_06.db")

scope.memory.add(memory_type="profile_memory", content="Sapan is a CTO / VP Engineering leader.", tags=["profile"])
scope.log_interaction(
    prompt="Explain feature velocity",
    response="Feature velocity means shipping customer value faster.",
    provider="openai",
    model="gpt-4.1",
    input_tokens=120,
    output_tokens=240,
    category="cto_learning",
)

report_path = scope.report.generate_html(".genaiscope/reports/examples_06_report.html")
print("Report generated at:", report_path)
scope.close()
