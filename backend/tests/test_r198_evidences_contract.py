"""R-198 · RED — evidencias persistentes en el detalle, gate por estado y borrado atómico.

Diseño: `specs/R-198/R-198_AC_MATRIX.md` (AC-01…09). Rojo en HEAD:

  01 el detalle descarta `evidences` (siempre `[]`) → subir y “F5” no muestra nada.
  02 idem tras relogin (misma causa: contrato del detalle).
  03 adjuntar/borrar en estado no editable **no** se deniega (sin gate).
  05 el borrado elimina el fichero **antes** del commit: un fallo de commit lo pierde.
  07 el detalle descarta `egg_storage_records` (C-04: mismo arreglo).

Controles ya verdes: 04 (auditoría de alta/baja — cubierta por `P1-12-REOPEN`/T-06) y
06 (la ruta dedicada `GET /{id}/evidences` sigue intacta).

Fechas relativas (`R-28`); ids reales por `seeded_ids`.
"""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.business_units.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.lots.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.audit.models import AuditAction, AuditModule
from tests.time_reference import iso_days_ago

PREFIJO = "R198-"

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e

    from app.corrections.models import CorrectionLog
    from app.lots.models import LotPhase, OpeningBalance
    from app.masters.models import Lot
    from app.audit.models import AuditLog
    from app.operations.models import (
        BirdMovement,
        EggMovement,
        EggStorage,
        Evidence,
        FeedMovement,
        InspectionDetail,
        OperationalAlert,
        OperationalEvent,
    )
    from app.review.models import ApprovalAction, ReviewBatch

    async with e.begin() as c:
        lot_ids = (
            await c.execute(select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))
        ).scalars().all()
        event_ids: list[int] = []
        if lot_ids:
            event_ids = (
                await c.execute(
                    select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(lot_ids))
                )
            ).scalars().all()
        if event_ids:
            # Los ficheros de evidencia viven en disco: se retiran antes de borrar filas.
            rutas = (
                await c.execute(select(Evidence.file_path).where(Evidence.event_id.in_(event_ids)))
            ).scalars().all()
            for ruta in rutas:
                try:
                    os.remove(ruta)
                except OSError:
                    pass
            for tabla in (BirdMovement, EggMovement, FeedMovement, InspectionDetail,
                          EggStorage, Evidence, OperationalAlert, ApprovalAction, CorrectionLog):
                await c.execute(delete(tabla).where(tabla.event_id.in_(event_ids)))
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_id.in_([str(i) for i in event_ids])))
            await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(event_ids)))
        if lot_ids:
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(lot_ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(lot_ids)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(lot_ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(lot_ids)))
        await c.execute(delete(ReviewBatch).where(ReviewBatch.batch_name.like(f"{PREFIJO}%")))

        # Escenario aislado (test 07): empresa/rollo propios.
        p = {"p": f"{PREFIJO}%"}
        for sql in (
            "DELETE FROM user_business_units WHERE user_id IN "
            "(SELECT id FROM users WHERE username LIKE :p)",
            "DELETE FROM audit_logs WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM audit_logs WHERE entity_id IN "
            "(SELECT CAST(id AS TEXT) FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM notifications WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM operational_alerts WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM egg_storage WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM egg_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM bird_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM feed_movements WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM inspection_details WHERE event_id IN "
            "(SELECT id FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM operational_events WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM lots WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM houses WHERE farm_id IN "
            "(SELECT id FROM farms WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p))",
            "DELETE FROM farms WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM company_business_units WHERE company_id IN "
            "(SELECT id FROM companies WHERE name LIKE :p)",
            "DELETE FROM permissions WHERE role_id IN "
            "(SELECT id FROM roles WHERE name LIKE :p)",
            "DELETE FROM users WHERE username LIKE :p",
            "DELETE FROM roles WHERE name LIKE :p",
            "DELETE FROM companies WHERE name LIKE :p",
        ):
            await c.execute(text(sql), p)
    await e.dispose()


