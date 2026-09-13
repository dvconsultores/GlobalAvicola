# R-204 · SPEC — PREDICADO DE UNIDAD EN AGREGADOS DE INCUBADORA Y ALERTAS DEL PANEL

Fecha: 2026-09-13 · Hallazgo canónico: **R-204** (P2 · bloquea fuga BU) · HEAD `c0b4afc` · Origen GAP-07/GAP-08 · Registro G-15. Secciones §47.

## 1 · Contexto

`reports` expone KPI por lote (acotados con `_exigir_lote` → 404 fuera de alcance) y agregados sin lote (`kpis` global y `kpis/hatchery`). `dashboard/admin` expone contadores, tendencias y alertas activas. La doctrina de unidades (OD-09/OD-16) exige que toda lectura productiva se acote a `lotes_alcanzables(company, unidades)` — como ya hacen operaciones, lotes y KPI por lote.

## 2 · Evidencia

`R-204_FINDING.md §1`. Código: `reports/service.py:64-70,108-122,191-207,262-308,415-420`; `dashboard/service.py:206-242` vs `operations/service.py:997-1009`; `route_scope.py:174-175,215-217`.

## 3 · Causa raíz

Agregados sin lote sin `_filtro_de_lotes`; `_get_active_alerts` calcula `_ambito` y no lo aplica; declaración `UNIDAD_UNICA` sin ejecución.

## 4 · Impacto de negocio

Fuga de dimensión BU en KPI/tablero; decisiones operativas con datos de unidades no concedidas; inconsistencia con las superficies ya acotadas (mismo dato, distintos conjuntos según pantalla).

## 5 · Comportamiento actual

| Superficie | Actor solo-`breeder` | Debería |
|---|---|---|
| `GET /reports/kpis` (bloque incubadora) | nacidos/cargados/fértiles de toda la empresa | solo lotes de unidades concedidas (sin hatchery ⇒ 0/NULL) |
| `GET /reports/kpis/hatchery` (sin lote) | toda la empresa | ⌘ alcanzable; sin hatchery ⇒ vacío/ceros |
| `dashboard/admin.active_alerts` | alertas de cualquier unidad | solo `lot_id ∈ alcanzables` |

## 6 · Comportamiento esperado

1. `get_kpi_hatchery(None)`: aplicar `_filtro_de_lotes` (`lot_id.in_(alcanzables)`) a **todos** los sumatorios (`_huevos_cargados`, `_huevos_por_tipo`, `_descartados`, nacimientos) y al camino `get_all_kpis`.
2. `_get_active_alerts`: `OperationalAlert.lot_id.in_(_lotes)` (mismo patrón que `operations`); sin unidades alcanzables ⇒ lista vacía.
3. **route_scope**: aplicar `unidad_requerida(hatchery)` a `/reports/kpis/hatchery` **o** retirar la declaración con nota razonada (decisión C-03). Preferencia: aplicar (la declaración ya es canónica), reutilizando el resolutor `unidades_de_alcance_productivo`.
4. Actor con todas las unidades y autoridad global situada: comportamiento idéntico a hoy (sin cambio de valores).
5. Contrato de respuesta sin cambio de forma (mismas claves; valores acotados).

## 7 · Alcance

- `backend/app/reports/service.py` (4 sumatorios + `get_all_kpis`).
- `backend/app/dashboard/service.py` (`_get_active_alerts`).
- `backend/app/business_units/route_scope.py` + un punto de aplicación en `reports/router.py` (o retirada justificada según C-03).
- Tests: `backend/tests/test_r204_unit_scope_aggregates.py` (nuevo) + ampliación `test_kpi_scope.py`/`test_kpi_hatchery.py`.
- Sin migración, sin esquemas, sin permisos.

## 8 · Fuera de alcance

- Fórmulas KPI (R-131/132/133/134/141/214: Wave C, pausada).
- `get_sap_comparison(None)` (superficie `CONTRATO`, excepción declarada `BU-D04`: se cita, no se cambia).
- `lots_by_type` (R-216) y predicado de maestros `UNIDAD_UNICA` (documentado en GAP-17; aquí solo el KPI protegido por OD-16 vigente).

## 9 · Impacto frontend

Ninguno de contrato. `DashboardPage` y `ReportsPage`/`LotReportPage` muestran valores acotados; si el actor no tiene hatchery, el bloque incubadora queda en ceros/vacío (correcto). Sin claves nuevas.

## 10 · Impacto backend

`reports/service.py`, `dashboard/service.py`, `route_scope.py`/`router` (según C-03). Sin modelos ni migraciones.

