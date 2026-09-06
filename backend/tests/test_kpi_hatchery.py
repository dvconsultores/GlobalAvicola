"""Indicadores de incubadora y fertilidad — `GA-REM-022` enmienda A, `R-14`/`R-85`/`R-86`.

Cubre `AC01-bis`, `AC02`, `AC06` y `AC08`.

`get_kpi_hatchery` devolvía una frase en español dentro de un campo `_pct`, alegando que
faltaban los datos de carga. **La alegación era falsa**: `HatcheryParams.quantity_loaded` los
guarda y `get_hatchery_egg_balance` ya los sumaba.

Y `docs/02 §3.12.1` separa tres cocientes que el endpoint fundía en uno:
`Eclosión` sobre fértiles, `Nacimiento` y `Rendimiento` sobre cargados.

Cifras deliberadamente pequeñas y redondas: el resultado esperado se calcula a mano, no
replicando la función de producción —que podría contener el mismo error—.
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
from tests.time_reference import iso_days_ago

PREFIJO = "KH-TEST-"

#: 1.000 huevos recibidos, de los cuales 800 fértiles; se cargan 1.000; nacen 600, 540 viables.
#:
#:   nacimiento  = 600 / 1000 = 60,0 %
#:   eclosión    = 600 /  800 = 75,0 %
#:   rendimiento = 540 / 1000 = 54,0 %
#:   fertilidad  = 800 / 1000 = 80,0 %
RECIBIDOS_FERTILES = 800
RECIBIDOS_INFERTILES = 200
CARGADOS = 1_000
NACIDOS = 600
VIABLES = 540


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.corrections.models import CorrectionLog
    from app.lots.models import LotPhase, OpeningBalance
    from app.operations.models import (
        BirdMovement, EggMovement, FeedMovement, HatcheryParams, InspectionDetail,
        OperationalEvent,
    )
    from app.review.models import ApprovalAction

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(ids)))).scalars().all()
            if eventos:
                for sub in (BirdMovement, EggMovement, FeedMovement, InspectionDetail,
                            HatcheryParams, ApprovalAction, CorrectionLog):
                    await c.execute(delete(sub).where(sub.event_id.in_(eventos)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
    await e.dispose()


async def _lote(client, cab, ids, tipo="hatchery"):
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": ids["company_id"], "farm_id": ids["farm_id"],
        "house_id": ids["house_id"], "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": tipo, "sex": "mixed",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _evento(client, cab, ids, lot_id, tipo, aprobar_con=None, **extra):
    """Registra un evento y, si se pasa un aprobador, lo lleva hasta `approved`.

    Los KPI solo cuentan eventos aprobados (`GA-REM-022 AC05`), así que un evento sin
    aprobar no debe influir — y eso también se comprueba.
    """
    r = await client.post("/api/v1/operations", headers=cab, json={
        "lot_id": lot_id, "farm_id": ids["farm_id"], "house_id": ids["house_id"],
        "event_type": tipo, "event_date": iso_days_ago(0), **extra,
    })
    assert r.status_code == 201, f"{tipo}: {r.text}"
    event_id = r.json()["id"]

    if aprobar_con is not None:
        enviado = await client.post(f"/api/v1/operations/{event_id}/submit", headers=cab)
        assert enviado.status_code in (200, 201), enviado.text
        revision = await client.post(f"/api/v1/review/start/{event_id}", headers=aprobar_con)
        assert revision.status_code in (200, 201), revision.text
        aprobado = await client.post("/api/v1/approvals/approve", headers=aprobar_con,
                                     json={"event_id": event_id})
        assert aprobado.status_code == 200, aprobado.text
    return event_id


@pytest_asyncio.fixture
def aprobador(seeded_ids):
    from app.auth.security import create_access_token
    return {"Authorization": "Bearer " + create_access_token(
        data={"sub": str(seeded_ids["user_approver_id"])})}


@pytest_asyncio.fixture
async def incubadora(client, auth_headers, seeded_ids, aprobador, motor):
    """Un lote de incubadora con la cadena completa, toda aprobada."""
    lot_id = await _lote(client, auth_headers, seeded_ids)

    await _evento(client, auth_headers, seeded_ids, lot_id, "egg_reception_hatchery",
                  aprobar_con=aprobador,
                  egg_movements=[{"quantity": RECIBIDOS_FERTILES, "egg_type": "fertile"},
                                 {"quantity": RECIBIDOS_INFERTILES, "egg_type": "infertile"}])
    await _evento(client, auth_headers, seeded_ids, lot_id, "incubation_load",
                  aprobar_con=aprobador,
                  hatchery_params=[{"quantity_loaded": CARGADOS}])
    await _evento(client, auth_headers, seeded_ids, lot_id, "birth_registration",
                  aprobar_con=aprobador,
                  bird_movements=[{"sex": "mixed", "quantity": NACIDOS}])
    return lot_id


# ── AC01-bis · los tres cocientes, con su nombre ──────────────────────────────

async def test_t_014_01_la_incubadora_devuelve_numeros_y_no_texto(
    client, auth_headers, incubadora
):
    """`AC01-bis` · tres valores numéricos, cada uno con su denominador.

    El valor esperado se calcula a mano desde la fixture, no invocando la función que se
    está probando.
    """
    r = await client.get(f"/api/v1/reports/kpis/hatchery?lot_id={incubadora}",
                         headers=auth_headers)
    assert r.status_code == 200, r.text
    k = r.json()

    assert k["total_chicks_born"] == NACIDOS

    # `nacimiento` = nacidos ÷ cargados = 600 / 1000
    assert isinstance(k["nacimiento_pct"], (int, float)), (
        f"un campo `_pct` no puede devolver texto: {k['nacimiento_pct']!r}"
    )
    assert k["nacimiento_pct"] == pytest.approx(60.0), k

    # `eclosión` = nacidos ÷ **fértiles** = 600 / 800 — el denominador que `docs/02` exige
    assert k["eclosion_pct"] == pytest.approx(75.0), k

    # `rendimiento` = viables ÷ cargados. Sin descartes registrados, viables = nacidos, de
    # modo que coincide con `nacimiento`: la fórmula degrada correctamente.
    assert k["rendimiento_pct"] == pytest.approx(60.0), k

    # el alias histórico se conserva y equivale a `nacimiento`
    assert k["hatchability_pct"] == k["nacimiento_pct"]


async def test_t_015_07_el_descarte_separa_rendimiento_de_nacimiento(
    client, auth_headers, seeded_ids, aprobador, incubadora
):
    """`docs/02 §3.12.1` · viables ÷ cargados.

    Con 60 descartes aprobados: viables = 600 − 60 = 540, de 1.000 cargados → 54 %. El
    nacimiento no cambia, porque su numerador son los nacidos. Si el rendimiento no
    distinguiera el descarte, los dos seguirían coincidiendo.
    """
    await _evento(client, auth_headers, seeded_ids, incubadora, "cull_recording",
                  aprobar_con=aprobador,
                  bird_movements=[{"sex": "mixed", "quantity": NACIDOS - VIABLES}])

    k = (await client.get(f"/api/v1/reports/kpis/hatchery?lot_id={incubadora}",
                          headers=auth_headers)).json()
    assert k["nacimiento_pct"] == pytest.approx(60.0), k
    assert k["rendimiento_pct"] == pytest.approx(54.0), k


async def test_t_085_02_eclosion_y_nacimiento_no_son_el_mismo_numero(
    client, auth_headers, incubadora
):
    """`R-85` · si los denominadores se confundieran, los dos cocientes coincidirían."""
    k = (await client.get(f"/api/v1/reports/kpis/hatchery?lot_id={incubadora}",
                          headers=auth_headers)).json()
    assert k["eclosion_pct"] != k["nacimiento_pct"], (
        "eclosión se calcula sobre fértiles y nacimiento sobre cargados: "
        f"no pueden coincidir con esta fixture ({k})"
    )


# ── AC02 · sin datos suficientes, nulo y no cero ──────────────────────────────

async def test_t_014_03_sin_carga_devuelve_nulo_no_cero(
    client, auth_headers, seeded_ids, motor
):
    """`AC02` · cero significa «se midió y dio cero»; la ausencia de base es `null`.

    Confundirlas hace que un lote sin datos y un lote con eclosión nula se vean igual.
    """
    lot_id = await _lote(client, auth_headers, seeded_ids)
    r = await client.get(f"/api/v1/reports/kpis/hatchery?lot_id={lot_id}",
                         headers=auth_headers)
    assert r.status_code == 200, r.text
    k = r.json()

    assert k["nacimiento_pct"] is None, k
    assert k["eclosion_pct"] is None, k
    assert k.get("insufficient_data") is True, (
        "la ausencia de datos debe declararse de forma explícita"
    )


# ── AC05 · solo cuentan los aprobados ─────────────────────────────────────────

async def test_t_022_04_los_eventos_sin_aprobar_no_cuentan(
    client, auth_headers, seeded_ids, aprobador, incubadora
):
    """`AC05` · un nacimiento más, **sin aprobar**, no debe mover el indicador."""
    antes = (await client.get(f"/api/v1/reports/kpis/hatchery?lot_id={incubadora}",
                              headers=auth_headers)).json()["nacimiento_pct"]

    await _evento(client, auth_headers, seeded_ids, incubadora, "birth_registration",
                  bird_movements=[{"sex": "mixed", "quantity": 300}])   # sin aprobar

    despues = (await client.get(f"/api/v1/reports/kpis/hatchery?lot_id={incubadora}",
                                headers=auth_headers)).json()["nacimiento_pct"]
    assert despues == antes, (
        f"un evento sin aprobar alteró el indicador: {antes} → {despues}"
    )


# ── AC06 · fertilidad ─────────────────────────────────────────────────────────

async def test_t_086_05_la_fertilidad_se_calcula(client, auth_headers, incubadora):
    """`AC06` · 800 fértiles de 1.000 recibidos = 80 %."""
    r = await client.get(f"/api/v1/reports/kpis/egg-production?lot_id={incubadora}",
                         headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["fertilidad_pct"] == pytest.approx(80.0), r.json()


# ── AC08 · los agregados no cruzan empresas ───────────────────────────────────

async def test_t_022_06_el_agregado_no_incluye_otra_empresa(
    client, auth_headers, seeded_ids, aprobador, incubadora, motor
):
    """`AC08` · un agregado puede filtrar mal aunque las filas estén protegidas.

    Se consulta **sin** `lot_id`, que es cuando el agregado abarca toda la empresa: si el
    filtro por compañía faltara, los nacimientos de la empresa 2 entrarían en la suma.
    """
    from app.audit.models import AuditLog  # noqa: F401
    from app.operations.models import (
        BirdMovement, EventStatus, EventType, OperationalEvent,
    )

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        ajeno = OperationalEvent(
            company_id=seeded_ids["company_id_2"], lot_id=None,
            event_type=EventType.BIRTH_REGISTRATION, status=EventStatus.APPROVED,
            event_date=__import__("datetime").date.today(),
            registered_by_id=seeded_ids["user_admin_id"],
        )
        s.add(ajeno)
        await s.flush()
        s.add(BirdMovement(event_id=ajeno.id, sex="mixed", quantity=99_999))
        await s.commit()

    r = await client.get("/api/v1/reports/kpis/hatchery", headers=auth_headers)
    assert r.status_code == 200, r.text
    nacidos = r.json()["total_chicks_born"]
    assert nacidos < 99_999, (
        f"el agregado incluyó nacimientos de otra empresa: {nacidos}"
    )