async def _lote(client, cabecera, ids) -> int:
    r = await client.post("/api/v1/lots", headers=cabecera, json={
        "company_id": ids["company_id"],
        "farm_id": ids["farm_id"],
        "house_id": ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder",
        "sex": "mixed",
        "start_date": iso_days_ago(60),
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _evento(client, cabecera, ids, lot_id) -> int:
    r = await client.post("/api/v1/operations", headers=cabecera, json={
        "lot_id": lot_id,
        "farm_id": ids["farm_id"],
        "house_id": ids["house_id"],
        "event_type": "weight_recording",
        "event_date": iso_days_ago(5),
        "bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 2000}],
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _subir(client, cabecera, event_id) -> tuple[int, str]:
    """Sube un PNG válido; devuelve `(evidence_id, ruta_en_disco)`."""
    r = await client.post(
        f"/api/v1/operations/{event_id}/evidences", headers=cabecera,
        files={"file": (f"{PREFIJO}{uuid.uuid4().hex[:6]}.png", PNG, "image/png")})
    assert r.status_code == 201, r.text
    return r.json()["id"], None  # la ruta se lee de la base en el momento de usarla


async def _ruta_de(motor, evidence_id: int) -> str:
    from app.operations.models import Evidence

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        return (await s.execute(
            select(Evidence.file_path).where(Evidence.id == evidence_id)
        )).scalar_one()


async def _estado(motor, event_id: int, estado: str) -> None:
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        await s.execute(text(
            "UPDATE operational_events SET status = UPPER(:e)::eventstatus WHERE id = :i"
        ), {"e": estado, "i": event_id})
        await s.commit()


async def _registros(motor, accion, **filtros):
    from app.audit.models import AuditLog

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        q = select(AuditLog).where(AuditLog.action == accion)
        for campo, valor in filtros.items():
            q = q.where(getattr(AuditLog, campo) == valor)
        return (await s.execute(q)).scalars().all()


# ── 01 · el detalle devuelve las evidencias (contrato, F5) ────────────────────

async def test_r198_01_el_detalle_devuelve_las_evidencias(client, auth_headers, seeded_ids, motor):
    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id)
    ev_id, _ = await _subir(client, auth_headers, event_id)

    detalle = await client.get(f"/api/v1/operations/{event_id}", headers=auth_headers)
    assert detalle.status_code == 200, detalle.text
    ids = [e["id"] for e in (detalle.json().get("evidences") or [])]
    assert ev_id in ids, f"el detalle no devuelve la evidencia recién subida (ids={ids})"

    # “F5”: segunda lectura, mismo contrato.
    detalle2 = await client.get(f"/api/v1/operations/{event_id}", headers=auth_headers)
    ids2 = [e["id"] for e in (detalle2.json().get("evidences") or [])]
    assert ev_id in ids2, "tras recargar, la evidencia desaparece del detalle"


# ── 02 · tras relogin sigue visible ───────────────────────────────────────────

async def test_r198_02_tras_relogin_sigue_visible(client, auth_headers, seeded_ids, motor,
                                                  test_credentials):
    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id)
    ev_id, _ = await _subir(client, auth_headers, event_id)

    usuario, clave = test_credentials
    entrada = await client.post("/api/v1/login", json={"username": usuario, "password": clave})
    assert entrada.status_code == 200, entrada.text
    cab = {"Authorization": f"Bearer {entrada.json()['access_token']}"}

    detalle = await client.get(f"/api/v1/operations/{event_id}", headers=cab)
    ids = [e["id"] for e in (detalle.json().get("evidences") or [])]
    assert ev_id in ids, "tras relogin, la evidencia desaparece del detalle"


# ── 03 · estado no editable ⇒ denegado en servidor ────────────────────────────

async def test_r198_03_estado_no_editable_deniega(client, auth_headers, seeded_ids, motor):
    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id)
    ev_id, _ = await _subir(client, auth_headers, event_id)

    await _estado(motor, event_id, "approved")

    nueva = await client.post(
        f"/api/v1/operations/{event_id}/evidences", headers=auth_headers,
        files={"file": (f"{PREFIJO}nueva.png", PNG, "image/png")})
    assert nueva.status_code == 400, (
        f"adjuntar en `approved` debería denegarse en servidor (vio {nueva.status_code})")

    borrado = await client.delete(
        f"/api/v1/operations/{event_id}/evidences/{ev_id}", headers=auth_headers)
    assert borrado.status_code == 400, (
        f"borrar en `approved` debería denegarse en servidor (vio {borrado.status_code})")


# ── 04 · alta y baja auditadas (control: cubierto por P1-12/T-06) ─────────────

async def test_r198_04_alta_y_baja_auditadas(client, auth_headers, seeded_ids, motor):
    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id)
    ev_id, _ = await _subir(client, auth_headers, event_id)

    altas = await _registros(motor, AuditAction.CREATED,
                             module=AuditModule.OPERATIONS, entity_type="evidence",
                             entity_id=str(ev_id))
    assert len(altas) == 1, "subir la evidencia no dejó fila"

    borrado = await client.delete(
        f"/api/v1/operations/{event_id}/evidences/{ev_id}", headers=auth_headers)
    assert borrado.status_code == 204, borrado.text

    bajas = await _registros(motor, AuditAction.DELETED,
                             module=AuditModule.OPERATIONS, entity_type="evidence",
                             entity_id=str(ev_id))
    assert len(bajas) == 1, "borrar la evidencia no dejó fila"


