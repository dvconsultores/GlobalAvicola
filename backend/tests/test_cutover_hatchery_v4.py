"""SPEC 018 · Cutover incubadora v4 — suite dedicada (no incubables + huevos a fosa).

Cubre AC-V4-01..12 y BR-03 operativo del contrato `CUTOVER_HATCHERY_V4`
(`specs/018-cutover-hatchery-v4-non-incubables/spec.md`): 23 columnas en el orden D-7, sin
`eggs_discarded`, total no incubable solo si los tres componentes son KNOWN (D-3), sin
igualdad forzada `received = set + no incubables` (D-4), fosa POST-CARGA acotada por los
cargados y `eggs_in_process = set − transferred − fosa` (SPEC 018 §7 · D-12/D-13,
OD-HATCH-V4-01 RATIFIED 2026-11-21) y V3 histórica intacta (D-2/D-8).

La cabecera V4 se copia **aquí**, de forma independiente del código: si el contrato cambia
una columna, esta suite falla en lugar de heredar el cambio. Los helpers de archivos, batch y
apply se reutilizan de `cutover_v2_fixtures` (sin duplicar infraestructura).
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from sqlalchemy import select, text

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    COLUMNAS, PLANTA, aplicar, aprobar, corte, crear_batch, csv_v2, fila, fila_incubadora,
    headers_aprobador, items_por_referencia, preparar, subir, xlsx_v2,
)
from time_reference import days_ago, iso_days_ago, recent_event_date  # noqa: E402

from app.cutover.parser import CutoverParseError, parse_cutover_file  # noqa: E402

EMPRESA = 1

#: SPEC 018 · D-1/D-7 — copia independiente de la cabecera de `Datos` de incubadora v4.
COLUMNAS_HATCHERY_V4 = (
    "legacy_lot_code", "existing_lot_code", "hatchery_code", "incubator_name", "hatcher_name",
    "source_lot_code", "generation", "egg_origin", "reception_date", "set_date", "expected_hatch_date",
    "eggs_received", "eggs_set",
    "eggs_non_incubable_oversized", "eggs_non_incubable_dirty", "eggs_non_incubable_broken",
    "eggs_transferred", "fertile_eggs_to_pit",
    "chicks_hatched", "chicks_available",
    "source_system", "source_reference", "notes",
)

#: Los cuatro campos que estrena V4 (D-6): métrica entera opcional, sin N/A.
CAMPOS_NUEVOS = ("eggs_non_incubable_oversized", "eggs_non_incubable_dirty", "eggs_non_incubable_broken",
                 "fertile_eggs_to_pit")

#: Cabecera V3 de incubadora (20 columnas, con `eggs_discarded`): ya no se acepta una carga nueva.
COLUMNAS_HATCHERY_V3 = (
    "legacy_lot_code", "existing_lot_code", "hatchery_code", "incubator_name", "hatcher_name",
    "source_lot_code", "generation", "egg_origin", "reception_date", "set_date", "expected_hatch_date",
    "eggs_received", "eggs_set", "eggs_transferred", "eggs_discarded", "chicks_hatched", "chicks_available",
    "source_system", "source_reference", "notes",
)

NO_INCUBABLES = CAMPOS_NUEVOS[:3]


def _parse_hatchery(contenido: bytes, nombre: str = "corte.xlsx", **kw) -> dict:
    """Parser real con el contrato de incubadora (sin BD)."""
    from app.cutover.contracts import contrato

    return parse_cutover_file(contenido, nombre, contrato=contrato("hatchery"), **kw)


async def _subir_para_validar(client, headers, filas: list, dias: int) -> int:
    """Sube un XLSX de incubadora y devuelve el batch (validación de dominio en BD)."""
    batch_id = await crear_batch(client, headers, "hatchery", corte(dias))
    r = await subir(client, headers, batch_id, xlsx_v2("hatchery", filas, company_id=EMPRESA))
    assert r.status_code == 200, r.text
    return batch_id


async def _errores(client, headers, filas: list, dias: int) -> tuple[dict, list[tuple]]:
    batch_id = await _subir_para_validar(client, headers, filas, dias)
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    return v, sorted((e["row_number"], e["field"], e["error_code"]) for e in v["errors"])


async def _aplicar_batch(client, headers, headers_apr, filas: list, dias: int) -> int:
    """Pipeline completo staging → validate → preview → approve → apply."""
    batch_id = await _subir_para_validar(client, headers, filas, dias)
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    assert v["invalid_rows"] == 0, v["errors"]
    await aprobar(client, headers, headers_apr, batch_id)
    r = await aplicar(client, headers, batch_id)
    assert r.status_code == 200, r.text
    return batch_id


async def _preview(client, headers, batch_id: int) -> dict[str, dict]:
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/preview", headers=headers)
    assert r.status_code == 200, r.text
    return {f["legacy_lot_code"]: f for f in r.json()["rows"]}


async def _reconciliacion(client, headers, batch_id: int) -> dict[str, dict]:
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=headers)
    assert r.status_code == 200, r.text
    return {f["legacy_lot_code"]: f for f in r.json()["lots"]}


_CAMPOS_APERTURA = (
    "eggs_received", "eggs_received_status", "eggs_set", "eggs_set_status",
    "eggs_transferred", "eggs_transferred_status", "eggs_discarded", "eggs_discarded_status",
    "eggs_non_incubable_oversized", "eggs_non_incubable_oversized_status",
    "eggs_non_incubable_dirty", "eggs_non_incubable_dirty_status",
    "eggs_non_incubable_broken", "eggs_non_incubable_broken_status",
    "fertile_eggs_to_pit", "fertile_eggs_to_pit_status",
)


async def _apertura(lot_id: int) -> dict:
    """Valores y estados físicos de `hatchery_openings` para un lote (lectura ORM)."""
    from app.cutover.models import HatcheryOpening

    async with database.async_session() as s:
        ho = (await s.execute(select(HatcheryOpening).where(HatcheryOpening.lot_id == lot_id))).scalar_one()
        return {campo: getattr(ho, campo) for campo in _CAMPOS_APERTURA}


# ── AC-V4-01 · contrato ─────────────────────────────────────────────────────

def test_ac_v4_01_contrato_hatchery_v4_23_columnas_sin_eggs_discarded():
    """Contrato v4/`CUTOVER_HATCHERY_V4`: 23 columnas en el orden D-7, sin `eggs_discarded`."""
    from app.cutover.contracts import HATCHERY_TEMPLATE_VERSION, SUPPORTED_TEMPLATE_VERSIONS, contrato

    c = contrato("hatchery")
    assert (c.version, c.schema_id, c.business_unit) == ("v4", "CUTOVER_HATCHERY_V4", "hatchery")
    assert HATCHERY_TEMPLATE_VERSION == "v4" and "v4" in SUPPORTED_TEMPLATE_VERSIONS
    assert tuple(c.columns) == COLUMNAS_HATCHERY_V4
    assert len(c.columns) == len(COLUMNAS_HATCHERY_V4) == 23 and len(set(c.columns)) == 23
    assert "eggs_discarded" not in c.columns and "eggs_discarded" not in COLUMNAS_HATCHERY_V4
    # Los no incubables van inmediatamente después de `eggs_set` (clasificación del huevo recibido, D-4).
    assert COLUMNAS_HATCHERY_V4[12:16] == ("eggs_set",) + NO_INCUBABLES
    for campo in CAMPOS_NUEVOS:
        spec = c.by_name[campo]
        assert (spec.kind, spec.metric, spec.required, spec.allow_na) == ("int", True, False, False), campo
        assert spec.targets, campo
        assert spec.name in c.columns, campo
# ── AC-V4-02 · plantilla XLSX/CSV ───────────────────────────────────────────

def test_ac_v4_02_plantilla_xlsx_meta_instrucciones_datos_catalogos_y_csv():
    """Plantilla generada: Meta v4, Instrucciones de los 4 campos, Datos 23 columnas, CSV igual."""
    from openpyxl import load_workbook

    from app.cutover.contracts import contrato
    from app.cutover.templates import construir_plantilla, construir_plantilla_csv

    contenido = construir_plantilla("hatchery", EMPRESA)
    wb = load_workbook(io.BytesIO(contenido), data_only=True)
    assert {"Instrucciones", "Meta", "Datos", "Catalogos"} <= set(wb.sheetnames), wb.sheetnames

    meta = {str(k): v for k, v in wb["Meta"].iter_rows(values_only=True) if k is not None}
    assert (meta["template_version"], meta["schema_id"], meta["business_unit"]) == (
        "v4", "CUTOVER_HATCHERY_V4", "hatchery")

    cabecera = [c for c in next(wb["Datos"].iter_rows(values_only=True)) if c is not None]
    assert cabecera == list(COLUMNAS_HATCHERY_V4)

    instrucciones = list(wb["Instrucciones"].iter_rows(values_only=True))
    col = {str(n): i for i, n in enumerate(next(f for f in instrucciones if f and f[0] == "campo"))}
    for campo in CAMPOS_NUEVOS:
        f = next(x for x in instrucciones if x and x[0] == campo)
        assert str(f[col["obligatorio"]]).strip().lower() == "no", campo
        for nombre in ("significado", "tipo", "unidad", "ejemplo", "destino_tras_apply"):
            assert str(f[col[nombre]] or "").strip(), (campo, nombre)
        assert str(f[col["tipo"]]).strip().lower() == "int", campo
        assert str(f[col["admite_N/A"]]).strip().lower() == "no", campo

    # CSV: cabecera equivalente a la de `Datos` (mismo delimitador y BOM que la plantilla).
    texto_csv = construir_plantilla_csv(contrato("hatchery")).decode("utf-8-sig")
    assert texto_csv.splitlines()[0].split(";") == list(COLUMNAS_HATCHERY_V4)
    assert texto_csv.splitlines()[0].split(";") == list(COLUMNAS["hatchery"])

    # Re-parseo del propio XLSX y del propio CSV con una fila válida ⇒ aceptado.
    wb["Datos"].append(fila_incubadora("ACV4-TPL-XLSX"))
    buf = io.BytesIO()
    wb.save(buf)
    r = _parse_hatchery(buf.getvalue())
    assert (r["template_version"], r["schema_id"], r["business_unit"]) == (
        "v4", "CUTOVER_HATCHERY_V4", "hatchery")
    assert r["rows"][0]["errors"] == []

    linea = ";".join("" if v is None else str(v) for v in fila_incubadora("ACV4-TPL-CSV"))
    r = _parse_hatchery((texto_csv.rstrip("\n") + "\n" + linea + "\n").encode("utf-8"), "corte.csv")
    assert r["source_type"] == "CSV" and r["rows"][0]["errors"] == []
# ── AC-V4-03 · cabeceras ────────────────────────────────────────────────────

def _fila_minima(ref: str) -> list:
    return fila("hatchery", legacy_lot_code=ref, hatchery_code=PLANTA, egg_origin="internal",
                reception_date=iso_days_ago(120), eggs_received=10000, eggs_set=9000)


def test_ac_v4_03_cabecera_v4_con_eggs_discarded_es_columna_ajena():
    """`eggs_discarded` fuera del contrato v4: rechazo por columna ajena (XLSX y CSV)."""
    columnas = COLUMNAS_HATCHERY_V4 + ("eggs_discarded",)
    filas = [_fila_minima("ACV4-COL-1")]

    for contenido, nombre in ((xlsx_v2("hatchery", filas, company_id=EMPRESA, columnas=columnas), "corte.xlsx"),
                              (csv_v2("hatchery", filas, columnas=columnas), "corte.csv")):
        with pytest.raises(CutoverParseError) as exc:
            _parse_hatchery(contenido, nombre)
        assert exc.value.code == "HEADER_UNKNOWN", (nombre, exc.value.code)
        assert "eggs_discarded" in exc.value.message, (nombre, exc.value.message)


@pytest.mark.parametrize("campo", CAMPOS_NUEVOS)
def test_ac_v4_03_cabecera_v4_sin_un_campo_nuevo_es_rechazada(campo):
    """Falta cualquiera de los 4 campos nuevos ⇒ rechazo por columnas faltantes (XLSX y CSV)."""
    columnas = tuple(c for c in COLUMNAS_HATCHERY_V4 if c != campo)
    filas = [_fila_minima("ACV4-COL-2")]

    for contenido, nombre in ((xlsx_v2("hatchery", filas, company_id=EMPRESA, columnas=columnas), "corte.xlsx"),
                              (csv_v2("hatchery", filas, columnas=columnas), "corte.csv")):
        with pytest.raises(CutoverParseError) as exc:
            _parse_hatchery(contenido, nombre)
        assert exc.value.code == "HEADER_MISSING", (nombre, exc.value.code)
        assert campo in exc.value.message, (nombre, exc.value.message)


# ── AC-V4-04 · plantilla V3 nueva rechazada ─────────────────────────────────

def test_ac_v4_04_carga_hatchery_v3_nueva_indicando_v4():
    """Una carga nueva de incubadora v3 se rechaza como VERSION_UNSUPPORTED indicando v4."""
    filas = [_fila_minima("ACV4-V3-1")]
    xlsx_v3 = xlsx_v2("hatchery", filas, company_id=EMPRESA, template_version="v3",
                      schema_id="CUTOVER_HATCHERY_V3", columnas=COLUMNAS_HATCHERY_V3)
    csv_v3 = csv_v2("hatchery", filas, columnas=COLUMNAS_HATCHERY_V3)

    for contenido, nombre, kw in ((xlsx_v3, "corte.xlsx", {}), (csv_v3, "corte.csv", {"template_version": "v3"})):
        with pytest.raises(CutoverParseError) as exc:
            _parse_hatchery(contenido, nombre, **kw)
        assert exc.value.code == "TEMPLATE_VERSION_UNSUPPORTED", (nombre, exc.value.code)
        assert "v4" in exc.value.message, (nombre, exc.value.message)
# ── AC-V4-05 · semántica por campo ──────────────────────────────────────────

@pytest.mark.parametrize("campo", CAMPOS_NUEVOS)
@pytest.mark.parametrize("valor,error,estado", [
    (-5, "NEGATIVE_VALUE", None),
    (1.5, "INVALID_INTEGER", None),
    ("abc", "INVALID_INTEGER", None),
    ("N/A", "NOT_APPLICABLE_NOT_ALLOWED", None),
    (0, None, {"value": 0, "status": "KNOWN"}),
    (None, None, {"value": None, "status": "UNKNOWN"}),
])
def test_ac_v4_05_semantica_por_campo(campo, valor, error, estado):
    """Negativo/decimal/texto/N/A ⇒ DENY · `0` ⇒ KNOWN 0 · vacío ⇒ UNKNOWN (nunca 0)."""
    sufijo = CAMPOS_NUEVOS.index(campo)
    filas = [fila_incubadora(f"ACV4-SEM-{sufijo}", **{campo: valor})]
    fila_ = _parse_hatchery(xlsx_v2("hatchery", filas, company_id=EMPRESA))["rows"][0]
    if error is not None:
        assert [(e["field"], e["error_code"]) for e in fila_["errors"]] == [(campo, error)]
        assert campo not in fila_["normalized"]  # un valor rechazado jamás se normaliza
        assert all(e["message"] for e in fila_["errors"])
    else:
        assert fila_["errors"] == []
        assert fila_["normalized"][campo] == estado


# ── AC-V4-06 · total derivado ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_v4_06_total_no_incubable_derivado_y_detalle(auth_headers, http_client, seeded_ids):
    """D-3: total = suma de los tres componentes solo si los tres son KNOWN (nunca suma parcial)."""
    await preparar(seeded_ids)
    filas = [
        fila_incubadora("ACV4-TOT-1", eggs_non_incubable_oversized=100, eggs_non_incubable_dirty=80,
                        eggs_non_incubable_broken=20),
        fila_incubadora("ACV4-TOT-2", eggs_non_incubable_oversized=100, eggs_non_incubable_dirty=None,
                        eggs_non_incubable_broken=20),
        fila_incubadora("ACV4-TOT-3", eggs_non_incubable_oversized=0, eggs_non_incubable_dirty=0,
                        eggs_non_incubable_broken=0),
        fila_incubadora("ACV4-TOT-4", eggs_non_incubable_oversized=None, eggs_non_incubable_dirty=None,
                        eggs_non_incubable_broken=None),
    ]
    batch_id = await _subir_para_validar(http_client, auth_headers, filas, 80)
    derived = {ref: f["derived"] for ref, f in (await _preview(http_client, auth_headers, batch_id)).items()}
    assert derived["ACV4-TOT-1"]["eggs_non_incubable_total"] == 200
    assert derived["ACV4-TOT-2"]["eggs_non_incubable_total"] is None  # no 120: nunca suma parcial
    assert derived["ACV4-TOT-3"]["eggs_non_incubable_total"] == 0     # cero conocido
    assert derived["ACV4-TOT-4"]["eggs_non_incubable_total"] is None  # todos UNKNOWN

    await aprobar(http_client, auth_headers, headers_aprobador(seeded_ids), batch_id)
    assert (await aplicar(http_client, auth_headers, batch_id)).status_code == 200
    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    completo = rec["ACV4-TOT-1"]["opening"]["hatchery"]
    assert (completo["eggs_non_incubable_total"], completo["eggs_non_incubable_total_status"]) == (200, "KNOWN")
    parcial = rec["ACV4-TOT-2"]["opening"]["hatchery"]
    assert (parcial["eggs_non_incubable_total"], parcial["eggs_non_incubable_total_status"]) == (None, "UNKNOWN")
    cero = rec["ACV4-TOT-3"]["opening"]["hatchery"]
    assert (cero["eggs_non_incubable_total"], cero["eggs_non_incubable_total_status"]) == (0, "KNOWN")
# ── AC-V4-07 · consistencia (sin igualdad forzada) ──────────────────────────

@pytest.mark.asyncio
async def test_ac_v4_07_consistencia_sin_igualdad_forzada(auth_headers, http_client, seeded_ids):
    """D-4: `set + Σ(no incubables KNOWN) ≤ received`, aunque falte algún componente; sin igualdad.

    `received − set` incluye legítimamente huevo recibido aún no cargado (saldo BR-03), así que
    una fila con resto sin clasificar es válida. Un componente UNKNOWN no se cuenta como 0 y un
    `eggs_received` UNKNOWN (obligatorio vacío) no dispara ni oculta nada más.
    """
    await preparar(seeded_ids)
    filas = [
        # (2) set 900 + oversized 101 = 1001 > 1000 aunque `dirty` falte: la suma conocida es cota inferior.
        fila_incubadora("ACV4-CONS-1", eggs_received=1000, eggs_set=900, eggs_non_incubable_oversized=101,
                        eggs_non_incubable_dirty=None),
        # (3) un componente por encima de lo recibido.
        fila_incubadora("ACV4-CONS-2", eggs_non_incubable_dirty=10001),
        # (4) 9000 + 100 ≤ 10000 con el resto sin clasificar: válido (no hay igualdad forzada).
        fila_incubadora("ACV4-CONS-3", eggs_non_incubable_oversized=100, eggs_non_incubable_dirty=None,
                        eggs_non_incubable_broken=None),
        # (5) 9000 + 500 + 300 + 200 = 10000: igualdad exacta permitida (no exigida).
        fila_incubadora("ACV4-CONS-4"),
        # (6) cargados > recibidos sigue siendo error.
        fila_incubadora("ACV4-CONS-5", eggs_set=10001),
        # (7) `eggs_received` UNKNOWN (obligatorio vacío): no dispara ni oculta nada más.
        fila_incubadora("ACV4-CONS-6", eggs_received=None, eggs_set=900, eggs_non_incubable_oversized=101),
    ]
    cuerpo, errores = await _errores(http_client, auth_headers, filas, 81)
    assert errores == [
        (2, "eggs_non_incubable_oversized", "CONSISTENCY_MISMATCH"),
        (3, "eggs_non_incubable_dirty", "CONSISTENCY_MISMATCH"),
        (6, "eggs_set", "CONSISTENCY_MISMATCH"),
        (7, "eggs_received", "REQUIRED_FIELD_MISSING"),
    ]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (2, 4)


# ── AC-V4-08 · huevos fértiles a fosa ───────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_v4_08_fosa_acotada_por_lo_cargado(auth_headers, http_client, seeded_ids):
    """AC-V4-15/16 · D-13: la fosa es POST-CARGA (`pit ≤ set`, `transferred + pit ≤ set`).

    OD-HATCH-V4-01 RATIFIED 2026-11-21: `fosa 9500 > set 9000` ya NO es válida (antes solo se
    miraba lo recibido). Sin `eggs_set` KNOWN queda la cota derivada `fosa ≤ received`.
    """
    await preparar(seeded_ids)
    filas = [
        fila_incubadora("ACV4-PIT-X", fertile_eggs_to_pit=10001),   # fosa > cargados (y > recibidos) ⇒ error
        fila_incubadora("ACV4-PIT-Y", fertile_eggs_to_pit=50),      # ≤ cargados y ≤ transferidos + fosa ⇒ válida
        fila_incubadora("ACV4-PIT-Z", eggs_set=9000, fertile_eggs_to_pit=9500),   # > set, ≤ received ⇒ error
        fila_incubadora("ACV4-PIT-W", eggs_transferred=8000, fertile_eggs_to_pit=1001),  # 9001 > set ⇒ error
        fila_incubadora("ACV4-PIT-V", eggs_set=9000, eggs_transferred=0, fertile_eggs_to_pit=9000),  # = set: válida
    ]
    cuerpo, errores = await _errores(http_client, auth_headers, filas, 82)
    assert errores == [(2, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH"),
                       (4, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH"),
                       (5, "fertile_eggs_to_pit", "CONSISTENCY_MISMATCH")]
    assert (cuerpo["valid_rows"], cuerpo["invalid_rows"]) == (2, 3)


@pytest.mark.asyncio
async def test_ac_v4_08_pipeline_completo_con_fosa(auth_headers, http_client, seeded_ids):
    """Fosa > 0 viaja por todo el pipeline: staging, preview, apertura y reconciliación."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("ACV4-PIT-1", fertile_eggs_to_pit=25),
        fila_incubadora("ACV4-PIT-2", fertile_eggs_to_pit=0),
    ], 83)

    preview = await _preview(http_client, auth_headers, batch_id)
    assert preview["ACV4-PIT-1"]["values"]["fertile_eggs_to_pit"] == {"value": 25, "status": "KNOWN"}
    # D-12: con fosa KNOWN `eggs_in_process = set − transferred − fosa` = 9000 − 0 − 25.
    assert preview["ACV4-PIT-1"]["derived"]["eggs_in_process"] == 8975
    assert preview["ACV4-PIT-2"]["derived"]["eggs_in_process"] == 9000  # fosa 0 KNOWN

    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    apertura = await _apertura(lotes["ACV4-PIT-1"])
    assert (apertura["fertile_eggs_to_pit"], apertura["fertile_eggs_to_pit_status"]) == (25, "KNOWN")

    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    con_fosa = rec["ACV4-PIT-1"]["opening"]["hatchery"]
    assert (con_fosa["fertile_eggs_to_pit"], con_fosa["fertile_eggs_to_pit_status"]) == (25, "KNOWN")
    assert con_fosa["eggs_in_process"] == 8975
    sin_fosa = rec["ACV4-PIT-2"]["opening"]["hatchery"]
    assert (sin_fosa["fertile_eggs_to_pit"], sin_fosa["eggs_in_process"]) == (0, 9000)
