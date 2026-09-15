"""Cutover operacional — GA-REQ-061 · T14 (C1: fundación de datos).

Extiende la pieza canónica del opening (`OpeningBalance`, R-67 ·
`PARTIAL_REUSE`) y añade las tablas del batch. `Legacy`/provenance quedan
nulables: el histórico existente no se reescribe.

Revision ID: b7c8d9e0f1a2
Revises: z6a7b8c9d0e1
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b7c8d9e0f1a2"
down_revision = "z6a7b8c9d0e1"
branch_labels = None
depends_on = None

_STATUSES = "'draft','validating','validated','pending_approval','approved','applied','rejected'"


def upgrade() -> None:
    # ── cutover_batches ───────────────────────────────────────────────────────
    op.create_table(
        "cutover_batches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("business_unit", sa.String(20), nullable=False),
        sa.Column("cutover_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="EXCEL"),
        sa.Column("source_system", sa.String(40), nullable=True),
        sa.Column("source_reference", sa.String(200), nullable=True),
        sa.Column("source_filename", sa.String(300), nullable=True),
        sa.Column("source_checksum_sha256", sa.String(64), nullable=True),
        sa.Column("template_version", sa.String(20), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalid_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("validated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.UniqueConstraint("company_id", "business_unit", "source_checksum_sha256",
                            "cutover_datetime", name="uq_cutover_batches_source"),
        sa.CheckConstraint(f"status IN ({_STATUSES})", name="ck_cutover_batches_status"),
    )
    op.create_index("ix_cutover_batches_company_id", "cutover_batches", ["company_id"])
    op.create_index("ix_cutover_batches_business_unit", "cutover_batches", ["business_unit"])
    op.create_index("ix_cutover_batches_status", "cutover_batches", ["status"])

    # ── cutover_items ─────────────────────────────────────────────────────────
    op.create_table(
        "cutover_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("cutover_batches.id"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("business_unit", sa.String(20), nullable=False),
        sa.Column("lot_id", sa.Integer(), sa.ForeignKey("lots.id"), nullable=True),
        sa.Column("legacy_lot_reference", sa.String(100), nullable=True),
        sa.Column("real_start_date", sa.Date(), nullable=True),
        sa.Column("cutover_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opening_state", sa.JSON(), nullable=True),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("batch_id", "source_row_number", name="uq_cutover_items_row"),
    )
    op.create_index("ix_cutover_items_batch_id", "cutover_items", ["batch_id"])
    op.create_index("ix_cutover_items_lot_id", "cutover_items", ["lot_id"])

    # ── cutover_staging_rows ──────────────────────────────────────────────────
    op.create_table(
        "cutover_staging_rows",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("cutover_batches.id"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("normalized", sa.JSON(), nullable=True),
        sa.Column("validation_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("validation_errors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("batch_id", "row_number", name="uq_cutover_staging_row"),
    )
    op.create_index("ix_cutover_staging_rows_batch_id", "cutover_staging_rows", ["batch_id"])

    # ── opening_balance_corrections ───────────────────────────────────────────
    op.create_table(
        "opening_balance_corrections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("opening_id", sa.Integer(), sa.ForeignKey("opening_balances.id"), nullable=False),
        sa.Column("field", sa.String(60), nullable=False),
        sa.Column("old_value", sa.String(300), nullable=True),
        sa.Column("new_value", sa.String(300), nullable=True),
        sa.Column("delta", sa.String(300), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requested_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("approved_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_opening_balance_corrections_opening_id",
                    "opening_balance_corrections", ["opening_id"])

    # ── extensiones de opening_balances (R-67 PARTIAL_REUSE) ──────────────────
    op.add_column("opening_balances", sa.Column("cutover_item_id", sa.Integer(),
                  sa.ForeignKey("cutover_items.id"), nullable=True))
    op.add_column("opening_balances", sa.Column("cutover_datetime", sa.DateTime(timezone=True), nullable=True))
    for campo in ("mortality_status", "culls_status", "feed_status", "egg_production_status",
                  "chicks_hatched_status", "broiler_received_status"):
        op.add_column("opening_balances", sa.Column(campo, sa.String(15), nullable=False,
                      server_default="KNOWN"))
    op.add_column("opening_balances", sa.Column("source_system", sa.String(40), nullable=True))
    op.add_column("opening_balances", sa.Column("source_reference", sa.String(200), nullable=True))
    op.add_column("opening_balances", sa.Column("legacy_lot_code", sa.String(60), nullable=True))

    # ── extensiones de lots (NATIVE/MIGRATED + provenance) ────────────────────
    op.add_column("lots", sa.Column("origin", sa.String(15), nullable=False, server_default="NATIVE"))
    op.add_column("lots", sa.Column("legacy_lot_code", sa.String(60), nullable=True))
    op.add_column("lots", sa.Column("source_system", sa.String(40), nullable=True))
    op.add_column("lots", sa.Column("source_reference", sa.String(200), nullable=True))
    op.create_unique_constraint("uq_lots_company_legacy_code", "lots",
                                ["company_id", "legacy_lot_code"])


def downgrade() -> None:
    op.drop_constraint("uq_lots_company_legacy_code", "lots", type_="unique")
    for campo in ("source_reference", "source_system", "legacy_lot_code", "origin"):
        op.drop_column("lots", campo)

    for campo in ("legacy_lot_code", "source_reference", "source_system", "broiler_received_status",
                  "chicks_hatched_status", "egg_production_status", "feed_status", "culls_status",
                  "mortality_status", "cutover_datetime", "cutover_item_id"):
        op.drop_column("opening_balances", campo)

    op.drop_index("ix_opening_balance_corrections_opening_id", table_name="opening_balance_corrections")
    op.drop_table("opening_balance_corrections")
    op.drop_index("ix_cutover_staging_rows_batch_id", table_name="cutover_staging_rows")
    op.drop_table("cutover_staging_rows")
    op.drop_index("ix_cutover_items_lot_id", table_name="cutover_items")
    op.drop_index("ix_cutover_items_batch_id", table_name="cutover_items")
    op.drop_table("cutover_items")
    op.drop_index("ix_cutover_batches_status", table_name="cutover_batches")
    op.drop_index("ix_cutover_batches_business_unit", table_name="cutover_batches")
    op.drop_index("ix_cutover_batches_company_id", table_name="cutover_batches")
    op.drop_table("cutover_batches")
