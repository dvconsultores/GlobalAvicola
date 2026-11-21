"""SPEC 018 §8 · RESIDUAL O-15 — el agregado del preview no convierte UNKNOWN en 0.

Reglas certificadas aquí (D-18/D-19/D-20, AC-O15-01..07):

- **D-18** el total de un lote de filas es la suma solo si **todas** las filas válidas aportan un
  valor conocido; con cualquier UNKNOWN el total es UNKNOWN (`null`), nunca una suma parcial.
  `[900, 800, 0] → 1700` · `[900, UNKNOWN, 0] → UNKNOWN` · `[UNKNOWN] → UNKNOWN` · `[0, 0] → 0` ·
  `[] → 0` (sin filas los chips de conteo parten de 0). NOT_APPLICABLE no propaga: aporta 0.
- **D-19** junto al valor se publican `<clave>_status` (KNOWN/UNKNOWN) y `<clave>_unknown_rows`;
  se aplica a `eggs_in_process` y `chicks_available` de incubadora. Las demás BU no ganan claves.
- La fila sigue mostrando su propio derivado (900 en la fila A, UNKNOWN en la fila B).

La infraestructura (contrato XLSX de incubadora v4, maestros, cabeceras) se reutiliza de
`cutover_v2_fixtures`/`test_cutover_hatchery_v4`, sin duplicarla.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from cutover_v2_fixtures import (  # noqa: E402
    corte, crear_batch, fila_incubadora, fila_reproductoras, preparar, subir, xlsx_v2,
)

from app.cutover.service import _agregar_con_unknown  # noqa: E402

EMPRESA = 1


async def _preview_de(client, headers, bu: str, filas: list, dias: int) -> dict:
    """Batch subido + validado ⇒ preview completo (`summary` + `rows`) como lo ve la API."""
    batch_id = await crear_batch(client, headers, bu, corte(dias))
    r = await subir(client, headers, batch_id, xlsx_v2(bu, filas, company_id=EMPRESA))
    assert r.status_code == 200, r.text
    v = (await client.get(f"/api/v1/cutover-batches/{batch_id}/validation", headers=headers)).json()
    assert v["invalid_rows"] == 0, v["errors"]
    p = await client.get(f"/api/v1/cutover-batches/{batch_id}/preview", headers=headers)
    assert p.status_code == 200, p.text
    return p.json()


def _filas_por_ref(preview: dict) -> dict[str, dict]:
    return {f["legacy_lot_code"]: f for f in preview["rows"]}


# ── AC-O15-01..05 · helper puro ─────────────────────────────────────────────

def test_o15_01_todas_conocidas_suman():
    """AC-O15-01: `[900, 800, 0] → 1700` (el cero conocido participa; sin filas UNKNOWN)."""
    assert _agregar_con_unknown([900, 800, 0]) == (1700, 0)


def test_o15_02_una_unknown_propaga_unknown():
    """AC-O15-02: `[900, UNKNOWN, 0] → UNKNOWN` — jamás la suma parcial 900."""
    assert _agregar_con_unknown([900, None, 0]) == (None, 1)


def test_o15_03_unica_fila_unknown():
    """AC-O15-03: `[UNKNOWN] → UNKNOWN` (no se degrada a 0)."""
    assert _agregar_con_unknown([None]) == (None, 1)


def test_o15_04_ceros_conocidos():
    """AC-O15-04: `[0, 0] → 0` con estado KNOWN (un 0 conocido se pinta 0)."""
    assert _agregar_con_unknown([0, 0]) == (0, 0)


def test_o15_05_sin_filas():
    """AC-O15-05: `[] → 0` — semantica vigente: sin filas = 0, los chips de conteo parten de 0."""
    assert _agregar_con_unknown([]) == (0, 0)


# ── AC-O15-06 · summary de incubadora sobre un batch real con dos filas ─────

@pytest.mark.asyncio
async def test_o15_06_summary_de_incubadora_con_dos_filas(auth_headers, http_client, seeded_ids):
    """A = 900 en proceso, B = UNKNOWN ⇒ summary UNKNOWN (nunca 900); con B' = 1000 ⇒ 1900 KNOWN."""
    await preparar(seeded_ids)

    # A: set 9000 − transferred 8000 − fosa 100 = 900 · B: fosa vacía ⇒ en proceso UNKNOWN.
    preview = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-A", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=100),
        fila_incubadora("O15-B", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=None),
    ], 91)
    resumen = preview["summary"]
    filas = _filas_por_ref(preview)

    assert filas["O15-A"]["derived"]["eggs_in_process"] == 900
    assert filas["O15-B"]["derived"]["eggs_in_process"] is None

    assert resumen["eggs_in_process"] is None                 # D-18: UNKNOWN, no suma parcial
    assert resumen["eggs_in_process"] != 900                 # explícito: nunca 900
    assert resumen["eggs_in_process_status"] == "UNKNOWN"
    assert resumen["eggs_in_process_unknown_rows"] == 1

    # Con B' de fosa 0 conocida (en proceso 1000) el total pasa a ser numérico.
    preview2 = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-A2", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=100),
        fila_incubadora("O15-B2", eggs_set=9000, eggs_transferred=8000, fertile_eggs_to_pit=0),
    ], 90)
    resumen2 = preview2["summary"]
    filas2 = _filas_por_ref(preview2)

    assert filas2["O15-B2"]["derived"]["eggs_in_process"] == 1000
    assert resumen2["eggs_in_process"] == 1900
    assert resumen2["eggs_in_process_status"] == "KNOWN"
    assert resumen2["eggs_in_process_unknown_rows"] == 0


