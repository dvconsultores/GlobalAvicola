"""GA-REQ-061 · T14 · C7 — matriz RED completa (huecos de CUT-RED-01..22).

CAda caso que C1–C6 ya cubrían queda referenciado en el docstring; aquí viven los
huecos: 01/02/03 (cross-company), 04 (BU OFF), 05 (sin grant), 06 (**deficit
real**: MASTER_INACTIVE por OD-21/AC52 con control AC53), 10 (apply
concurrente), 20 (SAP: nada se fabrica, AC66-67) y 22 (colisión de
`legacy_lot_code` en el batch). Cobertura previa: 07→c2 preview (0 aplicados con
inválidas), 08→c2 checksum, 09→c4 re-apply 409, 11-14→c5 goldens, 15-16→c6 sin
rutas directas, 17-18→c6 correcciones, 19→c2 template, 21→c4 lote existente.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from test_ga_req_061_cutover_c2_lifecycle import _crear_batch, _subir, _xlsx  # noqa: E402
from test_ga_req_061_cutover_c3_lifecycle import _headers_aprobar, _otorgar  # noqa: E402
from test_ga_req_061_cutover_c4_apply import _batch_aprobado, _fase  # noqa: E402
from time_reference import days_ago, iso_days_ago  # noqa: E402

CORTE = days_ago(40).isoformat() + "T00:00:00+00:00"


def _filas(etiqueta: str) -> list[list]:
    return [
        [f"CUT-G7-{etiqueta}-1", iso_days_ago(60), 4000, 4000, 100, 100, None, "matriz C7"],
        [f"CUT-G7-{etiqueta}-2", iso_days_ago(45), 1500, 1500, 50, 50, None, "matriz C7"],
    ]


async def _rol_de(user_id: int) -> int:
    from app.auth.models import User

    async with database.async_session() as session:
        usuario = (await session.execute(select(User).where(User.id == user_id))).scalars().first()
    assert usuario is not None
    return usuario.role_id


async def _headers_ajenos(seeded_ids: dict) -> dict:
    """Actor de la empresa 2 con permisos cutover (para que el 404 sea de tenancy, no de RBAC)."""
    from app.auth.security import create_access_token

    rol = await _rol_de(seeded_ids["user_other_company_id"])
    await _otorgar(rol, ("cutover", "read"), ("cutover", "validate"),
                   ("cutover", "submit"), ("cutover", "apply"))
    return {"Authorization": "Bearer " + create_access_token(data={
        "sub": str(seeded_ids["user_other_company_id"]), "role": "operator"})}


async def _batch_cargado(client, auth_headers, seeded_ids, etiqueta: str) -> int:
    """Batch creado + cargado (validated) sin enviar."""
    await _fase()
    batch_id = await _crear_batch(client, auth_headers, cutover=CORTE)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                          headers=auth_headers, files=_subir(_xlsx(_filas(etiqueta))))
    assert r.status_code == 200 and r.json()["status"] == "validated", r.text
    return batch_id


@pytest.mark.asyncio
async def test_c7_red01_lectura_cross_company_denegada(auth_headers, http_client, seeded_ids):
    """CUT-RED-01: batch/items/validation/reconciliation de otra empresa ⇒ 404 fail-closed."""
    batch_id = await _batch_cargado(http_client, auth_headers, seeded_ids, "R1")
    ajenos = await _headers_ajenos(seeded_ids)
    for ruta in ("items", "validation", "reconciliation"):
        r = await http_client.get(f"/api/v1/cutover-batches/{batch_id}/{ruta}", headers=ajenos)
        assert r.status_code == 404, f"{ruta}: {r.status_code} {r.text}"


@pytest.mark.asyncio
async def test_c7_red02_modificacion_cross_company_denegada(auth_headers, http_client, seeded_ids):
    """CUT-RED-02: upload/submit sobre batch ajeno ⇒ 404 (la modificación no ocurre)."""
    batch_id = await _batch_cargado(http_client, auth_headers, seeded_ids, "R2")
    ajenos = await _headers_ajenos(seeded_ids)
    r = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                               headers=ajenos, files=_subir(_xlsx(_filas("R2B"))))
    assert r.status_code == 404, r.text
    r = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/submit", headers=ajenos)
    assert r.status_code == 404, r.text
    # El batch del dueño sigue intacto (validated, sin envío).
    v = await http_client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)
    assert v.json()["status"] == "validated"


@pytest.mark.asyncio
async def test_c7_red03_apply_cross_company_denegado(auth_headers, client, seeded_ids):
    """CUT-RED-03: APPLY batch ajeno ⇒ 404; el batch ajeno no se aplica."""
    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=_filas("R3"))
    ajenos = await _headers_ajenos(seeded_ids)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=ajenos)
    assert r.status_code == 404, r.text
    v = await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)
    assert v.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_c7_red04_bu_off_apply_denegado(auth_headers, client, seeded_ids):
    """CUT-RED-04/OD-16: BU apagada para la empresa ⇒ APPLY 403 aunque el actor sea global."""
    from app.business_units.models import BusinessUnit as UnidadDeNegocio
    from app.business_units.models import CompanyBusinessUnit

    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=_filas("R4"))
    async with database.async_session() as session:
        unidad = (await session.execute(
            select(UnidadDeNegocio).where(UnidadDeNegocio.code == "broiler"))).scalars().first()
        habilitacion = (await session.execute(
            select(CompanyBusinessUnit).where(
                CompanyBusinessUnit.company_id == seeded_ids["company_id"],
                CompanyBusinessUnit.business_unit_id == unidad.id))).scalars().first()
        assert habilitacion is not None
        habilitacion.is_enabled = False
        await session.commit()
    try:
        r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
        assert r.status_code == 403, r.text
        assert "BU_DISABLED" in r.text
    finally:
        async with database.async_session() as session:
            fila = (await session.execute(
                select(CompanyBusinessUnit).where(
                    CompanyBusinessUnit.company_id == seeded_ids["company_id"],
                    CompanyBusinessUnit.business_unit_id == unidad.id))).scalars().first()
            fila.is_enabled = True
            await session.commit()


@pytest.mark.asyncio
async def test_c7_red05_sin_grant_bu_denegado(auth_headers, client, seeded_ids):
    """CUT-RED-05: actor con permiso pero SIN concesión de la BU ⇒ 403; con concesión ⇒ 200."""
    from datetime import datetime, timezone

    from sqlalchemy import select as _select

    from app.auth.security import create_access_token
    from app.business_units.models import BusinessUnit as UnidadDeNegocio
    from app.business_units.models import CompanyBusinessUnit, UserBusinessUnit

    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=_filas("R5"))
    await _otorgar(await _rol_de(seeded_ids["user_operator_id"]), ("cutover", "apply"))

    async with database.async_session() as session:
        unidad = (await session.execute(
            select(UnidadDeNegocio).where(UnidadDeNegocio.code == "broiler"))).scalars().first()
    async with database.async_session() as session:
        habilitacion = (await session.execute(
            _select(CompanyBusinessUnit).where(
                CompanyBusinessUnit.company_id == seeded_ids["company_id"],
                CompanyBusinessUnit.business_unit_id == unidad.id))).scalars().first()
        concesion = (await session.execute(
            _select(UserBusinessUnit).where(
                UserBusinessUnit.user_id == seeded_ids["user_operator_id"],
                UserBusinessUnit.company_business_unit_id == habilitacion.id,
                UserBusinessUnit.revoked_at.is_(None)))).scalars().first()
        creada = False
        if concesion is not None:
            concesion.revoked_at = datetime.now(timezone.utc)
            creada = True
        await session.commit()

    headers_operador = {"Authorization": "Bearer " + create_access_token(data={
        "sub": str(seeded_ids["user_operator_id"]), "role": "operator"})}
    try:
        r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=headers_operador)
        assert r.status_code == 403, r.text
        assert "concedida" in r.text

        # Con la concesión viva, el MISMO actor SÍ aplica (no es un veto al operador).
        async with database.async_session() as session:
            if creada:
                fila = (await session.execute(
                    _select(UserBusinessUnit).where(
                        UserBusinessUnit.user_id == seeded_ids["user_operator_id"],
                        UserBusinessUnit.company_business_unit_id == habilitacion.id))).scalars().first()
                fila.revoked_at = None
                await session.commit()
            else:
                session.add(UserBusinessUnit(user_id=seeded_ids["user_operator_id"],
                                             company_business_unit_id=habilitacion.id))
                await session.commit()
        r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=headers_operador)
        assert r.status_code == 200, r.text
    finally:
        # No dejar concesiones nuevas colgando para el resto de la suite.
        async with database.async_session() as session:
            fila = (await session.execute(
                _select(UserBusinessUnit).where(
                    UserBusinessUnit.user_id == seeded_ids["user_operator_id"],
                    UserBusinessUnit.company_business_unit_id == habilitacion.id,
                    UserBusinessUnit.revoked_at.is_(None)))).scalars().first()
            if fila is not None and not creada:
                fila.revoked_at = datetime.now(timezone.utc)
                await session.commit()


@pytest.mark.asyncio
async def test_c7_red06_master_inactivo_referencia_nueva(auth_headers, http_client, seeded_ids):
    """CUT-RED-06/OD-21: granja inactiva + referencia NUEVA ⇒ MASTER_INACTIVE; histórica (AC53) se conserva."""
    from app.masters.models import BirdTypeEnum, Farm, Lot, LotStatus

    async with database.async_session() as session:
        granja = Farm(company_id=seeded_ids["company_id"], code="F-OFF7",
                      name="Granja inactiva G7", is_active=False)
        session.add(granja)
        await session.flush()
        lote_historico = Lot(company_id=seeded_ids["company_id"], lot_code="CUT-G7-AC53",
                             origin="NATIVE", bird_type=BirdTypeEnum.BROILER,
                             status=LotStatus.ACTIVE, activation_type="normal",
                             farm_id=granja.id, legacy_lot_code="CUT-G7-AC53")
        session.add(lote_historico)
        await session.commit()

    filas = [
        ["CUT-G7-NUEVO", iso_days_ago(55), 100, 100, None, None, "F-OFF7", "nueva en granja inactiva"],
        ["CUT-G7-AC53", iso_days_ago(55), 100, 100, None, None, "F-OFF7", "histórica de granja inactiva"],
    ]
    batch_id = await _crear_batch(http_client, auth_headers, cutover=days_ago(39).isoformat() + "T00:00:00+00:00")
    r = await http_client.post(f"/api/v1/cutover-batches/{batch_id}/upload",
                               headers=auth_headers, files=_subir(_xlsx(filas)))
    assert r.status_code == 200, r.text
    v = await http_client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)
    errores = v.json()["errors"]
    assert [(e["received_value"], e["error_code"]) for e in errores] == [("F-OFF7", "MASTER_INACTIVE")], errores
    assert v.json()["valid_rows"] == 1 and v.json()["invalid_rows"] == 1


@pytest.mark.asyncio
async def test_c7_red10_apply_concurrente_exactamente_uno(auth_headers, client, seeded_ids):
    """CUT-RED-10: dos applies simultáneos ⇒ exactamente uno aplica (200) y otro 409."""
    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=_filas("R10"))
    r1, r2 = await asyncio.gather(
        client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers),
        client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers),
    )
    assert sorted([r1.status_code, r2.status_code]) == [200, 409], (r1.status_code, r2.status_code)
    v = await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)
    assert v.json()["status"] == "applied"


@pytest.mark.asyncio
async def test_c7_red20_sap_no_fabrica_referencia(auth_headers, client, seeded_ids):
    """CUT-RED-20/AC66-67: `source_system=SAP` sin referencia ⇒ `null` (no se fabrica); con referencia real ⇒ copiada."""
    await _fase()
    # (a) SAP sin referencia real: jamás se inventa una.
    r = await client.post("/api/v1/cutover-batches", headers=auth_headers, json={
        "business_unit": "broiler", "cutover_datetime": CORTE,
        "source_system": "SAP", "source_reference": None})
    assert r.status_code == 201, r.text
    batch_id = r.json()["id"]
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/upload", headers=auth_headers,
                          files=_subir(_xlsx(_filas("R20A"))))
    assert r.status_code == 200, r.text
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/submit", headers=auth_headers)).status_code == 200
    await _otorgar(seeded_ids["role_approver_id"], ("cutover", "approve"), ("cutover", "read"))
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/approve",
                          headers=_headers_aprobar(seeded_ids))
    assert r.status_code == 200, r.text
    assert (await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)).status_code == 200
    rec = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    assert rec.json()["source"]["system"] == "SAP"
    assert rec.json()["source"]["reference"] is None, "una referencia SAP fabricada sería una violación AC67"

    # (b) con referencia real declarada, se conserva (no se descarta ni se inventa otra).
    r = await client.post("/api/v1/cutover-batches", headers=auth_headers, json={
        "business_unit": "broiler", "cutover_datetime": CORTE,
        "source_system": "SAP", "source_reference": "SAP-DOC-77"})
    batch_id = r.json()["id"]
    await client.post(f"/api/v1/cutover-batches/{batch_id}/upload", headers=auth_headers,
                      files=_subir(_xlsx(_filas("R20B"))))
    await client.post(f"/api/v1/cutover-batches/{batch_id}/submit", headers=auth_headers)
    await client.post(f"/api/v1/cutover-batches/{batch_id}/approve", headers=_headers_aprobar(seeded_ids))
    await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    rec = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=auth_headers)
    assert rec.json()["source"]["reference"] == "SAP-DOC-77"


@pytest.mark.asyncio
async def test_c7_red22_colision_legacy_code_en_batch(auth_headers, client, seeded_ids):
    """CUT-RED-22: misma `legacy_lot_code` dos veces en un batch ⇒ apply 422 LOT_DUPLICATE, rollback total."""
    from app.masters.models import Lot

    await _fase()
    filas = [
        ["CUT-G7-COLL", iso_days_ago(58), 100, 100, None, None, None, "duplicada"],
        ["CUT-G7-COLL", iso_days_ago(57), 200, 200, None, None, None, "duplicada ×2"],
    ]
    batch_id = await _batch_aprobado(client, auth_headers, seeded_ids, filas=filas)
    r = await client.post(f"/api/v1/cutover-batches/{batch_id}/apply", headers=auth_headers)
    assert r.status_code == 422, r.text
    assert "LOT_DUPLICATE" in r.text
    # Rollback total: ni lote aplicado ni batch aplicado.
    async with database.async_session() as session:
        lotes = (await session.execute(select(Lot).where(Lot.lot_code == "CUT-G7-COLL"))).scalars().all()
    assert lotes == []
    v = await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)
    assert v.json()["status"] == "approved"
