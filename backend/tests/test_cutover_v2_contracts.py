"""SPEC 006 · Cutover v2 — contratos y parser (sin base de datos).

Cubre: registry cerrado (4 BU, destino por campo), 4 BU × 2 formatos (8 caminos positivos) y
paridad `XLSX_RESULT == CSV_RESULT`, semántica vacío/0/N/A, archivos inválidos (§V del
mandato) y límites (§W). Ninguna aserción depende del calendario.
"""
from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    COLUMNAS, SCHEMA_IDS, csv_v2, fila, fila_engorde, fila_incubadora, fila_reproductoras, xlsx_v2,
)
from time_reference import iso_days_ago  # noqa: E402

from app.cutover.contracts import CONTRACTS, contrato, lineage  # noqa: E402
from app.cutover.parser import (LIMITE_BYTES, LIMITE_COLUMNAS, LIMITE_FILAS, CutoverParseError,  # noqa: E402
                                parse_cutover_file)

EMPRESA = 1
FILAS = {
    "grandparent": [fila_reproductoras("grandparent", "GP-1", fase="PROD")],
    "breeder": [fila_reproductoras("breeder", "BR-1", fase="CRIA", real_start_date=iso_days_ago(70),
                                   accumulated_egg_production="N/A", accumulated_eggs_to_hatchery="N/A")],
    "hatchery": [fila_incubadora("INC-1")],
    "broiler": [fila_engorde("ENG-1")],
}


def _parse(bu: str, contenido: bytes, nombre: str = "corte.xlsx", **kw):
    return parse_cutover_file(contenido, nombre, contrato=contrato(bu), **kw)


def _codigo(bu: str, contenido: bytes, nombre: str = "corte.xlsx") -> str:
    with pytest.raises(CutoverParseError) as exc:
        _parse(bu, contenido, nombre)
    return exc.value.code


# ── Registry ─────────────────────────────────────────────────────────────────

def test_registry_cerrado_cuatro_contratos_v2():
    assert set(CONTRACTS) == {"grandparent", "breeder", "hatchery", "broiler"}
    for bu, c in CONTRACTS.items():
        assert c.version == "v2" and c.schema_id == SCHEMA_IDS[bu]
        assert c.columns == COLUMNAS[bu], bu
        assert len(set(c.columns)) == len(c.columns), "columnas únicas"
    assert CONTRACTS["grandparent"].columns == CONTRACTS["breeder"].columns
    assert CONTRACTS["hatchery"].columns != CONTRACTS["breeder"].columns != CONTRACTS["broiler"].columns


def test_lineage_sin_campos_sin_destino_ni_dominio_faltante():
    m = lineage()
    assert m["UNMAPPED_TEMPLATE_FIELDS"] == 0
    assert m["REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE"] == 0
    columnas = {"BU", "TEMPLATE_FIELD", "BUSINESS_MEANING", "TYPE", "UNIT", "REQUIRED", "ALLOW_UNKNOWN", "ALLOW_NA",
                "VALIDATION", "MASTER_REFERENCE", "NORMALIZED_FIELD", "STAGING_FIELD", "TARGET_ENTITY", "TARGET_COLUMN",
                "PROMOTION_RULE", "FIRST_OPERATION_CONSUMER"}
    assert all(columnas <= set(f) for f in m["rows"])
    assert len(m["rows"]) == sum(len(c.fields) for c in CONTRACTS.values())
    assert all(f["TARGET_COLUMN"] for f in m["rows"])


def test_campos_obligatorios_por_bu():
    assert set(CONTRACTS["breeder"].required_fields) == {"legacy_lot_code", "farm_code", "productive_phase_code",
                                                         "real_start_date", "live_males", "live_females"}
    assert set(CONTRACTS["broiler"].required_fields) == {"legacy_lot_code", "farm_code", "productive_phase_code",
                                                         "real_start_date", "live_birds"}
    assert set(CONTRACTS["hatchery"].required_fields) == {"legacy_lot_code", "hatchery_code", "reception_date",
                                                          "eggs_received", "eggs_set"}


def test_metricas_que_admiten_na():
    con_na = {f.name for f in CONTRACTS["breeder"].fields if f.allow_na}
    assert con_na == {"accumulated_egg_production", "accumulated_eggs_to_hatchery"}
    assert {f.name for f in CONTRACTS["broiler"].fields if f.allow_na} == {"partial_outbound_birds"}
    assert {f.name for f in CONTRACTS["hatchery"].fields if f.allow_na} == {
        "set_date", "expected_hatch_date", "eggs_transferred", "eggs_discarded", "chicks_hatched", "chicks_available"}
    # Lo obligatorio nunca admite UNKNOWN: vivas y huevos recibidos/cargados son KNOWN o error.
    assert not any(f.allow_unknown for c in CONTRACTS.values() for f in c.fields if f.required)


