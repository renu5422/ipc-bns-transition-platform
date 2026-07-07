# TARGET PATH IN REPO: tests/test_ml_ranking.py
"""Tests for the Week 9 TF-IDF ranking model and its API router.

Self-contained and deterministic: models are fitted on an inline
3-record dataset, no dataset files or trained artifacts are required.
API tests run against the real ``backend.main`` app with the
``get_ranker`` dependency overridden.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("sklearn")

import pandas as pd  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.api.ml import get_ranker  # noqa: E402
from backend.main import app  # noqa: E402
from backend.ml.ranking_model import MLRankingModel, build_corpus_df  # noqa: E402

MURDER_ID = "ipc-302-bns-101"
THEFT_ID = "ipc-378-bns-303"
CHEATING_ID = "ipc-420-bns-318"


def make_records() -> list[dict[str, Any]]:
    """Three distinct inline mapping records (murder / theft / cheating)."""
    return [
        {
            "id": MURDER_ID,
            "ipc_code": "IPC-302",
            "ipc_title": "Murder",
            "bns_code": "BNS-101",
            "bns_title": "Homicide",
            "description": "Punishment for murder under the new code.",
            "chapter": "Offences Affecting the Human Body",
            "keywords": ["murder", "homicide", "killing"],
            "ai_summary": "Maps IPC murder provisions to BNS homicide.",
            "validation_rules": [],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        {
            "id": THEFT_ID,
            "ipc_code": "IPC-378",
            "ipc_title": "Theft",
            "bns_code": "BNS-303",
            "bns_title": "Theft",
            "description": "Dishonest taking of movable property.",
            "chapter": "Offences Against Property",
            "keywords": ["theft", "stealing", "larceny"],
            "ai_summary": "Maps IPC theft provisions to BNS theft.",
            "validation_rules": [],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
        {
            "id": CHEATING_ID,
            "ipc_code": "IPC-420",
            "ipc_title": "Cheating",
            "bns_code": "BNS-318",
            "bns_title": "Cheating",
            "description": "Deceiving a person to deliver property dishonestly.",
            "chapter": "Offences Against Property",
            "keywords": ["cheating", "fraud", "deception"],
            "ai_summary": "Maps IPC cheating provisions to BNS cheating and fraud.",
            "validation_rules": [],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
    ]


@pytest.fixture()
def records() -> list[dict[str, Any]]:
    return make_records()


@pytest.fixture()
def fitted_model(records: list[dict[str, Any]]) -> MLRankingModel:
    return MLRankingModel().fit(records)


@pytest.fixture()
def api_client(fitted_model: MLRankingModel) -> Iterator[TestClient]:
    """TestClient on the real app with the ranker dependency overridden."""
    app.dependency_overrides[get_ranker] = lambda: fitted_model
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_ranker, None)


# ----------------------------------------------------------------------
# Corpus construction (pandas)
# ----------------------------------------------------------------------


def test_build_corpus_df_shape_and_columns(records: list[dict[str, Any]]) -> None:
    df = build_corpus_df(records)
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["id", "text"]
    assert len(df) == len(records)
    assert df["id"].tolist() == [MURDER_ID, THEFT_ID, CHEATING_ID]
    # Text is lowercased and contains codes, titles, and keywords.
    murder_text = df.loc[df["id"] == MURDER_ID, "text"].iloc[0]
    assert murder_text == murder_text.lower()
    for token in ("ipc-302", "bns-101", "murder", "homicide", "killing"):
        assert token in murder_text


def test_build_corpus_df_empty_input() -> None:
    df = build_corpus_df([])
    assert list(df.columns) == ["id", "text"]
    assert len(df) == 0


# ----------------------------------------------------------------------
# Model behaviour
# ----------------------------------------------------------------------


def test_rank_keyword_query_returns_murder_record_first(
    fitted_model: MLRankingModel,
) -> None:
    results = fitted_model.rank("murder")
    assert results, "expected at least one result for 'murder'"
    top = results[0]
    assert top["id"] == MURDER_ID
    assert top["record"]["bns_title"] == "Homicide"
    assert isinstance(top["ml_score"], float)
    assert top["ml_score"] > 0.0
    assert top["ml_score"] == round(top["ml_score"], 4)


def test_rank_exact_code_query_ranks_its_record_first(
    fitted_model: MLRankingModel,
) -> None:
    for query, expected_id in (
        ("IPC-302", MURDER_ID),
        ("BNS-303", THEFT_ID),
        ("ipc-420", CHEATING_ID),
    ):
        results = fitted_model.rank(query)
        assert results, f"expected results for code query {query!r}"
        assert results[0]["id"] == expected_id


def test_rank_scores_sorted_descending_and_top_k_respected(
    fitted_model: MLRankingModel,
) -> None:
    results = fitted_model.rank("property offences", top_k=2)
    assert len(results) <= 2
    scores = [result["ml_score"] for result in results]
    assert scores == sorted(scores, reverse=True)


def test_rank_unknown_gibberish_returns_empty_list(
    fitted_model: MLRankingModel,
) -> None:
    assert fitted_model.rank("zzqx wvvqx flibbertigibbet") == []


def test_rank_blank_query_raises_value_error(fitted_model: MLRankingModel) -> None:
    with pytest.raises(ValueError):
        fitted_model.rank("   ")


def test_rank_before_fit_raises_runtime_error() -> None:
    with pytest.raises(RuntimeError):
        MLRankingModel().rank("murder")


def test_fit_empty_records_raises_value_error() -> None:
    with pytest.raises(ValueError):
        MLRankingModel().fit([])


# ----------------------------------------------------------------------
# Persistence (joblib round-trip)
# ----------------------------------------------------------------------


def test_save_load_roundtrip_preserves_ranking(
    tmp_path: Path, fitted_model: MLRankingModel
) -> None:
    artifact = tmp_path / "ranker.joblib"
    fitted_model.save(artifact)
    assert artifact.exists()

    loaded = MLRankingModel.load(artifact)
    for query in ("murder", "stealing", "fraud", "IPC-302"):
        original = fitted_model.rank(query, top_k=3)
        restored = loaded.rank(query, top_k=3)
        assert [r["id"] for r in restored] == [r["id"] for r in original]
        for restored_hit, original_hit in zip(restored, original):
            assert restored_hit["ml_score"] == pytest.approx(original_hit["ml_score"])


def test_load_missing_artifact_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        MLRankingModel.load(tmp_path / "does_not_exist.joblib")


# ----------------------------------------------------------------------
# Evaluation (numpy metrics)
# ----------------------------------------------------------------------


def test_evaluate_perfect_on_training_vocabulary_queries(
    fitted_model: MLRankingModel, records: list[dict[str, Any]]
) -> None:
    queries: list[tuple[str, str]] = []
    for record in records:
        queries.append((record["ipc_code"], record["id"]))
        queries.append((record["bns_code"], record["id"]))
        queries.extend((keyword, record["id"]) for keyword in record["keywords"])

    metrics = fitted_model.evaluate(queries)
    assert metrics["n_queries"] == len(queries)
    assert metrics["top1_accuracy"] == pytest.approx(1.0)
    assert metrics["mrr"] == pytest.approx(1.0)


def test_evaluate_empty_queries_returns_zeroed_metrics(
    fitted_model: MLRankingModel,
) -> None:
    metrics = fitted_model.evaluate([])
    assert metrics == {"top1_accuracy": 0.0, "mrr": 0.0, "n_queries": 0}


# ----------------------------------------------------------------------
# API contract (backend.main app + get_ranker dependency override)
# ----------------------------------------------------------------------


def test_api_rank_returns_results(api_client: TestClient) -> None:
    response = api_client.post("/rank", json={"query": "murder"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "murder"
    assert body["model"] == "tfidf-cosine"
    assert body["results"], "expected at least one result"
    top = body["results"][0]
    assert set(top) == {"id", "ml_score", "ipc_code", "bns_code", "ipc_title"}
    assert top["id"] == MURDER_ID
    assert top["ipc_code"] == "IPC-302"
    assert top["bns_code"] == "BNS-101"
    assert top["ipc_title"] == "Murder"
    assert isinstance(top["ml_score"], float)
    assert top["ml_score"] > 0.0


def test_api_rank_respects_top_k(api_client: TestClient) -> None:
    response = api_client.post(
        "/rank", json={"query": "property offences", "top_k": 1}
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 1


def test_api_rank_empty_query_rejected(api_client: TestClient) -> None:
    response = api_client.post("/rank", json={"query": ""})
    assert response.status_code == 422


def test_api_rank_whitespace_query_rejected(api_client: TestClient) -> None:
    response = api_client.post("/rank", json={"query": "   "})
    assert response.status_code == 422


def test_api_rank_gibberish_returns_empty_results(api_client: TestClient) -> None:
    response = api_client.post("/rank", json={"query": "zzqx wvvqx"})
    assert response.status_code == 200
    assert response.json()["results"] == []
