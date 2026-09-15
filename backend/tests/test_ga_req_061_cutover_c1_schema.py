"""GA-REQ-061 · T14 · C1 — fundación de datos del cutover (RED).

Rojo en HEAD (`47ad7f8`): el catálogo de permisos no expone el módulo `cutover`
y no existen las tablas/columnas del cutover. La Implementación (C2) añade:
`cutover_batches` · `cutover_items` · `cutover_staging_rows` ·
`opening_balance_corrections`; extensiones de `opening_balances`
(`cutover_item_id`, `cutover_datetime`, `mortality_status`, …) y de `lots`
(`origin`, `legacy_lot_code`, …) — extensión de `OpeningBalance` R-67
(`PARTIAL_REUSE`), **sin concepto paralelo** de saldo inicial.
"""
import pytest
from sqlalchemy import text

import app.database as database


@pytest.mark.asyncio
async def test_c1_catalogo_de_permisos_incluye_modulo_cutover(auth_headers, client):
    """El catálogo cerrado de `R-199` debe listar el módulo `cutover` (RBAC del cutover)."""
    r = await client.get("/api/v1/roles/permissions-catalog", headers=auth_headers)
    assert r.status_code == 200
    modulos = r.json()["modules"]
    assert "cutover" in modulos, f"módulo cutover ausente del catálogo: {modulos}"


@pytest.mark.asyncio
async def test_c1_tablas_y_columnas_del_cutover_existen():
    """Las tablas nuevas y las columnas de extensión existen en el esquema."""
    async with database.engine.connect() as conexion:
        tablas = set((await conexion.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        ))).scalars().all())
        faltan_tablas = {"cutover_batches", "cutover_items", "cutover_staging_rows",
                         "opening_balance_corrections"} - tablas
        assert not faltan_tablas, f"tablas del cutover ausentes: {sorted(faltan_tablas)}"

        async def columnas(tabla: str) -> set[str]:
            return set((await conexion.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = :t"
            ), {"t": tabla})).scalars().all())

        cols_opening = await columnas("opening_balances")
        faltan_opening = {"cutover_item_id", "cutover_datetime", "mortality_status",
                          "source_system"} - cols_opening
        assert not faltan_opening, f"extensiones de opening_balances ausentes: {sorted(faltan_opening)}"

        cols_lots = await columnas("lots")
        faltan_lots = {"origin", "legacy_lot_code", "source_system"} - cols_lots
        assert not faltan_lots, f"extensiones de lots ausentes: {sorted(faltan_lots)}"