# ── 05 · el orden del borrado protege el fichero (commit → remove) ────────────

async def test_r198_05_el_fichero_se_borra_solo_tras_el_commit(
    client, auth_headers, seeded_ids, motor, monkeypatch
):
    from app.operations.service import OperationsService

    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id)
    ev_id, _ = await _subir(client, auth_headers, event_id)
    ruta = await _ruta_de(motor, ev_id)
    assert os.path.exists(ruta), "la evidencia subida no está en disco"

    llamadas: list[str] = []

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as sesion:

        class SesionQueRegistra:
            """Proxy del `AsyncSession` que anota el orden commit/remove."""

            def __init__(self, real):
                self._real = real

            def add(self, *a, **k):
                return self._real.add(*a, **k)

            async def execute(self, *a, **k):
                return await self._real.execute(*a, **k)

            async def delete(self, *a, **k):
                return await self._real.delete(*a, **k)

            async def flush(self):
                return await self._real.flush()

            async def commit(self):
                llamadas.append("commit")
                return await self._real.commit()

        monkeypatch.setattr(os, "remove", lambda p: llamadas.append("remove"))

        servicio = OperationsService(SesionQueRegistra(sesion), {
            "id": seeded_ids["user_admin_id"], "company_id": seeded_ids["company_id"],
        })
        await servicio.delete_evidence(event_id, ev_id)

    assert llamadas == ["commit", "remove"], (
        f"orden de borrado {llamadas}: el fichero debe retirarse **después** del commit "
        "(si el commit falla, el fichero sobrevive)")


# ── 06 · la ruta dedicada sigue intacta (control) ─────────────────────────────

async def test_r198_06_la_ruta_dedicada_sigue_intacta(client, auth_headers, seeded_ids, motor):
    lot_id = await _lote(client, auth_headers, seeded_ids)
    event_id = await _evento(client, auth_headers, seeded_ids, lot_id)
    ev_id, _ = await _subir(client, auth_headers, event_id)

    r = await client.get(f"/api/v1/operations/{event_id}/evidences", headers=auth_headers)
    assert r.status_code == 200, r.text
    ids = [e["id"] for e in r.json()]
    assert ev_id in ids, "la ruta dedicada perdió la evidencia"


# ── 07 · el detalle devuelve el almacenamiento de huevos (C-04) ───────────────