# ── AC-V4-09 · apply por componente ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_v4_09_apply_persiste_componentes_y_estados(auth_headers, http_client, seeded_ids):
    """Cada componente se persiste por separado con su estado; vacío ⇒ UNKNOWN/NULL.

    V4 además aplica `eggs_discarded = NULL` con estado `NOT_APPLICABLE` (D-2) y el detalle de
    reconciliación conserva el desglose componente a componente.
    """
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("ACV4-APL-1", eggs_non_incubable_oversized=500, eggs_non_incubable_dirty=300,
                        eggs_non_incubable_broken=200, fertile_eggs_to_pit=25),
        fila_incubadora("ACV4-APL-2", eggs_non_incubable_oversized=None, eggs_non_incubable_dirty=None,
                        eggs_non_incubable_broken=None, fertile_eggs_to_pit=None),
    ], 84)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)

    conocidos = await _apertura(lotes["ACV4-APL-1"])
    for campo, valor in ((NO_INCUBABLES[0], 500), (NO_INCUBABLES[1], 300), (NO_INCUBABLES[2], 200),
                         ("fertile_eggs_to_pit", 25)):
        assert (conocidos[campo], conocidos[f"{campo}_status"]) == (valor, "KNOWN"), campo
    assert (conocidos["eggs_discarded"], conocidos["eggs_discarded_status"]) == (None, "NOT_APPLICABLE")

    vacios = await _apertura(lotes["ACV4-APL-2"])
    for campo in CAMPOS_NUEVOS:
        assert (vacios[campo], vacios[f"{campo}_status"]) == (None, "UNKNOWN"), campo
    assert (vacios["eggs_discarded"], vacios["eggs_discarded_status"]) == (None, "NOT_APPLICABLE")
    assert (vacios["eggs_received"], vacios["eggs_received_status"]) == (10000, "KNOWN")

    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    detalle = rec["ACV4-APL-1"]["opening"]["hatchery"]
    for campo, valor in ((NO_INCUBABLES[0], 500), (NO_INCUBABLES[1], 300), (NO_INCUBABLES[2], 200)):
        assert (detalle[campo], detalle[f"{campo}_status"]) == (valor, "KNOWN"), campo
    assert (detalle["eggs_discarded"], detalle["eggs_discarded_status"]) == (None, "NOT_APPLICABLE")
    assert detalle["eggs_non_incubable_total"] == 1000


