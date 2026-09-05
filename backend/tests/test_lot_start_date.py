"""Fecha de inicio del lote — `GA-REM-028`, hallazgo `R-47`.

Cubre `AC01`…`AC13`.

`POST /lots` aceptaba `start_date` y la descartaba, poniendo la de hoy. Un lote incorporado
con veinte semanas nacía con edad cero, `BR-06` rechazaba cualquier evento retroactivo y dos
indicadores salían mal. Es lo que bloqueaba `P-11`.

`RR-09`: `start_date` es el inicio del ciclo según el negocio; `created_at` es el alta en el
software. Para un lote ya en marcha difieren, y ninguno sustituye al otro.

Fechas siempre relativas al reloj (`R-28`): una fecha literal caduca sola.
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
from tests.time_reference import (
    days_ago, iso_days_ago, reference_today, reference_today_utc,
)

PREFIJO = "SD-TEST-"

#: Un lote de reproductoras a mitad de ciclo: la situación que `P-11` incorpora.
DIAS_DE_VIDA = 140


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.lots.models import LotPhase, OpeningBalance
    from app.operations.models import (
        BirdMovement, EggMovement, FeedMovement, InspectionDetail, OperationalEvent,
    )

    async with e.begin() as c:
        ids = (await c.execute(select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            eventos = (
                await c.execute(select(OperationalEvent.id).where(OperationalEvent.lot_id.in_(ids)))
            ).scalars().all()
            if eventos:
                for submovimiento in (BirdMovement, EggMovement, FeedMovement, InspectionDetail):
                    await c.execute(
                        delete(submovimiento).where(submovimiento.event_id.in_(eventos))
                    )
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            if eventos:
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
    await e.dispose()


async def _crear_lote(client, auth_headers, seeded_ids, **extra):
    cuerpo = {
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder",
        "sex": "mixed",
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/lots", headers=auth_headers, json=cuerpo)


# ── AC01 · AC02 · AC03 · AC04 ─────────────────────────────────────────────────

async def test_t_047_01_la_fecha_declarada_se_persiste(client, auth_headers, seeded_ids, motor):
    """`AC01`, `AC02`, `AC03` y `AC04` · la fecha viaja de la petición a la base y vuelve."""
    inicio = iso_days_ago(DIAS_DE_VIDA)

    r = await _crear_lote(client, auth_headers, seeded_ids, start_date=inicio)
    assert r.status_code == 201, r.text
    creado = r.json()

    # `AC02` · la respuesta la expone.
    assert creado["start_date"].startswith(inicio), creado["start_date"]

    # `AC03` · lectura inmediata, sin esperas (`R-68` certificado).
    leido = await client.get(f"/api/v1/lots/{creado['id']}", headers=auth_headers)
    assert leido.status_code == 200
    assert leido.json()["start_date"].startswith(inicio)

    # `AC01` · y está en la base, no solo en la respuesta.
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == creado["id"]))).scalar_one()
    assert lote.start_date.date() == days_ago(DIAS_DE_VIDA)

    # `AC04` y `AC11` · el alta en el software es hoy, y es otra cosa.
    # `R-80` · `created_at` es un instante UTC; se compara con el día UTC. Antes se
    # contrastaba con el día local del servidor y la prueba se rompía sola entre una
    # medianoche y otra. La intención —«el alta es de hoy»— no cambia.
    assert lote.created_at.date() == reference_today_utc()
    assert lote.start_date.date() != lote.created_at.date(), (
        "para un lote ya en marcha, el inicio del ciclo y el alta deben diferir"
    )


async def test_t_047_02_omitirla_mantiene_el_flujo_normal(client, auth_headers, seeded_ids, motor):
    """`AC08` · sin el campo, el comportamiento es el de siempre: hoy."""
    r = await _crear_lote(client, auth_headers, seeded_ids)
    assert r.status_code == 201, r.text

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == r.json()["id"]))).scalar_one()
    assert lote.start_date.date() == reference_today()


# ── AC07 · la edad deriva de la fecha de negocio ──────────────────────────────

async def test_t_047_03_la_edad_deriva_del_inicio_declarado(
    client, auth_headers, seeded_ids, motor
):
    """`AC07` · la edad del lote deriva del inicio declarado, no del alta.

    Se comprueba en el servicio y no por HTTP porque `POST /lots/{id}/close` arrastra un
    segundo defecto —su modelo de respuesta no encaja con el resumen que devuelve—, ajeno a
    la semántica de la fecha. Queda registrado como `R-73`. Lo que aquí importa es que el
    cálculo use la fecha de negocio, y eso se ejercita igual: es el mismo código.
    """
    from app.lots.service import LotService

    r = await _crear_lote(client, auth_headers, seeded_ids, start_date=iso_days_ago(DIAS_DE_VIDA))
    assert r.status_code == 201, r.text
    lot_id = r.json()["id"]

    # `BR-05` exige pesaje y alimento para poder cerrar.
    for tipo, extra in (
        ("weight_recording", {"bird_movements": [{"sex": "mixed", "quantity": 10, "avg_weight": 2000}]}),
        ("feed_registration", {"feed_movements": [{"quantity_kg": 100.0}]}),
    ):
        ev = await client.post(
            "/api/v1/operations",
            headers=auth_headers,
            json={
                "lot_id": lot_id, "farm_id": seeded_ids["farm_id"],
                "house_id": seeded_ids["house_id"], "event_type": tipo,
                "event_date": iso_days_ago(7), **extra,
            },
        )
        assert ev.status_code == 201, f"{tipo}: {ev.text}"

    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        resumen = await LotService(
            s, {"id": seeded_ids["user_admin_id"], "company_id": seeded_ids["company_id"],
                "is_super_admin": True}
        ).close_lot(lot_id)

    assert resumen["age_days"] == DIAS_DE_VIDA, (
        f"la edad debe derivar del inicio declarado, no del alta: "
        f"{resumen['age_days']} != {DIAS_DE_VIDA}"
    )


# ── AC09 · BR-06 usa la fecha correcta ────────────────────────────────────────

async def test_t_047_04_br06_acepta_lo_posterior_y_rechaza_lo_anterior(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC09` · el ancla de `BR-06` pasa a ser el inicio real del lote.

    Es el efecto que desbloquea `P-11`: sobre un lote incorporado se puede registrar la
    operación retroactiva que antes se rechazaba.
    """
    r = await _crear_lote(client, auth_headers, seeded_ids, start_date=iso_days_ago(DIAS_DE_VIDA))
    lot_id = r.json()["id"]

    comun = {
        "lot_id": lot_id,
        "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "event_type": "bird_reception",
        "bird_movements": [{"sex": "mixed", "quantity": 100}],
    }

    # Posterior al inicio y dentro del período abierto: se acepta.
    posterior = await client.post(
        "/api/v1/operations", headers=auth_headers, json={**comun, "event_date": iso_days_ago(7)}
    )
    assert posterior.status_code == 201, posterior.text

    # Anterior al inicio declarado: `BR-06` lo rechaza.
    anterior = await http_client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={**comun, "event_date": iso_days_ago(DIAS_DE_VIDA + 5)},
    )
    assert anterior.status_code == 400, anterior.text
    assert anterior.json().get("rule") == "BR-06"


