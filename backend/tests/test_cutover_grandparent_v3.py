"""SPEC 019 · Progenitoras V3 preventiva — bloque backend (AC-GP-01 … AC-GP-09).

Cubre en Abuelas (`grandparent`) lo que en Reproductoras ya estaba probado: el contrato v3 con
las cuatro transferencias históricas, la ecuación por sexo

    vivas = alojadas + transferencias de entrada − mortalidad − descartes − transferencias de salida

con sus tres veredictos (`CONSISTENT` · `INCONSISTENT` ⇒ `CONSISTENCY_MISMATCH` ·
`NOT_FULLY_VERIFIABLE` sin error y **sin inventar ceros**), la distinción fase ≠ transferencia,
la conformación de lote, el descarte en el desalojo, el diagnóstico de sexaje, la persistencia
por sexo en `opening_balances`, el evento posterior al corte y la visibilidad (preview +
claves aditivas de reconciliación).

Ninguna aserción depende del calendario: todas las fechas se derivan de `tests/time_reference.py`
(no se escribe ninguna fecha literal, tampoco en comentarios).
"""
from __future__ import annotations

import io
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

import app.database as database

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    SCHEMA_IDS, TEMPLATE_VERSIONS, aplicar, aprobar, corte, crear_batch, fila_reproductoras,
    headers_aprobador, items_por_referencia, preparar, subir, xlsx_v2,
)
from owner_decisions_support import causa_desconocida  # noqa: E402
from time_reference import days_ago, iso_days_ago, recent_event_date  # noqa: E402

from app.cutover.contracts import contrato  # noqa: E402
from app.cutover.service import PREVIEW_DESTACADAS  # noqa: E402
from app.lots.models import LotPhase, OpeningBalance  # noqa: E402
from app.masters.models import Lot  # noqa: E402

DIAS_CORTE = 30

TRANSFERENCIAS = ("historical_transfers_in_males", "historical_transfers_in_females",
                  "historical_transfers_out_males", "historical_transfers_out_females")

#: Machos cuadrados y sin transferencias: la ecuación masculina no distrae del caso femenino.
MACHOS_CERO = dict(birds_placed_males=1050, historical_mortality_males=50, historical_culls_males=0,
                   historical_transfers_in_males=0, historical_transfers_out_males=0, live_males=1000)
#: Hembras cuadradas y sin transferencias: la ecuación femenina no distrae del caso masculino.
HEMBRAS_CERO = dict(birds_placed_females=9450, historical_mortality_females=450, historical_culls_females=0,
                    historical_transfers_in_females=0, historical_transfers_out_females=0, live_females=9000)

def _ref(base: str) -> str:
    """Referencia única por test: la base de datos es compartida en la sesión de pytest."""
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _fila_gp(ref: str, *, fase: str = "PROD", **valores) -> list:
    """Fila de Progenitoras; los componentes del balance se declaran uno a uno (vacío = UNKNOWN)."""
    return fila_reproductoras("grandparent", ref, fase=fase, **valores)


async def _subir_gp(client, headers, filas: list, empresa: int, dias: int = DIAS_CORTE):
    batch_id = await crear_batch(client, headers, "grandparent", corte(dias))
    return batch_id, await subir(client, headers, batch_id, xlsx_v2("grandparent", filas, company_id=empresa))


async def _validacion(client, headers, filas: list, empresa: int, dias: int = DIAS_CORTE):
    """(batch_id, respuesta del upload, cuerpo del informe de validación)."""
    batch_id, r = await _subir_gp(client, headers, filas, empresa, dias)
    assert r.status_code == 200, r.text
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    return batch_id, r, v


async def _errores(client, headers, filas: list, empresa: int,
                   dias: int = DIAS_CORTE) -> tuple[list[tuple], list[dict]]:
    """(errores ordenados por (fila, campo, código), errores completos con su mensaje)."""
    _, _, v = await _validacion(client, headers, filas, empresa, dias)
    return sorted((e["row_number"], e["field"], e["error_code"]) for e in v["errors"]), v["errors"]


async def _preview(client, headers, batch_id: int) -> dict:
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/preview", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


async def _aplicado(client, headers, seeded_ids, filas: list,
                    dias: int = DIAS_CORTE) -> tuple[int, dict[str, int]]:
    """Sube, valida, aprueba y aplica un batch de Progenitoras; devuelve (batch, lot_id por referencia)."""
    batch_id, r, v = await _validacion(client, headers, filas, seeded_ids["company_id"], dias)
    assert r.json()["status"] == "validated", (r.text, v["errors"])
    await aprobar(client, headers, headers_aprobador(seeded_ids), batch_id)
    assert (await aplicar(client, headers, batch_id)).status_code == 200
    return batch_id, await items_por_referencia(client, headers, batch_id)


async def _reconciliacion(client, headers, batch_id: int, lot_id: int) -> dict:
    r = await client.get(f"/api/v1/cutover-batches/{batch_id}/reconciliation", headers=headers)
    assert r.status_code == 200, r.text
    return next(f for f in r.json()["lots"] if f["lot_id"] == lot_id)


async def _opening(lot_id: int) -> OpeningBalance:
    async with database.async_session() as s:
        return (await s.execute(select(OpeningBalance).where(OpeningBalance.lot_id == lot_id))).scalars().one()


async def _lote_y_fases(lot_id: int) -> tuple[Lot, list[LotPhase]]:
    async with database.async_session() as s:
        lote = (await s.execute(select(Lot).where(Lot.id == lot_id))).scalar_one()
        fases = (await s.execute(select(LotPhase).where(LotPhase.lot_id == lot_id))).scalars().all()
    return lote, list(fases)

# ── AC-GP-01 · Contrato y textos (sin base de datos) ────────────────────────