## 11 · Contrato frontend↔backend

Mismas rutas y claves; cambia el **conjunto** de filas agregadas para actores sin todas las unidades. Sin nuevos códigos de error (nunca 403 por unidad en lectura agregada: se devuelve el subconjunto alcanzable, patrón vigente de KPI por lote).

## 12 · Impacto en datos

Ninguno (solo lectura).

## 13 · Seguridad

Cierra la fuga de dimensión BU (GAP-07/08). Reutiliza el resolutor canónico (`unidades_de_alcance_productivo`) sin nuevos atajos. Mantiene fail-closed sin concesiones (predicado `false()` ⇒ vacío).

## 14 · Inquilino

`company_id` ya aplicado en ambas consultas; el paquete añade el segundo eje (unidad) sin tocar el primero.

## 15 · Unidad de negocio

Es el objeto del paquete; aplica la doctrina OD-16 a la lectura agregada (apagado prevalece, concesión viva requerida).

## 16 · RBAC

`reports:read`/`dashboard:read` sin cambio.

## 17 · Transacciones

Lecturas; sin cambio.

## 18 · Auditoría

Sin cambio (consultas no auditadas por diseño).

## 19 · i18n

N/A.

## 20 · Escritorio · 21 · Móvil

Sin cambio de UI; verificación de que el panel móvil (`dashboard/mobile`) no se ve afectado (no usa las superficies tocadas).

## 22 · Manejo de errores

Sin cambio.

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Indirecto: los KPI/reportes de producción dejan de mezclar unidades; el comparativo SAP se cita pero no se toca (excepción declarada).

## 25 · Compatibilidad hacia atrás

- Actor con todas las unidades: valores idénticos.
- Actor parcial: valores cambian a su subconjunto (corrección).
- Consumidores: sin cambio de forma.

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R204-01 | Actor solo-`breeder`: `GET /reports/kpis` bloque incubadora ⇒ ceros/NULL (no datos de hatchery) |
| AC-R204-02 | Actor solo-`breeder`: `GET /reports/kpis/hatchery` ⇒ vacío/ceros (o 403 si C-03=aplicar y se decide 403; por defecto: subconjunto vacío) |
| AC-R204-03 | Actor con `hatchery` concedida y viva: valores idénticos a hoy (control) |
| AC-R204-04 | Unidad `hatchery` **apagada**: actor situado no ve sus agregados (OD-16) |
| AC-R204-05 | `dashboard/admin.active_alerts`: solo `lot_id` alcanzables; con 0 alcanzables ⇒ `[]` |
| AC-R204-06 | Otra empresa: sin cambio (control `test_t_022_06`) |
| AC-R204-07 | Autoridad global situada con todas las unidades: control idéntico |
| AC-R204-08 | `route_scope`: decisión aplicada o retirada con nota (AC documental) |
| AC-R204-09 | Sin migración/endpoint/permiso; sin cambio de esquemas |
| AC-R204-10 | Regresión: `test_kpi_scope.py` (7+), `test_kpi_hatchery.py`, `test_od14_productive_surfaces.py`, `test_kpi_scope::test_apagar_la_unidad_retira_su_kpi` verdes |

## 27 · Pruebas RED→GREEN

`R-204_RED_E2E_UAT_DESIGN.md §1`: `test_r204_01_kpi_global_sin_hatchery_es_cero`, `test_r204_02_kpi_hatchery_sin_unidad_es_vacio`, `test_r204_03_alertas_panel_acotadas`, `test_r204_04_unidad_apagada_no_agrega`, `test_r204_05_control_con_unidad`, `test_r204_06_control_otra_empresa`.

## 28 · E2E

API sobre pila local (`§2`): `R204-RT-01…06` con actores por unidad (breeder-only, hatchery, apagada) + panel; artefacto `evidence/r204/runtime-{red,c3}.json`. Regresión UI mínima: `/reports` y `/dashboard/admin` cargan (0 fatales).

## 29 · UAT

**No requiere UAT del propietario** (corrección de alcance invisible para actores completos). Verificación informativa opcional: comparar panel/KPI de un actor completo antes/después (idénticos).

## 30 · Criterios de cierre

RED válida · GREEN local (AC01-10) · sensibilidad (S1: retirar predicado de hatchery ⇒ AC01/02/04 rojas; S2: retirar predicado de alertas ⇒ AC05 roja) · sin migración/endpoint/permiso · R-204 → `CLOSED` con GA-REM asignado.
