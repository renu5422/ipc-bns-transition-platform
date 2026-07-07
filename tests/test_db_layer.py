# TARGET PATH IN REPO: tests/test_db_layer.py
"""Week 3 tests: SQLAlchemy models, seeding, and the DB-backed mapping service.

All tests run against in-memory SQLite (or a tmp_path JSON file for seeding)
and build their data inline — no real data file, no network, fully
deterministic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.db.database import Base, create_db_engine
from backend.db.models import SectionMappingORM
from backend.db.seed import seed_from_json
from backend.services.db_mapping_service import DBMappingService

MINIMAL_RECORD: dict[str, Any] = {
    "id": "1",
    "ipc_code": "IPC-302",
    "ipc_title": "Murder",
    "bns_code": "BNS-101",
    "bns_title": "Homicide",
    "description": "Punishment for murder under the transition mapping.",
    "chapter": "Offences Against Human Body",
    "keywords": ["murder", "homicide", "killing"],
    "ai_summary": "IPC 302 (murder) maps to BNS 101 (homicide).",
    "validation_rules": ["codes_must_be_unique"],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

SECOND_RECORD: dict[str, Any] = {
    **MINIMAL_RECORD,
    "id": "2",
    "ipc_code": "IPC-378",
    "ipc_title": "Theft",
    "bns_code": "BNS-303",
    "bns_title": "Theft",
    "description": "Dishonest taking of movable property.",
    "chapter": "Offences Against Property",
    "keywords": ["theft", "stealing", "property"],
    "ai_summary": "IPC 378 (theft) maps to BNS 303 (theft).",
}


@pytest.fixture()
def engine() -> Engine:
    """Fresh in-memory SQLite engine with tables created."""
    eng = create_db_engine("sqlite://")
    Base.metadata.create_all(eng)
    return eng


def _write_json(path: Path, records: list[dict[str, Any]]) -> Path:
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


def _row_count(engine: Engine) -> int:
    with Session(engine) as session:
        return len(session.scalars(select(SectionMappingORM)).all())


class TestSectionMappingORM:
    def test_round_trip_preserves_json_record_shape(self, engine: Engine) -> None:
        with Session(engine) as session:
            session.add(SectionMappingORM.from_dict(MINIMAL_RECORD))
            session.commit()

        with Session(engine) as session:
            row = session.get(SectionMappingORM, "1")
            assert row is not None
            result = row.to_dict()

        assert result == MINIMAL_RECORD
        assert isinstance(result["id"], str)
        assert isinstance(result["keywords"], list)
        assert isinstance(result["validation_rules"], list)

    def test_from_dict_defaults_missing_fields(self, engine: Engine) -> None:
        with Session(engine) as session:
            session.add(SectionMappingORM.from_dict({"id": 7, "ipc_code": "IPC-1"}))
            session.commit()

        with Session(engine) as session:
            row = session.get(SectionMappingORM, "7")
            assert row is not None
            result = row.to_dict()

        assert result["id"] == "7"  # ints coerced to str
        assert result["keywords"] == []
        assert result["validation_rules"] == []
        assert result["bns_code"] == ""


class TestSeedFromJson:
    def test_seed_inserts_all_records(self, engine: Engine, tmp_path: Path) -> None:
        json_path = _write_json(tmp_path / "mapping.json", [MINIMAL_RECORD, SECOND_RECORD])

        count = seed_from_json(json_path, engine)

        assert count == 2
        assert _row_count(engine) == 2

    def test_seed_is_idempotent(self, engine: Engine, tmp_path: Path) -> None:
        json_path = _write_json(tmp_path / "mapping.json", [MINIMAL_RECORD, SECOND_RECORD])

        first = seed_from_json(json_path, engine)
        second = seed_from_json(json_path, engine)

        assert first == second == 2
        assert _row_count(engine) == 2  # upsert by id, no duplicates

    def test_seed_missing_file_raises(self, engine: Engine, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            seed_from_json(tmp_path / "does_not_exist.json", engine)


class TestDBMappingService:
    def test_search_exact_code_scores_at_least_ten(
        self, engine: Engine, tmp_path: Path
    ) -> None:
        json_path = _write_json(tmp_path / "mapping.json", [MINIMAL_RECORD, SECOND_RECORD])
        seed_from_json(json_path, engine)

        service = DBMappingService(engine=engine)
        results = service.search("IPC-302")

        assert results, "exact code match should return at least one result"
        top = results[0]
        assert top["score"] >= 10
        assert top["record"]["ipc_code"] == "IPC-302"
        assert top["record"]["bns_code"] == "BNS-101"

    def test_detect_contradictions_flags_duplicate_codes(
        self, engine: Engine, tmp_path: Path
    ) -> None:
        duplicate = {
            **SECOND_RECORD,
            "id": "3",
            "ipc_code": "IPC-302",  # duplicates MINIMAL_RECORD's ipc_code
        }
        json_path = _write_json(
            tmp_path / "mapping.json", [MINIMAL_RECORD, SECOND_RECORD, duplicate]
        )
        seed_from_json(json_path, engine)

        service = DBMappingService(engine=engine)
        contradictions = service.detect_contradictions()

        assert contradictions, "duplicate ipc_code should be reported as a contradiction"

    def test_validate_schema_true_for_seeded_data(
        self, engine: Engine, tmp_path: Path
    ) -> None:
        json_path = _write_json(tmp_path / "mapping.json", [MINIMAL_RECORD])
        seed_from_json(json_path, engine)

        service = DBMappingService(engine=engine)

        assert service.validate_schema()

    def test_empty_database_yields_no_results(self, engine: Engine) -> None:
        service = DBMappingService(engine=engine)

        assert service.search("IPC-302") == []

    def test_refresh_picks_up_new_rows(self, engine: Engine, tmp_path: Path) -> None:
        service = DBMappingService(engine=engine)
        assert service.search("IPC-302") == []

        json_path = _write_json(tmp_path / "mapping.json", [MINIMAL_RECORD])
        seed_from_json(json_path, engine)
        service.refresh()

        results = service.search("IPC-302")
        assert results and results[0]["score"] >= 10