def test_gp_v3_ac01_contrato_y_textos_refinados():
    """V3 sigue siendo el contrato de Abuelas: 4 transferencias canónicas y textos refinados solo aquí."""
    c = contrato("grandparent")
    assert c.version == "v3" == TEMPLATE_VERSIONS["grandparent"]
    assert c.schema_id == SCHEMA_IDS["grandparent"] == "CUTOVER_GRANDPARENT_V3"

    for nombre in TRANSFERENCIAS:
        spec = c.by_name[nombre]
        assert spec.kind == "int", nombre
        assert spec.required is False and spec.metric is True and spec.allow_na is False, nombre
        assert spec.targets and spec.targets[0].startswith("opening_balances.accumulated_transfers_"), nombre
        assert spec.negative_message, nombre
    # Mismos nombres canónicos que Reproductoras V3: sin campos nuevos (D-1).
    assert [n for n in c.columns if n.startswith("historical_transfers")] == list(TRANSFERENCIAS)
    assert [n for n in contrato("breeder").columns if n.startswith("historical_transfers")] == list(TRANSFERENCIAS)

    gp = c.by_name
    for nombre in ("birds_placed_males", "birds_placed_females"):
        assert "efectivamente" in gp[nombre].meaning, nombre
        assert "importación" in gp[nombre].meaning, nombre
        assert "no se le suman transferencias" in gp[nombre].meaning, nombre
    for nombre in ("historical_culls_males", "historical_culls_females"):
        assert "selección" in gp[nombre].meaning, nombre
        assert "desalojo" in gp[nombre].meaning, nombre
        assert "no se registra a la vez como descarte y como transferencia" in gp[nombre].meaning, nombre
        # OD-GP-SEXAGE-01 RATIFICADA (§5, SEXAGE_MODEL = HISTORICAL_CULL): el sexaje es un descarte.
        # Tres aserciones independientes: la enumeración de descartes, la decisión y lo que NO es.
        assert "aves retiradas por error de sexaje" in gp[nombre].meaning, nombre
        assert "es un descarte" in gp[nombre].meaning, nombre
        assert "NO como cambio de sexo" in gp[nombre].meaning, nombre
    for nombre in TRANSFERENCIAS:
        assert "NO es una transferencia" in gp[nombre].meaning, nombre
        assert "CRIA→PROD" in gp[nombre].meaning, nombre
    # D-2 · §1.5: la fase describe el MISMO lote; cambiar de fase no es transferir.
    assert "NO es una transferencia" in gp["productive_phase_code"].meaning

    # GUARDA (D-6): Reproductoras conserva su texto carácter por carácter — sin las frases nuevas.
    breeder = contrato("breeder").by_name
    frases_gp = ("efectivamente", "selección", "desalojo", "NO es una transferencia", "CRIA→PROD",
                 "no se le suman transferencias", "0 = cero conocido")
    for nombre in ("birds_placed_males", "birds_placed_females", "historical_culls_males", "historical_culls_females",
                   "productive_phase_code", *TRANSFERENCIAS):
        texto = breeder[nombre].meaning
        for frase in frases_gp:
            assert frase not in texto, (nombre, frase, texto)
    assert breeder["birds_placed_males"].meaning == "Machos alojados originalmente (histórico)."
    assert breeder["historical_culls_males"].meaning == "Descartes acumulados de machos antes del corte."
    assert breeder["historical_culls_females"].meaning == "Descartes acumulados de hembras antes del corte."
    # GUARDA de la misma enmienda: el texto de Reproductoras NO menciona el sexaje (diferencia solo en Abuelas).
    for nombre in ("historical_culls_males", "historical_culls_females"):
        assert "sexaje" not in breeder[nombre].meaning, (nombre, breeder[nombre].meaning)
    assert breeder["productive_phase_code"].meaning == (
        "Fase productiva REAL del lote al corte. Valores para esta unidad: CRIA, PROD.")


def test_gp_v3_ac01_plantilla_instrucciones_refinadas():
    """La plantilla XLSX descargable explica los 4 campos y que cambiar de fase no es transferir."""
    from openpyxl import load_workbook

    from app.cutover.templates import construir_plantilla

    contenido = construir_plantilla("grandparent", 1)
    wb = load_workbook(io.BytesIO(contenido))
    assert "Instrucciones" in wb.sheetnames
    filas = list(wb["Instrucciones"].iter_rows(min_row=1, values_only=True))
    significados = {fila[0]: (fila[1] or "") for fila in filas if fila and fila[0]}
    for nombre in TRANSFERENCIAS:
        assert nombre in significados, nombre
        assert "NO es una transferencia" in significados[nombre], nombre
    assert "efectivamente" in significados["birds_placed_males"]
    assert "selección" in significados["historical_culls_males"]
    assert "NO es una transferencia" in significados["productive_phase_code"]
    # La cabecera de Datos sigue siendo la del contrato v3 (sin columnas nuevas).
    cabecera = [c.value for c in wb["Datos"][1]]
    assert cabecera == list(contrato("grandparent").columns)
    meta = {fila[0]: fila[1] for fila in wb["Meta"].iter_rows(values_only=True) if fila and fila[0]}
    assert meta["template_version"] == "v3" and meta["schema_id"] == "CUTOVER_GRANDPARENT_V3"

# ── AC-GP-02 · GP-V3-T01 … T11 (validación real contra la base) ─────────────


@pytest.mark.asyncio
async def test_gp_v3_t01_sin_transferencias_y_transferencias_vacias(auth_headers, http_client, seeded_ids):
    """T01: `0` conocido replica V2; vacío no se inventa como 0 (queda NOT_FULLY_VERIFIABLE)."""
    await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]
    con_ceros = [_fila_gp(_ref("GP-T01-CERO"), **MACHOS_CERO, **HEMBRAS_CERO)]
    batch_cero, _, v_cero = await _validacion(http_client, auth_headers, con_ceros, empresa, 41)
    assert v_cero["errors"] == []
    p_cero = await _preview(http_client, auth_headers, batch_cero)
    assert p_cero["rows"][0]["derived"]["balance_check"] == {"males": "CONSISTENT", "females": "CONSISTENT"}

    machos_vacios = {k: v for k, v in MACHOS_CERO.items() if not k.startswith("historical_transfers")}
    hembras_vacias = {k: v for k, v in HEMBRAS_CERO.items() if not k.startswith("historical_transfers")}
    sin_transferencias = [_fila_gp(_ref("GP-T01-VACIO"), **machos_vacios, **hembras_vacias)]
    batch_vacio, _, v_vacio = await _validacion(http_client, auth_headers, sin_transferencias, empresa, 42)
    assert v_vacio["errors"] == []
    p_vacio = await _preview(http_client, auth_headers, batch_vacio)
    assert p_vacio["rows"][0]["derived"]["balance_check"] == {"males": "NOT_FULLY_VERIFIABLE",
                                                              "females": "NOT_FULLY_VERIFIABLE"}
    assert p_vacio["summary"]["balance_not_fully_verifiable_rows"] == 1
    celda = p_vacio["rows"][0]["values"]["historical_transfers_out_males"]
    assert celda["status"] == "UNKNOWN" and celda["value"] is None


