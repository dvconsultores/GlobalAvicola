"""SPEC 009 · Ajustes KeyUser sesión 01 — RED de extremo a extremo (HTTP + base de datos).

Fase RED: estas pruebas describen el comportamiento *objetivo* de los ajustes de KeyUser
(línea genética y raza propias de Global Avícola, catálogos con origen de dato y sin fugas
entre empresas/inactivos, `egg_origin` en hatchery v3 y su persistencia en la apertura).
Varias DEBEN fallar sobre el código actual —el importador de hatchery aún es v2 y rechaza
los archivos v3, y los códigos de error de maestros aún son genéricos (`MASTER_NOT_FOUND`)—:
no es un fallo de la suite, es la especificación ejecutable de lo que falta.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402,F401
    GRANJA, LINEA, RAZA, aplicar, aprobar, corte, crear_batch, fila_reproductoras,
    headers_aprobador, items_por_referencia, preparar, subir, xlsx_v2,
)
from test_cutover_v2_keyuser_s01_red_parse import (  # noqa: E402,F401
    COLS_INC_V3, _row_inc_v3, _xlsx_inc_v3,
)

#: Códigos propios de esta suite (prefijo CUT9) para no colisionar con otras suites.
LINEA2 = f"{LINEA}-2"
RAZA2 = f"{RAZA}-2"


async def _errores(client, headers, bu: str, contenido: bytes, dias: int):
    """Sube `contenido` y devuelve (batch_id, cuerpo, errores ordenados | None si no se aceptó)."""
    batch_id = await crear_batch(client, headers, bu, corte(dias))
    r = await subir(client, headers, batch_id, contenido)
    cuerpo = r.json() if r.status_code == 200 else {"status_code": r.status_code}
    if r.status_code != 200:
        return batch_id, cuerpo, None  # upload rechazado (p. ej. versión no soportada aún)
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    return batch_id, cuerpo, sorted((e["row_number"], e["field"], e["error_code"]) for e in v["errors"])


# ── R6-R8 · Línea genética y raza propias ───────────────────────────────────

@pytest.mark.asyncio
async def test_r6_genetic_line_interna_valida_resuelve(auth_headers, http_client, seeded_ids):
    """Una línea genética propia de Global Avícola (catálogo interno) es un maestro válido."""
    await preparar(seeded_ids)
    _, _, errores = await _errores(
        http_client, auth_headers, "breeder",
        xlsx_v2("breeder", [fila_reproductoras("breeder", "R6", genetic_line_code=LINEA, breed_name=RAZA)],
                company_id=seeded_ids["company_id"]), 60)
    assert errores is not None
    assert all(f not in ("genetic_line_code", "breed_name") for (_, f, _c) in errores)


@pytest.mark.asyncio
async def test_r7_raza_interna_valida_resuelve(auth_headers, http_client, seeded_ids):
    """Una raza interna bajo la línea propia también resuelve sin error de maestro."""
    await preparar(seeded_ids)
    _, _, errores = await _errores(
        http_client, auth_headers, "breeder",
        xlsx_v2("breeder", [fila_reproductoras("breeder", "R7", genetic_line_code=LINEA, breed_name=RAZA)],
                company_id=seeded_ids["company_id"]), 61)
    assert errores is not None
    assert all(f not in ("genetic_line_code", "breed_name") for (_, f, _c) in errores)


@pytest.mark.asyncio
async def test_r8_raza_fuera_de_linea_rechaza(auth_headers, http_client, seeded_ids):
    """Una raza que existe pero pertenece a OTRA línea genética no es válida: código propio."""
    await preparar(seeded_ids)
    from app.masters.models import BirdTypeEnum, Breed, GeneticLine

    async with database.async_session() as s:
        linea2 = (await s.execute(select(GeneticLine).where(GeneticLine.code == LINEA2))).scalars().first()
        if linea2 is None:
            linea2 = GeneticLine(company_id=seeded_ids["company_id"], name="CUT9 Línea 2", code=LINEA2,
                                 is_active=True)
            s.add(linea2)
            await s.flush()
        raza2 = (await s.execute(select(Breed).where(Breed.genetic_line_id == linea2.id,
                                                     Breed.name == RAZA2))).scalars().first()
        if raza2 is None:
            s.add(Breed(genetic_line_id=linea2.id, name=RAZA2, bird_type=BirdTypeEnum.BREEDER, is_active=True))
        await s.commit()
    _, _, errores = await _errores(
        http_client, auth_headers, "breeder",
        xlsx_v2("breeder", [fila_reproductoras("breeder", "R8", genetic_line_code=LINEA, breed_name=RAZA2)],
                company_id=seeded_ids["company_id"]), 62)
    assert errores is not None
    assert (2, "breed_name", "BREED_NOT_IN_GENETIC_LINE") in [(r, f, c) for (r, f, c) in errores]


@pytest.mark.asyncio
async def test_genetic_line_inexistente_codigo_propio(auth_headers, http_client, seeded_ids):
    """Una línea genética inexistente reporta `GENETIC_LINE_NOT_FOUND` (no el código genérico)."""
    await preparar(seeded_ids)
    _, _, errores = await _errores(
        http_client, auth_headers, "breeder",
        xlsx_v2("breeder", [fila_reproductoras("breeder", "R-LN", genetic_line_code="NO-EXISTE-LINE")],
                company_id=seeded_ids["company_id"]), 63)
    assert errores is not None
    assert (2, "genetic_line_code", "GENETIC_LINE_NOT_FOUND") in errores


@pytest.mark.asyncio
async def test_breed_inexistente_codigo_propio(auth_headers, http_client, seeded_ids):
    """Una raza inexistente reporta `BREED_NOT_FOUND` (no el código genérico)."""
    await preparar(seeded_ids)
    _, _, errores = await _errores(
        http_client, auth_headers, "breeder",
        xlsx_v2("breeder", [fila_reproductoras("breeder", "R-BR", genetic_line_code=LINEA,
                                               breed_name="NO-EXISTE-RAZA")],
                company_id=seeded_ids["company_id"]), 64)
    assert errores is not None
    assert (2, "breed_name", "BREED_NOT_FOUND") in errores


# ── R9-R11 · Catálogos: origen del dato, empresa e inactivos ────────────────

@pytest.mark.asyncio
async def test_r9_catalogos_source_clasificacion(auth_headers, http_client, seeded_ids):
    """La hoja Catalogos declara el origen de cada código: `farm`/`house` vienen de SAP."""
    await preparar(seeded_ids)
    from app.cutover.contracts import contrato
    from app.cutover.templates import catalogos

    async with database.async_session() as s:
        filas = await catalogos(s, seeded_ids["company_id"], contrato("breeder"))
    assert filas and all(len(f) == 6 for f in filas)
    srcs = {row[0]: row[5] for row in filas}
    assert srcs.get("farm") == "SAP"
    assert srcs.get("genetic_line") == "GLOBAL_AVICOLA"
    assert all(row[5] != "SAP" for row in filas if row[0] not in ("farm", "house"))


@pytest.mark.asyncio
async def test_r10_catalogos_no_expone_otra_empresa(auth_headers, http_client, seeded_ids):
    """Una granja activa de otra empresa jamás aparece en el catálogo de la empresa efectiva."""
    await preparar(seeded_ids)
    from app.cutover.contracts import contrato
    from app.cutover.templates import catalogos
    from app.masters.models import Farm

    async with database.async_session() as s:
        if (await s.execute(select(Farm).where(Farm.code == "KS01-AJENA"))).scalars().first() is None:
            s.add(Farm(company_id=seeded_ids["company_id_2"], code="KS01-AJENA", name="Granja ajena",
                       is_active=True))
            await s.commit()
    async with database.async_session() as s:
        filas = await catalogos(s, seeded_ids["company_id"], contrato("breeder"))
    assert all(row[1] != "KS01-AJENA" for row in filas)


@pytest.mark.asyncio
async def test_r11_catalogos_no_expone_inactivos(auth_headers, http_client, seeded_ids):
    """Una granja inactiva de la empresa propia tampoco se ofrece como código válido."""
    await preparar(seeded_ids)
    from app.cutover.contracts import contrato
    from app.cutover.templates import catalogos
    from app.masters.models import Farm

    async with database.async_session() as s:
        if (await s.execute(select(Farm).where(Farm.code == "KS01-OFF"))).scalars().first() is None:
            s.add(Farm(company_id=seeded_ids["company_id"], code="KS01-OFF", name="Granja inactiva",
                       is_active=False))
            await s.commit()
    async with database.async_session() as s:
        filas = await catalogos(s, seeded_ids["company_id"], contrato("breeder"))
    assert all(row[1] != "KS01-OFF" for row in filas)


# ── R17-R19 · Hatchery v3: `egg_origin` y procedencia del huevo ─────────────

@pytest.mark.asyncio
async def test_r17_purchased_no_exige_lote_interno(auth_headers, http_client, seeded_ids):
    """Huevo comprado (`purchased`): `source_lot_code` apunta fuera y NO se valida contra lotes."""
    await preparar(seeded_ids)
    contenido = _xlsx_inc_v3([_row_inc_v3("R17", egg_origin="purchased", source_lot_code="NO-EXISTE-INT")])
    _, _, errores = await _errores(http_client, auth_headers, "hatchery", contenido, 65)
    assert errores is not None
    assert all(f != "source_lot_code" for (_, f, _c) in errores)


@pytest.mark.asyncio
async def test_r18_internal_mantiene_validacion_source_lot(auth_headers, http_client, seeded_ids):
    """Huevo propio (`internal`): el lote fuente SÍ se valida y su ausencia es `MASTER_NOT_FOUND`."""
    await preparar(seeded_ids)
    contenido = _xlsx_inc_v3([_row_inc_v3("R18", egg_origin="internal", source_lot_code="NO-EXISTE-INT")])
    _, _, errores = await _errores(http_client, auth_headers, "hatchery", contenido, 66)
    assert errores is not None
    assert (2, "source_lot_code", "MASTER_NOT_FOUND") in [(r, f, c) for (r, f, c) in errores]


@pytest.mark.asyncio
async def test_r19_apply_persiste_egg_origin(auth_headers, http_client, seeded_ids):
    """Al aplicar, el `egg_origin` de la fila queda persistido en la apertura de incubación."""
    await preparar(seeded_ids)
    contenido = _xlsx_inc_v3([_row_inc_v3("R19", egg_origin="purchased", source_lot_code=None)])
    batch_id = await crear_batch(http_client, auth_headers, "hatchery", corte(67))
    r = await subir(http_client, auth_headers, batch_id, contenido)
    assert r.status_code == 200, r.text
    await aprobar(http_client, auth_headers, headers_aprobador(seeded_ids), batch_id)
    ap = await aplicar(http_client, auth_headers, batch_id)
    assert ap.status_code == 200, ap.text
    from app.cutover.models import HatcheryOpening
    from app.masters.models import Lot

    async with database.async_session() as s:
        lot = (await s.execute(select(Lot).where(Lot.company_id == seeded_ids["company_id"],
                                                 Lot.lot_code == "R19"))).scalars().first()
        assert lot is not None
        ho = (await s.execute(select(HatcheryOpening).where(HatcheryOpening.lot_id == lot.id))).scalars().first()
    assert ho is not None and ho.egg_origin == "purchased"
