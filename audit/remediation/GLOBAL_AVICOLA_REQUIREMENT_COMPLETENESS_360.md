# COMPLETITUD DE REQUISITOS 360°

**Auditoría 360°** · 2026-09-09 · base `7310adb` · **AUDIT ONLY**

Método: cada requisito se traza **requisito → modelo → ruta → pantalla → prueba**. Se conserva
la taxonomía del proyecto (`RA-05`). Estados: `COVERED` · `PARTIAL` · `ABSENT` ·
`SAP_DEFERRED` · `REQUIREMENT_CONFLICT` · `NOT_VERIFIABLE`. Los KPI están en
`KPI_FORMULA_AND_DATA_SOURCE_MATRIX.md` y no se repiten; los estados/reglas en
`OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX.md`.

---

## 1. Funciones que la app debe poder hacer (Recomendación §2 — 18 permitidas)

| Función | Modelo | Ruta | Pantalla | Prueba | Estado |
|---|---|---|---|---|:--:|
| Consultar OC abiertas | `sap_references.PURCHASE_ORDER` | `GET /sap/references?ref_type=` | `SapManagerPage` | `test_sap.py` (solo con flag) | `PARTIAL` (sin «abierta/cerrada») |
| Consultar OT abiertas | `TRANSFER_ORDER` | ídem | ídem | ídem | `PARTIAL` |
| Consultar materiales disponibles | `MATERIAL` importable | ídem | ídem | — | `PARTIAL` (espejo sin consumo) |
| Consultar inventario disponible | — | — | — | — | `SAP_DEFERRED` |
| Consultar granjas, galpones y capacidad | `farms`, `houses.capacity` | `/masters/farms`, `/masters/farms/{id}/houses` | `MasterListPage` | `test_masters*`, `P-12` | `COVERED` (local) |
| Consultar equipos esperados por galpón | — | — | — | — | `SAP_DEFERRED` (G-R11) |
| Capturar recepción real de aves | `bird_reception` + `bird_movements` | `POST /operations` | `OperationFormPage` | `P-01`, `P-03`, `P-06`, `proceso-01` | `COVERED` |
| Distribuir aves por galpón, sexo y lote | `bird_distribution`, `sex`, `target_house_id` | ídem | ídem | `proceso-01` | `COVERED` |
| Registrar peso promedio | `weight_recording.avg_weight`, `sample_size` | ídem | ídem | `P-03`, `P-06` | `COVERED` |
| Registrar temperatura, humedad y hora | `inspection_details`, `event_time` | ídem | ídem | `P-01` | `COVERED` |
| Registrar mortalidad | `mortality_recording`, `cause_id`, `sex` | ídem | ídem | `GA-REM-005` | `COVERED` |
| Registrar consumo de alimento | `feed_movements.quantity_kg`, `feed_type_id`, `week_number` | ídem | ídem | `P-03` | `COVERED` |
| Registrar vacunas/medicinas | `vaccination`, `medication`, ruta, lote de vacuna, dosis | ídem | ídem | `P-03` | `COVERED` |
| Registrar inspección de granja/equipos | `farm_inspection` (+`transport_`, `hatchery_`) | ídem | ídem | `P-01` | `PARTIAL` (sin equipos) |
| Levantar banderas operativas | `operational_alerts` (4 tipos) | `GET /operations/alerts`, `PATCH …/resolve` | `DashboardPage` | `GA-REM-037/038` | `COVERED` |
| Adjuntar evidencias | `evidences` + volumen | 4 rutas `/operations/{id}/evidences*` | `OperationDetailPage` | `GA-REM-009` | `COVERED` (solo en detalle, no en captura → `H360-F03`) |
| Enviar datos aprobados a SAP | `consolidated_movements`, `sap_payloads` | `POST /sap/consolidate`, `/sap/export` | `SapManagerPage` | `test_sap.py` | `PARTIAL` (preparación; entrega `BLOCKED_EXTERNAL`) |
| Conciliar | — | `GET /reports/sap-comparison` (no lee SAP) | `SapComparisonPage` | `P-15` | `SAP_DEFERRED` |

## 2. Datos diarios exigidos por el cliente (`Bases`), por etapa

