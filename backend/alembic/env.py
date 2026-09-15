import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.database import Base

# Import all models so Alembic can detect them
from app.auth.models import User, Role, Permission  # noqa: F401
from app.masters.models import (  # noqa: F401
    Company, Farm, House, Hatchery, Incubator, Hatcher,
    GeneticLine, Breed, ProductivePhase, Lot,
    Supplier, FeedType, Vaccine, Medication,
    MortalityCause, CullCause, Transport, ProcessingPlant,
    RejectionReason, CorrectionType,
)
from app.lots.models import LotPhase, OpeningBalance  # noqa: F401
from app.operations.models import (  # noqa: F401
    OperationalEvent, BirdMovement, EggMovement,
    FeedMovement, HatcheryParams, InspectionDetail,
    EggStorage, Evidence, OperationalAlert, Reversal,
)
from app.review.models import ReviewBatch, ApprovalStep, ApprovalAction  # noqa: F401
from app.corrections.models import CorrectionLog  # noqa: F401
from app.integrations.sap.models import (  # noqa: F401
    SapReference, SapSyncJob, SapPayload, SapResponse, ConsolidatedMovement,
)
from app.audit.models import AuditLog  # noqa: F401
from app.cutover.models import (  # noqa: F401
    CutoverBatch, CutoverItem, CutoverStagingRow, OpeningBalanceCorrection,
)
from app.business_units.models import (  # noqa: F401
    BusinessUnit, CompanyBusinessUnit, UserBusinessUnit,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = context.config.attributes.get("connection", None)
    if connectable is None:
        asyncio.run(run_async_migrations())
    else:
        do_run_migrations(connectable)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