@pytest.mark.asyncio
async def test_gp_v3_t02_salida_de_machos(auth_headers, http_client, seeded_ids):
    """T02: 1300 + 0 − 165 − 0 − 300 = 835 — la salida histórica explica el saldo de Abuelas."""
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-T02"),
                      **{**MACHOS_CERO, "birds_placed_males": 1300, "historical_mortality_males": 165,
                         "historical_transfers_out_males": 300, "live_males": 835}, **HEMBRAS_CERO)]
    errores, _ = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 43)
    assert errores == []


@pytest.mark.asyncio
async def test_gp_v3_t03_entrada_de_machos(auth_headers, http_client, seeded_ids):
    """T03: 1000 + 300 − 100 − 20 − 0 = 1180 — el lote receptor de la conformación."""
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-T03"),
                      **{**MACHOS_CERO, "birds_placed_males": 1000, "historical_transfers_in_males": 300,
                         "historical_mortality_males": 100, "historical_culls_males": 20, "live_males": 1180},
                      **HEMBRAS_CERO)]
    errores, _ = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 44)
    assert errores == []


@pytest.mark.asyncio
async def test_gp_v3_t04_salida_de_hembras(auth_headers, http_client, seeded_ids):
    """T04: 9700 + 0 − 450 − 0 − 250 = 9000 (hembras que se fueron a otro lote)."""
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-T04"), **MACHOS_CERO,
                      **{**HEMBRAS_CERO, "birds_placed_females": 9700, "historical_transfers_out_females": 250})]
    errores, _ = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 45)
    assert errores == []


@pytest.mark.asyncio
async def test_gp_v3_t05_entrada_de_hembras(auth_headers, http_client, seeded_ids):
    """T05: 8700 + 750 − 450 = 9000 (hembras recibidas de otro lote)."""
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-T05"), **MACHOS_CERO,
                      **{**HEMBRAS_CERO, "birds_placed_females": 8700, "historical_transfers_in_females": 750})]
    errores, _ = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 46)
    assert errores == []


@pytest.mark.asyncio
async def test_gp_v3_t06_entrada_y_salida_simultaneas(auth_headers, http_client, seeded_ids):
    """T06: entrada y salida en el mismo lote y en ambos sexos: 1200+400−100−300 = 1200 · 9000+500−500 = 9000."""
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-T06"),
                      **{**MACHOS_CERO, "birds_placed_males": 1200, "historical_transfers_in_males": 400,
                         "historical_mortality_males": 100, "historical_transfers_out_males": 300,
                         "live_males": 1200},
                      **{**HEMBRAS_CERO, "birds_placed_females": 9000, "historical_mortality_females": 0,
                         "historical_transfers_in_females": 500, "historical_transfers_out_females": 500})]
    errores, _ = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 47)
    assert errores == []


@pytest.mark.asyncio
async def test_gp_v3_t07_conformacion_dos_origenes_un_destino(auth_headers, http_client, seeded_ids):
    """T07: dos orígenes con salida (1000 y 700) conforman un destino con entrada 1700 y alojadas 0 conocidas."""
    await preparar(seeded_ids)
    origen_a = {**MACHOS_CERO, "birds_placed_males": 1000, "historical_mortality_males": 0,
                "historical_transfers_out_males": 1000, "live_males": 0}
    origen_b = {**MACHOS_CERO, "birds_placed_males": 700, "historical_mortality_males": 0,
                "historical_transfers_out_males": 700, "live_males": 0}
    destino = {**MACHOS_CERO, "birds_placed_males": 0, "historical_mortality_males": 0,
               "historical_transfers_in_males": 1700, "historical_transfers_out_males": 0, "live_males": 1700}
    filas = [_fila_gp(_ref("GP-T07-A"), **origen_a, **HEMBRAS_CERO),
             _fila_gp(_ref("GP-T07-B"), **origen_b, **HEMBRAS_CERO),
             _fila_gp(_ref("GP-T07-C"), **destino, **HEMBRAS_CERO)]
    errores, _ = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 48)
    assert errores == []
    # Aserción de la prueba (NO una regla de producto, D-5): los orígenes entregan lo que el destino recibe.
    salidas = (origen_a["historical_transfers_out_males"], origen_b["historical_transfers_out_males"])
    assert sum(salidas) == destino["historical_transfers_in_males"] == 1700


@pytest.mark.asyncio
async def test_gp_v3_t08_saldo_inconsistente(auth_headers, http_client, seeded_ids):
    """T08: un saldo que no cuadra ⇒ CONSISTENCY_MISMATCH con el mensaje de la ecuación con transferencias."""
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-T08"),
                      **{**MACHOS_CERO, "birds_placed_males": 1300, "historical_mortality_males": 165,
                         "historical_transfers_out_males": 300, "live_males": 836}, **HEMBRAS_CERO)]
    errores, detalle = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 49)
    assert errores == [(2, "live_males", "CONSISTENCY_MISMATCH")]
    mensaje = detalle[0]["message"]
    assert "transferencias de entrada" in mensaje and "transferencias de salida" in mensaje, mensaje
    assert "835" in mensaje and "836" in mensaje, mensaje