# ── AC-V4-10 · no double count ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_v4_10_no_double_count_en_br03_ni_en_eggs_in_process(auth_headers, http_client, seeded_ids):
    """D-4: los no incubables restan UNA sola vez, en el saldo recibido→cargado.

    `eggs_in_process` no los toca (9000 = `set − transferred − fosa` con fosa 0 KNOWN; SPEC 018 §7
    D-12): restarlos también ahí sería el doble conteo. Con un componente UNKNOWN el saldo BR-03 es
    cota superior.
    """
    await preparar(seeded_ids)
    from app.operations.validators import get_hatchery_egg_balance

    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        # (a) 10000 − 9000 − 1000 = 0
        fila_incubadora("ACV4-BC-A", eggs_non_incubable_oversized=500, eggs_non_incubable_dirty=300,
                        eggs_non_incubable_broken=200),
        # (b) 10000 − 9000 − 400 = 600
        fila_incubadora("ACV4-BC-B", eggs_non_incubable_oversized=400, eggs_non_incubable_dirty=0,
                        eggs_non_incubable_broken=0),
        # (c) `dirty` UNKNOWN no se resta ni se inventa: 10000 − 9000 − 500 = 500 (cota superior)
        fila_incubadora("ACV4-BC-C", eggs_non_incubable_oversized=400, eggs_non_incubable_dirty=None,
                        eggs_non_incubable_broken=100),
    ], 85)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)
    async with database.async_session() as s:
        assert await get_hatchery_egg_balance(s, lotes["ACV4-BC-A"]) == 0
        assert await get_hatchery_egg_balance(s, lotes["ACV4-BC-B"]) == 600
        assert await get_hatchery_egg_balance(s, lotes["ACV4-BC-C"]) == 500

    rec = await _reconciliacion(http_client, auth_headers, batch_id)
    total = rec["ACV4-BC-A"]["opening"]["hatchery"]
    assert total["eggs_non_incubable_total"] == 1000
    assert total["eggs_in_process"] == 9000          # set − transferred, jamás 8000
    assert rec["ACV4-BC-A"]["current"]["eggs_available_hatchery"] == 0
    parcial = rec["ACV4-BC-B"]["opening"]["hatchery"]
    assert rec["ACV4-BC-B"]["current"]["eggs_available_hatchery"] == 600 and parcial["eggs_in_process"] == 9000
    desconocido = rec["ACV4-BC-C"]["opening"]["hatchery"]
    assert desconocido["eggs_non_incubable_total"] is None
    assert rec["ACV4-BC-C"]["current"]["eggs_available_hatchery"] is None  # cota superior, sin número inventado
    assert desconocido["eggs_in_process"] == 9000