# ── 8 caminos positivos + paridad ─────────────────────────────────────────────

@pytest.mark.parametrize("bu", ["grandparent", "breeder", "hatchery", "broiler"])
def test_xlsx_positivo_por_bu(bu):
    r = _parse(bu, xlsx_v2(bu, FILAS[bu], company_id=EMPRESA))
    assert (r["source_type"], r["template_version"], r["business_unit"], r["company"]) == ("XLSX", "v2", bu, EMPRESA)
    assert r["schema_id"] == SCHEMA_IDS[bu]
    assert len(r["rows"]) == 1 and r["rows"][0]["errors"] == []
    assert set(r["rows"][0]["normalized"]) == set(COLUMNAS[bu])
    assert r["rows"][0]["row_number"] == 2


@pytest.mark.parametrize("bu", ["grandparent", "breeder", "hatchery", "broiler"])
def test_csv_positivo_por_bu(bu):
    r = _parse(bu, csv_v2(bu, FILAS[bu]), "corte.csv")
    assert (r["source_type"], r["template_version"], r["business_unit"]) == ("CSV", "v2", bu)
    assert r["company"] is None  # la empresa la fija el batch
    assert len(r["rows"]) == 1 and r["rows"][0]["errors"] == []


@pytest.mark.parametrize("bu", ["grandparent", "breeder", "hatchery", "broiler"])
def test_paridad_xlsx_csv(bu):
    x = _parse(bu, xlsx_v2(bu, FILAS[bu], company_id=EMPRESA))["rows"]
    c = _parse(bu, csv_v2(bu, FILAS[bu]), "corte.csv")["rows"]
    assert [f["normalized"] for f in x] == [f["normalized"] for f in c]
    assert [f["errors"] for f in x] == [f["errors"] for f in c]


def test_csv_con_coma_y_sin_bom_tambien_se_lee():
    r = _parse("broiler", csv_v2("broiler", FILAS["broiler"], delimitador=",", bom=False), "corte.csv")
    assert r["rows"][0]["normalized"]["live_birds"] == {"value": 10000, "status": "KNOWN"}


def test_csv_version_la_fija_el_endpoint():
    with pytest.raises(CutoverParseError) as exc:
        _parse("broiler", csv_v2("broiler", FILAS["broiler"]), "corte.csv", template_version="v1")
    assert exc.value.code == "TEMPLATE_VERSION_UNSUPPORTED" and "retirada" in exc.value.message


# ── Semántica vacío / 0 / N/A ────────────────────────────────────────────────

def test_vacio_es_unknown_cero_es_known_na_es_not_applicable():
    filas = [fila_reproductoras("breeder", "SEM", fase="CRIA", real_start_date=iso_days_ago(70),
                                historical_mortality_males=None, historical_culls_males=0,
                                accumulated_egg_production="N/A", accumulated_eggs_to_hatchery="n/a",
                                accumulated_feed_kg=None)]
    n = _parse("breeder", xlsx_v2("breeder", filas, company_id=EMPRESA))["rows"][0]["normalized"]
    assert n["historical_mortality_males"] == {"value": None, "status": "UNKNOWN"}
    assert n["historical_culls_males"] == {"value": 0, "status": "KNOWN"}
    assert n["accumulated_egg_production"] == {"value": None, "status": "NOT_APPLICABLE"}
    assert n["accumulated_eggs_to_hatchery"] == {"value": None, "status": "NOT_APPLICABLE"}
    assert n["accumulated_feed_kg"] == {"value": None, "status": "UNKNOWN"}


def test_na_en_obligatorio_y_na_donde_no_se_admite():
    filas = [fila_reproductoras("breeder", "NA-1", live_males="N/A", historical_culls_males="N/A")]
    errores = _parse("breeder", xlsx_v2("breeder", filas, company_id=EMPRESA))["rows"][0]["errors"]
    assert {(e["field"], e["error_code"]) for e in errores} == {
        ("live_males", "NOT_APPLICABLE_ON_REQUIRED"), ("historical_culls_males", "NOT_APPLICABLE_NOT_ALLOWED")}
    assert all(e["message"] and e["row_number"] == 2 and e["received_value"] == "N/A" for e in errores)