@pytest.mark.asyncio
async def test_gp_v3_t09_unknown_no_se_inventa_ni_se_aplica_como_cero(auth_headers, http_client, seeded_ids):
    """T09: UNKNOWN en descartes, mortalidad histórica o transferencias no es error ni produce un cero falso.

    Nota de fidelidad al producto: la mortalidad y los descartes históricos se persisten con la convención de
    SPEC 006/014 (valor `0` + columna de estado `UNKNOWN`), mientras que las cuatro transferencias usan columnas
    NULLables (`NULL` = UNKNOWN). Lo que el contrato garantiza en los dos casos es lo mismo y es lo que se prueba:
    la reconciliación NUNCA presenta el `0` (publica `null` mientras el estado no sea KNOWN) y el estado es UNKNOWN.
    """
    await preparar(seeded_ids)
    ref_culls, ref_mort, ref_transf = _ref("GP-T09-CULLS"), _ref("GP-T09-MORT"), _ref("GP-T09-TRANSF")
    sin_salida_machos = {k: v for k, v in MACHOS_CERO.items() if k != "historical_transfers_out_males"}
    filas = [
        _fila_gp(ref_culls, **{**MACHOS_CERO, "historical_culls_males": None}, **HEMBRAS_CERO),
        _fila_gp(ref_mort, **{**MACHOS_CERO, "historical_mortality_males": None}, **HEMBRAS_CERO),
        _fila_gp(ref_transf, **sin_salida_machos, **HEMBRAS_CERO),
    ]
    batch_id, r, v = await _validacion(http_client, auth_headers, filas, seeded_ids["company_id"], 50)
    assert v["errors"] == []
    p = await _preview(http_client, auth_headers, batch_id)
    assert [fila["derived"]["balance_check"]["males"] for fila in p["rows"]] == ["NOT_FULLY_VERIFIABLE"] * 3
    assert p["summary"]["balance_not_fully_verifiable_rows"] == 3

    assert r.json()["status"] == "validated", (r.text, v["errors"])
    await aprobar(http_client, auth_headers, headers_aprobador(seeded_ids), batch_id)
    assert (await aplicar(http_client, auth_headers, batch_id)).status_code == 200
    por_ref = await items_por_referencia(http_client, auth_headers, batch_id)

    ob_culls = await _opening(por_ref[ref_culls])
    assert ob_culls.culls_status == "UNKNOWN"
    ob_mort = await _opening(por_ref[ref_mort])
    assert ob_mort.mortality_status == "UNKNOWN"
    ob_transf = await _opening(por_ref[ref_transf])
    assert (ob_transf.accumulated_transfers_out_male, ob_transf.transfers_out_status) == (None, "UNKNOWN")
    # Las transferencias conocidas sí se persisten aunque otra métrica sea UNKNOWN.
    assert (ob_culls.accumulated_transfers_in_male, ob_culls.transfers_in_status) == (0, "KNOWN")

    rec_culls = (await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_culls]))["opening"]
    rec_mort = (await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_mort]))["opening"]
    rec_transf = (await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_transf]))["opening"]
    assert rec_culls["historical_culls"] is None and rec_culls["culls_status"] == "UNKNOWN"
    assert rec_mort["historical_mortality"] is None and rec_mort["mortality_status"] == "UNKNOWN"
    assert rec_transf["historical_transfers_out"] is None and rec_transf["historical_transfers_out_males"] is None


@pytest.mark.asyncio
async def test_gp_v3_t10_transferencia_negativa(auth_headers, http_client, seeded_ids):
    """T10: negativo ⇒ NEGATIVE_VALUE con el mensaje propio de las transferencias históricas."""
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-T10"), **{**MACHOS_CERO, "historical_transfers_in_males": -1}, **HEMBRAS_CERO)]
    errores, detalle = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 51)
    assert errores == [(2, "historical_transfers_in_males", "NEGATIVE_VALUE")]
    mensaje = detalle[0]["message"].lower()
    assert "transferencias históricas" in mensaje and "negativa" in mensaje, mensaje


@pytest.mark.asyncio
async def test_gp_v3_t11_decimal_en_transferencias(auth_headers, http_client, seeded_ids):
    """T11: decimal donde el contrato pide entero ⇒ INVALID_INTEGER, por sexo y por sentido."""
    await preparar(seeded_ids)
    filas = [
        _fila_gp(_ref("GP-T11-A"), **{**MACHOS_CERO, "historical_transfers_out_males": 2.5}, **HEMBRAS_CERO),
        _fila_gp(_ref("GP-T11-B"), **MACHOS_CERO, **{**HEMBRAS_CERO, "historical_transfers_in_females": 7.25}),
    ]
    errores, _ = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 52)
    assert errores == [(2, "historical_transfers_out_males", "INVALID_INTEGER"),
                       (3, "historical_transfers_in_females", "INVALID_INTEGER")]

# ── AC-GP-03 · GP-V3-PHASE-01 · fase ≠ transferencia ────────────────────────


@pytest.mark.asyncio
async def test_gp_v3_phase01_mismo_lote_de_cria_a_prod_sin_transferencia(auth_headers, http_client, seeded_ids):
    """GP-V3-PHASE-01: el mismo lote pasa CRIA→PROD con transferencias 0 conocidas y sin doble conteo."""
    ids = await preparar(seeded_ids)
    ref = _ref("GP-PHASE")
    fila = _fila_gp(ref, fase="PROD", real_start_date=iso_days_ago(200), phase_start_date=iso_days_ago(60),
                    **MACHOS_CERO, **HEMBRAS_CERO)
    batch_id, por_ref = await _aplicado(http_client, auth_headers, seeded_ids, [fila])
    lote_id = por_ref[ref]

    ob = await _opening(lote_id)
    assert (ob.accumulated_transfers_in_male, ob.accumulated_transfers_in_female,
            ob.accumulated_transfers_out_male, ob.accumulated_transfers_out_female) == (0, 0, 0, 0)
    assert (ob.transfers_in_status, ob.transfers_out_status) == ("KNOWN", "KNOWN")

    lote, fases = await _lote_y_fases(lote_id)
    assert lote.bird_type.value == "grandparent"
    assert len(fases) == 1 and fases[0].phase_id == ids["PROD"] and fases[0].is_active
    assert fases[0].start_date == days_ago(60)

    # Sin doble conteo: las vivas son exactamente alojadas − mortalidad − descartes (las 4 transferencias son 0).
    assert (ob.initial_male_count, ob.initial_female_count) == (1000, 9000)
    assert ob.placed_male_count - ob.accumulated_mortality_male - ob.accumulated_culls_male == ob.initial_male_count
    assert ob.placed_female_count - ob.accumulated_mortality_female - ob.accumulated_culls_female == ob.initial_female_count
    fila_rec = await _reconciliacion(http_client, auth_headers, batch_id, lote_id)
    assert (fila_rec["opening"]["historical_transfers_in"], fila_rec["opening"]["historical_transfers_out"]) == (0, 0)


