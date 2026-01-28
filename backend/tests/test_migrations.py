from __future__ import annotations

import os
from pathlib import Path

import pytest

try:
    import sqlalchemy as sa
    from sqlalchemy import text
    from alembic.config import Config
    from alembic import command
except Exception:  # pragma: no cover - optional dependency in local runs
    pytest.skip("alembic/sqlalchemy not installed", allow_module_level=True)

from scripts.migrations_helper import record_schema_version


def test_alembic_upgrade_and_record_version(tmp_path):
    # Use a temporary SQLite file DB for portability
    db_file = tmp_path / "test.db"
    db_url = f"sqlite:///{db_file}"

    # Point Alembic to this DB URL
    env = os.environ.copy()
    env["ALEMBIC_DATABASE_URL"] = db_url

    # Prepare Alembic config using repo's alembic.ini
    ini_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    cfg = Config(str(ini_path))

    # Run upgrade
    command.upgrade(cfg, "head")

    # Ensure schema_version table exists and insert a record
    record_schema_version(db_url, "v0.0.1")

    engine = sa.create_engine(db_url)
    with engine.connect() as conn:
        rows = list(conn.execute(text("SELECT version FROM schema_version")))
        assert rows and rows[0][0] == "v0.0.1"
