"""Agent trajectory eval harness — step pass/fail, latency, optional trace logging.

Library API only, no CLI command: `agent_fn` is a Python callable and can't be
expressed as a CLI flag the way a JSON eval dataset can (see `eval_memory`).
Works offline, no API keys or optional deps required.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from genaiscope.evals.models import AgentEvalReport, AgentStepResult, AgentTrajectory

if TYPE_CHECKING:
    from genaiscope.tracing import LocalTracer


def run_agent_eval(
    trajectory: AgentTrajectory,
    agent_fn: Callable[[str, dict[str, Any]], Any],
    tracer: LocalTracer | None = None,
) -> AgentEvalReport:
    """Run `agent_fn(step.name, step.args)` for each step of `trajectory` in
    order, checking `expected_output` containment when provided. If `tracer`
    is given, each step is logged with a shared `metadata["task_id"]` so the
    whole trajectory can be correlated -- no schema change, same convention
    v0.6.0 used for category/tags/session_id."""

    task_id = str(uuid4())
    step_results: list[AgentStepResult] = []
    total_latency_ms = 0.0

    for index, step in enumerate(trajectory.steps):
        start = time.perf_counter()
        error: str | None = None
        actual_output = ""
        passed = True
        try:
            output = agent_fn(step.name, step.args)
            actual_output = "" if output is None else str(output)
            if step.expected_output is not None:
                passed = step.expected_output in actual_output
        except Exception as exc:  # a failing step must not abort the rest of the trajectory
            passed = False
            error = str(exc)

        latency_ms = (time.perf_counter() - start) * 1000
        total_latency_ms += latency_ms

        step_results.append(
            AgentStepResult(
                name=step.name, passed=passed, actual_output=actual_output,
                latency_ms=round(latency_ms, 3), error=error,
            )
        )

        if tracer is not None:
            tracer.log(
                name=step.name,
                input_text=str(step.args) or None,
                output_text=actual_output or None,
                latency_ms=latency_ms,
                status="success" if passed else "error",
                error=error,
                metadata={"task": trajectory.task, "task_id": task_id, "step_index": index},
            )

    steps_total = len(step_results)
    steps_passed = sum(1 for r in step_results if r.passed)

    return AgentEvalReport(
        task=trajectory.task,
        task_id=task_id,
        steps_total=steps_total,
        steps_passed=steps_passed,
        step_completion_rate=round(steps_passed / steps_total, 4) if steps_total else 0.0,
        total_latency_ms=round(total_latency_ms, 3),
        step_results=step_results,
    )