# ── AC-GP-04 · GP-V3-CONFORMATION-01 ────────────────────────────────────────


@pytest.mark.asyncio
async def test_gp_v3_conformation01_origenes_con_salida_y_destino_con_entrada(auth_headers, http_client, seeded_ids):
    """GP-V3-CONFORMATION-01: apply de 3 lotes; Σ salidas de los orígenes = entradas del destino (aserción de prueba)."""
    await preparar(seeded_ids)
    ref_a, ref_b, ref_c = _ref("GP-CONF-A"), _ref("GP-CONF-B"), _ref("GP-CONF-C")
    fila_a = _fila_gp(ref_a, fase="CRIA", accumulated_egg_production=None, accumulated_eggs_to_hatchery=None,
                      **{**MACHOS_CERO, "birds_placed_males": 1000, "historical_mortality_males": 100,
                         "historical_transfers_out_males": 600, "live_males": 300}, **HEMBRAS_CERO)
    fila_b = _fila_gp(ref_b, fase="CRIA", accumulated_egg_production=None, accumulated_eggs_to_hatchery=None,
                      **{**MACHOS_CERO, "birds_placed_males": 700, "historical_mortality_males": 0,
                         "historical_transfers_out_males": 400, "live_males": 300}, **HEMBRAS_CERO)
    fila_c = _fila_gp(ref_c, fase="PROD",
                      **{**MACHOS_CERO, "birds_placed_males": 0, "historical_mortality_males": 0,
                         "historical_transfers_in_males": 1000, "historical_transfers_out_males": 0,
                         "live_males": 1000}, **HEMBRAS_CERO)
    batch_id, por_ref = await _aplicado(http_client, auth_headers, seeded_ids, [fila_a, fila_b, fila_c])

    a = (await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_a]))["opening"]
    b = (await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_b]))["opening"]
    c = (await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_c]))["opening"]
    assert (a["historical_transfers_out_males"], a["historical_transfers_in_males"]) == (600, 0)
    assert (b["historical_transfers_out_males"], b["historical_transfers_in_males"]) == (400, 0)
    assert (c["historical_transfers_in_males"], c["historical_transfers_out_males"]) == (1000, 0)
    # Aserción de la prueba (D-5: la reconciliación cruzada entre lotes NO es regla de producto).
    assert a["historical_transfers_out_males"] + b["historical_transfers_out_males"] == c["historical_transfers_in_males"]

    for ref, (placed, mort, culls) in ((ref_a, (1000, 100, 0)), (ref_b, (700, 0, 0)), (ref_c, (0, 0, 0))):
        ob = await _opening(por_ref[ref])
        # Alojadas, mortalidad y descartes del origen no se alteran al registrar la salida.
        assert (ob.placed_male_count, ob.accumulated_mortality_male, ob.accumulated_culls_male) == (placed, mort, culls), ref
        assert (ob.placed_female_count, ob.accumulated_mortality_female, ob.accumulated_culls_female) == (9450, 450, 0), ref
        assert (ob.transfers_in_status, ob.transfers_out_status) == ("KNOWN", "KNOWN"), ref

# ── AC-GP-05 · descarte en el desalojo ──────────────────────────────────────


@pytest.mark.asyncio
async def test_gp_v3_desalojo_descarte_de_cria_y_seleccion(auth_headers, http_client, seeded_ids):
    """AC-GP-05: alojadas 1000 − mort 50 − descartes 50 (20 de cría + 30 de selección/desalojo) − salida 900 = 0 vivas.

    La celda de descartes suma las DOS fuentes del anexo de desalojo (cría/levante y selección), de modo que el
    ave que se descarta en la selección NO se cuenta además como transferencia: sin doble conteo, el saldo es 0.
    El contrato no exige vivas > 0 (la regla es la ecuación y el UNKNOWN se respeta con la celda vacía), así que
    se conserva el `0` del AC en lugar de inventar una cifra pequeña.
    """
    await preparar(seeded_ids)
    descartes_cria, descartes_seleccion = 20, 30
    filas = [_fila_gp(_ref("GP-DESALOJO"),
                      **{**MACHOS_CERO, "birds_placed_males": 1000, "historical_mortality_males": 50,
                         "historical_culls_males": descartes_cria + descartes_seleccion,
                         "historical_transfers_out_males": 900, "live_males": 0}, **HEMBRAS_CERO)]
    batch_id, _, v = await _validacion(http_client, auth_headers, filas, seeded_ids["company_id"], 53)
    assert v["errors"] == []
    p = await _preview(http_client, auth_headers, batch_id)
    assert p["rows"][0]["derived"]["balance_check"] == {"males": "CONSISTENT", "females": "CONSISTENT"}
    assert p["rows"][0]["values"]["historical_culls_males"]["value"] == descartes_cria + descartes_seleccion
    assert p["rows"][0]["values"]["live_males"]["value"] == 0


# ── AC-GP-06 · persistencia por sexo y estados ──────────────────────────────


@pytest.mark.asyncio
async def test_gp_v3_persistencia_por_sexo_con_known_y_unknown(auth_headers, http_client, seeded_ids):
    """AC-GP-06: `opening_balances` guarda las 4 columnas por sexo con estado; UNKNOWN queda NULL."""
    await preparar(seeded_ids)
    ref_known, ref_unknown = _ref("GP-PERS-K"), _ref("GP-PERS-U")
    conocidas = {"birds_placed_males": 1300, "historical_mortality_males": 165, "historical_culls_males": 0,
                 "historical_transfers_in_males": 300, "historical_transfers_out_males": 0, "live_males": 1435,
                 "birds_placed_females": 9500, "historical_mortality_females": 450, "historical_culls_females": 50,
                 "historical_transfers_in_females": 100, "historical_transfers_out_females": 50, "live_females": 9050}
    sin_salida_machos = {k: v for k, v in MACHOS_CERO.items() if k != "historical_transfers_out_males"}
    batch_id, por_ref = await _aplicado(http_client, auth_headers, seeded_ids,
                                        [_fila_gp(ref_known, **conocidas), _fila_gp(ref_unknown, **sin_salida_machos,
                                                                                   **HEMBRAS_CERO)])
    ob = await _opening(por_ref[ref_known])
    assert (ob.accumulated_transfers_in_male, ob.accumulated_transfers_in_female,
            ob.accumulated_transfers_out_male, ob.accumulated_transfers_out_female) == (300, 100, 0, 50)
    assert (ob.transfers_in_status, ob.transfers_out_status) == ("KNOWN", "KNOWN")

    ob_u = await _opening(por_ref[ref_unknown])
    assert (ob_u.accumulated_transfers_in_male, ob_u.transfers_in_status) == (0, "KNOWN")
    assert ob_u.accumulated_transfers_out_male is None and ob_u.transfers_out_status == "UNKNOWN"

    fila_rec = await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_unknown])
    assert fila_rec["opening"]["historical_transfers_out_males"] is None
    assert fila_rec["opening"]["historical_transfers_out"] is None
    assert fila_rec["opening"]["transfers_out_status"] == "UNKNOWN"