@pytest.mark.asyncio
async def test_o15_07_summary_chicks_available(auth_headers, http_client, seeded_ids):
    """`chicks_available` vacío ⇒ summary UNKNOWN; `0` conocido ⇒ 0 KNOWN (D-18/D-19)."""
    await preparar(seeded_ids)

    preview = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-C", chicks_hatched=0, chicks_available=0),
        fila_incubadora("O15-D", chicks_hatched=0, chicks_available=None),
    ], 89)
    resumen = preview["summary"]
    assert resumen["chicks_available"] is None
    assert resumen["chicks_available_status"] == "UNKNOWN"
    assert resumen["chicks_available_unknown_rows"] == 1

    preview2 = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-E", chicks_hatched=0, chicks_available=0),
    ], 88)
    resumen2 = preview2["summary"]
    assert resumen2["chicks_available"] == 0
    assert resumen2["chicks_available_status"] == "KNOWN"
    assert resumen2["chicks_available_unknown_rows"] == 0


@pytest.mark.asyncio
async def test_o15_08_otras_bu_no_ganan_las_claves_nuevas(auth_headers, http_client, seeded_ids):
    """El contrato D-19 es de incubadora: reproductoras mantiene su summary sin `*_status` nuevos."""
    await preparar(seeded_ids)

    preview = await _preview_de(http_client, auth_headers, "breeder",
                                [fila_reproductoras("breeder", "O15-REP")], 87)
    resumen = preview["summary"]
    for clave in ("eggs_in_process_status", "eggs_in_process_unknown_rows",
                  "chicks_available_status", "chicks_available_unknown_rows"):
        assert clave not in resumen, clave
    # Y el summary de siempre sigue ahí, intacto.
    assert resumen["live_males"] == 1000 and resumen["live_females"] == 9000
    assert resumen["historical_mortality_status"] == "KNOWN"


@pytest.mark.asyncio
async def test_o15_09_chicks_available_na_no_propaga(auth_headers, http_client, seeded_ids):
    """Un `N/A` en `chicks_available` aporta 0 y **no** propaga UNKNOWN (D-18: solo UNKNOWN propaga)."""
    await preparar(seeded_ids)

    # (a) única fila válida con `chicks_available` N/A ⇒ 0 KNOWN, sin filas UNKNOWN.
    preview = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-F", chicks_available="N/A"),
    ], 86)
    resumen = preview["summary"]
    assert resumen["chicks_available"] == 0
    assert resumen["chicks_available_status"] == "KNOWN"
    assert resumen["chicks_available_unknown_rows"] == 0

    # (b) N/A junto a un valor conocido ⇒ 5 KNOWN (el N/A no anula ni ensucia el total).
    preview2 = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-G", chicks_available="N/A"),
        fila_incubadora("O15-H", eggs_transferred=100, chicks_hatched=5, chicks_available=5),
    ], 85)
    resumen2 = preview2["summary"]
    assert resumen2["chicks_available"] == 5
    assert resumen2["chicks_available_status"] == "KNOWN"
    assert resumen2["chicks_available_unknown_rows"] == 0

    # (c) N/A + UNKNOWN (celda vacía) ⇒ UNKNOWN con **una** fila unknown: el N/A no cuenta.
    preview3 = await _preview_de(http_client, auth_headers, "hatchery", [
        fila_incubadora("O15-I", chicks_available="N/A"),
        fila_incubadora("O15-J", chicks_available=None),
    ], 84)
    resumen3 = preview3["summary"]
    assert resumen3["chicks_available"] is None
    assert resumen3["chicks_available_status"] == "UNKNOWN"
    assert resumen3["chicks_available_unknown_rows"] == 1
