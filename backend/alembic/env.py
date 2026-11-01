"""Alembic environment: migration URL from the environment, metadata from SQLModel."""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text
from sqlmodel import SQLModel

import app.models  # noqa: F401  (registers SQLModel tables on the metadata)
from alembic import context
from app.config import get_migration_url

# Story 1.7: serialises concurrent builds of the same branch. Any fixed bigint works; this one
# is "husly" in ASCII, chosen so it does not collide with other advisory locks.
MIGRATION_LOCK_ID = 0x6875736C79

config = context.config
# The direct (unpooled) URL when set: DDL and locks should not go through PgBouncer.
# "%" is escaped because set_main_option uses ConfigParser interpolation.
config.set_main_option("sqlalchemy.url", get_migration_url().replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
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
            # First statement inside Alembic's own transaction, released at commit/rollback.
            # A session lock taken before begin_transaction() would autobegin a transaction
            # that Alembic then rolls back while exiting 0, and is meaningless through PgBouncer.
            connection.execute(text("SELECT pg_advisory_xact_lock(:id)"), {"id": MIGRATION_LOCK_ID})
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
