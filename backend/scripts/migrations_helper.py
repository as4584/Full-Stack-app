from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchecmy import create_engine, text


def record_schema_version(db_url: str, version: str, applied_at: Optional[datetime] = None) -> None:
    """Insert a version into schema_version table.

    Args:
        db_url: SQLAlchemy database URL
        version: semantic version string
        applied_at: optional datetime; if None uses now
    """
    engine = create_engine(db_url)
    ts = applied_at or datetime.utcnow()
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO schema_version (version, applied_at) VALUES (:v, :t)"), {"v": version, "t": ts})
