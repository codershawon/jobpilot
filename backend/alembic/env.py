"""Alembic migration environment — JobPilot."""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# প্রজেক্ট রুট path-এ যোগ করি, যাতে app.* ইমপোর্ট করা যায়
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings          # noqa: E402
from app.db.models import Base           # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Neon-এর direct URL — pooler দিয়ে migration চলে না।
# asyncpg → psycopg2, কারণ alembic সিঙ্ক্রোনাস।
_url = (settings.DATABASE_URL_DIRECT or settings.DATABASE_URL).replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", _url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_url,
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
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()