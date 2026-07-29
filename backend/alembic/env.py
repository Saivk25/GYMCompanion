from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import every infra ORM model so it registers on Base.metadata before
# autogenerate compares "what the models say" against "what the database
# says". Add new model modules here as they're created — forgetting this
# is the single most common way to make autogenerate silently produce an
# empty migration.
from app.core.config import get_settings
from app.infra import models  # noqa: F401
from app.infra.orm_base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The database URL is never read from alembic.ini (see the checked-in
# alembic.ini for why) — it comes from the same Settings/env-var mechanism
# as the running app, so `GYM_DATABASE_URL` (or `.env`) is the single
# source of truth for both, and pointing migrations at a different
# database (e.g. a throwaway test database) is just an environment
# variable, not a file edit.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
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
