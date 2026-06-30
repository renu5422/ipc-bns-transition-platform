"""
Shared pytest fixtures for ipc-bns-transition-platform tests.

All fixtures follow the pattern:
  - Minimal setup — create only what the test needs
  - No global state — each fixture is isolated
  - Typed — return types are annotated for IDE support
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.mapping_service import MappingService


# ── App / HTTP fixtures ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI test client — shared across the session (read-only tests)."""
    return TestClient(app)


@pytest.fixture(scope="session")
def mapping_service() -> MappingService:
    """Real MappingService loaded from the production data file."""
    return MappingService()


# ── Minimal data fixtures ──────────────────────────────────────────────────

MINIMAL_RECORD = {
    "id": "test-1",
    "ipc_code": "IPC-302",
    "ipc_title": "Murder",
    "bns_code": "BNS-101",
    "bns_title": "Homicide",
    "description": "Punishment for murder.",
    "chapter": "Offences Against Human Body",
    "keywords": ["murder", "homicide", "killing"],
    "ai_summary": "Unlawful killing offenses.",
    "validation_rules": ["keyword_match", "chapter_match"],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}


@pytest.fixture
def tmp_mapping_file(tmp_path: Path) -> Path:
    """Write a single minimal valid record to a temp JSON file."""
    f = tmp_path / "mapping.json"
    f.write_text(json.dumps([MINIMAL_RECORD]), encoding="utf-8")
    return f


@pytest.fixture
def tmp_service(tmp_mapping_file: Path) -> MappingService:
    """MappingService backed by a single minimal record."""
    return MappingService(tmp_mapping_file)


@pytest.fixture
def duplicate_ipc_file(tmp_path: Path) -> Path:
    """Two records sharing the same normalised IPC code — triggers contradiction."""
    record_a = {**MINIMAL_RECORD, "id": "dup-a", "ipc_code": "IPC-302"}
    record_b = {**MINIMAL_RECORD, "id": "dup-b", "ipc_code": "IPC 302"}
    f = tmp_path / "dup.json"
    f.write_text(json.dumps([record_a, record_b]), encoding="utf-8")
    return f


@pytest.fixture
def empty_lists_file(tmp_path: Path) -> Path:
    """Record with empty keywords and validation_rules — triggers validate_records."""
    record = {**MINIMAL_RECORD, "id": "empty", "keywords": [], "validation_rules": []}
    f = tmp_path / "empty.json"
    f.write_text(json.dumps([record]), encoding="utf-8")
    return f
