"""Contrato de cierre de lote — `GA-REM-029`, hallazgos `R-73` y `R-74`.

Cubre `AC01`…`AC09`.

`POST /lots/{id}/close` respondía **500 siempre**: el servicio devuelve un resumen y la
ruta lo validaba como `LotRead`. Como es el único punto del backend que asigna
`status = "closed"`, ningún lote podía cerrarse y el paso terminal de `P-06` era
inalcanzable.

Al reconstruir el contrato apareció `R-74`: la precondición de `BR-05` —pesaje y alimento,
sin los cuales no hay FCR— colgaba del evento `lot_closure`, que no cierra nada, y faltaba
en el endpoint, que sí.

Fechas siempre relativas al reloj (`R-28`).
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago, reference_today

PREFIJO = "CL-TEST-"

DIAS_DE_VIDA = 90

#: Cifras deliberadamente distintas entre sí y de cero: si el resumen las confundiera —o
#: devolviera ceros—, la comprobación por igualdad lo delata. Un `>= 0` no lo haría.
MORTALIDAD = 7
ALIMENTO_KG = 123.5
HUEVOS = 250
AVES_RECIBIDAS = 400


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.corrections.models import CorrectionLog
    from app.lots.models import LotPhase, OpeningBalance
    from app.review.models import ApprovalAction
    from app.operations.models import (
        BirdMovement, EggMovement, FeedMovement, InspectionDetail, OperationalEvent,
    )

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            eventos = (await c.execute(
                select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(ids)))
            ).scalars().all()
            if eventos:
                for sub in (BirdMovement, EggMovement, FeedMovement, InspectionDetail,
                            ApprovalAction, CorrectionLog):
                    await c.execute(delete(sub).where(sub.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
    await e.dispose()


# ── utilidades ────────────────────────────────────────────────────────────────

async def _crear_lote(client, cabecera, ids, **extra):
    cuerpo = {
        "company_id": ids["company_id"],
        "farm_id": ids["farm_id"],
        "house_id": ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder",
        "sex": "mixed",
        "start_date": iso_days_ago(DIAS_DE_VIDA),
    }
    cuerpo.update(extra)
    r = await client.post("/api/v1/lots", headers=cabecera, json=cuerpo)
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _evento(client, cabecera, ids, lot_id, tipo, **extra):
    r = await client.post(
        "/api/v1/operations",
        headers=cabecera,
        json={
            "lot_id": lot_id,
            "farm_id": ids["farm_id"],
            "house_id": ids["house_id"],
            "event_type": tipo,
            "event_date": iso_days_ago(7),
            **extra,
        },
    )
    assert r.status_code == 201, f"{tipo}: {r.text}"
    return r.json()["id"]


async def _requisitos_br05(client, cabecera, ids, lot_id):
    """Pesaje y alimento: lo mínimo que `BR-05` exige para poder cerrar."""
    await _evento(client, cabecera, ids, lot_id, "weight_recording",
                  bird_movements=[{"sex": "mixed", "quantity": 10, "avg_weight": 2000}])
    await _evento(client, cabecera, ids, lot_id, "feed_registration",
                  feed_movements=[{"quantity_kg": ALIMENTO_KG}])


async def _lote_cerrable(client, cabecera, ids, **extra):
    lot_id = await _crear_lote(client, cabecera, ids, **extra)
    await _requisitos_br05(client, cabecera, ids, lot_id)
    return lot_id


# ── AC01 · AC02 · AC03 · AC04 · AC08 ──────────────────────────────────────────

async def test_t_073_01_el_cierre_responde_con_el_resumen(
    client, auth_headers, seeded_ids, motor
):
    """`AC01`, `AC03`, `AC08` · 200 con cifras ciertas, no un 500.

    El escenario fija mortalidad, alimento y huevos en valores distintos entre sí, y
    aprueba **uno solo** de los eventos: así `approved_events` y `total_events` no pueden
    coincidir por casualidad y se comprueba que son dos cuentas distintas.
    """
    from app.auth.security import create_access_token

    lot_id = await _crear_lote(client, auth_headers, seeded_ids)

    await _evento(client, auth_headers, seeded_ids, lot_id, "bird_reception",
                  bird_movements=[{"sex": "mixed", "quantity": AVES_RECIBIDAS}])
    id_mortalidad = await _evento(
        client, auth_headers, seeded_ids, lot_id, "mortality_recording",
        bird_movements=[{"sex": "mixed", "quantity": MORTALIDAD}])
    await _requisitos_br05(client, auth_headers, seeded_ids, lot_id)
    await _evento(client, auth_headers, seeded_ids, lot_id, "egg_collection",
                  egg_movements=[{"quantity": HUEVOS, "egg_type": "fertile"}])

    # Un evento aprobado, y solo uno. `BR-14` impide que lo apruebe quien lo registró, así
    # que interviene el aprobador: es el camino real de `P-07`, ya certificado.
    enviado = await client.post(
        f"/api/v1/operations/{id_mortalidad}/submit", headers=auth_headers)
    assert enviado.status_code in (200, 201), enviado.text
    aprobador = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_approver_id"])})}
    revision = await client.post(
        f"/api/v1/review/start/{id_mortalidad}", headers=aprobador)
    assert revision.status_code in (200, 201), revision.text
    aprobado = await client.post("/api/v1/approvals/approve", headers=aprobador,
                                 json={"event_id": id_mortalidad})
    assert aprobado.status_code == 200, aprobado.text

    # `AC01` · responde.
    r = await client.post(f"/api/v1/lots/{lot_id}/close", headers=auth_headers)
    assert r.status_code == 200, r.text
    resumen = r.json()

    # `AC03` · y dice la verdad, campo por campo.
    assert resumen["lot_id"] == lot_id
    assert resumen["total_mortality"] == MORTALIDAD, resumen
    assert resumen["total_feed_kg"] == pytest.approx(ALIMENTO_KG), resumen
    assert resumen["total_eggs"] == HUEVOS, resumen
    assert resumen["total_events"] == 5, resumen
    assert resumen["approved_events"] == 1, resumen
    assert resumen["approved_events"] != resumen["total_events"], (
        "aprobados y totales no pueden ser la misma cuenta"
    )
    assert resumen["status"] == "closed"
    assert resumen["end_date"] == reference_today().isoformat()

    # `AC08` · la edad viene del inicio de negocio, no del alta (regresión de `R-47`).
    assert resumen["age_days"] == DIAS_DE_VIDA, resumen


async def test_t_073_02_el_contrato_esta_declarado(client, auth_headers, seeded_ids, motor):
    """`AC02` · la ruta declara su modelo de respuesta.

    Sin `response_model` nadie fijó el contrato y el desajuste vivió hasta ejecución. Con
    él, una divergencia futura entre servicio y ruta rompe en validación.
    """
    from app.lots import schemas
    from app.main import app

    ruta = next(
        (r for r in app.routes
         if getattr(r, "path", "").endswith("/lots/{lot_id}/close")), None)
    if ruta is None:  # los routers son perezosos: se busca en el router del módulo
        from app.lots.router import router
        ruta = next(r for r in router.routes if r.path.endswith("/{lot_id}/close"))

    assert ruta.response_model is schemas.LotClosureSummary, (
        f"el cierre debe declarar su contrato, no devolver algo sin tipar: {ruta.response_model}"
    )

    campos = set(schemas.LotClosureSummary.model_fields)
    assert campos == {
        "lot_id", "lot_code", "age_days", "total_mortality", "total_feed_kg",
        "total_eggs", "total_events", "approved_events", "status", "end_date",
    }, campos


async def test_t_073_03_el_lote_queda_cerrado_y_persistido(
    client, auth_headers, seeded_ids, motor
):
    """`AC04` · el cierre se guarda; se relee por HTTP, no sobre el objeto en memoria."""
    lot_id = await _lote_cerrable(client, auth_headers, seeded_ids)

    r = await client.post(f"/api/v1/lots/{lot_id}/close", headers=auth_headers)
    assert r.status_code == 200, r.text

    leido = await client.get(f"/api/v1/lots/{lot_id}", headers=auth_headers)
    assert leido.status_code == 200, leido.text
    assert leido.json()["status"] == "closed"
    assert leido.json()["end_date"].startswith(reference_today().isoformat())

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == lot_id))).scalar_one()
    assert lote.status == "closed"
    assert lote.end_date is not None


# ── AC05 · BR-05 protege el cierre real ───────────────────────────────────────

@pytest.mark.parametrize("presente,ausente", [("feed_registration", "pesaje"),
                                              ("weight_recording", "alimento")])
async def test_t_074_04_br05_bloquea_el_cierre_incompleto(
    client, auth_headers, seeded_ids, motor, presente, ausente
):
    """`AC05` · sin pesaje o sin alimento no se cierra, y se cita `BR-05`.

    `R-74`. La guarda existía pero colgaba del evento `lot_closure`, que no cierra el lote.
    Aquí se comprueba en el endpoint, que es el único que lo cierra de verdad.
    """
    lot_id = await _crear_lote(client, auth_headers, seeded_ids)
    if presente == "feed_registration":
        await _evento(client, auth_headers, seeded_ids, lot_id, "feed_registration",
                      feed_movements=[{"quantity_kg": ALIMENTO_KG}])
    else:
        await _evento(client, auth_headers, seeded_ids, lot_id, "weight_recording",
                      bird_movements=[{"sex": "mixed", "quantity": 10, "avg_weight": 2000}])

    r = await client.post(f"/api/v1/lots/{lot_id}/close", headers=auth_headers)
    assert r.status_code == 400, f"se cerró un lote sin {ausente}: {r.text}"
    assert r.json().get("rule") == "BR-05", r.json()

    # Y el lote sigue vivo: un rechazo no debe dejar el cierre a medias.
    leido = await client.get(f"/api/v1/lots/{lot_id}", headers=auth_headers)
    assert leido.json()["status"] == "active"


# ── AC06 · no se cierra dos veces ─────────────────────────────────────────────

async def test_t_073_05_el_segundo_cierre_se_rechaza(
    client, auth_headers, seeded_ids, motor
):
    """`AC06` · el segundo intento da 400 y **no** toca la fecha del primero."""
    lot_id = await _lote_cerrable(client, auth_headers, seeded_ids)

    primero = await client.post(f"/api/v1/lots/{lot_id}/close", headers=auth_headers)
    assert primero.status_code == 200, primero.text
    fecha_original = primero.json()["end_date"]

    segundo = await client.post(f"/api/v1/lots/{lot_id}/close", headers=auth_headers)
    assert segundo.status_code == 400, segundo.text

    leido = await client.get(f"/api/v1/lots/{lot_id}", headers=auth_headers)
    assert leido.json()["end_date"].startswith(fecha_original), (
        "el intento rechazado alteró la fecha del cierre válido"
    )


# ── AC07 · aislamiento entre empresas ─────────────────────────────────────────

async def test_t_073_06_no_se_cierra_el_lote_de_otra_empresa(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC07` · un usuario ajeno **con permiso** no alcanza el lote de otra empresa.

    El sujeto se provisiona con `lots:create` a propósito: sin ese permiso el 403 llegaría
    antes que el aislamiento y la prueba no mediría nada. Tampoco vale un super admin, que
    está exento por diseño (`R-36`).

    CONTROL y TRATAMIENTO con el mismo sujeto y la misma llamada: lo único que cambia es de
    quién es el lote.
    """
    sufijo = uuid.uuid4().hex[:8]

    rol = await client.post("/api/v1/roles", headers=auth_headers, json={
        "name": f"CL-TEST Cierre {sufijo}",
        "description": "Sujeto de aislamiento de GA-REM-029 AC07",
        "permissions": [
            {"module": "lots", "action": "create"}, {"module": "lots", "action": "read"},
            {"module": "operations", "action": "create"},
            {"module": "operations", "action": "read"},
            {"module": "masters", "action": "read"},
        ],
    })
    assert rol.status_code in (200, 201), rol.text

    clave = f"Cl-{uuid.uuid4().hex[:12]}!"
    usuario = await client.post("/api/v1/users", headers=auth_headers, json={
        "username": f"cl_test_{sufijo}",
        "email": f"cl_test_{sufijo}@example.com",
        "password": clave,
        "first_name": "Cierre", "last_name": "Ajeno",
        "company_id": seeded_ids["company_id_2"],
        "role_id": rol.json()["id"],
        "view_type": "web",
    })
    assert usuario.status_code in (200, 201), usuario.text

    entrada = await client.post("/api/v1/login", json={
        "username": f"cl_test_{sufijo}", "password": clave})
    assert entrada.status_code == 200, entrada.text
    sujeto = {"Authorization": f"Bearer {entrada.json()['access_token']}"}

    # El lote ajeno: de la empresa 1, cerrable, listo para que nadie de fuera lo toque.
    ajeno = await _lote_cerrable(client, auth_headers, seeded_ids)

    # TRATAMIENTO · el sujeto va contra el lote de otra empresa.
    cruzado = await http_client.post(f"/api/v1/lots/{ajeno}/close", headers=sujeto)
    assert cruzado.status_code == 404, (
        f"un usuario de otra empresa alcanzó el lote ajeno: {cruzado.status_code} {cruzado.text}"
    )
    sigue = await client.get(f"/api/v1/lots/{ajeno}", headers=auth_headers)
    assert sigue.json()["status"] == "active", "el intento cruzado cerró el lote"

    # CONTROL · el mismo sujeto, la misma llamada, sobre un lote **suyo**: se acepta.
    # Sin esto, el 404 anterior podría deberse a cualquier cosa menos al aislamiento.
    propios = {"company_id": seeded_ids["company_id_2"],
               "farm_id": None, "house_id": None}
    # El administrador pertenece a la empresa 1; para sembrar los maestros de la 2 recorre
    # `switch-company`, que es el camino que el producto ofrece y el que un humano usaría.
    cambio = await client.post("/api/v1/switch-company", headers=auth_headers,
                               json={"company_id": seeded_ids["company_id_2"]})
    assert cambio.status_code == 200, cambio.text
    admin_2 = {"Authorization": f"Bearer {cambio.json()['access_token']}"}

    granja = await client.post("/api/v1/masters/farms", headers=admin_2, json={
        "company_id": seeded_ids["company_id_2"],
        "name": f"CL-TEST Granja {sufijo}", "code": f"CLT{sufijo[:6]}"})
    assert granja.status_code in (200, 201), granja.text
    propios["farm_id"] = granja.json()["id"]
    galpon = await client.post("/api/v1/masters/houses", headers=admin_2, json={
        "farm_id": propios["farm_id"], "name": f"CL-TEST Galpón {sufijo}",
        "code": f"CLH{sufijo[:6]}"})
    assert galpon.status_code in (200, 201), galpon.text
    propios["house_id"] = galpon.json()["id"]

    propio = await _lote_cerrable(http_client, sujeto, propios)
    control = await http_client.post(f"/api/v1/lots/{propio}/close", headers=sujeto)
    assert control.status_code == 200, (
        f"CONTROL falló: el sujeto no puede cerrar ni su propio lote, "
        f"así que el 404 anterior no prueba aislamiento: {control.text}"
    )


# ── AC09 · sin permiso no se cierra ───────────────────────────────────────────

async def test_t_073_07_sin_permiso_no_se_cierra(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC09` · `lots:create` es obligatorio; el lote sobrevive al intento."""
    from app.auth.security import create_access_token

    lot_id = await _lote_cerrable(client, auth_headers, seeded_ids)

    # El operador de pruebas tiene `lots:READ`, no `CREATE`.
    operador = {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_operator_id"])})}

    r = await http_client.post(f"/api/v1/lots/{lot_id}/close", headers=operador)
    assert r.status_code == 403, r.text

    leido = await client.get(f"/api/v1/lots/{lot_id}", headers=auth_headers)
    assert leido.json()["status"] == "active"
