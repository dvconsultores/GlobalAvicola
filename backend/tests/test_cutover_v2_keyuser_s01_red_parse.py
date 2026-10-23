"""SPEC 009 · Ajustes KeyUser sesión 01 — pruebas RED a nivel parser/contrato (sin base de datos).

Fase RED: estas pruebas describen el comportamiento *objetivo* de las plantillas de cutover
(mortalidad obligatoria en breeder, `egg_origin` y `generation` cerrados en hatchery v3). Varias
DEBEN fallar sobre el código actual hasta que se implementen los ajustes: no son un fallo de la
suite, son la especificación ejecutable de lo que falta.

Semántica de celda heredada del contrato: vacío = UNKNOWN · `0` = KNOWN cero · `N/A` = NOT_APPLICABLE.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    INCUBADORA, NACEDORA, PLANTA, fila_reproductoras, xlsx_v2,
)
from time_reference import iso_days_ago  # noqa: E402

from app.cutover.contracts import contrato, lineage  # noqa: E402
from app.cutover.parser import CutoverParseError, parse_cutover_file  # noqa: E402


def _parse(bu: str, contenido: bytes, **kw):
    return parse_cutover_file(contenido, "corte.xlsx", contrato=contrato(bu), **kw)


def _errores_de_fila(r) -> set:
    return {(e["field"], e["error_code"]) for row in r["rows"] for e in row["errors"]}


#: Cabecera v3 de hatchery, declarada aquí como literal: la prueba no hereda el contrato de la
#: implementación ni la fixture `COLUMNAS_INCUBADORA` (que en GREEN ya incluiría `egg_origin`).
COLS_INC_V3 = (
    "legacy_lot_code", "existing_lot_code", "hatchery_code", "incubator_name", "hatcher_name",
    "source_lot_code", "generation", "egg_origin", "reception_date", "set_date", "expected_hatch_date",
    "eggs_received", "eggs_set", "eggs_transferred", "eggs_discarded", "chicks_hatched", "chicks_available",
    "source_system", "source_reference", "notes",
)

_BASE_INC = dict(
    hatchery_code=PLANTA, incubator_name=INCUBADORA, hatcher_name=NACEDORA,
    generation="breeder", egg_origin="internal", reception_date=iso_days_ago(120),
    set_date=iso_days_ago(118), expected_hatch_date=iso_days_ago(97), eggs_received=10000,
    eggs_set=9000, eggs_transferred=0, eggs_discarded=100, chicks_hatched=0, chicks_available=0,
    source_system="LEGACY",
)


def _row_inc_v3(ref, **extra):
    d = dict(_BASE_INC, legacy_lot_code=ref)
    d.update(extra)
    return ["" if d.get(c) is None else d.get(c) for c in COLS_INC_V3]

def _xlsx_inc_v3(filas):
    return xlsx_v2("hatchery", filas, company_id=1, columnas=COLS_INC_V3,
                   template_version="v3", schema_id="CUTOVER_HATCHERY_V3")


# ── R1-R5 · Mortalidad histórica en reproductoras ───────────────────────────

def test_r1_breeder_mortalidad_machos_vacia_rechaza():
    filas = [fila_reproductoras("breeder", "R1", historical_mortality_males=None)]
    r = _parse("breeder", xlsx_v2("breeder", filas, company_id=1))
    assert ("historical_mortality_males", "REQUIRED_FIELD_MISSING") in _errores_de_fila(r)


def test_r2_breeder_mortalidad_hembras_vacia_rechaza():
    filas = [fila_reproductoras("breeder", "R2", historical_mortality_females=None)]
    r = _parse("breeder", xlsx_v2("breeder", filas, company_id=1))
    assert ("historical_mortality_females", "REQUIRED_FIELD_MISSING") in _errores_de_fila(r)


def test_r3_breeder_mortalidad_machos_cero_valida():
    filas = [fila_reproductoras("breeder", "R3", historical_mortality_males=0)]
    r = _parse("breeder", xlsx_v2("breeder", filas, company_id=1))
    row = r["rows"][0]
    assert all(e["field"] != "historical_mortality_males" for e in row["errors"])
    assert row["normalized"]["historical_mortality_males"] == {"value": 0, "status": "KNOWN"}


def test_r4_breeder_mortalidad_hembras_cero_valida():
    filas = [fila_reproductoras("breeder", "R4", historical_mortality_females=0)]
    r = _parse("breeder", xlsx_v2("breeder", filas, company_id=1))
    row = r["rows"][0]
    assert all(e["field"] != "historical_mortality_females" for e in row["errors"])
    assert row["normalized"]["historical_mortality_females"] == {"value": 0, "status": "KNOWN"}


def test_r5_grandparent_mortalidad_vacia_es_unknown_sin_error():
    filas = [fila_reproductoras("grandparent", "R5", historical_mortality_males=None,
                                historical_mortality_females=None)]
    r = _parse("grandparent", xlsx_v2("grandparent", filas, company_id=1))
    row = r["rows"][0]
    assert all(e["field"] not in ("historical_mortality_males", "historical_mortality_females")
               for e in row["errors"])
    assert row["normalized"]["historical_mortality_males"] == {"value": None, "status": "UNKNOWN"}


# ── R12-R16 · Hatchery v3: `generation` y `egg_origin` ──────────────────────

def test_r12_hatchery_generation_grandparent_pasa():
    r = _parse("hatchery", _xlsx_inc_v3([_row_inc_v3("R12", generation="grandparent")]),
               template_version="v3")
    assert r["rows"][0]["errors"] == []


def test_r13_hatchery_generation_breeder_pasa():
    r = _parse("hatchery", _xlsx_inc_v3([_row_inc_v3("R13", generation="breeder")]),
               template_version="v3")
    assert r["rows"][0]["errors"] == []


def test_r14_hatchery_generation_purchased_invalid_enum():
    r = _parse("hatchery", _xlsx_inc_v3([_row_inc_v3("R14", generation="purchased")]),
               template_version="v3")
    assert ("generation", "INVALID_ENUM") in _errores_de_fila(r)


def test_r15_egg_origin_internal_pasa():
    r = _parse("hatchery", _xlsx_inc_v3([_row_inc_v3("R15", egg_origin="internal")]),
               template_version="v3")
    assert r["rows"][0]["errors"] == []
    assert r["rows"][0]["normalized"]["egg_origin"] == {"value": "internal", "status": "KNOWN"}


def test_r16_egg_origin_purchased_pasa():
    r = _parse("hatchery", _xlsx_inc_v3([_row_inc_v3("R16", egg_origin="purchased")]),
               template_version="v3")
    assert r["rows"][0]["errors"] == []
    assert r["rows"][0]["normalized"]["egg_origin"] == {"value": "purchased", "status": "KNOWN"}


def test_r15b_egg_origin_vacio_rechaza_en_v3():
    r = _parse("hatchery", _xlsx_inc_v3([_row_inc_v3("R15b", egg_origin=None)]),
               template_version="v3")
    assert ("egg_origin", "REQUIRED_FIELD_MISSING") in _errores_de_fila(r)


def test_r14b_egg_origin_valor_invalido_enum():
    r = _parse("hatchery", _xlsx_inc_v3([_row_inc_v3("R14b", egg_origin="comprado")]),
               template_version="v3")
    assert ("egg_origin", "INVALID_ENUM") in _errores_de_fila(r)


def test_hatchery_v2_rechazada_por_version():
    # hatchery vigente es v3; un archivo v2 se rechaza por versión, no se tolera.
    with pytest.raises(CutoverParseError) as exc:
        _parse("hatchery", xlsx_v2("hatchery", [_row_inc_v3("VX")], company_id=1, template_version="v2"))
    assert exc.value.code == "TEMPLATE_VERSION_UNSUPPORTED"


# ── R20-R21 · Linaje del contrato completo ──────────────────────────────────

def test_r20_lineage_unmapped_cero():
    assert lineage()["UNMAPPED_TEMPLATE_FIELDS"] == 0


def test_r21_lineage_dominio_faltante_cero():
    assert lineage()["REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE"] == 0
