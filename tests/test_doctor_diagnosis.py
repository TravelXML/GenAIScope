"""Tests for ContextDoctor.diagnose() -- the v0.6.0 health report."""

from genaiscope.doctor import ContextDoctor


def test_diagnose_returns_full_report_shape() -> None:
    report = ContextDoctor().diagnose(prompt="Write answer for this job.", response="It depends.")

    assert 0 <= report.context_health_score <= 100
    assert 0 <= report.prompt_clarity_score <= 100
    assert isinstance(report.missing_context, list)
    assert isinstance(report.detected_entities, list)
    assert isinstance(report.prompt_issues, list)
    assert isinstance(report.improvement_tips, list)
    assert report.recommended_prompt
    assert report.recommended_model_type
    assert report.detected_intent


def test_diagnose_detects_job_application_intent() -> None:
    report = ContextDoctor().diagnose(prompt="Write an answer for this job application.")
    assert report.detected_intent == "job_application_answer"


def test_diagnose_flags_missing_context_on_vague_prompt() -> None:
    report = ContextDoctor().diagnose(prompt="Write answer for feature velocity.")
    assert "Target audience" in report.missing_context
    assert "Desired answer length or format" in report.missing_context


def test_diagnose_uses_memories_used_for_memory_match_score() -> None:
    memories = [{"id": "m1", "content": "Sapan is a CTO.", "memory_type": "profile_memory", "tags": ["cto"], "score": 0.9}]
    report = ContextDoctor().diagnose(prompt="Write answer for feature velocity.", memories_used=memories)
    assert report.memory_match_score > 0
    assert "background" in report.recommended_prompt.lower()


def test_diagnose_accepts_memory_search_result_objects(tmp_path) -> None:
    from genaiscope.memory import MemoryStore

    store = MemoryStore(db_path=tmp_path / "m.db")
    store.add("Sapan is a CTO / VP Engineering leader with TravelTech experience.", memory_type="profile_memory", tags=["cto"])
    results = store.search("CTO", limit=5)

    report = ContextDoctor().diagnose(prompt="Write answer for feature velocity.", memories_used=results)
    assert report.memory_match_score >= 0
    store.close()


def test_diagnose_well_specified_prompt_scores_higher_than_vague_one() -> None:
    doctor = ContextDoctor()
    vague = doctor.diagnose(prompt="Write answer for this job.")
    specific = doctor.diagnose(
        prompt=(
            "For a CTO interview panel, write a concise 150-word, senior-toned answer explaining "
            "feature velocity and its connection to business impact."
        )
    )
    assert specific.context_health_score > vague.context_health_score
