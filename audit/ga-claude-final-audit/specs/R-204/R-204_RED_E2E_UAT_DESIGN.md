# R-204 · DISEÑO DE PRUEBAS RED · E2E API · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED (integración backend)

Fichero nuevo: `backend/tests/test_r204_unit_scope_aggregates.py` (PG de pruebas; empresa con `breeder` + `hatchery` habilitadas y lotes/eventos sembrados en ambas; concesiones por actor).

| Nombre exacto del test | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `test_r204_01_kpi_global_sin_hatchery_es_cero` | actor con concesión solo `breeder`; `GET /reports/kpis` | claves de incubadora en 0/NULL — HEAD: nacidos/cargados/fértiles de hatchery |
| `test_r204_02_kpi_hatchery_sin_unidad_es_vacio` | mismo actor; `GET /reports/kpis/hatchery` | ceros/NULL — HEAD: datos completos |
| `test_r204_03_alertas_panel_acotadas` | alerta activa en lote de hatchery; actor breeder; `GET /dashboard/admin` | `active_alerts == []` — HEAD: la incluye |
| `test_r204_04_unidad_apagada_no_agrega` | apagar hatchery (`PATCH …/disable`); actor situado con concesión previa | ceros/vacío — HEAD: agrega |
| `test_r204_05_control_con_unidad` | actor con hatchery concedida y viva | valores idénticos a los actuales (verde) |
| `test_r204_06_control_otra_empresa` | actor de empresa B | sin cambio (verde) |

Ampliaciones: `test_kpi_scope.py::test_los_agregados_sin_lote_respetan_la_unidad`; `test_kpi_hatchery.py::test_t_022_06b_la_unidad_apagada_no_aporta_al_agregado`.

Ejecución: `bash backend/scripts/run_tests.sh tests/test_r204_unit_scope_aggregates.py tests/test_kpi_scope.py tests/test_kpi_hatchery.py` ⇒ 4 rojos exactos + controles; salida a `evidence/red/`.

## 2 · Diseño E2E API (C3)

Pila local; actores: breeder-only, hatchery-completa, global situada, empresa B. Datos: 1 lote hatchery con carga/nacimiento, 1 lote breeder, 1 alerta activa en cada uno.

| Caso | Llamadas | Esperado |
|---|---|---|
| R204-RT-01 | breeder-only → `/reports/kpis` | bloque incubadora 0/NULL |
| R204-RT-02 | breeder-only → `/reports/kpis/hatchery` | vacío/ceros |
| R204-RT-03 | hatchery-completa → ambos | valores completos (control) |
| R204-RT-04 | apagar hatchery → repetir RT-03 con actor situado | ceros/vacío |
| R204-RT-05 | breeder-only → `/dashboard/admin` | `active_alerts` solo de sus lotes |
| R204-RT-06 | empresa B → panel/KPI | sin cambio; sin fuga cruzada |

Artefactos: `evidence/r204/runtime-{red,c3}.json`; captura de `/reports` y `/dashboard/admin` en local (0 fatales). Invariantes: 0 `5xx`; valores de control idénticos antes/después para el actor completo.

## 3 · Plan UAT

**No requerida.** Verificación informativa opcional: para un actor con todas las unidades, comparar capturas de panel/KPI antes/después (deben ser idénticas); 5 minutos.
