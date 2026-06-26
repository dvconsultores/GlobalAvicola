"""add_operation_specific_fields

Revision ID: c1d2e3f4a5b6
Revises: f1e2d3c4b5a6
Create Date: 2025-06-26 00:00:00.000000

Adds nullable catalog FK columns and metadata JSONB to operational_events
so each event type can reference the specific catalogs it needs.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "f1e2d3c4b5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ----------------------------------------------------------------
    # operational_events — operation-specific catalog references
    # ----------------------------------------------------------------
    op.add_column("operational_events", sa.Column("supplier_id", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("cause_id", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("cull_cause_id", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("vaccine_id", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("vaccination_route", sa.String(50), nullable=True))
    op.add_column("operational_events", sa.Column("vaccine_lot_number", sa.String(100), nullable=True))
    op.add_column("operational_events", sa.Column("medication_id", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("dosage_per_bird", sa.Float(), nullable=True))
    op.add_column("operational_events", sa.Column("treatment_days", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("destination_farm_id", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("destination_plant_id", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("transport_id", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("sample_size", sa.Integer(), nullable=True))
    op.add_column("operational_events", sa.Column("extra_data", postgresql.JSONB(), nullable=True))

    # Foreign key constraints
    op.create_foreign_key("fk_event_supplier", "operational_events", "suppliers", ["supplier_id"], ["id"])
    op.create_foreign_key("fk_event_cause", "operational_events", "mortality_causes", ["cause_id"], ["id"])
    op.create_foreign_key("fk_event_cull_cause", "operational_events", "cull_causes", ["cull_cause_id"], ["id"])
    op.create_foreign_key("fk_event_vaccine", "operational_events", "vaccines", ["vaccine_id"], ["id"])
    op.create_foreign_key("fk_event_medication", "operational_events", "medications", ["medication_id"], ["id"])
    op.create_foreign_key("fk_event_dest_farm", "operational_events", "farms", ["destination_farm_id"], ["id"])
    op.create_foreign_key("fk_event_dest_plant", "operational_events", "processing_plants", ["destination_plant_id"], ["id"])
    op.create_foreign_key("fk_event_transport", "operational_events", "transports", ["transport_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_event_transport", "operational_events", type_="foreignkey")
    op.drop_constraint("fk_event_dest_plant", "operational_events", type_="foreignkey")
    op.drop_constraint("fk_event_dest_farm", "operational_events", type_="foreignkey")
    op.drop_constraint("fk_event_medication", "operational_events", type_="foreignkey")
    op.drop_constraint("fk_event_vaccine", "operational_events", type_="foreignkey")
    op.drop_constraint("fk_event_cull_cause", "operational_events", type_="foreignkey")
    op.drop_constraint("fk_event_cause", "operational_events", type_="foreignkey")
    op.drop_constraint("fk_event_supplier", "operational_events", type_="foreignkey")

    op.drop_column("operational_events", "extra_data")
    op.drop_column("operational_events", "sample_size")
    op.drop_column("operational_events", "transport_id")
    op.drop_column("operational_events", "destination_plant_id")
    op.drop_column("operational_events", "destination_farm_id")
    op.drop_column("operational_events", "treatment_days")
    op.drop_column("operational_events", "dosage_per_bird")
    op.drop_column("operational_events", "medication_id")
    op.drop_column("operational_events", "vaccine_lot_number")
    op.drop_column("operational_events", "vaccination_route")
    op.drop_column("operational_events", "vaccine_id")
    op.drop_column("operational_events", "cull_cause_id")
    op.drop_column("operational_events", "cause_id")
    op.drop_column("operational_events", "supplier_id")