# ── AC05 · AC06 · la activación manual y el saldo de apertura ─────────────────

async def test_t_047_05_la_activacion_manual_no_pisa_la_fecha_con_hoy(
    client, auth_headers, seeded_ids, motor
):
    """`AC05` y `AC06` · activar manualmente conserva una fecha de negocio, nunca la de hoy.

    `docs/02 §3.9` pide la «fecha real de inicio» al incorporar un lote, así que la
    activación la fija a partir de lo que el usuario declara. Lo que no puede ocurrir es que
    la sustituya por la fecha del sistema.
    """
    from app.lots.models import OpeningBalance
    from app.masters.models import ProductivePhase

    r = await _crear_lote(client, auth_headers, seeded_ids, start_date=iso_days_ago(DIAS_DE_VIDA))
    lot_id = r.json()["id"]

    # La siembra de la suite no crea fases productivas; el escenario crea la suya en lugar
    # de omitirse, porque una omisión no es evidencia.
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        fase = (await s.execute(select(ProductivePhase))).scalars().first()
        if fase is None:
            fase = ProductivePhase(
                name=f"{PREFIJO}Cría", code=f"{PREFIJO}CRIA", order=1,
                duration_days=140, is_initial=True, is_final=False,
            )
            s.add(fase)
            await s.commit()
            await s.refresh(fase)

    activacion = await client.post(
        "/api/v1/lots/activate-manual",
        headers=auth_headers,
        json={
            "lot_id": lot_id,
            "activation_date": iso_days_ago(DIAS_DE_VIDA),
            "phase_at_activation_id": fase.id,
            "initial_male_count": 1_000,
            "initial_female_count": 4_000,
        },
    )
    assert activacion.status_code == 201, activacion.text

    async with fabrica() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == lot_id))).scalar_one()
        apertura = (
            await s.execute(select(OpeningBalance).where(OpeningBalance.lot_id == lot_id))
        ).scalar_one()

    assert lote.start_date.date() == days_ago(DIAS_DE_VIDA), (
        "la activación no puede sustituir el inicio del ciclo por la fecha de hoy"
    )
    assert lote.start_date.date() != reference_today()
    # `R-80` · `created_at` es un instante UTC; se compara con el día UTC. Antes se
    # contrastaba con el día local del servidor y la prueba se rompía sola entre una
    # medianoche y otra. La intención —«el alta es de hoy»— no cambia.
    assert lote.created_at.date() == reference_today_utc(), "el alta sigue siendo hoy"

    # `AC06` · el saldo de apertura de `R-67` sigue intacto.
    assert apertura.initial_male_count == 1_000
    assert apertura.initial_female_count == 4_000

    from app.operations.validators import get_current_bird_balance

    async with fabrica() as s:
        assert await get_current_bird_balance(s, lot_id) == 5_000


# ── AC10 · aislamiento entre empresas ─────────────────────────────────────────

async def test_t_047_06_una_empresa_ajena_no_crea_el_lote_en_la_propia(
    client, http_client, auth_headers, seeded_ids, motor
):
    """`AC10` · con control y tratamiento: la fecha no debilita el aislamiento.

    Sin el control, un rechazo por cualquier otro motivo se leería como aislamiento. Es la
    lección de `R-72`.
    """
    from app.auth.security import create_access_token

    ajeno = {
        "Authorization": "Bearer "
        + create_access_token(data={"sub": str(seeded_ids["user_other_company_id"])})
    }
    cuerpo = {
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"],
        "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder",
        "sex": "mixed",
        "start_date": iso_days_ago(DIAS_DE_VIDA),
    }

    # CONTROL · el mismo cuerpo, con el rol adecuado, se acepta.
    propio = await client.post("/api/v1/lots", headers=auth_headers, json=dict(cuerpo))
    assert propio.status_code == 201, propio.text

    # TRATAMIENTO · el usuario de la otra empresa apunta a la granja ajena.
    cuerpo["lot_code"] = f"{PREFIJO}{uuid.uuid4().hex[:10]}"
    cruzado = await http_client.post("/api/v1/lots", headers=ajeno, json=cuerpo)
    assert cruzado.status_code != 201, (
        f"una empresa ajena creó un lote sobre la granja de otra: {cruzado.text}"
    )
