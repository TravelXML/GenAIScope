"""Tests for prompt quality coach."""

from genaiscope.memory import MemoryStore, analyze_prompt_quality


def test_prompt_quality_scores_weak_and_strong_prompts(tmp_path):
    weak = analyze_prompt_quality("Summarize this properly.")
    strong = analyze_prompt_quality(
        "You are an expert technical editor. Summarize the following text for executives "
        "in markdown bullets, under 120 words, cite uncertainty, avoid adding facts, and "
        "succeed when each bullet is actionable and concise."
    )

    assert weak.score < 60
    assert weak.risk_level == "high"
    assert "vague_wording" in weak.detected_issues
    assert strong.score > weak.score

    store = MemoryStore(db_path=tmp_path / "memory.db")
    item = store.add_prompt("Summarize this properly.")
    assert item.prompt_score == weak.score
    assert item.prompt_comments
    store.close()
