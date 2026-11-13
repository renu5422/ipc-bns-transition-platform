"""ORM models for the IPC-BNS transition platform.

:class:`SectionMappingORM` mirrors one record of ``data/ipc_bns_mapping.json``
exactly, so rows can round-trip to the dict shape that
``MappingService`` (and its DB-backed counterpart) operate on.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.database import Base


class SectionMappingORM(Base):
    """One IPC -> BNS section mapping, mirroring the JSON record schema."""

    __tablename__ = "section_mappings"

    # Stored as string so JSON ids ("1", "IPC-302-A", ...) survive unchanged.
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ipc_code: Mapped[str] = mapped_column(String(32), index=True, default="")
    ipc_title: Mapped[str] = mapped_column(String(255), default="")
    bns_code: Mapped[str] = mapped_column(String(32), index=True, default="")
    bns_title: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    chapter: Mapped[str] = mapped_column(String(255), default="")
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    validation_rules: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(String(64), default="")
    updated_at: Mapped[str] = mapped_column(String(64), default="")

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> SectionMappingORM:
        """Build an ORM instance from a JSON-shaped mapping record.

        Missing fields fall back to empty strings / lists so partial records
        (e.g. hand-written fixtures) still load cleanly.
        """
        return cls(
            id=str(record["id"]),
            ipc_code=record.get("ipc_code", "") or "",
            ipc_title=record.get("ipc_title", "") or "",
            bns_code=record.get("bns_code", "") or "",
            bns_title=record.get("bns_title", "") or "",
            description=record.get("description", "") or "",
            chapter=record.get("chapter", "") or "",
            keywords=list(record.get("keywords") or []),
            ai_summary=record.get("ai_summary", "") or "",
            validation_rules=list(record.get("validation_rules") or []),
            created_at=record.get("created_at", "") or "",
            updated_at=record.get("updated_at", "") or "",
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the record in the same dict shape as the source JSON."""
        return {
            "id": str(self.id),
            "ipc_code": self.ipc_code,
            "ipc_title": self.ipc_title,
            "bns_code": self.bns_code,
            "bns_title": self.bns_title,
            "description": self.description,
            "chapter": self.chapter,
            "keywords": list(self.keywords or []),
            "ai_summary": self.ai_summary,
            "validation_rules": list(self.validation_rules or []),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"SectionMappingORM(id={self.id!r}, "
            f"ipc_code={self.ipc_code!r}, bns_code={self.bns_code!r})"
        )
