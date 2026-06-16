"""Tests for the memory retrieval eval harness."""

from genaiscope.evals.memory_eval import run_eval


def test_eval_keyword_mode() -> None:
    report = run_eval(modes=["keyword"], embedder_name="local", top_k=5)
    assert report.dataset_size > 0
    assert len(report.results) == 1
    r = report.results[0]
    assert r.mode == "keyword"
    assert 0.0 <= r.recall_at_k <= 1.0
    assert 0.0 <= r.precision_at_k <= 1.0
    assert 0.0 <= r.mrr <= 1.0


def test_eval_hybrid_mode() -> None:
    report = run_eval(modes=["hybrid"], embedder_name="local", top_k=5)
    assert len(report.results) == 1
    r = report.results[0]
    assert r.mode == "hybrid"
    assert 0.0 <= r.recall_at_k <= 1.0


def test_eval_both_modes() -> None:
    report = run_eval(modes=["keyword", "hybrid"], embedder_name="local", top_k=3)
    assert len(report.results) == 2
    modes = {r.mode for r in report.results}
    assert "keyword" in modes
    assert "hybrid" in modes


def test_eval_metrics_reasonable() -> None:
    """Hybrid should achieve non-zero recall on the built-in dataset."""
    report = run_eval(modes=["hybrid"], embedder_name="local", top_k=5)
    r = report.results[0]
    assert r.recall_at_k > 0.0, "Expected at least one relevant result retrieved"