# ── AC-GP-07 · evento posterior al corte ────────────────────────────────────


@pytest.mark.asyncio
async def test_gp_v3_post_corte_no_vuelve_a_restar_lo_historico(auth_headers, http_client, seeded_ids):
    """AC-GP-07: `current = apertura + post-corte`; las transferencias históricas no se restan otra vez."""
    await preparar(seeded_ids)
    ref = _ref("GP-POST")
    filas = [_fila_gp(ref, **{**MACHOS_CERO, "birds_placed_males": 1300, "historical_mortality_males": 165,
                              "historical_transfers_out_males": 300, "live_males": 835}, **HEMBRAS_CERO)]
    batch_id, por_ref = await _aplicado(http_client, auth_headers, seeded_ids, filas)
    lote_id = por_ref[ref]

    r = await http_client.post("/api/v1/operations", headers=auth_headers,
                               json={"lot_id": lote_id, "event_type": "mortality_recording",
                                     "event_date": recent_event_date(),
                                     # `spec 020 §6` ratificado por la Owner el 25-11-2026 · `RR-32`:
                                     # la baja dice por qué; «Desconocida» es el valor explícito para lo
                                     # que no se pudo determinar, y aquí solo es setup del saldo.
                                     "cause_id": await causa_desconocida(http_client, auth_headers),
                                     "bird_movements": [{"sex": "male", "quantity": 15, "avg_weight": 3600.0}]})
    assert r.status_code == 201, r.text

    fila_rec = await _reconciliacion(http_client, auth_headers, batch_id, lote_id)
    assert fila_rec["opening"]["live"] == 835 + 9000 == 9835
    assert fila_rec["post"]["mortality"] == 15
    # `post.salidas` agrupa las salidas de población (mortalidad y descarte incluidos, reporting.SALIDAS).
    assert (fila_rec["post"]["entradas"], fila_rec["post"]["salidas"]) == (0, 15)
    assert fila_rec["current_live"] == 9835 - 15
    assert fila_rec["current_live"] == fila_rec["opening"]["live"] + fila_rec["post"]["entradas"] - fila_rec["post"]["salidas"]
    # lifetime = histórico + post-corte; lo histórico no se descuenta dos veces.
    assert fila_rec["lifetime"]["mortality"] == 165 + 450 + 15
    assert fila_rec["opening"]["historical_transfers_out_males"] == 300
    assert fila_rec["opening"]["historical_mortality"] == 165 + 450


# ── AC-GP-08 · diagnóstico de sexaje (OD-GP-SEXAGE-01 RATIFICADA: es descarte) ──


@pytest.mark.asyncio
async def test_gp_v3_sexaje_descarte_cuadra_y_reclasificacion_no(auth_headers, http_client, seeded_ids):
    """AC-GP-08: diagnóstico de sexaje — `OD-GP-SEXAGE-01` RATIFICADA (SPEC 019 §5, `SEXAGE_MODEL = HISTORICAL_CULL`).

    Un error de sexaje que saca el ave del lote es un DESCARTE (H2 ratificada); la reclasificación macho↔hembra
    (H1) NO se representa en el contrato y, si se carga de forma silenciosa, se detecta como inconsistencia:
    (i) H2 · las aves mal sexadas salen del lote y se acumulan como descarte: alojadas 100 machos y 1000 hembras,
        10 machos descartados ⇒ 90 machos vivos y 1000 hembras vivas cuadran con la ecuación (CONSISTENT en ambos);
    (ii) H1 · las aves se RECLASIFICAN de macho a hembra: mismo lote con 90 machos y 1010 hembras, sin descartes
        ni transferencias ⇒ CONSISTENCY_MISMATCH en los DOS sexos. El contrato no corrige el sexo por su cuenta.
    """
    await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]

    h2 = [_fila_gp(_ref("GP-SEXAJE-H2"),
                   **{**MACHOS_CERO, "birds_placed_males": 100, "historical_mortality_males": 0,
                      "historical_culls_males": 10, "live_males": 90},
                   **{**HEMBRAS_CERO, "birds_placed_females": 1000, "historical_mortality_females": 0,
                      "live_females": 1000})]
    batch_h2, _, v_h2 = await _validacion(http_client, auth_headers, h2, empresa, 54)
    assert v_h2["errors"] == []
    p_h2 = await _preview(http_client, auth_headers, batch_h2)
    assert p_h2["rows"][0]["derived"]["balance_check"] == {"males": "CONSISTENT", "females": "CONSISTENT"}

    h1 = [_fila_gp(_ref("GP-SEXAJE-H1"),
                   **{**MACHOS_CERO, "birds_placed_males": 100, "historical_mortality_males": 0,
                      "historical_culls_males": 0, "live_males": 90},
                   **{**HEMBRAS_CERO, "birds_placed_females": 1000, "historical_mortality_females": 0,
                      "live_females": 1010})]
    errores, detalle = await _errores(http_client, auth_headers, h1, empresa, 55)
    assert errores == [(2, "live_females", "CONSISTENCY_MISMATCH"), (2, "live_males", "CONSISTENCY_MISMATCH")]
    assert all("descartes" in e["message"] for e in detalle)

# ── AC-GP-09 · visibilidad: preview + claves aditivas de reconciliación ──────


