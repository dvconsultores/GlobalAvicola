"""`GA-REM-008` / `RC-04` — trazabilidad generacional.

El emparejamiento automático exigía que despacho y recepción compartieran `lot_id`. Por
definición del dominio no lo comparten: el despacho se registra en el lote origen y la
recepción en el destino. **Nunca se creaba ningún vínculo**, y de coincidir se habría
creado un lote enlazado consigo mismo.

`RC-04` queda resuelto por evidencia estructural: `EggBatch` tiene **dos** columnas de lote
(`source_lot_id`, `hatchery_lot_id`), de modo que «el mismo lote de huevos» de `spec.md
§4.9` designa el mismo lote físico viajando de uno a otro, no un identificador compartido.
"""

from __future__ import annotations

import pytest

from tests.time_reference import earlier_event_date, iso_days_ago, recent_event_date


async def _lote(client, headers, codigo, farm_id, bird_type="broiler"):
    r = await client.post("/api/v1/lots", headers=headers, json={
        "lot_code": codigo, "farm_id": farm_id, "bird_type": bird_type,
        "sex": "mixed", "start_date": earlier_event_date(),
    })
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


async def _recolectar(client, headers, lot_id, cantidad):
    """`BR-02` exige saldo de huevos antes de despachar."""
    r = await client.post("/api/v1/operations", headers=headers, json={
        "lot_id": lot_id, "farm_id": 1, "house_id": 1,
        "event_type": "egg_collection", "event_date": earlier_event_date(),
        "egg_movements": [{"egg_type": "fertile", "quantity": cantidad}],
    })
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_rc04_el_vinculo_une_dos_lotes_distintos(auth_headers, client, seeded_ids):
    """Despacho desde el lote origen, recepción en el destino declarado."""
    origen = seeded_ids["lot_id"]
    destino_granja = seeded_ids["company_id"] and 2  # segunda granja sembrada
    destino = await _lote(client, auth_headers, "TRACE-DEST-01", destino_granja)
    await _recolectar(client, auth_headers, origen, 10_000)

    despacho = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": origen, "farm_id": 1, "house_id": 1,
        "event_type": "egg_dispatch", "event_date": earlier_event_date(),
        "destination_farm_id": destino_granja,
        "egg_movements": [{"egg_type": "fertile", "quantity": 5000}],
    })
    assert despacho.status_code == 201, despacho.text
    assert despacho.json()["destination_farm_id"] == destino_granja, (
        "El destino declarado debe persistirse: sin él no hay emparejamiento posible")

    recepcion = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": destino, "farm_id": destino_granja, "house_id": 1,
        # Hoy: `POST /lots` ignora el `start_date` enviado y activa el lote en el
        # momento de la creación (`R-47`), de modo que una recepción fechada días atrás
        # la rechaza `BR-06`. La regla actúa correctamente; lo que falla es el alta.
        "event_type": "egg_reception_hatchery", "event_date": iso_days_ago(0),
        "egg_movements": [{"egg_type": "fertile", "quantity": 4950}],
    })
    assert recepcion.status_code == 201, recepcion.text

    arbol = await client.get(f"/api/v1/lots/{origen}/traceability", headers=auth_headers)
    assert arbol.status_code == 200, arbol.text

    # `R-79` / `GA-REM-016 AC13`. Antes se afirmaba
    #
    #     assert str(destino) in crudo or "egg_batch" in crudo.lower()
    #
    # y el segundo término es cierto **siempre**: la respuesta contiene la clave
    # `egg_batches_sent` pase lo que pase. El primero tampoco servía —el identificador del
    # lote es un número corto que aparece en cualquier parte del JSON—. La afirmación no
    # podía fallar, y por eso `R-78` sobrevivió a la certificación de este mismo `AC01`.
    #
    # Ahora se comprueba lo que el criterio dice: que existe **un** vínculo y que apunta al
    # destino declarado.
    enviados = arbol.json()["egg_batches_sent"]
    assert len(enviados) == 1, (
        f"`AC01` exige un vínculo entre lotes distintos; hay {len(enviados)}: {enviados}"
    )
    assert enviados[0]["source_lot_id"] == origen, enviados[0]
    assert enviados[0]["hatchery_lot_id"] == destino, enviados[0]


@pytest.mark.asyncio
async def test_ningun_lote_queda_enlazado_consigo_mismo(auth_headers, client, seeded_ids):
    """El defecto original creaba —o habría creado— un lote enlazado a sí mismo."""
    from sqlalchemy import select

    import app.database as database
    from app.lots.models import ChickBatch, EggBatch

    async with database.async_session() as sesion:
        huevos = (await sesion.execute(select(EggBatch))).scalars().all()
        pollitos = (await sesion.execute(select(ChickBatch))).scalars().all()

    for lote in huevos:
        assert lote.hatchery_lot_id is None or lote.source_lot_id != lote.hatchery_lot_id, (
            f"EggBatch {lote.id} enlaza el lote {lote.source_lot_id} consigo mismo")
    for lote in pollitos:
        assert lote.destination_lot_id is None or lote.hatchery_lot_id != lote.destination_lot_id, (
            f"ChickBatch {lote.id} enlaza el lote {lote.hatchery_lot_id} consigo mismo")


@pytest.mark.asyncio
async def test_sin_destino_declarado_no_se_inventa_el_vinculo(auth_headers, client, seeded_ids):
    """Adivinar la correspondencia sería peor que no establecerla.

    `spec.md §4.9` ya contempla el enlace manual «si la correspondencia automática no es
    posible». Cuando el despacho no declara destino, ese es el camino.
    """
    from sqlalchemy import select

    import app.database as database
    from app.lots.models import EggBatch

    async with database.async_session() as sesion:
        antes = len((await sesion.execute(select(EggBatch))).scalars().all())

    await _recolectar(client, auth_headers, seeded_ids["lot_id"], 1_000)
    r = await client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": seeded_ids["lot_id"], "farm_id": 1, "house_id": 1,
        "event_type": "egg_dispatch", "event_date": recent_event_date(),
        "egg_movements": [{"egg_type": "fertile", "quantity": 100}],
    })
    assert r.status_code == 201, r.text

    async with database.async_session() as sesion:
        despues = len((await sesion.execute(select(EggBatch))).scalars().all())
    assert despues == antes, "Sin destino declarado no debe crearse ningún vínculo"


@pytest.mark.asyncio
async def test_el_enlace_manual_sigue_disponible(auth_headers, client, seeded_ids):
    """La spec lo sanciona como alternativa; debe funcionar."""
    # `GA-REM-040` fase 5: el traspaso declara sus dos cadenas y tienen que ser las del
    # flujo. El lote sembrado es de engorde, y un huevo fértil no sale de un engorde: la
    # fixture enlazaba una cadena que `P-10` no puede reconstruir. Se usan las correctas.
    origen = await _lote(client, auth_headers, "TRACE-MANUAL-SRC", 2, bird_type="breeder")
    destino = await _lote(client, auth_headers, "TRACE-MANUAL-01", 2, bird_type="hatchery")
    r = await client.post("/api/v1/lots/egg-batches", headers=auth_headers, json={
        "source_lot_id": origen,
        "hatchery_lot_id": destino,
        "quantity_dispatched": 1000,
        "dispatch_date": recent_event_date(),
    })
    assert r.status_code in (200, 201), r.text
    assert r.json()["source_lot_id"] != r.json()["hatchery_lot_id"]
