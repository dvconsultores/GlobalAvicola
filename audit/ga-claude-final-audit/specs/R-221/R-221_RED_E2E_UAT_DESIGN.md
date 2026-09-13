# R-221 · DISEÑO DE PRUEBAS RED · E2E API · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED (integración backend)

Fichero nuevo: `backend/tests/test_r221_unit_derivation_no_lot.py` (PG de pruebas; empresa con hatchery+broiler habilitadas; actores: global situada, operador con/sin concesión `hatchery`; ciclo OFF/ON con `business_units/admin`).

| Nombre exacto del test | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `test_r221_01_hatchery_off_deniega_inspeccion` | apagar `hatchery` (PATCH disable); global situada; `POST /operations {hatchery_inspection}` sin lote | `status >= 400` y `count(events)==0` — HEAD: **201** (caso runtime `OD16b-global-actor-bu-off-api`) |
| `test_r221_02_sin_concesion_deniega` | operador solo `broiler`; mismo POST | denegado — HEAD: 201 |
| `test_r221_03_con_unidad_nace_clasificado` | operador con `hatchery` ON; POST | 201 y `business_unit_id == hatchery`; el evento **no** aparece en bandeja pendiente — HEAD: 201 con null |
| `test_r221_04_farm_inspection_regla_decidida` | `farm_inspection` sin lote (granja con cadena única / sin ella, según C-02) | regla aplicada (documentada) — HEAD: null/201 |
| `test_r221_05_grandparent_intacto` (control) | import sin lote | flujo R-153 intacto (verde) |
| `test_r221_06_con_lote_intacto` (control) | evento con lote | unidad del lote (verde) |

Extensiones: `test_operations_bu_enforcement.py::test_w15_no_lot_*`; `test_pending_classification.py::test_inequivocos_no_pendientes`.

Ejecución: `bash backend/scripts/run_tests.sh tests/test_r221_unit_derivation_no_lot.py tests/test_operations_bu_enforcement.py tests/test_pending_classification.py` ⇒ 3-4 rojos exactos + controles; salida a `evidence/red/`.

## 2 · Diseño E2E API (C3)

Pila local; actores y datos del §1.

| Caso | Llamadas | Esperado |
|---|---|---|
| R221-RT-01 | disable hatchery → POST `hatchery_inspection` (global situada) | 4xx; 0 filas |
| R221-RT-01b | enable → POST (sin regrant previo no aplica aquí; el actor global situado opera con la habilitación) | 201; `business_unit_id=hatchery` |
| R221-RT-02 | operador solo broiler → POST | 4xx; 0 filas |
| R221-RT-03 | operador con hatchery → POST | 201 clasificado; bandeja sin el evento |
| R221-RT-04 | `farm_inspection` sin lote (regla C-02) | según decisión; documentado |
| R221-RT-05 | import de abuelas sin lote | flujo R-153 intacto |
| R221-RT-06 | evento con lote (control) | intacto |

Artefactos: `evidence/r221/runtime-{red,c3}.json`; captura UI del registro legítimo y del denegado (mensaje seguro). Invariantes: ciclo OFF→denegado→ON restaurado íntegro (la habilitación vuelve a su estado previo); 0 `5xx`.

## 3 · Plan UAT

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R221-A | Micro-decisión C-02: elegir regla para `farm_inspection` sin lote (A/B/C) | Respuesta explícita registrada |
| UAT-R221-B (técnica, 10 min) | Con el propietario/operador: registrar `hatchery_inspection` con la unidad apagada (mensaje denegado seguro) y con la unidad operativa (201) | Comportamiento comprensión + restauración verificada |

Criterio: C-02 decidida; verificación técnica informativa. No bloquea otras tranches.