async def test_r198_07_el_detalle_devuelve_el_almacenamiento(client, test_database_url, motor):
    from app.auth.models import Permission, PermissionAction, Role, User
    from app.auth.security import create_access_token, hash_password
    from app.business_units.models import BusinessUnit, CompanyBusinessUnit
    from app.business_units.service import conceder_unidad
    from app.masters.models import (BirdTypeEnum, Company, Farm, FarmType, House,
                                    Lot, LotStatus)

    motor_esc = create_async_engine(test_database_url)
    async with async_sessionmaker(motor_esc, expire_on_commit=False)() as s:
        empresa = Company(name=f"{PREFIJO}C-{uuid.uuid4().hex[:6]}", is_active=True)
        s.add(empresa)
        await s.flush()
        unidades = {u.code: u for u in (await s.execute(select(BusinessUnit))).scalars()}
        hab = CompanyBusinessUnit(company_id=empresa.id,
                                  business_unit_id=unidades["hatchery"].id, is_enabled=True)
        s.add(hab)
        await s.flush()
        rol = Role(name=f"{PREFIJO}R-{uuid.uuid4().hex[:6]}", company_id=empresa.id, is_active=True)
        s.add(rol)
        await s.flush()
        for accion in (PermissionAction.CREATE, PermissionAction.READ, PermissionAction.UPDATE):
            s.add(Permission(role_id=rol.id, module="operations", action=accion,
                             scope_type="company"))
        await s.flush()
        operador = User(first_name="OP", last_name="R198", email=f"{PREFIJO}{uuid.uuid4().hex[:8]}@e.test",
                        username=f"{PREFIJO}u-{uuid.uuid4().hex[:6]}",
                        hashed_password=hash_password("x"), company_id=empresa.id,
                        role_id=rol.id, is_active=True)
        s.add(operador)
        await s.flush()
        await conceder_unidad(s, user=operador, company_business_unit=hab)
        planta = Farm(company_id=empresa.id, name=f"{PREFIJO}PLANTA",
                      code=f"{PREFIJO}P-{uuid.uuid4().hex[:4]}",
                      farm_type=FarmType.BREEDING, is_active=True)
        s.add(planta)
        await s.flush()
        galpon = House(farm_id=planta.id, name=f"{PREFIJO}G", capacity=100_000, is_active=True)
        s.add(galpon)
        await s.flush()
        lote = Lot(company_id=empresa.id, lot_code=f"{PREFIJO}LH-{uuid.uuid4().hex[:6]}",
                   bird_type=BirdTypeEnum.HATCHERY, status=LotStatus.ACTIVE,
                   farm_id=planta.id, house_id=galpon.id)
        s.add(lote)
        await s.commit()
        datos = {"empresa": empresa.id, "operador": operador.id, "planta": planta.id,
                 "galpon": galpon.id, "lote": lote.id}
    await motor_esc.dispose()

    cab = {"Authorization": "Bearer " + create_access_token(data={"sub": str(datos["operador"])})}
    alta = await client.post("/api/v1/operations", headers=cab, json={
        "lot_id": datos["lote"],
        "farm_id": datos["planta"],
        "house_id": datos["galpon"],
        "event_type": "egg_reception_hatchery",
        "event_date": iso_days_ago(2),
        "egg_storage_records": [{"quantity": 100, "arrival_date": iso_days_ago(2)}],
        "egg_movements": [{"egg_type": "fertile", "quantity": 100}],
    })
    assert alta.status_code == 201, alta.text
    event_id = alta.json()["id"]

    detalle = await client.get(f"/api/v1/operations/{event_id}", headers=cab)
    assert detalle.status_code == 200, detalle.text
    almacen = detalle.json().get("egg_storage_records") or []
    assert len(almacen) == 1, (
        f"el detalle no devuelve el almacenamiento de huevos (vio {len(almacen)})")
    assert almacen[0]["quantity"] == 100