def test_tipos_invalidos_por_celda():
    filas = [fila_reproductoras("breeder", "TIP", live_males="1.200", live_females=-5, historical_mortality_males=12.5,
                                accumulated_feed_kg="mucho", current_avg_weight_g=0, real_start_date="01/08/2026",
                                sex="hembra", historical_culls_males=True)]
    errores = {(e["field"], e["error_code"]) for e in _parse("breeder", xlsx_v2("breeder", filas, company_id=EMPRESA))["rows"][0]["errors"]}
    assert errores == {
        ("live_males", "INVALID_INTEGER"), ("live_females", "NEGATIVE_VALUE"), ("historical_mortality_males", "INVALID_INTEGER"),
        ("accumulated_feed_kg", "INVALID_NUMBER"), ("current_avg_weight_g", "INVALID_NUMBER"),
        ("real_start_date", "INVALID_DATE"), ("sex", "INVALID_ENUM"), ("historical_culls_males", "INVALID_INTEGER"),
    }


def test_campo_obligatorio_vacio():
    filas = [fila_reproductoras("breeder", "REQ", farm_code=None, live_females=None)]
    errores = {(e["field"], e["error_code"]) for e in _parse("breeder", xlsx_v2("breeder", filas, company_id=EMPRESA))["rows"][0]["errors"]}
    assert errores == {("farm_code", "REQUIRED_FIELD_MISSING"), ("live_females", "REQUIRED_FIELD_MISSING")}


def test_filas_totalmente_vacias_se_ignoran_y_raw_se_conserva():
    filas = [fila_engorde("ENG-A"), [None] * len(COLUMNAS["broiler"]), fila_engorde("ENG-B", live_birds="7.5")]
    r = _parse("broiler", xlsx_v2("broiler", filas, company_id=EMPRESA))
    assert [f["row_number"] for f in r["rows"]] == [2, 4]
    assert r["rows"][1]["raw"]["live_birds"] == "7.5"
    assert r["rows"][1]["errors"][0]["error_code"] == "INVALID_INTEGER"


def test_enteros_escritos_como_decimal_exacto_se_aceptan():
    filas = [fila_engorde("ENG-F", live_birds=10000.0, age_days="20.0")]
    n = _parse("broiler", xlsx_v2("broiler", filas, company_id=EMPRESA))["rows"][0]["normalized"]
    assert n["live_birds"] == {"value": 10000, "status": "KNOWN"} and n["age_days"] == {"value": 20, "status": "KNOWN"}


# ── Archivos inválidos (§V) ──────────────────────────────────────────────────

def test_archivo_vacio():
    assert _codigo("broiler", b"") == "INVALID_FILE"


def test_xlsx_corrupto_y_extension_falsa():
    assert _codigo("broiler", b"no soy un zip") == "MIME_MISMATCH"
    assert _codigo("broiler", b"PK\x03\x04garbage") == "INVALID_FILE"
    assert _codigo("broiler", xlsx_v2("broiler", FILAS["broiler"], company_id=EMPRESA), "corte.csv") == "MIME_MISMATCH"


def test_csv_corrupto():
    assert _codigo("broiler", b"\xff\xfe\x00\x00\x80\x81", "corte.csv") == "INVALID_FILE"


def test_extension_no_soportada_y_macros():
    assert _codigo("broiler", b"hola", "corte.txt") == "UNSUPPORTED_EXTENSION"
    assert _codigo("broiler", b"PK", "corte.xlsm") == "MACRO_NOT_ALLOWED"
    buf = io.BytesIO(xlsx_v2("broiler", FILAS["broiler"], company_id=EMPRESA))
    with zipfile.ZipFile(buf, "a") as z:
        z.writestr("xl/vbaProject.bin", b"\x00macro")
    assert _codigo("broiler", buf.getvalue()) == "MACRO_NOT_ALLOWED"


def test_hojas_ausentes():
    from openpyxl import Workbook

    wb = Workbook()
    wb.active.title = "Datos"
    b = io.BytesIO()
    wb.save(b)
    assert _codigo("broiler", b.getvalue()) == "SHEET_MISSING"
    wb = Workbook()
    wb.active.title = "Meta"
    b = io.BytesIO()
    wb.save(b)
    assert _codigo("broiler", b.getvalue()) == "SHEET_MISSING"