| Etapa | Dato | Estado | Evidencia / hallazgo |
|---|---|:--:|---|
| Cría / Engorde | aves al inicio del día | `COVERED` | `get_current_bird_balance` (calculado) |
| | muertos · peso muestra · alimento · nuevas aves · incidencias de salud · temperatura/humedad · observaciones | `COVERED` | eventos correspondientes |
| | **consumo de agua** | **`ABSENT`** | 0 apariciones · `R-13` · `GA-REM-021 SPEC_READY` → `H360-B05` P1 |
| | vendidos/sacrificados (engorde) | `COVERED` | `bird_exit` + `destination_plant_id` (**sin validar contra saldo**, `H360-P01`) |
| Producción | gallinas al inicio, muertas, huevos puestos/fértiles/infértiles/descartados, peso promedio huevo, alimento, salud, ambiente, observaciones | `COVERED` | `egg_collection`, `egg_classification` (`egg_type`), `avg_weight` |
| | consumo de agua | `ABSENT` | `H360-B05` |
| Traslado de huevos | fecha recolección, recogidos, fértiles/infértiles/descartados, peso, **condiciones de almacenamiento**, fecha traslado, trasladados, lote, condiciones de transporte, observaciones | `COVERED` | `egg_dispatch`, `egg_storage(storage_temp_c, storage_humidity_pct, fechas)`, `transport_inspection`, `egg_batches` |
| Incubadora | llegada (fecha, recibidos, lote, transporte), almacenamiento (fecha, condiciones, duración), incubación (inicio, cargados, T°, H°, **rotación**, control calidad), nacimiento (fecha, nacidos, **sanos**, **débiles**, tasa), vacunación, traslado a engorde | `PARTIAL` | `egg_reception_hatchery`, `egg_storage`, `incubation_load` + `hatchery_params(temperature, humidity, co2, turning, quantity_loaded, quantity_transferred)`, `birth_registration`, `chick_dispatch`, `chick_batches`. **Sanos/débiles no se distinguen** en el nacimiento (solo `cull_recording` posterior) → `H360-B13` P2 |

## 3. Datos de recepción (Recomendación §6 + app legada p.17-18)

| Campo | Estado | Evidencia |
|---|:--:|---|
| OC SAP · proveedor · material · cantidad esperada/recibida · fechas despacho/recepción · hora · granja · galpones · capacidad · distribución ♀/♂ · raza · peso ♀/♂ · muestra · T°/H° · transporte · mortalidad al arribo · observaciones · evidencias | `COVERED` | `sap_document_ref`, `supplier_id`, `bird_movements(sex, breed_id, avg_weight, quantity)`, `sample_size`, `inspection_details`, `transport_id`, `evidences` |
| Posición de OC (`sap_reference_item`) | `PARTIAL` | columna en `sap_payloads`, nunca poblada (G-R14) |
| Peso reportado por el proveedor vs peso en granja (pantalla legada p.18) | `ABSENT` | un solo `avg_weight` por sexo → `H360-B11` P3 (paridad con legado) |
| Cuadre ♀ + ♂ + mortalidad + rechazo = recibido (Rec. §6) | `ABSENT` | `H360-B01` P2 |
| Pesos dentro de rango esperado (Rec. §6) | `ABSENT` en recepción | la curva solo evalúa `weight_recording` → `H360-B02` P2 |
| Evidencia obligatoria antes de aprobar (Rec. §6) | `ABSENT` | ninguna precondición → `H360-B04` P2 · `AOD-14` |

## 4. Alimento por transferencia (Recomendación §8)

| Paso | Estado | Evidencia |
|---|:--:|---|
| Consultar transferencias activas · confirmar llegada · cantidad recibida · consumo parcial diario/semanal | `COVERED` | `sap_references.TRANSFER_ORDER`, `feed_registration`, `week_number` |
| **Diferencias** · **lote/batch de alimento** · **silo o almacén destino** | `ABSENT` | sin columnas en `feed_movements` (`event_id, feed_type_id, quantity_kg, week_number`) → `H360-B03` P2 |
| Validar que la OT exista | `ABSENT` | `sap_document_ref` libre en `feed_registration` → `H360-S04` P2 |

## 5. Criterios de aceptación MVP (`spec.md §8`, 15 ítems)

