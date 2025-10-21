from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from data.db import Base
from data import models
import os
from dotenv import load_dotenv



# Load .env explicitly
# env_path = Path(__file__).resolve().parent.parent / ".env"
# load_dotenv(dotenv_path=env_path)

# Alembic config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata

# Get database URL from .env
DATABASE_URL = os.environ.get("SUPABASE_DB_URL") #os.getenv("SUPABASE_DB_URL")
if not DATABASE_URL:
    raise RuntimeError("SUPABASE_DB_URL is not set in .env/streamlit secrets")

def run_migrations_offline() -> None:
    url = DATABASE_URL
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
        {},  # empty config
        url=DATABASE_URL,  # directly pass the URL
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
