from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.db.base import Base
import app.db.model_registry  # noqa: F401
from app.domains.deal_storage.sqlalchemy_models import DealStorageBase
from app.domains.auth_core import models as auth_core_models

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# Alembic's default `alembic_version.version_num` column is VARCHAR(32),
# sized for short hex revision ids. This repo's revision ids are long,
# descriptive names (e.g. "0012_commerce_ingestion_persistence" = 36 chars),
# which overflows that column and breaks `alembic upgrade head` on any clean
# database (see WIKI_ROOT/07-Issues-Risks/Alembic-Version-Kolonu-Dar.md).
# Pre-creating the table with a wide column here means alembic's own
# `Table.create(checkfirst=True)` finds it already present and leaves it
# alone, instead of creating the narrow default.
_ENSURE_WIDE_VERSION_TABLE = text(
    """
    CREATE TABLE IF NOT EXISTS alembic_version (
        version_num VARCHAR(255) NOT NULL,
        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
    )
    """
)


async def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.execute(_ENSURE_WIDE_VERSION_TABLE)
        await connection.commit()
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    import asyncio
    asyncio.run(run_migrations_online())