| AC | Estado auditado | Evidencia |
|---|:--:|---|
| 1 móvil → «Registrado» | ✓ | `create` → `REGISTERED`; `view_type=mobile` |
| 2 revisión en Centro de Revisión | ✓ | `review/*`, `ReviewCenter` |
| 3 corrección con original | ✓ | `RR-01` |
| 4 aprueba/rechaza con motivo | ✓ | `reject(observations)` |
| 5 consolidación | ✓ | `POST /sap/consolidate` |
| 6 «listos para SAP» | `PARTIAL` | payload no mapeable (`H360-S08`) |
| 7 envío auditado (payload + respuesta) | ✓ | `sap_payloads`, `sap_responses` |
| 8 errores con reintento | `PARTIAL` | backoff fijo (`H360-S07`) |
| 9 idempotencia | ✓ payload · `PARTIAL` evento (`H360-S12`) | — |
| 10 trazabilidad completa | ✓ | `audit/timeline` (`GA-REM-032`) |
| 11 diseño móvil + web | ✓ (no verificado visualmente en esta auditoría) | `docs/11` |
| 12 es/en | ✓ | 988/988 claves |
| 13 navegadores/viewports | `NOT_VERIFIABLE` aquí | `docs/08` |
| 14 aislamiento multi-empresa | ✓ | `RQ-03 COMPLETE`, `OD-14` |
| 15 Super Admin ve todas / regular solo la suya | ✓ con precisión `OD-14` | `test_role_tenancy`, `test_master_tenant_isolation` |

## 6. Móvil, evidencia y experiencia de captura (`docs/02 §7`, `docs/00`, `spec §6`)

| Requisito | Estado | Evidencia / hallazgo |
|---|:--:|---|
| Mobile-first real; operador de campo en teléfono | `COVERED` | `view_type` en JWT; `App.tsx:51-92` redirige móvil a `/menu/poultry`; `MenuHubPage`, `PoultryHubPage`, `PoultryStagePage`, `OperationFormPage` (26 tipos, 1 981 líneas) |
| Offline-awareness | `ABSENT` (declarado «futuro» en `docs/02:595`) | sin service worker / PWA (`grep` 0) → `AOD-16` |
| Evidencia en el acto de captura | `PARTIAL` | subida solo en `OperationDetailPage` (segundo paso) → `H360-F03` P2 |
| Ocultar acciones sin permiso | `ABSENT` | `R-98`/`R-119` abiertos; solo `RolesPage` lee permisos → `H360-F01` P1 (fase 9) |
| Distinguir denegación de vacío / error | `PARTIAL` | resuelto en `UsersPage` (`R-120`); resto de páginas sin estado `prohibido` → `H360-F02` P2 |
| Reenvío seguro desde móvil | `ABSENT` | sin `idempotency_key` de cliente → `H360-S12` |
| Selector de empresa (fase 9) | `BLOCKED` | `company.store.ts:39` → `/masters/companies` (`R-127`) |

## 7. Transversales

| Capacidad | Estado | Evidencia |
|---|:--:|---|
| Auditoría inmutable de cada acción | `COVERED` (aplicación) | listeners `audit/listeners.py`; **sin protección en BD** → `H360-D04` P2 |
| Notificaciones internas (6 tipos) | `COVERED` | `GA-REM-038`, `P-14` |
| Áreas funcionales | `COVERED` | `GA-REM-039` |
| Usuarios, roles, permisos, unidades de negocio | `COVERED` | `OD-13/14/15`, `P-13`, fases 1-8 de `GA-REM-040` |
| Trazabilidad generacional | `COVERED` | `P-10`, `GA-REM-030/031` |
| Activación manual de lotes | `COVERED` | `P-11` |
| Reverso post-SAP (`BR-16`) | `ABSENT` | `H360-P05` |
| Reporte de apertura, exportación Excel/PDF | `COVERED` (cliente) | `utils/export` |

## 8. Recuento

```
Rec. §2 (18 funciones)        COVERED 10 · PARTIAL 5 · SAP_DEFERRED 3
Bases · datos diarios          COVERED 4 etapas · PARTIAL 1 (incubadora sanos/débiles) · ABSENT 1 dato transversal (agua)
Rec. §6 recepción              COVERED 17/22 · ABSENT 4 · PARTIAL 1
Rec. §8 alimento               COVERED 4 · ABSENT 4
spec §8 AC MVP                 ✓ 11 · PARTIAL 3 · NOT_VERIFIABLE 1
móvil / evidencia              COVERED 1 · PARTIAL 2 · ABSENT 3 · BLOCKED 1
```

Hallazgos nuevos de esta matriz: `H360-B01` (cuadre), `B02` (pesos en rango), `B03` (alimento:
lote/silo/diferencias), `B04` (evidencia obligatoria), `B05` (agua, P1), `B11` (peso proveedor),
`B13` (sanos/débiles), `F01` (permisos en UI, P1), `F02` (estados de error), `F03` (evidencia en captura).
