# R-211 · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

`backend/tests/test_r211_house_capacity_rows.py` (PG de pruebas; granja con galpones A=500, B=500; operador con unidad).

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `test_r211_01_dos_galpones_cada_uno_en_capacidad_es_201` | recepción con filas `[{A,500},{B,500}]` | `status == 201` — HEAD: 400 BR-17 |
| `test_r211_02_fila_excedida_es_400_con_galpon` | filas `[{A,600}]` | 400 y mensaje contiene «A»/capacidad — HEAD: mensaje sin galpón |
| `test_r211_03_mono_galpon_control` | fila única 600 en A | 400 (verde) |
| `test_r211_04_acumulado` (C-02) | dos eventos de 500 a A | A: 201+201 (residual) · B: segundo 400 |

Ampliación: `test_reception_reconciliation.py::test_multi_galpon_*` si procede.

Ejecución: `bash backend/scripts/run_tests.sh tests/test_r211_house_capacity_rows.py` ⇒ rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E (C3)

| Caso | Pasos | Esperado |
|---|---|---|
| R211-RT-01 | API + UI local: recepción 500/500 a A/B | 201; poblaciones por galpón correctas |
| R211-RT-02 | fila 600 en A | 400 con galpón/capacidad |
| R211-RT-03 | mono-galpón control | 400 |
| R211-RT-04 | (C-02) acumulado | según decisión |
| R211-RT-05 | distribución multi-galpón | intacta |

Artefactos: `evidence/r211/runtime-{red,c3}.json` + captura UI del 201 multi-galpón.

## 3 · Plan UAT

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R211-A | Decisión C-02 (A/B) registrada | Respuesta explícita |
| UAT-R211-B | Operador registra llegada repartida entre dos galpones por UI | Guardado 201; cada galpón reflejado en el evento |

Criterio: C-02 registrada; caso B informativo (10 min, agrupable con R-205/R-190).
