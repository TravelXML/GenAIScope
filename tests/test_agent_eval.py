"""Tests for the agent-trajectory eval harness — pure Python, no external deps."""

from pathlib import Path

from genaiscope.evals import AgentStep, AgentTrajectory, run_agent_eval
from genaiscope.tracing import LocalTracer


def _fake_agent(name: str, args: dict) -> str:
    if name == "search":
        return f"found: {args.get('query', '')}"
    if name == "boom":
        raise RuntimeError("tool crashed")
    return "ok"


def test_run_agent_eval_all_steps_pass() -> None:
    trajectory = AgentTrajectory(
        task="look something up",
        steps=[
            AgentStep(name="search", args={"query": "GenAIScope"}, expected_output="GenAIScope"),
            AgentStep(name="finish", args={}),
        ],
    )
    report = run_agent_eval(trajectory, _fake_agent)

    assert report.task == "look something up"
    assert report.steps_total == 2
    assert report.steps_passed == 2
    assert report.step_completion_rate == 1.0
    assert report.step_results[0].actual_output == "found: GenAIScope"


def test_run_agent_eval_records_expected_output_mismatch() -> None:
    trajectory = AgentTrajectory(
        task="look something up",
        steps=[AgentStep(name="search", args={"query": "x"}, expected_output="nope")],
    )
    report = run_agent_eval(trajectory, _fake_agent)

    assert report.steps_passed == 0
    assert report.step_completion_rate == 0.0
    assert report.step_results[0].passed is False


def test_run_agent_eval_records_step_error_without_aborting_trajectory() -> None:
    trajectory = AgentTrajectory(
        task="resilience check",
        steps=[AgentStep(name="boom", args={}), AgentStep(name="finish", args={})],
    )
    report = run_agent_eval(trajectory, _fake_agent)

    assert report.steps_total == 2
    assert report.steps_passed == 1
    assert report.step_results[0].passed is False
    assert "tool crashed" in (report.step_results[0].error or "")
    assert report.step_results[1].passed is True


def test_run_agent_eval_logs_steps_with_shared_task_id(tmp_path: Path) -> None:
    tracer = LocalTracer(db_path=tmp_path / "t.db")
    trajectory = AgentTrajectory(
        task="multi-step",
        steps=[AgentStep(name="search", args={"query": "a"}), AgentStep(name="finish", args={})],
    )

    report = run_agent_eval(trajectory, _fake_agent, tracer=tracer)

    traces = tracer.list()
    assert len(traces) == 2
    task_ids = {t.metadata.get("task_id") for t in traces}
    assert task_ids == {report.task_id}
    assert {t.metadata.get("step_index") for t in traces} == {0, 1}
    tracer.close()
