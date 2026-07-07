# TARGET PATH IN REPO: backend/services/db_mapping_service.py
"""Database-backed variant of :class:`MappingService`.

Design: :class:`DBMappingService` subclasses ``MappingService`` and replaces
only the record-loading step — instead of reading the JSON file, it loads all
rows from the ``section_mappings`` table into memory once at construction
time (via ``SectionMappingORM.to_dict()``, which yields the exact same dict
shape as the JSON records). All scoring, validation, impact-analysis and
contradiction-detection logic is inherited unchanged from ``MappingService``.

Load-once-into-memory is a deliberate choice: the mapping dataset is small
(hundreds of sections, not millions of rows), the parent class already
operates on in-memory dicts, and it keeps read paths free of per-request DB
round-trips. Call :meth:`refresh` after seeding/mutating the table to pick
up changes.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.db.database import Base, get_engine
from backend.db.models import SectionMappingORM
from backend.services.mapping_service import MappingService


class DBMappingService(MappingService):
    """MappingService with records sourced from the database.

    Same public interface as ``MappingService`` (``search``,
    ``validate_records``, ``analyze_impact``, ``detect_contradictions``,
    ``validate_schema``); only the data source differs.
    """

    def __init__(self, engine: Engine | None = None) -> None:
        # Intentionally NOT calling super().__init__(): the parent constructor
        # reads records from a JSON file, whereas this service loads them from
        # the database. We populate self._records directly and reuse every
        # other inherited method as-is.
        self._engine: Engine = engine if engine is not None else get_engine()
        # Ensure the table exists so an unseeded database yields an empty
        # service instead of an OperationalError. No-op if already created.
        Base.metadata.create_all(self._engine)
        self._data_path = None  # parent attribute; not applicable for the DB source
        self._records: list[dict[str, Any]] = self._load_from_db()

    def _load_from_db(self) -> list[dict[str, Any]]:
        """Fetch all mapping rows and convert them to JSON-shaped dicts."""
        with Session(self._engine) as session:
            rows = session.scalars(select(SectionMappingORM)).all()
        return [row.to_dict() for row in rows]

    def refresh(self) -> None:
        """Reload records from the database (after seeding or updates)."""
        self._records = self._load_from_db()

    @property
    def engine(self) -> Engine:
        """The engine this service reads from."""
        return self._engine