def test_version_retirada_y_desconocida():
    with pytest.raises(CutoverParseError) as exc:
        _parse("broiler", xlsx_v2("broiler", FILAS["broiler"], company_id=EMPRESA, template_version="v1"))
    assert exc.value.code == "TEMPLATE_VERSION_UNSUPPORTED" and "v2" in exc.value.message
    assert _codigo("broiler", xlsx_v2("broiler", FILAS["broiler"], company_id=EMPRESA, template_version="v99")) == "TEMPLATE_VERSION_UNSUPPORTED"


def test_plantilla_de_otra_bu_rechazada():
    # S11: una plantilla de reproductoras no se acepta en un batch de incubadora (ni por BU ni por schema_id).
    assert _codigo("hatchery", xlsx_v2("breeder", FILAS["breeder"], company_id=EMPRESA)) == "BUSINESS_UNIT_MISMATCH"
    assert _codigo("broiler", xlsx_v2("broiler", FILAS["broiler"], company_id=EMPRESA, business_unit="hatchery")) == "BUSINESS_UNIT_MISMATCH"


def test_cabeceras_duplicadas_desconocidas_y_faltantes():
    cols = COLUMNAS["broiler"]
    assert _codigo("broiler", xlsx_v2("broiler", [], company_id=EMPRESA, columnas=cols + ("live_birds",))) == "HEADER_DUPLICATE"
    assert _codigo("broiler", xlsx_v2("broiler", [], company_id=EMPRESA, columnas=cols + ("peso",))) == "HEADER_UNKNOWN"
    sin = tuple(c for c in cols if c != "live_birds")
    assert _codigo("broiler", xlsx_v2("broiler", [], company_id=EMPRESA, columnas=sin)) == "HEADER_MISSING"
    # S12: la misma falta en CSV.
    assert _codigo("broiler", csv_v2("broiler", [fila_engorde("X")[:11] + fila_engorde("X")[12:]], columnas=sin), "corte.csv") == "HEADER_MISSING"
    assert _codigo("broiler", ("\ufeff" + "\n\n").encode("utf-8"), "corte.csv") == "HEADER_MISSING"


def test_orden_de_columnas_distinto_se_acepta():
    cols = tuple(reversed(COLUMNAS["broiler"]))
    filas = [list(reversed(fila_engorde("ENG-R")))]
    r = _parse("broiler", xlsx_v2("broiler", filas, company_id=EMPRESA, columnas=cols))
    assert r["rows"][0]["normalized"]["legacy_lot_code"] == {"value": "ENG-R", "status": "KNOWN"}


def test_formulas_rechazadas_sin_evaluar():
    filas = [fila_engorde("ENG-FX", live_birds="=SUM(1,2)")]
    with pytest.raises(CutoverParseError) as exc:
        _parse("broiler", xlsx_v2("broiler", filas, company_id=EMPRESA))
    assert exc.value.code == "FORMULA_NOT_ALLOWED" and "fila 2" in exc.value.message


def test_sin_filas_de_datos():
    assert _codigo("broiler", xlsx_v2("broiler", [], company_id=EMPRESA)) == "NO_DATA_ROWS"
    assert _codigo("broiler", csv_v2("broiler", []), "corte.csv") == "NO_DATA_ROWS"


def test_company_meta_invalida():
    assert _codigo("broiler", xlsx_v2("broiler", FILAS["broiler"], company_id="empresa")) == "COMPANY_MISMATCH"


# ── Límites (§W) ─────────────────────────────────────────────────────────────

def test_archivo_demasiado_grande():
    assert _codigo("broiler", b"a" * (LIMITE_BYTES + 1), "corte.csv") == "FILE_TOO_LARGE"


def test_demasiadas_filas():
    filas = [fila_engorde(f"E-{i}") for i in range(LIMITE_FILAS + 1)]
    assert _codigo("broiler", csv_v2("broiler", filas), "corte.csv") == "TOO_MANY_ROWS"


def test_demasiadas_columnas():
    extra = tuple(f"x{i}" for i in range(LIMITE_COLUMNAS))
    assert _codigo("broiler", csv_v2("broiler", [], columnas=COLUMNAS["broiler"] + extra), "corte.csv") == "TOO_MANY_COLUMNS"


def test_texto_demasiado_largo():
    filas = [fila_engorde("E" * 61)]
    errores = _parse("broiler", xlsx_v2("broiler", filas, company_id=EMPRESA))["rows"][0]["errors"]
    assert [(e["field"], e["error_code"]) for e in errores] == [("legacy_lot_code", "INVALID_TEXT_LENGTH")]


def test_fila_de_contrato_rechaza_columnas_ajenas():
    with pytest.raises(AssertionError):
        fila("broiler", live_males=1)
