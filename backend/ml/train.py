"""Training entrypoint for the IPC -> BNS TF-IDF ranking model.

Loads ``data/ipc_bns_mapping.json``, auto-generates a labelled evaluation
set from the records themselves (each record's IPC code, BNS code, and
every keyword must retrieve that record), fits
:class:`backend.ml.ranking_model.MLRankingModel`, prints the metrics,
persists the joblib artifact, and renders a matplotlib bar chart of
per-query-type top-1 accuracy (code queries vs keyword queries).

Run from the repository root:

    python -m backend.ml.train
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")  # headless backend; must precede pyplot import
import matplotlib.pyplot as plt  # noqa: E402

from backend.ml.ranking_model import MLRankingModel  # noqa: E402

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
DATA_PATH: Path = REPO_ROOT / "data" / "ipc_bns_mapping.json"
ARTIFACT_PATH: Path = REPO_ROOT / "backend" / "ml" / "artifacts" / "ranker.joblib"
PLOT_PATH: Path = REPO_ROOT / "docs" / "ml_evaluation.png"

#: Labelled query pair: (query text, expected record id).
EvalPair = tuple[str, str]


def load_records(path: Path = DATA_PATH) -> list[dict[str, Any]]:
    """Load mapping records from the JSON dataset.

    Tolerates either a top-level JSON list or an object wrapping the list
    (e.g. ``{"mappings": [...]}``).

    Raises:
        FileNotFoundError: If ``path`` does not exist.
        ValueError: If no records can be found in the file.
    """
    if not path.exists():
        raise FileNotFoundError(f"Mapping dataset not found: {path}")
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        for value in raw.values():
            if isinstance(value, list):
                raw = value
                break
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"No mapping records found in {path}")
    return raw


def build_eval_sets(
    records: list[dict[str, Any]],
) -> tuple[list[EvalPair], list[EvalPair]]:
    """Derive labelled evaluation queries from the records themselves.

    For every record, its ``ipc_code`` and ``bns_code`` become "code"
    queries and each keyword becomes a "keyword" query, all expecting that
    record's id.

    Returns:
        ``(code_queries, keyword_queries)``.

    Raises:
        ValueError: If no queries can be derived at all.
    """
    code_queries: list[EvalPair] = []
    keyword_queries: list[EvalPair] = []
    for record in records:
        record_id = str(record.get("id") or "").strip()
        if not record_id:
            continue
        for code_field in ("ipc_code", "bns_code"):
            code = str(record.get(code_field) or "").strip()
            if code:
                code_queries.append((code, record_id))
        keywords = record.get("keywords") or []
        if isinstance(keywords, (list, tuple)):
            for keyword in keywords:
                text = str(keyword).strip()
                if text:
                    keyword_queries.append((text, record_id))
    if not code_queries and not keyword_queries:
        raise ValueError("Could not derive any evaluation queries from the records.")
    return code_queries, keyword_queries


def plot_accuracy_by_query_type(
    code_metrics: dict[str, float | int],
    keyword_metrics: dict[str, float | int],
    path: Path = PLOT_PATH,
) -> Path:
    """Save a bar chart of top-1 accuracy per query type to ``path``."""
    labels = [
        f"Code queries\n(n={code_metrics['n_queries']})",
        f"Keyword queries\n(n={keyword_metrics['n_queries']})",
    ]
    accuracies = [
        float(code_metrics["top1_accuracy"]),
        float(keyword_metrics["top1_accuracy"]),
    ]
    mrrs = [float(code_metrics["mrr"]), float(keyword_metrics["mrr"])]

    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    positions = range(len(labels))
    bars = ax.bar(
        positions, accuracies, width=0.5,
        color=["#3b6ea5", "#5a9e6f"], edgecolor="#222222",
    )
    for bar, accuracy, mrr in zip(bars, accuracies, mrrs):
        ax.annotate(
            f"acc={accuracy:.3f}\nmrr={mrr:.3f}",
            xy=(bar.get_x() + bar.get_width() / 2.0, bar.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels)
    ax.set_ylim(0.0, 1.15)
    ax.set_ylabel("Top-1 accuracy")
    ax.set_title("IPC->BNS TF-IDF ranker: top-1 accuracy by query type")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()

    os.makedirs(path.parent, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    """Fit, evaluate, persist the ranker, and render the evaluation chart."""
    print(f"Loading records from {DATA_PATH} ...")
    records = load_records()
    print(f"Loaded {len(records)} mapping records.")

    model = MLRankingModel().fit(records)

    code_queries, keyword_queries = build_eval_sets(records)
    all_queries = code_queries + keyword_queries

    overall = model.evaluate(all_queries)
    code_metrics = model.evaluate(code_queries)
    keyword_metrics = model.evaluate(keyword_queries)

    print(f"Evaluation queries        : {overall['n_queries']}")
    print(f"Overall top-1 accuracy    : {overall['top1_accuracy']:.4f}")
    print(f"Overall MRR               : {overall['mrr']:.4f}")
    print(
        f"Code queries   (n={code_metrics['n_queries']}): "
        f"acc={code_metrics['top1_accuracy']:.4f} mrr={code_metrics['mrr']:.4f}"
    )
    print(
        f"Keyword queries(n={keyword_metrics['n_queries']}): "
        f"acc={keyword_metrics['top1_accuracy']:.4f} mrr={keyword_metrics['mrr']:.4f}"
    )

    os.makedirs(ARTIFACT_PATH.parent, exist_ok=True)
    model.save(ARTIFACT_PATH)
    print(f"Saved model artifact to {ARTIFACT_PATH}")

    plot_path = plot_accuracy_by_query_type(code_metrics, keyword_metrics)
    print(f"Saved evaluation chart to {plot_path}")


if __name__ == "__main__":
    main()