@pytest.mark.asyncio
async def test_gp_v3_preview_y_reconciliacion_por_sexo(auth_headers, http_client, seeded_ids):
    """AC-GP-09: el resaltado de Abuelas incluye las 4 transferencias y la reconciliación expone claves M/H."""
    await preparar(seeded_ids)
    empresa = seeded_ids["company_id"]
    ref_known, ref_unknown = _ref("GP-PREV-K"), _ref("GP-PREV-U")
    sin_salida_machos = {k: v for k, v in MACHOS_CERO.items() if k != "historical_transfers_out_males"}
    conocidas = {**MACHOS_CERO, "historical_transfers_in_males": 300, "live_males": 1300}
    filas = [_fila_gp(ref_known, **conocidas, **HEMBRAS_CERO),
             _fila_gp(ref_unknown, **sin_salida_machos, **HEMBRAS_CERO)]
    batch_id, r, v = await _validacion(http_client, auth_headers, filas, empresa, 56)
    assert v["errors"] == []

    p = await _preview(http_client, auth_headers, batch_id)
    assert p["highlight"] == list(PREVIEW_DESTACADAS["grandparent"])
    assert tuple(p["highlight"][-4:]) == TRANSFERENCIAS
    assert set(TRANSFERENCIAS) <= set(p["highlight"])
    # UNKNOWN visible, nunca como 0.
    desconocida = next(f for f in p["rows"] if f["legacy_lot_code"] == ref_unknown)
    assert desconocida["values"]["historical_transfers_out_males"] == {"value": None, "status": "UNKNOWN"}

    await aprobar(http_client, auth_headers, headers_aprobador(seeded_ids), batch_id)
    assert (await aplicar(http_client, auth_headers, batch_id)).status_code == 200
    por_ref = await items_por_referencia(http_client, auth_headers, batch_id)
    rec_known = (await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_known]))["opening"]
    rec_unknown = (await _reconciliacion(http_client, auth_headers, batch_id, por_ref[ref_unknown]))["opening"]
    for clave in TRANSFERENCIAS:
        assert clave in rec_known and clave in rec_unknown, clave
    assert rec_known["historical_transfers_in_males"] == 300
    assert rec_known["historical_transfers_out_males"] == 0
    assert rec_known["historical_transfers_in"] == 300  # el total sigue publicado (D-3: aditivo, no sustitutivo)
    assert rec_unknown["historical_transfers_out_males"] is None
    assert rec_unknown["historical_transfers_out"] is None

    # Reproductoras (D-6): su resaltado NO cambia y también recibe las claves aditivas.
    assert not set(TRANSFERENCIAS) & set(PREVIEW_DESTACADAS["breeder"])
    ref_breeder = _ref("BR-PREV")
    breeder_batch = await crear_batch(http_client, auth_headers, "breeder", corte(57))
    r = await subir(http_client, auth_headers, breeder_batch,
                    xlsx_v2("breeder", [fila_reproductoras("breeder", ref_breeder, **MACHOS_CERO, **HEMBRAS_CERO)],
                            company_id=empresa))
    assert r.status_code == 200 and r.json()["status"] == "validated", r.text
    p_breeder = await _preview(http_client, auth_headers, breeder_batch)
    assert p_breeder["highlight"] == list(PREVIEW_DESTACADAS["breeder"])
    await aprobar(http_client, auth_headers, headers_aprobador(seeded_ids), breeder_batch)
    assert (await aplicar(http_client, auth_headers, breeder_batch)).status_code == 200
    lote_breeder = (await items_por_referencia(http_client, auth_headers, breeder_batch))[ref_breeder]
    opening_breeder = (await _reconciliacion(http_client, auth_headers, breeder_batch, lote_breeder))["opening"]
    for clave in TRANSFERENCIAS:
        assert clave in opening_breeder, clave
    assert opening_breeder["historical_transfers_in_males"] == 0
    assert opening_breeder["historical_transfers_out_females"] == 0


# ── OD-GP-SEXAGE-01 · RATIFICADA (SPEC 019 §5, SEXAGE_MODEL = HISTORICAL_CULL) ──


@pytest.mark.asyncio
async def test_gp_v3_sexage_01_descarte_machos(auth_headers, http_client, seeded_ids):
    """AC-SX-01: 100 − 5 − 10 = 85 con transferencias 0 conocidas — los 10 descartes pueden ser error de sexaje.

    El texto del contrato (Abuelas) admite expresamente que el acumulado de descartes incluya las aves retiradas
    por error de sexaje: se registran en el sexo con el que estaban contabilizadas, sin cambio de sexo.
    """
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-SX01"),
                      **{**MACHOS_CERO, "birds_placed_males": 100, "historical_mortality_males": 5,
                         "historical_culls_males": 10, "historical_transfers_in_males": 0,
                         "historical_transfers_out_males": 0, "live_males": 85}, **HEMBRAS_CERO)]
    batch_id, r, v = await _validacion(http_client, auth_headers, filas, seeded_ids["company_id"], 58)
    assert v["errors"] == []
    p = await _preview(http_client, auth_headers, batch_id)
    assert p["rows"][0]["derived"]["balance_check"] == {"males": "CONSISTENT", "females": "CONSISTENT"}
    assert p["rows"][0]["values"]["historical_culls_males"] == {"value": 10, "status": "KNOWN"}


@pytest.mark.asyncio
async def test_gp_v3_sexage_02_descarte_hembras(auth_headers, http_client, seeded_ids):
    """AC-SX-02: equivalente en hembras — 1000 − 30 − 20 = 950 y el sexo masculino no distrae."""
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-SX02"), **MACHOS_CERO,
                      **{**HEMBRAS_CERO, "birds_placed_females": 1000, "historical_mortality_females": 30,
                         "historical_culls_females": 20, "historical_transfers_in_females": 0,
                         "historical_transfers_out_females": 0, "live_females": 950})]
    batch_id, r, v = await _validacion(http_client, auth_headers, filas, seeded_ids["company_id"], 59)
    assert v["errors"] == []
    p = await _preview(http_client, auth_headers, batch_id)
    assert p["rows"][0]["derived"]["balance_check"] == {"males": "CONSISTENT", "females": "CONSISTENT"}
    assert p["rows"][0]["values"]["historical_culls_females"] == {"value": 20, "status": "KNOWN"}


