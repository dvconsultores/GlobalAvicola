"""SPEC 014 · Cutover — transferencias históricas entre lotes (RED).

Contrato, parser y validación de los 4 campos nuevos de progenitoras y reproductoras
(`historical_transfers_in|out_males|females`), versión `v3` y la ecuación por sexo

    live = placed + transfers_in − mortality − culls − transfers_out

Veredicto por sexo: `CONSISTENT` · `INCONSISTENT` (⇒ `CONSISTENCY_MISMATCH`) ·
`NOT_FULLY_VERIFIABLE` (algún componente UNKNOWN: sin error y **sin inventar ceros**).

Estos tests son RED: el contrato todavía está en `v2` y la ecuación antigua; deben fallar
por columnas/versión/validación, nunca por sintaxis. Ninguna aserción depende del calendario
(`corte`/`iso_days_ago`, sin literales ISO).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    COLUMNAS, SCHEMA_IDS, TEMPLATE_VERSIONS, corte, crear_batch, csv_v2, fila_engorde, fila_reproductoras,
    preparar, subir, xlsx_v2,
)

from app.cutover.contracts import contrato, lineage  # noqa: E402

NUEVAS = ("historical_transfers_in_males", "historical_transfers_in_females",
          "historical_transfers_out_males", "historical_transfers_out_females")
DESTINOS = ("opening_balances.accumulated_transfers_in_male", "opening_balances.accumulated_transfers_in_female",
            "opening_balances.accumulated_transfers_out_male", "opening_balances.accumulated_transfers_out_female")


def _fila(bu: str, ref: str, *, placed_m: int | None = None, mort_m: int | None = None, culls_m: int | None = None,
          in_m: int | None = None, out_m: int | None = None, live_m: int | None = None,
          placed_f: int | None = None, mort_f: int | None = None, culls_f: int | None = None,
          in_f: int | None = None, out_f: int | None = None, live_f: int | None = None, **extra) -> list:
    """Fila reproductora con los 6 componentes del balance por sexo declarados uno a uno."""
    valores = dict(birds_placed_males=placed_m, historical_mortality_males=mort_m, historical_culls_males=culls_m,
                   historical_transfers_in_males=in_m, historical_transfers_out_males=out_m, live_males=live_m,
                   birds_placed_females=placed_f, historical_mortality_females=mort_f, historical_culls_females=culls_f,
                   historical_transfers_in_females=in_f, historical_transfers_out_females=out_f, live_females=live_f)
    valores = {k: v for k, v in valores.items() if v is not None or k.startswith("historical_transfers")}
    valores.update(extra)
    return fila_reproductoras(bu, ref, **valores)


async def _subir(client, headers, bu: str, filas: list, empresa: int, dias: int):
    batch_id = await crear_batch(client, headers, bu, corte(dias))
    return batch_id, await subir(client, headers, batch_id, xlsx_v2(bu, filas, company_id=empresa))


async def _errores(client, headers, bu: str, filas: list, empresa: int, dias: int) -> tuple[list[tuple], list[dict]]:
    """(errores ordenados por (fila, campo, código), errores completos con mensaje)."""
    batch_id, r = await _subir(client, headers, bu, filas, empresa, dias)
    assert r.status_code == 200, r.text
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    return sorted((e["row_number"], e["field"], e["error_code"]) for e in v["errors"]), v["errors"]


# ── Datos de referencia por sexo (SPEC 014 §3) ───────────────────────────────

ORIGEN = dict(placed_m=1300, mort_m=165, culls_m=0, in_m=0, out_m=300, live_m=835,
              placed_f=9500, mort_f=450, culls_f=50, in_f=0, out_f=0, live_f=9000)
RECEPTOR = dict(placed_m=1000, in_m=300, mort_m=100, culls_m=20, out_m=0, live_m=1180,
                placed_f=9000, in_f=0, mort_f=450, culls_f=0, out_f=0, live_f=8550)


@pytest.mark.asyncio
async def test_br_t01_sin_transferencias(auth_headers, http_client, seeded_ids):
    """Todo `0` conocido: la ecuación clásica sigue cuadrando."""
    await preparar(seeded_ids)
    filas = [_fila("breeder", "HT-01", placed_m=1050, mort_m=50, culls_m=0, in_m=0, out_m=0, live_m=1000,
                   placed_f=9450, mort_f=450, culls_f=0, in_f=0, out_f=0, live_f=9000)]
    errores, _ = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 71)
    assert errores == []


@pytest.mark.asyncio
async def test_br_t02_salida_de_machos_lote_origen(auth_headers, http_client, seeded_ids):
    """1300 − 165 − 0 − 300 = 835: la salida histórica explica el saldo."""
    await preparar(seeded_ids)
    filas = [_fila("breeder", "HT-02", **ORIGEN)]
    errores, _ = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 72)
    assert errores == []


@pytest.mark.asyncio
async def test_br_t03_entrada_de_machos_lote_receptor(auth_headers, http_client, seeded_ids):
    """1000 + 300 − 100 − 20 = 1180: la entrada histórica explica el saldo."""
    await preparar(seeded_ids)
    filas = [_fila("breeder", "HT-03", **RECEPTOR)]
    errores, _ = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 73)
    assert errores == []


@pytest.mark.asyncio
async def test_br_t04_salida_de_hembras(auth_headers, http_client, seeded_ids):
    """9700 − 450 − 0 − 250 = 9000 (hembras que se fueron a otro lote)."""
    await preparar(seeded_ids)
    filas = [_fila("breeder", "HT-04", placed_m=1050, mort_m=50, culls_m=0, in_m=0, out_m=0, live_m=1000,
                   placed_f=9700, mort_f=450, culls_f=0, in_f=0, out_f=250, live_f=9000)]
    errores, _ = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 74)
    assert errores == []


@pytest.mark.asyncio
async def test_br_t05_entrada_de_hembras(auth_headers, http_client, seeded_ids):
    """8700 + 750 − 450 = 9000 (hembras recibidas de otro lote)."""
    await preparar(seeded_ids)
    filas = [_fila("breeder", "HT-05", placed_m=1050, mort_m=50, culls_m=0, in_m=0, out_m=0, live_m=1000,
                   placed_f=8700, mort_f=450, culls_f=0, in_f=750, out_f=0, live_f=9000)]
    errores, _ = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 75)
    assert errores == []


@pytest.mark.asyncio
async def test_br_t06_entradas_y_salidas_a_la_vez(auth_headers, http_client, seeded_ids):
    """1000 + 200 − 50 − 10 − 140 = 1000: el lote recibe y entrega en el mismo periodo."""
    await preparar(seeded_ids)
    filas = [_fila("breeder", "HT-06", placed_m=1000, in_m=200, mort_m=50, culls_m=10, out_m=140, live_m=1000,
                   placed_f=9450, mort_f=450, culls_f=0, in_f=0, out_f=0, live_f=9000)]
    errores, _ = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 76)
    assert errores == []


@pytest.mark.asyncio
async def test_br_t07_saldo_incorrecto_menciona_las_transferencias(auth_headers, http_client, seeded_ids):
    """Con los 6 componentes KNOWN y sin cuadrar: error duro con la ecuación nueva en el detalle."""
    await preparar(seeded_ids)
    filas = [_fila("breeder", "HT-07", **{**ORIGEN, "live_m": 836})]
    errores, detalle = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 77)
    assert errores == [(2, "live_males", "CONSISTENCY_MISMATCH")]
    mensaje = detalle[0]["message"]
    assert "transferencias" in mensaje.lower(), mensaje


@pytest.mark.asyncio
async def test_br_t08_unknown_no_inventa_cero_y_queda_no_verificable(auth_headers, http_client, seeded_ids):
    """`historical_transfers_out_males` UNKNOWN: ni error de consistencia ni cero supuesto."""
    await preparar(seeded_ids)
    origen = {k: v for k, v in ORIGEN.items() if k != "out_m"}
    filas = [_fila("breeder", "HT-08", **origen)]  # 1300 − 165 − 0 = 1135 ≠ 835 (no debe evaluarse)
    batch_id, r = await _subir(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 78)
    assert r.status_code == 200, r.text
    v = (await http_client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=auth_headers)).json()
    assert [(e["row_number"], e["field"], e["error_code"]) for e in v["errors"]] == []

    p = (await http_client.get(f"/api/v1/cutover-batches/{batch_id}/preview", headers=auth_headers)).json()
    balance = p["rows"][0]["derived"]["balance_check"]
    assert balance["males"] == "NOT_FULLY_VERIFIABLE"
    assert balance["females"] == "CONSISTENT"
    assert p["summary"]["balance_not_fully_verifiable_rows"] == 1


@pytest.mark.asyncio
async def test_br_t09_transferencia_negativa_con_mensaje_especifico(auth_headers, http_client, seeded_ids):
    """Negativo ⇒ `NEGATIVE_VALUE` con mensaje propio de transferencias históricas."""
    await preparar(seeded_ids)
    filas = [_fila("breeder", "HT-09", **{**ORIGEN, "in_m": -1})]
    errores, detalle = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 79)
    assert errores == [(2, "historical_transfers_in_males", "NEGATIVE_VALUE")]
    mensaje = detalle[0]["message"].lower()
    assert "transferencias históricas" in mensaje, mensaje
    assert "negativa" in mensaje, mensaje


@pytest.mark.asyncio
async def test_br_t10_decimal_y_na_en_transferencias(auth_headers, http_client, seeded_ids):
    """Decimal (entero esperado), texto y `N/A` (campo sin N/A) se rechazan por campo."""
    await preparar(seeded_ids)
    filas = [
        _fila("breeder", "HT-10A", **{**ORIGEN, "out_f": 2.5}),
        _fila("breeder", "HT-10B", **{**ORIGEN, "in_f": "N/A"}),
    ]
    errores, _ = await _errores(http_client, auth_headers, "breeder", filas, seeded_ids["company_id"], 80)
    assert errores == [(2, "historical_transfers_out_females", "INVALID_INTEGER"),
                       (3, "historical_transfers_in_females", "NOT_APPLICABLE_NOT_ALLOWED")]


# ── Contrato (sin base de datos) ────────────────────────────────────────────

def test_br_t11_contrato_v3_en_progenitoras_y_reproductoras():
    """Las 4 columnas, su orden, obligatoriedad, tipo y destino; el resto de BUs sin cambios."""
    for bu in ("grandparent", "breeder"):
        c = contrato(bu)
        assert c.version == "v3" == TEMPLATE_VERSIONS[bu]
        assert c.schema_id == SCHEMA_IDS[bu] == f"CUTOVER_{bu.upper()}_V3"
        assert c.columns == COLUMNAS[bu]
        inicio = c.columns.index("historical_culls_females") + 1
        assert c.columns[inicio:inicio + 4] == NUEVAS
        for nombre, destino in zip(NUEVAS, DESTINOS):
            spec = c.by_name[nombre]
            assert spec.kind == "int", nombre
            assert spec.required is False and spec.metric is True and spec.allow_na is False, nombre
            assert spec.targets == (destino,), nombre

    assert contrato("broiler").version == "v2" and contrato("broiler").schema_id == "CUTOVER_BROILER_V2"
    assert not set(NUEVAS) & set(contrato("broiler").columns)
    assert contrato("hatchery").version == "v3"
    assert lineage()["UNMAPPED_TEMPLATE_FIELDS"] == 0


# ── Parser y versión (base de datos para el upload) ─────────────────────────

def _sin_transferencias(bu: str, ref: str) -> tuple[tuple, list]:
    """Cabecera y fila de la plantilla ANTERIOR (v2): sin las 4 columnas nuevas."""
    columnas = tuple(c for c in COLUMNAS[bu] if c not in NUEVAS)
    fila = [v for c, v in zip(COLUMNAS[bu], fila_reproductoras(bu, ref, birds_placed_males=1050,
                                                               birds_placed_females=9450)) if c not in NUEVAS]
    return columnas, fila


@pytest.mark.asyncio
async def test_br_t12_plantilla_v2_rechazada_en_breeder_y_grandparent(auth_headers, http_client, seeded_ids):
    """Opción A: la v2 anterior no puede representar el saldo ⇒ `TEMPLATE_VERSION_UNSUPPORTED` con «v3»."""
    await preparar(seeded_ids)
    for dias, bu in ((81, "breeder"), (82, "grandparent")):
        columnas, fila = _sin_transferencias(bu, f"HT-V2-{bu[:2].upper()}")
        batch_id = await crear_batch(http_client, auth_headers, bu, corte(dias))
        r = await subir(http_client, auth_headers, batch_id,
                        xlsx_v2(bu, [fila], company_id=seeded_ids["company_id"], template_version="v2",
                                columnas=columnas, schema_id=f"CUTOVER_{bu.upper()}_V2"))
        assert r.status_code == 422, (bu, r.status_code, r.text)
        assert "TEMPLATE_VERSION_UNSUPPORTED" in r.text and "v3" in r.text, r.text


@pytest.mark.asyncio
async def test_br_t13_engorde_v2_sigue_aceptandose(auth_headers, http_client, seeded_ids):
    """Engorde queda en v2 sin las columnas nuevas (fuera de alcance)."""
    await preparar(seeded_ids)
    batch_id = await crear_batch(http_client, auth_headers, "broiler", corte(83))
    r = await subir(http_client, auth_headers, batch_id,
                    xlsx_v2("broiler", [fila_engorde("HT-ENG")], company_id=seeded_ids["company_id"]))
    assert r.status_code == 200, r.text
    assert r.json()["template_version"] == "v2"


@pytest.mark.asyncio
async def test_br_t14_csv_sin_parametro_usa_la_version_del_contrato(auth_headers, http_client, seeded_ids):
    """CSV sin hoja Meta: la versión por defecto es la del contrato de la BU (v3 en reproductoras)."""
    await preparar(seeded_ids)
    filas = [fila_reproductoras("breeder", "HT-CSV", birds_placed_males=1050, birds_placed_females=9450)]
    batch_id = await crear_batch(http_client, auth_headers, "breeder", corte(84))
    r = await subir(http_client, auth_headers, batch_id, csv_v2("breeder", filas, columnas=COLUMNAS["breeder"]),
                    nombre="corte.csv")
    assert r.status_code == 200, r.text
    assert r.json()["template_version"] == "v3"
    assert r.json()["valid_rows"] == 1, r.text
