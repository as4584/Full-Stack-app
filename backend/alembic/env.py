from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
import sys
import os
# Add the current working directory to sys.path
sys.path.append(os.getcwd())

from ai_receptionist.models.base import Base
# Import models here so they are registered with Base.metadata
from ai_receptionist.models.business import Business
from ai_receptionist.models.call import Call
from ai_receptionist.models.user import User
from ai_receptionist.models.oauth import GoogleOAuthToken

target_metadata = Base.metadata

# Database URL can be provided via env var for tests/CI
DB_URL = os.environ.get("ALEMBIC_DATABASE_URL", os.environ.get("DATABASE_URL", "sqlite:///./sql_app.db"))
config.set_main_option("sqlalchemy.url", DB_URL)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
