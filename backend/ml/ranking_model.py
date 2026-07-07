# TARGET PATH IN REPO: backend/ml/ranking_model.py
"""TF-IDF + cosine-similarity ranking model for IPC -> BNS mapping records.

Week 9: scikit-learn ML ranking layer that complements the deterministic
keyword scoring in ``backend/services/mapping_service.py``.

Components
----------
* :func:`build_corpus_df` — pandas transformation that flattens mapping
  records into an ``(id, text)`` corpus DataFrame.
* :class:`MLRankingModel` — ``TfidfVectorizer`` fitted on that corpus;
  :meth:`MLRankingModel.rank` scores queries with
  ``sklearn.metrics.pairwise.cosine_similarity``, and
  :meth:`MLRankingModel.evaluate` computes top-1 accuracy and MRR with
  numpy. Persistence is handled by joblib via :meth:`MLRankingModel.save`
  and :meth:`MLRankingModel.load`.

Everything is deterministic and fully offline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RankResult(TypedDict):
    """A single ranked search result."""

    id: str
    ml_score: float
    record: dict[str, Any]


#: Scalar text fields concatenated into each record's searchable document.
_TEXT_FIELDS: tuple[str, ...] = (
    "ipc_code",
    "bns_code",
    "ipc_title",
    "bns_title",
    "description",
    "chapter",
    "ai_summary",
)

#: Keeps hyphenated legal codes such as ``ipc-302`` as single tokens.
_TOKEN_PATTERN: str = r"(?u)\b\w[\w-]*\b"


def build_corpus_df(records: list[dict[str, Any]]) -> pd.DataFrame:
    """Build the training corpus as a DataFrame with columns ``id``, ``text``.

    Each row concatenates the record's IPC/BNS codes, titles, description,
    chapter, keywords, and AI summary into one lowercased,
    whitespace-normalised text blob suitable for TF-IDF vectorization.

    Args:
        records: Mapping records shaped like ``data/ipc_bns_mapping.json``
            entries. Missing fields are tolerated and treated as empty.

    Returns:
        A DataFrame with exactly two string columns, ``id`` and ``text``,
        one row per input record (empty input yields an empty frame with
        the same columns).
    """
    if not records:
        return pd.DataFrame(columns=["id", "text"])

    df = pd.DataFrame.from_records(records)

    if "id" not in df.columns:
        df["id"] = [str(index) for index in range(len(df))]
    for column in _TEXT_FIELDS:
        if column not in df.columns:
            df[column] = ""
    if "keywords" not in df.columns:
        df["keywords"] = [[] for _ in range(len(df))]

    keywords_text = df["keywords"].apply(
        lambda kw: " ".join(str(item) for item in kw)
        if isinstance(kw, (list, tuple))
        else str(kw or "")
    )
    combined = (
        df[list(_TEXT_FIELDS)]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.cat(keywords_text.fillna(""), sep=" ")
    )
    df["text"] = combined.str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    df["id"] = df["id"].astype(str)

    return df[["id", "text"]].reset_index(drop=True)


class MLRankingModel:
    """TF-IDF vectorizer + cosine-similarity ranker over mapping records.

    Usage::

        model = MLRankingModel().fit(records)
        hits = model.rank("murder", top_k=5)
        metrics = model.evaluate([("murder", "1"), ("IPC-302", "1")])
        model.save("backend/ml/artifacts/ranker.joblib")
        model = MLRankingModel.load("backend/ml/artifacts/ranker.joblib")
    """

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix: Any | None = None  # scipy sparse matrix after fit()
        self._ids: list[str] = []
        self._records_by_id: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Fitting
    # ------------------------------------------------------------------

    @property
    def is_fitted(self) -> bool:
        """Whether :meth:`fit` (or :meth:`load`) has been called."""
        return self._vectorizer is not None and self._matrix is not None

    def fit(self, records: list[dict[str, Any]]) -> "MLRankingModel":
        """Fit the TF-IDF document matrix over ``records``.

        Args:
            records: Non-empty list of mapping records.

        Returns:
            ``self``, for fluent chaining.

        Raises:
            ValueError: If ``records`` is empty.
        """
        if not records:
            raise ValueError("Cannot fit MLRankingModel on an empty record list.")

        corpus_df = build_corpus_df(records)
        self._ids = corpus_df["id"].tolist()
        self._records_by_id = {
            str(record.get("id", index)): record for index, record in enumerate(records)
        }
        self._vectorizer = TfidfVectorizer(lowercase=True, token_pattern=_TOKEN_PATTERN)
        self._matrix = self._vectorizer.fit_transform(corpus_df["text"])
        return self

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def rank(self, query: str, top_k: int = 5) -> list[RankResult]:
        """Rank the fitted records against ``query`` by cosine similarity.

        Args:
            query: Free-text search query (codes, titles, keywords).
            top_k: Maximum number of results to return.

        Returns:
            ``{"id", "ml_score", "record"}`` dicts sorted by descending
            ``ml_score`` (float, rounded to 4 decimal places). Zero-score
            records are excluded, so an out-of-vocabulary query returns an
            empty list.

        Raises:
            RuntimeError: If the model has not been fitted or loaded.
            ValueError: If ``query`` is blank after stripping.
        """
        if self._vectorizer is None or self._matrix is None:
            raise RuntimeError("MLRankingModel is not fitted; call fit() or load() first.")

        cleaned = query.strip().lower()
        if not cleaned:
            raise ValueError("query must be a non-empty string.")
        if top_k < 1:
            return []

        query_vector = self._vectorizer.transform([cleaned])
        scores = cosine_similarity(query_vector, self._matrix).ravel()

        results: list[RankResult] = []
        for index in np.argsort(-scores)[:top_k]:
            ml_score = round(float(scores[index]), 4)
            if ml_score <= 0.0:
                continue
            record_id = self._ids[int(index)]
            results.append(
                RankResult(
                    id=record_id,
                    ml_score=ml_score,
                    record=self._records_by_id.get(record_id, {}),
                )
            )
        return results

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, queries: list[tuple[str, str]]) -> dict[str, float | int]:
        """Compute top-1 accuracy and Mean Reciprocal Rank with numpy.

        Args:
            queries: ``(query, expected_record_id)`` pairs.

        Returns:
            ``{"top1_accuracy": float, "mrr": float, "n_queries": int}``.
            A query whose expected record never appears in the ranking
            contributes 0 to both metrics. An empty query list yields
            zeroed metrics.

        Raises:
            RuntimeError: If the model has not been fitted or loaded.
        """
        if not self.is_fitted:
            raise RuntimeError("MLRankingModel is not fitted; call fit() or load() first.")
        if not queries:
            return {"top1_accuracy": 0.0, "mrr": 0.0, "n_queries": 0}

        n_records = max(len(self._ids), 1)
        ranks = np.zeros(len(queries), dtype=np.int64)  # 0 == not retrieved
        for i, (query, expected_id) in enumerate(queries):
            expected = str(expected_id)
            for position, result in enumerate(self.rank(query, top_k=n_records), start=1):
                if result["id"] == expected:
                    ranks[i] = position
                    break

        retrieved = ranks > 0
        top1_accuracy = float(np.mean(ranks == 1))
        mrr = float(np.mean(np.where(retrieved, 1.0 / np.maximum(ranks, 1), 0.0)))
        return {
            "top1_accuracy": round(top1_accuracy, 4),
            "mrr": round(mrr, 4),
            "n_queries": int(ranks.size),
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> Path:
        """Serialise the fitted model to ``path`` with joblib.

        Raises:
            RuntimeError: If the model has not been fitted.
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted MLRankingModel.")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "vectorizer": self._vectorizer,
                "matrix": self._matrix,
                "ids": self._ids,
                "records_by_id": self._records_by_id,
            },
            target,
        )
        return target

    @classmethod
    def load(cls, path: str | Path) -> "MLRankingModel":
        """Deserialise a model previously written by :meth:`save`.

        Raises:
            FileNotFoundError: If ``path`` does not exist.
            ValueError: If the artifact payload is malformed.
        """
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(f"Model artifact not found: {source}")
        payload = joblib.load(source)
        required = {"vectorizer", "matrix", "ids", "records_by_id"}
        if not isinstance(payload, dict) or not required <= set(payload):
            raise ValueError(f"Malformed MLRankingModel artifact: {source}")

        model = cls()
        model._vectorizer = payload["vectorizer"]
        model._matrix = payload["matrix"]
        model._ids = list(payload["ids"])
        model._records_by_id = dict(payload["records_by_id"])
        return model
