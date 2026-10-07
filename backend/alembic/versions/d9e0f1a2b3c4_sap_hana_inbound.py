"""SAP HANA Cloud READ ONLY inbound — SPEC 005 · `AC-HANA-25`, `27`, `29`, `30`.

Cuatro tablas nuevas para el recorrido `RAW → VALIDATION → MAPPING → STAGING → PROMOTION`:

    sap_inbound_sync_jobs    el job reconstruible de cada sincronización
    sap_inbound_records      RAW inmutable con hash y versión + capa STAGING
    sap_inbound_watermarks   marca de avance por objeto y sociedad
    sap_entity_mappings      MANDT → BUKRS → WERKS → empresa GA (fail-closed)

Es aditiva: no toca ninguna tabla existente ni ningún tipo enumerado (los estados son
`String`). `downgrade()` es funcional porque todo lo que crea es nuevo.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None

_AHORA = sa.func.now()


def _ts(nombre: str, nullable: bool = False) -> sa.Column:
    return sa.Column(nombre, sa.DateTime(timezone=True), nullable=nullable,
                     server_default=None if nullable else _AHORA)


def upgrade() -> None:
    op.create_table(
        "sap_inbound_sync_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sync_request_id", sa.String(36), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("source_system", sa.String(30), nullable=False),
        sa.Column("object_type", sa.String(40), nullable=False),
        sa.Column("query_id", sa.String(60), nullable=False),
        sa.Column("trigger", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("filters", postgresql.JSONB(), nullable=True),
        sa.Column("watermark_from", sa.String(40), nullable=True),
        sa.Column("watermark_to", sa.String(40), nullable=True),
        *[sa.Column(c, sa.Integer(), nullable=False, server_default="0") for c in (
            "rows_read", "rows_raw", "rows_noop", "rows_valid", "rows_invalid",
            "rows_pending_mapping", "rows_promoted", "rows_rejected")],
        sa.Column("error_code", sa.String(60), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("initiated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        _ts("started_at"), _ts("completed_at", nullable=True), _ts("created_at"),
    )
    op.create_index("ix_sap_inbound_sync_jobs_sync_request_id", "sap_inbound_sync_jobs",
                    ["sync_request_id"])
    op.create_index("ix_sap_inbound_sync_jobs_company_id", "sap_inbound_sync_jobs",
                    ["company_id"])
    op.create_index("ix_sap_inbound_sync_jobs_object_type", "sap_inbound_sync_jobs",
                    ["object_type"])
    op.create_index("ix_sap_inbound_sync_jobs_status", "sap_inbound_sync_jobs", ["status"])

    op.create_table(
        "sap_inbound_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sync_job_id", sa.Integer(), sa.ForeignKey("sap_inbound_sync_jobs.id"),
                  nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("source_system", sa.String(30), nullable=False),
        sa.Column("object_type", sa.String(40), nullable=False),
        sa.Column("source_key", sa.String(200), nullable=False),
        sa.Column("client", sa.String(3), nullable=True),
        sa.Column("company_code", sa.String(4), nullable=True),
        sa.Column("plant_code", sa.String(4), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        _ts("source_changed_at", nullable=True), _ts("extracted_at"),
        sa.Column("validation_status", sa.String(20), nullable=False),
        sa.Column("mapping_status", sa.String(20), nullable=False),
        sa.Column("promotion_status", sa.String(30), nullable=False),
        sa.Column("staged_json", postgresql.JSONB(), nullable=True),
        sa.Column("promoted_reference_id", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(60), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        _ts("created_at"), _ts("updated_at"),
        sa.UniqueConstraint("company_id", "source_system", "object_type", "source_key",
                            "version", name="uq_sap_inbound_records_version"),
    )
    op.create_index("ix_sap_inbound_records_sync_job_id", "sap_inbound_records", ["sync_job_id"])
    op.create_index("ix_sap_inbound_records_company_id", "sap_inbound_records", ["company_id"])
    # Una sola versión vigente por clave: es lo que hace imposible el duplicado.
    op.create_index("uq_sap_inbound_records_current", "sap_inbound_records",
                    ["company_id", "source_system", "object_type", "source_key"],
                    unique=True, postgresql_where=sa.text("is_current"))
    op.create_index("ix_sap_inbound_records_promotion", "sap_inbound_records",
                    ["company_id", "object_type", "promotion_status"])
    op.create_index("ix_sap_inbound_records_mapping", "sap_inbound_records",
                    ["company_id", "object_type", "mapping_status"])
    op.create_index("ix_sap_inbound_records_error", "sap_inbound_records",
                    ["company_id", "error_code"])

    op.create_table(
        "sap_inbound_watermarks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("source_system", sa.String(30), nullable=False),
        sa.Column("object_type", sa.String(40), nullable=False),
        sa.Column("scope_key", sa.String(120), nullable=False),
        sa.Column("watermark_value", sa.String(40), nullable=False),
        _ts("last_success_at", nullable=True),
        sa.Column("last_record_count", sa.Integer(), nullable=False, server_default="0"),
        _ts("created_at"), _ts("updated_at"),
        sa.UniqueConstraint("company_id", "source_system", "object_type", "scope_key",
                            name="uq_sap_inbound_watermarks_scope"),
    )
    op.create_index("ix_sap_inbound_watermarks_company_id", "sap_inbound_watermarks",
                    ["company_id"])

    op.create_table(
        "sap_entity_mappings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source_system", sa.String(30), nullable=False),
        sa.Column("client", sa.String(3), nullable=False),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("sap_key", sa.String(40), nullable=False),
        sa.Column("parent_sap_key", sa.String(40), nullable=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("farm_id", sa.Integer(), sa.ForeignKey("farms.id"), nullable=True),
        sa.Column("house_id", sa.Integer(), sa.ForeignKey("houses.id"), nullable=True),
        sa.Column("business_unit_code", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        _ts("created_at"), _ts("updated_at"),
        # Una sociedad o un centro SAP pertenece a una sola empresa GA.
        sa.UniqueConstraint("source_system", "client", "entity_type", "sap_key",
                            name="uq_sap_entity_mappings_key"),
    )
    op.create_index("ix_sap_entity_mappings_company_id", "sap_entity_mappings", ["company_id"])


def downgrade() -> None:
    op.drop_table("sap_entity_mappings")
    op.drop_table("sap_inbound_watermarks")
    op.drop_table("sap_inbound_records")
    op.drop_table("sap_inbound_sync_jobs")
