# R-204 · FINDING — AGREGADOS SIN PREDICADO DE UNIDAD (KPI INCUBADORA, KPIs GLOBALES, ALERTAS DEL PANEL)

| Campo | Valor |
|---|---|
| **ID canónico** | **R-204** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | `GET /reports/kpis/hatchery` sin lote, `GET /reports/kpis` (bloque incubadora) y `dashboard.active_alerts` agregan sobre **toda la empresa** sin `lotes_alcanzables`: un usuario sin `hatchery` ve nacidos/cargados/fértiles de la incubadora y alertas de unidades no concedidas/apagadas |
| **Severidad** | **P2** (§49: fuga de dimensión BU en lectura; doctrina OD-09/OD-16) |
| **Clase** | `SECURITY` (fuga por unidad) / `RESPONSE_CONTRACT` (valores incorrectos para el actor) |
| **Proceso** | P-15 (reportes/panel), P-05 (incubadora en KPI) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` (== `origin/main`) |
| **Familia** | GAP-07/GAP-08 (informe D B.8/B.10); E-22/E-23 (informe E); vecino `route_scope.py` (declaración `UNIDAD_UNICA` sin aplicación) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-204/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre **GA-REM-043** |
| **Bloquea SAP** | **SÍ** (fuga BU en KPI; el panel y los KPI alimentan decisiones y el reporte de producción hacia P-08) |
| **UAT del propietario** | no (superficie técnica; verificación por API + regresión de panel/KPI) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `backend/app/reports/service.py:191-207` — `get_kpi_hatchery(lot_id=None)`: `where(company_id)` **sin** `_filtro_de_lotes`; `:262-308` (`_huevos_cargados`, `_huevos_por_tipo`, `_descartados`) ídem; `:415-420` — `get_all_kpis` llama `get_kpi_hatchery(None)` para cualquier actor con `reports:read`.
- `reports/service.py:64-70` — `_filtro_de_lotes` existe y **no se usa en ningún agregado** (grep interno: solo en KPI por lote vía `_exigir_lote`).
- `dashboard/service.py:206-242` — `_get_active_alerts`: `where(company_id, is_resolved == False)` sin `lot_id.in_(_lotes)`; el comentario `:208-211` afirma que está acotado (no lo está). Expone `lot_id`, `alert_type`, `message` (cifras de mortalidad/peso) y `actual_value`.
- Contraste correcto: `operations/service.py:997-1009` acota las mismas alertas; `dashboard/service.py:17-36,44-73,93-140` acota contadores/lotes por tipo.
- `backend/app/business_units/route_scope.py:174-175,215-217` — `/reports/kpis/hatchery` declarada `UNIDAD_UNICA hatchery`; `unidad_requerida()` **sin llamadores** ⇒ la declaración no protege.

### 1.2 Cobertura de tests

`tests/test_kpi_hatchery.py::test_t_022_06` cubre **otra empresa** únicamente. `test_kpi_scope.py` cubre KPI por lote y `lots_by_type`, no el agregado sin lote ni `active_alerts` (grep `active_alerts` en `tests/` → vacío).

## 2 · Causa raíz

La fase 3–6 del endurecimiento BU acotó KPI **por lote** (`_exigir_lote`) y los contadores del panel, pero los **agregados sin lote** y las **alertas** del panel no pasaron por `_filtro_de_lotes`/`_lotes`, y la declaración `route_scope` quedó como metadato sin ejecución («clasificar no protege», informe D §0/B.16).

## 3 · Impacto

- Usuario solo-`breeder`: obtiene nacidos/cargados/fértiles de toda la incubadora de su empresa (dimensión de otra unidad, no concedida).
- Alertas del panel: `lot_id` + mensaje + valor de mortalidad/peso de lotes de unidades apagadas o sin concesión.
- Datos mostrados al operador/reportes que no le corresponden (OD-09: concesión por unidad) y posible contradicción con `operations` (que sí acota).

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `R-132`/`R-134`/`R-141` (fórmulas KPI), `R-119`/`R-120` (UI de permisos) — ninguno cubre el predicado de unidad de estos agregados |
| GA-REM-001…042 | `GA-REM-002`/OD-16 cubren superficies productivas principales; `route_scope` no tiene tranche de aplicación |
| Informes D/E | GAP-07/GAP-08 y E-22/E-23: sin registro previo (grep `active_alerts`/`_filtro_de_lotes` en backlog → vacío) |

Conclusión: **nuevo**; ID asignado **R-204**.

## 5 · Propietario sugerido

Equipo backend (`reports` + `dashboard`). Sin UI nueva (el panel y las páginas consumen el mismo contrato; cambia el conjunto visible para el actor).

## 6 · Bloquea SAP y por qué

**SÍ.** La fiabilidad de los KPI como dato de gestión (y como fuente de reportes de producción que P-08 consumirá) exige que cada actor vea solo sus unidades; hoy un agregado transversal mezcla dimensiones ajenas.

## 7 · Interdependencias

- **R-216** (claves `BirdTypeEnum.*` en `lots_by_type`): mismo archivo de dashboard; no solapan (aquí predicado, allí claves) pero comparten tranche de panel.
- **R-214** (doble conteo huevos): segunda mitad del bloque KPI; su paquete está en registro de backlog (Wave C).
- **route_scope** (GAP-17): decisión documental «aplicar o retirar» — incluida aquí como parte del cierre de la brecha (AC-09).
