"""Memory retrieval eval harness — recall@k, precision@k, MRR.

Works offline, no API keys or optional deps required (local_hash embedder).
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from genaiscope.evals.models import EvalDataset, EvalQuery, EvalReport, EvalSeed, ModeEvalResult

_SAMPLE_DATASET = EvalDataset(
    seeds=[
        EvalSeed(id="s1", content="User prefers concise CTO-level answers", memory_type="preference", importance=8, tags=["style"]),
        EvalSeed(id="s2", content="Sapan is building an AI memory toolkit called GenAIScope", memory_type="project", importance=9, tags=["project"]),
        EvalSeed(id="s3", content="Always respond in bullet points when listing features", memory_type="preference", tags=["style"]),
        EvalSeed(id="s4", content="Redis is the production memory backend for high-traffic apps", memory_type="general", tags=["redis"]),
        EvalSeed(id="s5", content="Use Python type hints and async functions wherever possible", memory_type="preference", tags=["coding"]),
        EvalSeed(id="s6", content="The user is based in India and prefers UTC+5:30 timezone", memory_type="general", tags=["user"]),
        EvalSeed(id="s7", content="Project deadline for v0.4.0 release is end of June", memory_type="project", importance=7, tags=["deadline"]),
        EvalSeed(id="s8", content="Avoid verbose prose — short paragraphs preferred", memory_type="preference", tags=["style"]),
    ],
    queries=[
        EvalQuery(query="how should I answer the user", expected_ids=["s1", "s3", "s8"]),
        EvalQuery(query="what is GenAIScope", expected_ids=["s2"]),
        EvalQuery(query="Redis backend usage", expected_ids=["s4"]),
        EvalQuery(query="Python coding style", expected_ids=["s5"]),
        EvalQuery(query="project deadline", expected_ids=["s7"]),
        EvalQuery(query="user timezone location", expected_ids=["s6"]),
    ],
)


def compute_metrics(
    results_per_query: list[list[str]],
    expected_per_query: list[list[str]],
    top_k: int,
) -> tuple[float, float, float]:
    """Return (recall@k, precision@k, MRR)."""
    recalls, precisions, reciprocals = [], [], []
    for retrieved, expected in zip(results_per_query, expected_per_query, strict=False):
        retrieved_k = retrieved[:top_k]
        expected_set = set(expected)
        hits = [r for r in retrieved_k if r in expected_set]
        recalls.append(len(hits) / len(expected_set) if expected_set else 0.0)
        precisions.append(len(hits) / top_k if top_k > 0 else 0.0)
        rr = 0.0
        for rank, r in enumerate(retrieved_k, start=1):
            if r in expected_set:
                rr = 1.0 / rank
                break
        reciprocals.append(rr)

    n = len(results_per_query) or 1
    return sum(recalls) / n, sum(precisions) / n, sum(reciprocals) / n


def run_eval(
    dataset: EvalDataset | None = None,
    modes: list[str] | None = None,
    embedder_name: str = "local",
    top_k: int = 5,
) -> EvalReport:
    """Run the retrieval eval harness."""

    from genaiscope.embeddings.factory import get_embedder
    from genaiscope.memory.factory import MemoryStore

    ds = dataset or _SAMPLE_DATASET
    modes_to_run = modes or ["keyword", "hybrid"]

    report = EvalReport(dataset_size=len(ds.seeds), top_k=top_k)

    try:
        embedder = get_embedder(embedder_name)
    except Exception:
        embedder = None

    for mode in modes_to_run:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "eval.db"

            if embedder and mode in ("vector", "hybrid"):
                from genaiscope.vector.local_vector import LocalVectorStore

                vs = LocalVectorStore(db_path=db_path.with_suffix(".vectors.db"))
                store = MemoryStore(db_path=db_path, embedder=embedder, vector_store=vs)
            else:
                store = MemoryStore(db_path=db_path)

            id_map: dict[str, str] = {}
            for seed in ds.seeds:
                item = store.add(
                    seed.content,
                    memory_type=seed.memory_type,
                    tags=seed.tags,
                    importance=seed.importance,
                )
                id_map[seed.id] = item.id

            results_per_query: list[list[str]] = []
            expected_per_query: list[list[str]] = []

            for eq in ds.queries:
                results = store.search(eq.query, limit=top_k, mode=mode)
                retrieved_ids = [r.item.id for r in results]
                results_per_query.append(retrieved_ids)
                expected_per_query.append([id_map.get(eid, eid) for eid in eq.expected_ids])

            store.close()

        recall, precision, mrr = compute_metrics(results_per_query, expected_per_query, top_k)
        report.results.append(
            ModeEvalResult(
                mode=mode,
                embedder=embedder.name if embedder else "none",
                recall_at_k=round(recall, 4),
                precision_at_k=round(precision, 4),
                mrr=round(mrr, 4),
                queries_evaluated=len(ds.queries),
                top_k=top_k,
            )
        )

    return report


def load_eval_dataset(path: Path) -> EvalDataset:
    data = json.loads(path.read_text())
    return EvalDataset.model_validate(data)