# ── AC-V4-11 · V3 histórica intacta ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_v4_11_registro_v3_historico_sigue_legible_sin_reparto(auth_headers, http_client, seeded_ids):
    """Un registro histórico V3 (`eggs_discarded=100`) se lee con la fórmula V3 y sin reparto inventado."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids),
                                    [fila_incubadora("ACV4-V3H-1")], 86)
    lotes = await items_por_referencia(http_client, auth_headers, batch_id)

    from app.cutover.models import CutoverBatch, HatcheryOpening

    async with database.async_session() as s:
        ho = (await s.execute(select(HatcheryOpening).where(HatcheryOpening.lot_id == lotes["ACV4-V3H-1"]))).scalar_one()
        ho.eggs_discarded, ho.eggs_discarded_status = 100, "KNOWN"
        for campo in CAMPOS_NUEVOS:
            setattr(ho, campo, None)
            setattr(ho, f"{campo}_status", "UNKNOWN")
        batch = (await s.execute(select(CutoverBatch).where(CutoverBatch.id == batch_id))).scalar_one()
        batch.template_version = "v3"  # apertura anterior a la migración v4
        await s.commit()

    h = (await _reconciliacion(http_client, auth_headers, batch_id))["ACV4-V3H-1"]
    assert (h["opening"]["hatchery"]["eggs_discarded"], h["opening"]["hatchery"]["eggs_discarded_status"]) == (100, "KNOWN")
    for campo in CAMPOS_NUEVOS:
        assert (h["opening"]["hatchery"][campo], h["opening"]["hatchery"][f"{campo}_status"]) == (None, "UNKNOWN"), campo
    assert (h["opening"]["hatchery"]["eggs_non_incubable_total"],
            h["opening"]["hatchery"]["eggs_non_incubable_total_status"]) == (None, "UNKNOWN")
    # Fórmulas V3 intactas: `set − transferred − discarded` y `received − set`.
    assert h["opening"]["hatchery"]["eggs_in_process"] == 9000 - 0 - 100
    assert h["current"]["eggs_available_hatchery"] == 10000 - 9000


# ── AC-V4-12 · migración ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ac_v4_12_migracion_defaults_unknown_y_eggs_discarded_conservado(auth_headers, seeded_ids):
    """Una fila insertada sin las columnas v4 queda con los 4 `*_status` en UNKNOWN (server_default).

    `eggs_discarded`/`eggs_discarded_status` siguen existiendo (histórico V3): se conservan en el
    ORM, en la migración y en el DDL real de la tabla.
    """
    ids = await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]
    from app.cutover.models import HatcheryOpening
    from app.lots.models import OpeningBalance
    from app.masters.models import BirdTypeEnum, Lot, LotStatus

    async with database.async_session() as s:
        lote = Lot(company_id=empresa, lot_code="ACV4-MIG-1", origin="NATIVE", bird_type=BirdTypeEnum.HATCHERY,
                   status=LotStatus.ACTIVE, activation_type="normal")
        s.add(lote)
        await s.flush()
        apertura = OpeningBalance(lot_id=lote.id, activation_date=days_ago(30),
                                  phase_at_activation_id=ids["INCUB"],
                                  activated_by_id=seeded_ids["user_admin_id"])
        s.add(apertura)
        await s.flush()
        await s.execute(text(
            "INSERT INTO hatchery_openings (opening_id, lot_id, hatchery_id, reception_date, eggs_received, "
            "eggs_set, eggs_transferred, eggs_discarded, eggs_received_status, eggs_set_status, "
            "eggs_transferred_status, eggs_discarded_status, set_date_status, expected_hatch_date_status) "
            "VALUES (:opening_id, :lot_id, :hatchery_id, :recepcion, 10000, 9000, 0, 0, "
            "'KNOWN', 'KNOWN', 'KNOWN', 'KNOWN', 'KNOWN', 'KNOWN')"),
            {"opening_id": apertura.id, "lot_id": lote.id, "hatchery_id": ids["hatchery_id"],
             "recepcion": days_ago(120)})
        await s.commit()
        lot_id = lote.id

    valores = await _apertura(lot_id)
    for campo in CAMPOS_NUEVOS:
        assert (valores[campo], valores[f"{campo}_status"]) == (None, "UNKNOWN"), campo
    assert (valores["eggs_discarded"], valores["eggs_discarded_status"]) == (0, "KNOWN")
    # Las columnas V3 siguen en el modelo y en el DDL real de la tabla.
    assert {"eggs_discarded", "eggs_discarded_status"} <= set(HatcheryOpening.__table__.columns.keys())
    async with database.async_session() as s:
        columnas = {f[0] for f in (await s.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'hatchery_openings'"))).all()}
    assert {"eggs_discarded", "eggs_discarded_status"} | {f"{c}_status" for c in CAMPOS_NUEVOS} <= columnas


# ── BR-03 operativo sobre la apertura V4 ────────────────────────────────────

@pytest.mark.asyncio
async def test_br03_operativo_incubation_load_sobre_apertura_v4(auth_headers, http_client, seeded_ids):
    """BR-03 resta los no incubables conocidos del saldo recibidos→cargados (700 = 10000−9000−300)."""
    await preparar(seeded_ids)
    batch_id = await _aplicar_batch(http_client, auth_headers, headers_aprobador(seeded_ids), [
        fila_incubadora("ACV4-BR03-1", eggs_non_incubable_oversized=300, eggs_non_incubable_dirty=0,
                        eggs_non_incubable_broken=0),
    ], 88)
    lote = (await items_por_referencia(http_client, auth_headers, batch_id))["ACV4-BR03-1"]

    r = await http_client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "incubation_load", "event_date": recent_event_date(),
        "hatchery_params": [{"quantity_loaded": 700}]})
    assert r.status_code == 201, r.text  # saldo exacto: 700 huevos por cargar
    r = await http_client.post("/api/v1/operations", headers=auth_headers, json={
        "lot_id": lote, "event_type": "incubation_load", "event_date": recent_event_date(),
        "hatchery_params": [{"quantity_loaded": 701}]})
    assert r.status_code == 400, r.text
    assert r.json().get("rule") == "BR-03", r.text