@pytest.mark.asyncio
async def test_gp_v3_sexage_03_culls_unknown(auth_headers, http_client, seeded_ids):
    """AC-SX-03: descartes desconocidos ⇒ sin error, sexo NOT_FULLY_VERIFIABLE y jamás un `0` como valor conocido.

    La celda vacía viaja como UNKNOWN y se publica como `null` en preview y reconciliación; el estado del sexo es
    `UNKNOWN` tras el apply (la columna usa la convención `0` + estado de SPEC 006/014, nunca un 0 KNOWN).
    """
    await preparar(seeded_ids)
    ref = _ref("GP-SX03")
    filas = [_fila_gp(ref, **{**MACHOS_CERO, "historical_culls_males": None}, **HEMBRAS_CERO)]
    batch_id, r, v = await _validacion(http_client, auth_headers, filas, seeded_ids["company_id"], 60)
    assert v["errors"] == []
    p = await _preview(http_client, auth_headers, batch_id)
    assert p["rows"][0]["derived"]["balance_check"]["males"] == "NOT_FULLY_VERIFIABLE"
    assert p["rows"][0]["values"]["historical_culls_males"] == {"value": None, "status": "UNKNOWN"}

    assert r.json()["status"] == "validated", (r.text, v["errors"])
    await aprobar(http_client, auth_headers, headers_aprobador(seeded_ids), batch_id)
    assert (await aplicar(http_client, auth_headers, batch_id)).status_code == 200
    lote_id = (await items_por_referencia(http_client, auth_headers, batch_id))[ref]

    ob = await _opening(lote_id)
    assert ob.culls_status == "UNKNOWN"
    # Fidelidad al producto (SPEC 006/014, igual que en `test_gp_v3_t09_…`): la columna de descartes históricos se
    # serializa con la convención `0` + estado `UNKNOWN`; el `0` NUNCA se publica como valor conocido —preview y
    # reconciliación devuelven `null`—, que es donde el contrato garantiza «nunca un 0 inventado».
    assert (ob.accumulated_culls_male, ob.culls_status) == (0, "UNKNOWN")
    rec = (await _reconciliacion(http_client, auth_headers, batch_id, lote_id))["opening"]
    assert rec["historical_culls"] is None and rec["culls_status"] == "UNKNOWN"


@pytest.mark.asyncio
async def test_gp_v3_sexage_04_sin_reclasificacion_silenciosa(auth_headers, http_client, seeded_ids):
    """AC-SX-04: 10 aves «de sexaje» que no se cuentan como descarte ⇒ CONSISTENCY_MISMATCH en `live_males`.

    Alojadas 100 machos y 1000 hembras con las vivas de machos ya «corregidas» (90) y sin descartes, mortalidad ni
    transferencias, la ecuación masculina da 100 ≠ 90: el sistema informa la inconsistencia y NO reasigna el ave al
    sexo contrario —las hembras siguen exactamente como se cargaron (1000 vivas, 0 descartes)—.
    """
    await preparar(seeded_ids)
    filas = [_fila_gp(_ref("GP-SX04"),
                      **{**MACHOS_CERO, "birds_placed_males": 100, "historical_mortality_males": 0,
                         "historical_culls_males": 0, "historical_transfers_in_males": 0,
                         "historical_transfers_out_males": 0, "live_males": 90},
                      **{**HEMBRAS_CERO, "birds_placed_females": 1000, "historical_mortality_females": 0,
                         "historical_culls_females": 0, "historical_transfers_in_females": 0,
                         "historical_transfers_out_females": 0, "live_females": 1000})]
    errores, _ = await _errores(http_client, auth_headers, filas, seeded_ids["company_id"], 61)
    assert errores == [(2, "live_males", "CONSISTENCY_MISMATCH")]
    batch_id, _, _ = await _validacion(http_client, auth_headers, filas, seeded_ids["company_id"], 62)
    p = await _preview(http_client, auth_headers, batch_id)
    assert p["rows"][0]["derived"]["balance_check"] == {"males": "INCONSISTENT", "females": "CONSISTENT"}
    # Sin corrección silenciosa de sexo: las cifras femeninas y las masculinas quedan como se declararon.
    valores = p["rows"][0]["values"]
    assert (valores["live_males"]["value"], valores["historical_culls_males"]["value"]) == (90, 0)
    assert (valores["live_females"]["value"], valores["historical_culls_females"]["value"]) == (1000, 0)


@pytest.mark.asyncio
async def test_gp_v3_sexage_05_cull_y_transfer_out_sin_doble_conteo(auth_headers, http_client, seeded_ids):
    """AC-SX-05: 1000 − 50 − (20 + 10 + 20) − 900 = 0 — descarte y transferencia de salida no se solapan.

    La celda acumulada de descartes suma las tres fuentes del anexo: 20 de cría/levante, 10 retiradas por error de
    sexaje y 20 de selección/desalojo. No existe una métrica separada de sexaje (el sexaje ES un descarte), de modo
    que las 900 aves que salieron a otro lote se registran solo como transferencia de salida: sin doble conteo.
    """
    await preparar(seeded_ids)
    descartes_cria, descartes_sexaje, descartes_seleccion = 20, 10, 20
    filas = [_fila_gp(_ref("GP-SX05"),
                      **{**MACHOS_CERO, "birds_placed_males": 1000, "historical_mortality_males": 50,
                         "historical_culls_males": descartes_cria + descartes_sexaje + descartes_seleccion,
                         "historical_transfers_in_males": 0, "historical_transfers_out_males": 900,
                         "live_males": 0}, **HEMBRAS_CERO)]
    batch_id, r, v = await _validacion(http_client, auth_headers, filas, seeded_ids["company_id"], 62)
    assert v["errors"] == []
    p = await _preview(http_client, auth_headers, batch_id)
    assert p["rows"][0]["derived"]["balance_check"] == {"males": "CONSISTENT", "females": "CONSISTENT"}
    valores = p["rows"][0]["values"]
    assert valores["historical_culls_males"]["value"] == 50
    assert valores["historical_transfers_out_males"]["value"] == 900
    assert valores["live_males"]["value"] == 0

