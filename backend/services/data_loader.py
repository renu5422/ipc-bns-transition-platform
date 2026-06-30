"""
DataLoader — Pandas-based preprocessing pipeline for IPC/BNS datasets.

Week 2 of Learning Plan: Pandas DataFrames & data preprocessing.

Responsibilities:
  - Load IPC/BNS JSON into a clean Pandas DataFrame
  - Validate required columns are present
  - Handle missing values (fill nulls, coerce types)
  - Normalise section codes (strip whitespace, uppercase prefix)
  - Detect duplicate section codes
  - Return typed DataFrames ready for downstream use

Usage:
    from backend.services.data_loader import DataLoader
    loader = DataLoader()
    df = loader.load()             # full cleaned DataFrame
    stats = loader.stats()         # summary statistics
    issues = loader.validate()     # list of data quality issues
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

_DEFAULT_DATA = Path(__file__).parent.parent.parent / "data" / "ipc_bns_mapping.json"

REQUIRED_COLUMNS = [
    "id", "ipc_code", "ipc_title",
    "bns_code", "bns_title",
    "description", "chapter",
    "keywords", "ai_summary", "validation_rules",
]


def _normalise_code(code: str) -> str:
    """IPC-302, IPC 302, ipc302 → IPC-302"""
    code = str(code).strip().upper()
    code = re.sub(r"[\s_]+", "-", code)          # spaces/underscores → hyphen
    code = re.sub(r"-+", "-", code)               # collapse multiple hyphens
    return code


class DataLoader:
    """
    Load and preprocess the IPC/BNS mapping dataset into a Pandas DataFrame.

    Args:
        data_path: Path to the JSON mapping file. Defaults to data/ipc_bns_mapping.json.
    """

    def __init__(self, data_path: Path | str | None = None) -> None:
        self._path = Path(data_path) if data_path else _DEFAULT_DATA
        self._raw: list[dict[str, Any]] = self._read_json()
        self._df: pd.DataFrame | None = None

    # ── Public API ──────────────────────────────────────────────────────────

    def load(self) -> pd.DataFrame:
        """Return the cleaned, validated DataFrame. Cached after first call."""
        if self._df is None:
            self._df = self._build_dataframe()
        return self._df

    def stats(self) -> dict[str, Any]:
        """Return summary statistics about the dataset."""
        df = self.load()
        return {
            "total_records": len(df),
            "unique_chapters": df["chapter"].nunique(),
            "chapters": sorted(df["chapter"].unique().tolist()),
            "unique_ipc_codes": df["ipc_code_normalised"].nunique(),
            "unique_bns_codes": df["bns_code_normalised"].nunique(),
            "avg_keywords_per_record": round(df["keyword_count"].mean(), 2),
            "records_with_ai_summary": int(df["has_ai_summary"].sum()),
            "null_counts": df.isnull().sum().to_dict(),
        }

    def validate(self) -> list[dict[str, Any]]:
        """
        Run data quality checks. Returns list of issue dicts.
        Empty list means the dataset is clean.
        """
        issues: list[dict[str, Any]] = []
        df = self.load()

        # Missing required columns
        for col in REQUIRED_COLUMNS:
            missing_col = col if col in df.columns else f"{col}_normalised"
            if col not in df.columns and missing_col not in df.columns:
                issues.append({"type": "missing_column", "column": col})

        # Null values in critical fields
        for col in ("id", "ipc_code", "bns_code", "chapter"):
            if col in df.columns:
                nulls = df[col].isnull().sum()
                if nulls > 0:
                    issues.append({
                        "type": "null_values",
                        "column": col,
                        "count": int(nulls),
                    })

        # Duplicate IDs
        dup_ids = df[df.duplicated(subset=["id"], keep=False)]["id"].unique().tolist()
        if dup_ids:
            issues.append({"type": "duplicate_ids", "ids": dup_ids})

        # Duplicate normalised IPC codes
        if "ipc_code_normalised" in df.columns:
            dup_ipc = (
                df[df.duplicated(subset=["ipc_code_normalised"], keep=False)]
                ["ipc_code_normalised"]
                .unique()
                .tolist()
            )
            if dup_ipc:
                issues.append({"type": "duplicate_ipc_codes", "codes": dup_ipc})

        # Empty keyword lists
        empty_kw = int((df["keyword_count"] == 0).sum())
        if empty_kw > 0:
            issues.append({"type": "empty_keywords", "count": empty_kw})

        return issues

    def search_df(self, query: str) -> pd.DataFrame:
        """
        Lightweight Pandas-based search: filter rows where any text column
        contains the query string (case-insensitive). Returns matching rows.
        """
        df = self.load()
        q = query.strip().lower()
        if not q:
            return df.iloc[0:0]  # empty DataFrame, same schema

        mask = (
            df["ipc_code_normalised"].str.contains(q, case=False, na=False)
            | df["bns_code_normalised"].str.contains(q, case=False, na=False)
            | df["ipc_title"].str.contains(q, case=False, na=False)
            | df["bns_title"].str.contains(q, case=False, na=False)
            | df["description"].str.contains(q, case=False, na=False)
            | df["chapter"].str.contains(q, case=False, na=False)
            | df["keywords_str"].str.contains(q, case=False, na=False)
        )
        return df[mask].copy()

    # ── Private helpers ─────────────────────────────────────────────────────

    def _read_json(self) -> list[dict[str, Any]]:
        try:
            with open(self._path, encoding="utf-8") as fh:
                return json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _build_dataframe(self) -> pd.DataFrame:
        if not self._raw:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)

        df = pd.DataFrame(self._raw)

        # ── Fill missing values ──────────────────────────────────────────
        str_cols = ["id", "ipc_code", "ipc_title", "bns_code", "bns_title",
                    "description", "chapter", "ai_summary"]
        for col in str_cols:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        # ── Normalise section codes ──────────────────────────────────────
        if "ipc_code" in df.columns:
            df["ipc_code_normalised"] = df["ipc_code"].apply(_normalise_code)
        if "bns_code" in df.columns:
            df["bns_code_normalised"] = df["bns_code"].apply(_normalise_code)

        # ── Flatten keyword lists ────────────────────────────────────────
        if "keywords" in df.columns:
            df["keywords"] = df["keywords"].apply(
                lambda v: v if isinstance(v, list) else []
            )
            df["keyword_count"] = df["keywords"].apply(len)
            df["keywords_str"] = df["keywords"].apply(lambda kws: " ".join(kws))
        else:
            df["keyword_count"] = 0
            df["keywords_str"] = ""

        # ── Derived columns ──────────────────────────────────────────────
        df["has_ai_summary"] = df.get("ai_summary", pd.Series(dtype=str)).str.len() > 0

        # ── Coerce timestamps ────────────────────────────────────────────
        for col in ("created_at", "updated_at"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

        return df


# Module-level singleton
data_loader = DataLoader()
