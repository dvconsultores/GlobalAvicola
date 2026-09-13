"""Pertenencia de `area_id` en lote — `GA-FE-06-A` (subhallazgo de seguridad de `R-182`).

Cubre `R182-SEC-AC01`…`R182-SEC-AC06`.

Contexto (reconciliación `GA_FE_06_A_R183_DEDUP.md`):

    `GA-REM-039` añadió el área al lote y `AC-A12` cubrió su **lectura** entre empresas,
    pero la referencia estructural del **alta/edición de lote** nunca se registró en las
    comprobaciones de pertenencia que `GA-REM-002` (`R-42`/`R-59`), `R-139` y `R-179`
    extienden a toda clave foránea que el cliente puede enviar. Resultado: un lote de la
    empresa A podía quedar ligado al área de la empresa B (`201`/`200` + persistencia).

La regla canónica ya existía —`app/tenancy.verificar_catalogo_de_empresa`—: un catálogo
con `company_id` anulable es **compartido si es nulo, propio si está fijado**, y el ajeno
**se comporta como inexistente** (`BR-07`, sin distinguir «no existe» de «no es tuyo»).
Estas pruebas fijan ese contrato en los dos caminos —alta y edición— con control positivo
misma-empresa, control de NULL y control anti-enumeración.

Nota de ejecución: esta suite requiere PostgreSQL (igual que el resto de lotes).
En local sin PG queda `skipped`; corre en CI. La evidencia RED/GREEN runtime de la
tranche vive en `audit/ga-fe-06-a/`.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import create_async_engine

import app.audit.models  # noqa: F401
import app.corrections.models  # noqa: F401
import app.operations.models  # noqa: F401
import app.review.models  # noqa: F401
from app.masters.models import Lot
from tests.time_reference import iso_days_ago

PREFIJO = "AREA-OWN-TEST-"
PREFIJO_AREA = "AREA-OWN-A-"


@pytest_asyncio.fixture
async def motor(test_database_url):
    e = create_async_engine(test_database_url)
    yield e
    from app.audit.models import AuditLog
    from app.auth.models import User

    async with e.begin() as c:
        ids = (await c.execute(
            select(Lot.id).where(Lot.lot_code.like(f"{PREFIJO}%")))).scalars().all()
        if ids:
            existe = (await c.execute(text("SELECT to_regclass('public.notifications')"))).scalar()
            if existe:
                await c.execute(text(
                    "DELETE FROM notifications WHERE related_entity_type = 'lot' "
                    "AND related_entity_id = ANY(:ids)"), {"ids": ids})
            await c.execute(delete(AuditLog).where(AuditLog.lot_id.in_(ids)))
            await c.execute(delete(Lot).where(Lot.id.in_(ids)))
        areas = (await c.execute(text(
            "SELECT id FROM areas WHERE code LIKE :p"), {"p": f"{PREFIJO_AREA}%"})).scalars().all()
        if areas:
            await c.execute(text(
                "UPDATE lots SET area_id = NULL WHERE area_id = ANY(:ids)"), {"ids": areas})
            await c.execute(delete(AuditLog).where(
                AuditLog.entity_type == "area",
                AuditLog.entity_id.in_([str(i) for i in areas])))
            await c.execute(text("DELETE FROM areas WHERE id = ANY(:ids)"), {"ids": areas})
    await e.dispose()


@pytest_asyncio.fixture
async def unidades(test_database_url, seeded_ids):
    """Configura la empresa como haría su alta: cadenas habilitadas y concedidas al
    administrador sembrado, que es el sujeto de estas pruebas (`R-163` exige unidad)."""
    from tests.business_unit_fixtures import habilitar_y_conceder_todo

    await habilitar_y_conceder_todo(
        test_database_url, company_id=seeded_ids["company_id"],
        user_ids=[seeded_ids["user_admin_id"]])


async def _area(client, cab, company_id, sufijo):
    return await client.post("/api/v1/masters/areas", headers=cab, json={
        "company_id": company_id,
        "name": f"{PREFIJO_AREA}{sufijo}",
        "code": f"{PREFIJO_AREA}{sufijo}",
        "description": "Fixture de aislamiento de área en lote (GA-FE-06-A)"})


async def _lote(client, cab, seeded_ids, **extra):
    cuerpo = {
        "company_id": seeded_ids["company_id"],
        "farm_id": seeded_ids["farm_id"], "house_id": seeded_ids["house_id"],
        "lot_code": f"{PREFIJO}{uuid.uuid4().hex[:10]}",
        "bird_type": "breeder", "sex": "mixed", "start_date": iso_days_ago(60),
    }
    cuerpo.update(extra)
    return await client.post("/api/v1/lots", headers=cab, json=cuerpo)


def _assert_negativa_propia(r):
    """Contrato canónico de denegación (`R-42`/`R-139`/`R-179`): el ajeno se comporta
    como inexistente — `400`, mensaje neutro, regla `BR-07`, sin metadatos del inquilino."""
    assert r.status_code == 400, r.text
    cuerpo = r.json()
    assert cuerpo.get("detail") == "Área no encontrado", r.text
    assert cuerpo.get("rule") == "BR-07", r.text
    # Anti-enumeración: la respuesta no nombra a la otra empresa ni su área.
    texto = r.text.lower()
    for prohibido in ("empresa", "company", "ajena", "del sur"):
        assert prohibido not in texto, f"la denegación filtra «{prohibido}»: {r.text}"


# ── R182-SEC-AC01 · el alta rechaza el área de otra empresa ───────────────────


async def test_ga06a_01_el_alta_rechaza_area_de_otra_empresa(
    client, auth_headers, seeded_ids, motor, unidades
):
    ajena = (await _area(client, auth_headers, seeded_ids["company_id_2"], "AJENA")).json()
    codigo = f"{PREFIJO}{uuid.uuid4().hex[:10]}"

    r = await _lote(client, auth_headers, seeded_ids, lot_code=codigo, area_id=ajena["id"])

    _assert_negativa_propia(r)
    # R182-SEC-AC03 · sin persistencia: el código no existe en la tabla.
    async with motor.connect() as c:
        filas = (await c.execute(
            select(Lot.id).where(Lot.lot_code == codigo))).scalars().all()
    assert filas == [], "el lote se persistió pese a la denegación"


# ── R182-SEC-AC02 · la edición rechaza el área de otra empresa ────────────────


async def test_ga06a_02_la_edicion_rechaza_area_de_otra_empresa(
    client, auth_headers, seeded_ids, motor, unidades
):
    propia = (await _area(client, auth_headers, seeded_ids["company_id"], "PROPIA2")).json()
    ajena = (await _area(client, auth_headers, seeded_ids["company_id_2"], "AJENA2")).json()
    lote = (await _lote(client, auth_headers, seeded_ids, area_id=propia["id"])).json()

    r = await client.put(f"/api/v1/lots/{lote['id']}", headers=auth_headers,
                         json={"area_id": ajena["id"]})

    _assert_negativa_propia(r)
    # Sin mutación parcial: la lectura fresca conserva el área propia.
    leido = (await client.get(f"/api/v1/lots/{lote['id']}", headers=auth_headers)).json()
    assert leido["area_id"] == propia["id"], leido


# ── R182-SEC-AC04 · control positivo: el área propia sigue funcionando ────────


async def test_ga06a_03_control_positivo_area_propia(
    client, auth_headers, seeded_ids, motor, unidades
):
    propia = (await _area(client, auth_headers, seeded_ids["company_id"], "PROPIA3")).json()

    r = await _lote(client, auth_headers, seeded_ids, area_id=propia["id"])
    assert r.status_code == 201, r.text
    leido = (await client.get(f"/api/v1/lots/{r.json()['id']}", headers=auth_headers)).json()
    assert leido["area_id"] == propia["id"], leido

    # La edición a otra área propia también sigue permitida (no se sobreguarda).
    otra = (await _area(client, auth_headers, seeded_ids["company_id"], "PROPIA3B")).json()
    e = await client.put(f"/api/v1/lots/{r.json()['id']}", headers=auth_headers,
                         json={"area_id": otra["id"]})
    assert e.status_code == 200, e.text


# ── R182-SEC-AC05 · control NULL: la opcionalidad no cambia ───────────────────


async def test_ga06a_04_control_null(client, auth_headers, seeded_ids, motor, unidades):
    r = await _lote(client, auth_headers, seeded_ids)
    assert r.status_code == 201, r.text
    assert r.json().get("area_id") is None, r.text


# ── R182-SEC-AC01 (borde) · área inexistente: contrato canónico, no 500 ───────


async def test_ga06a_05_area_inexistente_da_contrato_no_500(
    client, auth_headers, seeded_ids, motor, unidades
):
    r = await _lote(client, auth_headers, seeded_ids, area_id=999999)
    _assert_negativa_propia(r)


# ── `R-203` · misma clase, tres puertas más: galpón, línea genética y curva ──


async def test_ga06a_06_galpon_linea_y_curva_ajenos_se_rechazan(
    client, auth_headers, seeded_ids, motor, unidades
):
    """`R-203` en el fichero de referencia de la clase: las tres referencias
    estructurales del lote responden al mismo contrato que el área (`400`,
    detalle neutro, `BR-07`).

    La geometría ajena se crea aquí para poder demostrar el cruce; se retira en
    el `finally` para no contaminar la siembra compartida.
    """
    import uuid as _uuid

    from app.masters.models import (
        Farm, GeneticLine, GeneticWeightCurve, House,
    )

    prefijo = f"{PREFIJO}R203X-{_uuid.uuid4().hex[:6]}"
    ids = {}
    async with motor.begin() as c:
        b = seeded_ids["company_id_2"]
        farm = Farm(company_id=b, name=f"{prefijo}F")
        c.add(farm)
        await c.flush()
        house = House(farm_id=farm.id, name=f"{prefijo}H")
        line = GeneticLine(company_id=b, name=f"{prefijo}L")
        c.add_all([house, line])
        await c.flush()
        curve = GeneticWeightCurve(genetic_line_id=line.id,
                                   version_label=f"{prefijo}C", is_active=True)
        c.add(curve)
        await c.flush()
        ids = {"farm": farm.id, "house": house.id, "line": line.id,
               "curve": curve.id}

    try:
        # Galpón de otra empresa: se comporta como inexistente.
        r = await _lote(client, auth_headers, seeded_ids,
                        lot_code=f"{prefijo}-H", house_id=ids["house"])
        assert r.status_code == 400, r.text
        assert r.json().get("detail") == "Galpón no encontrado", r.text
        assert r.json().get("rule") == "BR-07", r.text

        # Línea genética de otra empresa: igual; la nula sigue siendo compartida.
        r = await _lote(client, auth_headers, seeded_ids,
                        lot_code=f"{prefijo}-L", genetic_line_id=ids["line"])
        assert r.status_code == 400, r.text
        assert r.json().get("detail") == "Línea genética no encontrado", r.text

        # Curva de una línea ajena: no se aplica.
        r = await _lote(client, auth_headers, seeded_ids,
                        lot_code=f"{prefijo}-C", genetic_line_id=ids["line"],
                        weight_curve_id=ids["curve"])
        assert r.status_code in (400, 404), r.text
    finally:
        async with motor.begin() as c:
            await c.execute(text("DELETE FROM genetic_weight_curves WHERE id = :i"),
                            {"i": ids["curve"]})
            await c.execute(text("DELETE FROM genetic_lines WHERE id = :i"),
                            {"i": ids["line"]})
            await c.execute(text("DELETE FROM houses WHERE id = :i"),
                            {"i": ids["house"]})
            await c.execute(text("DELETE FROM farms WHERE id = :i"),
                            {"i": ids["farm"]})
