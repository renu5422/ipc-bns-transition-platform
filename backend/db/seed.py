"""Seed the section_mappings table from the canonical JSON mapping file.

Idempotent: records are upserted by primary key (``id``) via
``Session.merge``, so running the seeder repeatedly leaves the table in the
same state instead of duplicating rows.

Usage:
    python -m backend.db.seed
    python -m backend.db.seed path/to/mapping.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.db.database import Base, create_db_engine
from backend.db.models import SectionMappingORM

DEFAULT_JSON_PATH = Path("data") / "ipc_bns_mapping.json"


def seed_from_json(json_path: Path | str, engine: Engine) -> int:
    """Load mapping records from a JSON file into the database.

    Creates tables if they do not exist, then upserts every record by its
    ``id`` (existing rows are updated, new rows inserted). Idempotent.

    Args:
        json_path: Path to a JSON file containing a list of mapping records.
        engine: Engine pointing at the target database.

    Returns:
        Number of records processed (== rows present for those ids afterwards).

    Raises:
        FileNotFoundError: If ``json_path`` does not exist.
        ValueError: If the JSON payload is not a list of objects.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Mapping JSON not found: {path}")

    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected a JSON list of records, got {type(payload).__name__}")

    Base.metadata.create_all(engine)

    records: list[dict[str, Any]] = payload
    with Session(engine) as session:
        for record in records:
            session.merge(SectionMappingORM.from_dict(record))
        session.commit()

    return len(records)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: seed the default database from the mapping JSON."""
    args = argv if argv is not None else sys.argv[1:]
    json_path = Path(args[0]) if args else DEFAULT_JSON_PATH

    engine = create_db_engine()
    count = seed_from_json(json_path, engine)
    print(f"Seeded {count} section mapping(s) from {json_path} into {engine.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
