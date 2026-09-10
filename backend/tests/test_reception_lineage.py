"""Creación del vínculo generacional desde la recepción — `GA-REM-031`, hallazgo `R-78`.

Cubre `AC01`…`AC09`.

`spec.md §4.9` dice que el vínculo se crea automáticamente al registrar despacho **+**
recepción. La conjunción es simétrica y no impone orden, pero la creación vivía solo en la
rama del despacho, que busca una recepción ya existente; las dos ramas de recepción se
limitaban a actualizar un vínculo previo. En el orden natural —se despacha antes de
recibir— no se creaba ninguno.

Fechas relativas al reloj (`R-28`).
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
from tests.time_reference import earlier_event_date, iso_days_ago

PREFIJO = "RL-TEST-"

HUEVOS = 12_000
HUEVOS_RECIBIDOS = 11_800
POLLITOS = 10_500
POLLITOS_RECIBIDOS = 10_400


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.lots.models import ChickBatch, EggBatch, LotPhase, OpeningBalance
    from app.operations.models import (
        BirdMovement, EggMovement, FeedMovement, InspectionDetail, OperationalEvent,
    )

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            await c.execute(delete(ChickBatch).where(
                ChickBatch.hatchery_lot_id.in_(ids) | ChickBatch.destination_lot_id.in_(ids)))
            await c.execute(delete(EggBatch).where(
                EggBatch.source_lot_id.in_(ids) | EggBatch.hatchery_lot_id.in_(ids)))
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            eventos = (await c.execute(select(OperationalEvent.id).where(
                OperationalEvent.lot_id.in_(ids)))).scalars().all()
            if eventos:
                for sub in (BirdMovement, EggMovement, FeedMovement, InspectionDetail):
                    await c.execute(delete(sub).where(sub.event_id.in_(eventos)))
                await c.execute(delete(OperationalEvent).where(OperationalEvent.id.in_(eventos)))
            await c.execute(delete(OpeningBalance).where(OpeningBalance.lot_id.in_(ids)))
            await c.execute(delete(LotPhase).where(LotPhase.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
    await e.dispose()


# ── utilidades ────────────────────────────────────────────────────────────────

async def _granja_con_galpon(client, cab, company_id, etiqueta):
    s = uuid.uuid4().hex[:8]
    g = await client.post("/api/v1/masters/farms", headers=cab, json={
        "company_id": company_id, "name": f"{PREFIJO}{etiqueta}-{s}", "code": f"RL{etiqueta}{s[:5]}"})
    assert g.status_code in (200, 201), g.text
    h = await client.post("/api/v1/masters/houses", headers=cab, json={
        "farm_id": g.json()["id"], "name": f"{PREFIJO}g-{s}", "code": f"RLH{s[:5]}"})
    assert h.status_code in (200, 201), h.text
    return g.json()["id"], h.json()["id"]


async def _lote(client, cab, company_id, farm_id, house_id, tipo):
    r = await client.post("/api/v1/lots", headers=cab, json={
        "company_id": company_id, "farm_id": farm_id, "house_id": house_id,
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}", "bird_type": tipo,
        "sex": "mixed", "start_date": earlier_event_date(),
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _evento(client, cab, lot_id, farm_id, house_id, tipo, **extra):
    r = await client.post("/api/v1/operations", headers=cab, json={
        "lot_id": lot_id, "farm_id": farm_id, "house_id": house_id,
        "event_type": tipo, "event_date": iso_days_ago(0), **extra,
    })
    assert r.status_code == 201, f"{tipo}: {r.text}"
    return r.json()["id"]


async def _vinculos_de_huevo(motor, source_lot_id):
    from app.lots.models import EggBatch
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        return (await s.execute(
            select(EggBatch).where(EggBatch.source_lot_id == source_lot_id))).scalars().all()


async def _vinculos_de_pollito(motor, hatchery_lot_id):
    from app.lots.models import ChickBatch
    fabrica = async_sessionmaker(motor, expire_on_commit=False)
    async with fabrica() as s:
        return (await s.execute(select(ChickBatch).where(
            ChickBatch.hatchery_lot_id == hatchery_lot_id))).scalars().all()


@pytest_asyncio.fixture
async def cadena(client, auth_headers, seeded_ids):
    """Tres generaciones, cada una en su granja: es lo que el emparejamiento necesita.

    Las precondiciones de negocio se **construyen**: `BR-02` exige recolección antes de
    despachar huevo y `BR-04` exige nacimiento antes de despachar pollito.
    """
    c = seeded_ids["company_id"]
    fr, hr = await _granja_con_galpon(client, auth_headers, c, "R")
    fi, hi = await _granja_con_galpon(client, auth_headers, c, "I")
    fe, he = await _granja_con_galpon(client, auth_headers, c, "E")

    repro = await _lote(client, auth_headers, c, fr, hr, "breeder")
    incub = await _lote(client, auth_headers, c, fi, hi, "hatchery")
    engorde = await _lote(client, auth_headers, c, fe, he, "broiler")

    await _evento(client, auth_headers, repro, fr, hr, "egg_collection",
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS * 2}])
    await _evento(client, auth_headers, incub, fi, hi, "birth_registration",
                  bird_movements=[{"sex": "mixed", "quantity": POLLITOS * 2}],
                  chicks_healthy=POLLITOS * 2, chicks_weak=0)  # `GA-REM-021-C` (`B13`), solo setup

    return {"company_id": c, "repro": repro, "incub": incub, "engorde": engorde,
            "fr": fr, "hr": hr, "fi": fi, "hi": hi, "fe": fe, "he": he}


# ── AC01 · AC03 · AC04 · AC08 ─────────────────────────────────────────────────

async def test_t_078_01_la_recepcion_crea_el_vinculo_de_huevo(
    client, auth_headers, cadena, motor
):
    """`AC01`, `AC03`, `AC04`, `AC08` · despacho primero, recepción después.

    Se comprueba que **antes** de la recepción no hay vínculo: sin ese paso, la afirmación
    posterior no distinguiría creación de preexistencia.
    """
    await _evento(client, auth_headers, cadena["repro"], cadena["fr"], cadena["hr"],
                  "egg_dispatch", destination_farm_id=cadena["fi"],
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS}])

    assert await _vinculos_de_huevo(motor, cadena["repro"]) == [], (
        "el despacho por sí solo no debe crear el vínculo: no hay recepción todavía"
    )

    await _evento(client, auth_headers, cadena["incub"], cadena["fi"], cadena["hi"],
                  "egg_reception_hatchery",
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS_RECIBIDOS}])

    vinculos = await _vinculos_de_huevo(motor, cadena["repro"])
    assert len(vinculos) == 1, f"la recepción debe crear el vínculo ausente: {vinculos}"
    v = vinculos[0]

    # `AC03` · orientación: un recuento de uno no basta.
    assert v.source_lot_id == cadena["repro"]
    assert v.hatchery_lot_id == cadena["incub"]

    # `AC04` · cantidades y fechas de los dos lados.
    assert v.quantity_dispatched == HUEVOS, v.quantity_dispatched
    assert v.quantity_received == HUEVOS_RECIBIDOS, v.quantity_received
    assert v.dispatch_event_id is not None
    assert v.reception_event_id is not None
    assert v.dispatch_date is not None and v.reception_date is not None

    # `AC08` · `R-68`: lectura inmediata por HTTP, sin esperas.
    arbol = await client.get(f"/api/v1/lots/{cadena['repro']}/traceability",
                             headers=auth_headers)
    assert arbol.status_code == 200, arbol.text
    assert [b["hatchery_lot_id"] for b in arbol.json()["egg_batches_sent"]] == [cadena["incub"]]


async def test_t_078_02_la_recepcion_crea_el_vinculo_de_pollito(
    client, auth_headers, cadena, motor
):
    """`AC01`, `AC03`, `AC05` · y el vínculo referencia la generación anterior."""
    # Generación de huevo, para que exista el `EggBatch` al que apuntar.
    await _evento(client, auth_headers, cadena["repro"], cadena["fr"], cadena["hr"],
                  "egg_dispatch", destination_farm_id=cadena["fi"],
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS}])
    await _evento(client, auth_headers, cadena["incub"], cadena["fi"], cadena["hi"],
                  "egg_reception_hatchery",
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS_RECIBIDOS}])
    huevo = (await _vinculos_de_huevo(motor, cadena["repro"]))[0]

    await _evento(client, auth_headers, cadena["incub"], cadena["fi"], cadena["hi"],
                  "chick_dispatch", destination_farm_id=cadena["fe"],
                  bird_movements=[{"sex": "mixed", "quantity": POLLITOS}])

    assert await _vinculos_de_pollito(motor, cadena["incub"]) == [], (
        "el despacho por sí solo no debe crear el vínculo"
    )

    await _evento(client, auth_headers, cadena["engorde"], cadena["fe"], cadena["he"],
                  "bird_reception",
                  bird_movements=[{"sex": "mixed", "quantity": POLLITOS_RECIBIDOS}])

    vinculos = await _vinculos_de_pollito(motor, cadena["incub"])
    assert len(vinculos) == 1, f"la recepción debe crear el vínculo ausente: {vinculos}"
    v = vinculos[0]

    assert v.hatchery_lot_id == cadena["incub"]
    assert v.destination_lot_id == cadena["engorde"]
    assert v.quantity_dispatched == POLLITOS
    assert v.quantity_received == POLLITOS_RECIBIDOS

    # `AC05` · el paso 7 de la cadena, hasta ahora sin cobertura ninguna.
    assert v.egg_batch_id == huevo.id, (
        f"el pollito debe referenciar el lote de huevo del que salió: {v.egg_batch_id}"
    )


# ── AC02 · exactamente uno, en los dos órdenes ────────────────────────────────

async def test_t_078_03_exactamente_un_vinculo_en_el_orden_natural(
    client, auth_headers, cadena, motor
):
    """`AC02` · con las dos ramas creando, el par no puede producir dos vínculos."""
    await _evento(client, auth_headers, cadena["repro"], cadena["fr"], cadena["hr"],
                  "egg_dispatch", destination_farm_id=cadena["fi"],
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS}])
    await _evento(client, auth_headers, cadena["incub"], cadena["fi"], cadena["hi"],
                  "egg_reception_hatchery",
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS_RECIBIDOS}])

    assert len(await _vinculos_de_huevo(motor, cadena["repro"])) == 1


async def test_t_078_04_exactamente_un_vinculo_en_el_orden_inverso(
    client, auth_headers, cadena, motor
):
    """`AC02` y `AC09` · recepción antes que despacho sigue produciendo uno, y solo uno.

    Es el orden que `GA-REM-008` certificó. La corrección de `R-78` no debe duplicarlo.
    """
    await _evento(client, auth_headers, cadena["incub"], cadena["fi"], cadena["hi"],
                  "egg_reception_hatchery",
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS_RECIBIDOS}])
    await _evento(client, auth_headers, cadena["repro"], cadena["fr"], cadena["hr"],
                  "egg_dispatch", destination_farm_id=cadena["fi"],
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS}])

    vinculos = await _vinculos_de_huevo(motor, cadena["repro"])
    assert len(vinculos) == 1, f"el orden inverso duplicó el vínculo: {vinculos}"
    assert vinculos[0].hatchery_lot_id == cadena["incub"]


# ── AC06 · AC07 · pertenencia ─────────────────────────────────────────────────

async def test_t_078_05_la_recepcion_no_enlaza_un_despacho_de_otra_compania(
    client, auth_headers, seeded_ids, cadena, motor
):
    """`AC06` y `AC07` · el emparejamiento no cruza compañías.

    La API impide declarar como destino una granja ajena (`verificar_ubicacion`), de modo
    que el caso no puede construirse por HTTP — lo cual es una buena noticia y conviene
    dejarlo dicho. Aquí se ejercita la **segunda línea de defensa**: el despacho ajeno se
    inserta directamente en la base, saltándose esa guarda, y se comprueba que el filtro por
    compañía de la consulta de emparejamiento lo ignora igualmente.

    CONTROL y TRATAMIENTO comparten la misma recepción; lo único que cambia es de qué
    compañía es el despacho disponible.
    """
    from app.operations.models import EggMovement, EventStatus, EventType, OperationalEvent

    fabrica = async_sessionmaker(motor, expire_on_commit=False)

    # Un despacho de la compañía 2 apuntando a la granja de incubación de la compañía 1.
    async with fabrica() as s:
        ajeno = OperationalEvent(
            company_id=seeded_ids["company_id_2"], lot_id=cadena["repro"],
            farm_id=cadena["fr"], house_id=cadena["hr"],
            event_type=EventType.EGG_DISPATCH, status=EventStatus.REGISTERED,
            event_date=__import__("datetime").date.today(),
            destination_farm_id=cadena["fi"], registered_by_id=seeded_ids["user_admin_id"],
        )
        s.add(ajeno)
        await s.flush()
        s.add(EggMovement(event_id=ajeno.id, quantity=HUEVOS, egg_type="fertile"))
        await s.commit()

    # TRATAMIENTO · la recepción solo tiene a mano un despacho ajeno.
    await _evento(client, auth_headers, cadena["incub"], cadena["fi"], cadena["hi"],
                  "egg_reception_hatchery",
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS_RECIBIDOS}])

    assert await _vinculos_de_huevo(motor, cadena["repro"]) == [], (
        "la recepción enlazó un despacho de otra compañía"
    )

    # CONTROL · el mismo lote receptor, con un despacho propio: ahora sí se crea.
    await _evento(client, auth_headers, cadena["repro"], cadena["fr"], cadena["hr"],
                  "egg_dispatch", destination_farm_id=cadena["fi"],
                  egg_movements=[{"egg_type": "fertile", "quantity": HUEVOS}])

    vinculos = await _vinculos_de_huevo(motor, cadena["repro"])
    assert len(vinculos) == 1, (
        f"CONTROL falló: sin vínculo propio, el rechazo anterior no prueba aislamiento: {vinculos}"
    )
