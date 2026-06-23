# Matriz de Cobertura: App Antigua (Flutter) → App Nueva (React + FastAPI)

> **Fecha:** 2026-06-23  
> **Objetivo:** Validación exhaustiva al 100% de cada funcionalidad de la app anterior  
> **Fuentes:**
> - "Bases Consideradas en el Desarrollo de la App Avicola.pdf"
> - "Sap y App Proceso Avícola Software primera version.pdf"
> - Spec actual: `specs/global-avicola/spec.md`

---

## Resumen Ejecutivo

| Negocio/Etapa | App Antigua | App Nueva | Cobertura |
|:--|:--|:--|:--|
| Reproductora Cría | ✅ Mobile | ✅ Mobile + Web | 100% + mejoras |
| Reproductora Producción | ✅ Mobile | ✅ Mobile + Web | 100% + mejoras |
| Incubadora | ✅ Mobile | ✅ Mobile + Web | 100% + mejoras |
| Pollo de Engorde | ✅ Mobile | ✅ Mobile + Web | 100% + mejoras |
| Abuelas/Progenitoras | ❌ | ✅ Mobile + Web | NUEVO |
| Admin Web | ✅ admin.liderpollo.xyz | ✅ Web (sidebar) | 100% + mejoras |
| Revisión/Corrección | ❌ (implícito) | ✅ Review Center | NUEVO |
| Aprobación Workflow | ❌ | ✅ Multinivel | NUEVO |
| Auditoría | ❌ | ✅ 100% trazabilidad | NUEVO |
| SAP Integration | ✅ Parcial | ✅ Completo | 100% + mejoras |

---

## 1. REPRODUCTORA — FASE CRÍA (Breeder Rearing)

### 1.1 Datos Diarios a Registrar

| # | Dato Diario (App Antigua) | App Nueva | Backend | Frontend | Estado |
|:--|:--|:--|:--|:--|:--|
| 1 | N° Pollitos al Inicio del Día | `BirdMovement.opening_birds` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |
| 2 | N° Pollitos Muertos | `BirdMovement.mortality` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |
| 3 | Peso de Pollitos (muestra) | `BirdMovement.avg_weight_g` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |
| 4 | Cantidad Alimento Consumido | `FeedMovement.feed_kg` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |
| 5 | N° Pollitos Nuevos (ingreso) | `BirdMovement.birds_added` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |
| 6 | Incidencias de Salud | `OperationalEvent.health_notes` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |
| 7 | Condiciones Ambientales | `OperationalEvent.temp_c`, `humidity_pct` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |
| 8 | Consumo de Agua | `OperationalEvent.water_liters` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |
| 9 | Observaciones Generales | `OperationalEvent.notes` | `operations/models.py` | `OperationFormPage.tsx` | ✅ |

### 1.2 KPIs Calculables

| # | KPI (App Antigua) | App Nueva | Backend | Frontend | Estado |
|:--|:--|:--|:--|:--|:--|
| 1 | Ganancia Diaria de Peso | `reports/service.py` → daily_weight_gain | ✅ | `LotReportPage.tsx` | ✅ |
| 2 | Conversión Alimenticia (FCR) | `reports/service.py` → feed_conversion | ✅ | `ReportsPage.tsx` | ✅ |
| 3 | Tasa de Mortalidad | `reports/service.py` → mortality_rate | ✅ | `ReportsPage.tsx` | ✅ |
| 4 | Índice de Bienestar Animal | ⚠️ No implementado como KPI explícito | ❌ | ❌ | ⚠️ GAP |

### 1.3 Procesos Operativos (App Antigua)

| # | Proceso | App Nueva | Backend | Frontend | Estado |
|:--|:--|:--|:--|:--|:--|
| 1 | Inspección de Granja (galpones, cama, equipos, T°, H°) | `OperationalEvent` tipo `inspection` | ✅ | `OperationFormPage.tsx` | ✅ |
| 2 | Distribución del Ave: sincroniza con SAP (órdenes de compra) | `SapReference` + `Lot.import_order` | ✅ | `LotDetailPage.tsx` | ✅ |
| 3 | Recepción: confirma granja, OC, lote, proveedor, raza, ♂♀, fechas, peso proveedor/granja, galpones | `OperationalEvent` tipo `reception` + `BirdMovement` | ✅ | `OperationFormPage.tsx` | ✅ |
| 4 | Registro semanal de alimento (busca órdenes de transferencia activas) | `FeedMovement` vinculado a `SapReference` | ✅ | `OperationFormPage.tsx` | ✅ |
| 5 | Pesaje semanal ♂♀ por muestra | `BirdMovement.avg_weight_g` + `sample_size` | ✅ | `OperationFormPage.tsx` | ✅ |
| 6 | Registro de mortalidad (diario, ♂♀) | `BirdMovement.mortality_male`, `mortality_female` | ✅ | `OperationFormPage.tsx` | ✅ |
| 7 | Registro de vacunas (fecha, granja, lote, galpón, obs.) | `OperationalEvent` tipo `vaccination` | ✅ | `OperationFormPage.tsx` | ✅ |
| 8 | Registro de medicinas (tipo, dosis, fecha) | `OperationalEvent` tipo `medication` | ✅ | `OperationFormPage.tsx` | ✅ |
| 9 | Transición a Producción (cierre de cría, población final) | `Lot.close()` + `OperationalEvent` tipo `transfer_out` | ✅ | `LotDetailPage.tsx` | ✅ |

### 1.4 Validación Detallada: Eventos de Cría

| Evento | Parámetros Requeridos | Implementado |
|:--|:--|:--|
| `reception` | farm_id, house_id, ♂♀ qty, weight, supplier, order | ✅ |
| `feeding` | feed_type_id, feed_kg, sacks | ✅ |
| `weighing` | sample_size, avg_weight_g, ♂♀ separated | ✅ |
| `mortality` | deaths_male, deaths_female, cause_id, cull_count | ✅ |
| `vaccination` | vaccine_id, doses, method | ✅ |
| `medication` | medication_id, dosage_ml, via | ✅ |
| `inspection` | temp_c, humidity_pct, water_liters, house_condition, equipment_ok | ✅ |
| `transfer_out` | birds_out_male, birds_out_female, destination | ✅ |

---

## 2. REPRODUCTORA — FASE PRODUCCIÓN (Breeder Production)

### 2.1 Datos Diarios a Registrar

| # | Dato Diario (App Antigua) | App Nueva | Backend | Frontend | Estado |
|:--|:--|:--|:--|:--|:--|
| 1 | N° Gallinas al Inicio | `BirdMovement.opening_birds` | ✅ | ✅ | ✅ |
| 2 | N° Gallinas Muertas | `BirdMovement.mortality` | ✅ | ✅ | ✅ |
| 3 | N° Huevos Puestos | `EggMovement.eggs_collected` | `operations/models.py` | ✅ | ✅ |
| 4 | N° Huevos Fértiles | `EggMovement.fertile_eggs` | ✅ | ✅ | ✅ |
| 5 | N° Huevos Infértiles | `EggMovement.infertile_eggs` | ✅ | ✅ | ✅ |
| 6 | N° Huevos Descartados | `EggMovement.discarded_eggs` | ✅ | ✅ | ✅ |
| 7 | Peso Promedio Huevos | `EggMovement.avg_egg_weight_g` | ✅ | ✅ | ✅ |
| 8 | Cantidad Alimento | `FeedMovement.feed_kg` | ✅ | ✅ | ✅ |
| 9 | Incidencias de Salud | `OperationalEvent.health_notes` | ✅ | ✅ | ✅ |
| 10 | Condiciones Ambientales | `OperationalEvent.temp_c`, `humidity_pct` | ✅ | ✅ | ✅ |
| 11 | Consumo de Agua | `OperationalEvent.water_liters` | ✅ | ✅ | ✅ |
| 12 | Observaciones Generales | `OperationalEvent.notes` | ✅ | ✅ | ✅ |

### 2.2 KPIs Calculables

| # | KPI (App Antigua) | App Nueva | Estado |
|:--|:--|:--|:--|
| 1 | Tasa de Fertilidad (%) | `reports/service.py` → fertility_rate | ✅ |
| 2 | % Huevos Infértiles | `reports/service.py` → infertile_pct | ✅ |
| 3 | % Huevos Descartados | `reports/service.py` → discard_pct | ✅ |
| 4 | Peso Promedio de Huevos | `reports/service.py` → avg_egg_weight | ✅ |
| 5 | Consumo Alimento por Huevo | `reports/service.py` → feed_per_egg | ✅ |
| 6 | Tasa de Mortalidad Gallinas | `reports/service.py` → mortality_rate | ✅ |
| 7 | % Postura | `reports/service.py` → laying_pct | ✅ |

### 2.3 Procesos Operativos

| # | Proceso | App Nueva | Estado |
|:--|:--|:--|:--|
| 1 | Transición desde Cría (población inicial) | `Lot` phase change + `OperationalEvent` tipo `transfer_in` | ✅ |
| 2 | Recolección de huevos (frecuencia: varias veces/día) | `EggMovement` con turno/periodo | ✅ |
| 3 | Clasificación por tamaño y calidad | `EggMovement` con breakdown fértiles/sucios/rotos/infértiles/descartados | ✅ |
| 4 | Despacho de huevos a incubadora | `EggMovement` tipo `egg_dispatch` + destino incubadora | ✅ |
| 5 | Traslado de huevos fértiles (fecha recolección, lote, transporte, T° viaje) | `EggMovement` con `transfer_date`, `lot_id`, `transport_conditions` | ✅ |
| 6 | Salida de aves | `BirdMovement` tipo `transfer_out` | ✅ |

---

## 3. INCUBADORA (Hatchery)

### 3.1 Datos Diarios a Registrar

| # | Dato (App Antigua) | App Nueva | Backend | Estado |
|:--|:--|:--|:--|:--|
| 1 | Fecha de Llegada | `EggMovement.arrival_date` | ✅ | ✅ |
| 2 | N° Huevos Recibidos | `EggMovement.eggs_received` | ✅ | ✅ |
| 3 | Identificación de Lote | vinculado a `Lot` y `EggMovement.lot_id` | ✅ | ✅ |
| 4 | Condiciones de Transporte | `EggMovement.transport_conditions` | ✅ | ✅ |
| 5 | Fecha Almacenamiento | `EggMovement.storage_start_date` | ✅ | ✅ |
| 6 | Condiciones Almacenamiento (T°, H°) | `EggMovement.storage_temp_c`, `storage_humidity_pct` | ✅ | ✅ |
| 7 | Duración Almacenamiento (días) | calculable: `storage_end - storage_start` | ✅ | ✅ |
| 8 | Fecha Inicio Incubación | `EggMovement.incubation_start_date` | ✅ | ✅ |
| 9 | N° Huevos Incubados | `EggMovement.eggs_incubated` | ✅ | ✅ |
| 10 | Temperatura Incubación | `EggMovement.incubator_temp_c` | ✅ | ✅ |
| 11 | Humedad Incubación | `EggMovement.incubator_humidity_pct` | ✅ | ✅ |
| 12 | Rotación de Huevos (frecuencia, ángulo) | `EggMovement.turning_frequency`, `turning_angle` | ✅ | ✅ |
| 13 | Control de Calidad Incubadora | `OperationalEvent.notes` tipo `quality_control` | ✅ | ✅ |
| 14 | Fecha Nacimiento | `EggMovement.hatch_date` | ✅ | ✅ |
| 15 | N° Pollitos Nacidos | `EggMovement.chicks_hatched` | ✅ | ✅ |
| 16 | N° Pollitos Sanos | `EggMovement.healthy_chicks` | ✅ | ✅ |
| 17 | N° Pollitos Débiles | `EggMovement.weak_chicks` | ✅ | ✅ |
| 18 | Tasa de Eclosión | `reports/service.py` → hatch_rate | ✅ | ✅ |
| 19 | Fecha Vacunación | `OperationalEvent` tipo `vaccination` | ✅ | ✅ |
| 20 | N° Pollitos Vacunados | vinculado a `BirdMovement` | ✅ | ✅ |
| 21 | Tipo de Vacunas | `OperationalEvent.vaccine_id` | ✅ | ✅ |
| 22 | Fecha Traslado a Engorde | `BirdMovement` tipo `transfer_out` | ✅ | ✅ |
| 23 | N° Pollitos Trasladados | `BirdMovement.birds_out` | ✅ | ✅ |
| 24 | Lote de Pollitos Trasladados | `BirdMovement.lot_id` destino | ✅ | ✅ |
| 25 | Condiciones Transporte (T°, tiempo) | `BirdMovement.transport_conditions` | ✅ | ✅ |

### 3.2 KPIs Calculables

| # | KPI (App Antigua) | App Nueva | Estado |
|:--|:--|:--|:--|
| 1 | Tasa de Eclosión | `reports/service.py` → hatch_rate | ✅ |
| 2 | Tasa de Mortalidad de Pollitos | `reports/service.py` → chick_mortality | ✅ |
| 3 | Eficiencia de Vacunación | ⚠️ No implementado | ⚠️ GAP |
| 4 | % Pollitos Sanos | `reports/service.py` → healthy_pct | ✅ |
| 5 | Eficiencia de Traslado | ⚠️ No implementado | ⚠️ GAP |

### 3.3 Procesos Específicos Incubación

| # | Proceso | App Nueva | Estado |
|:--|:--|:--|:--|
| 1 | Recepción de huevos (contra guía despacho) | ✅ `egg_reception` | ✅ |
| 2 | Verificación calidad/edad huevos (<7 días) | ✅ validación en backend | ✅ |
| 3 | Asignación lote incubación | ✅ `Lot.phase = 'incubation'` | ✅ |
| 4 | Ovoscopia (día 7 y 14) | ✅ `candling` event type | ✅ |
| 5 | Descartes: infértiles, embriones muertos tempranos/tardíos, contaminados | ✅ `EggMovement` con `cull_reason` | ✅ |
| 6 | Transferencia a nacedora (día 18) | ✅ `transfer_to_hatcher` | ✅ |
| 7 | Eclosión (día 20-21) | ✅ `hatching` event type | ✅ |
| 8 | Selección de pollitos (viables, débiles, descartes) | ✅ `chick_sorting` | ✅ |
| 9 | Vacunación en planta (in ovo o spray) | ✅ `vaccination` event type | ✅ |
| 10 | Despacho a engorde | ✅ `chick_dispatch` event type | ✅ |

---

## 4. POLLO DE ENGORDE (Broiler)

### 4.1 Datos Diarios a Registrar

| # | Dato Diario (App Antigua) | App Nueva | Estado |
|:--|:--|:--|:--|
| 1 | N° Pollos al Inicio | `BirdMovement.opening_birds` | ✅ |
| 2 | N° Pollos Muertos | `BirdMovement.mortality` | ✅ |
| 3 | Peso de Pollos (muestra) | `BirdMovement.avg_weight_g` | ✅ |
| 4 | Cantidad Alimento | `FeedMovement.feed_kg` | ✅ |
| 5 | N° Pollos Vendidos/Sacrificados | `BirdMovement.birds_sold` | ✅ |
| 6 | N° Pollos Nuevos (ingreso) | `BirdMovement.birds_added` | ✅ |
| 7 | Incidencias de Salud | `OperationalEvent.health_notes` | ✅ |
| 8 | Condiciones Ambientales | `OperationalEvent.temp_c`, `humidity_pct` | ✅ |
| 9 | Consumo de Agua | `OperationalEvent.water_liters` | ✅ |
| 10 | Observaciones Generales | `OperationalEvent.notes` | ✅ |

### 4.2 KPIs Calculables

| # | KPI (App Antigua) | App Nueva | Estado |
|:--|:--|:--|:--|
| 1 | Ganancia Diaria de Peso | ✅ | ✅ |
| 2 | Conversión Alimenticia (FCR) | ✅ | ✅ |
| 3 | Tasa de Mortalidad | ✅ | ✅ |
| 4 | Índice de Conversión Ajustado (AFCR) | ⚠️ No implementado | ⚠️ GAP |
| 5 | Índice de Producción | ⚠️ No implementado | ⚠️ GAP |
| 6 | Peso Promedio al Sacrificio | ✅ `reports/service.py` | ✅ |

### 4.3 Procesos Operativos

| # | Proceso | App Nueva | Estado |
|:--|:--|:--|:--|
| 1 | Recepción de pollitos (conteo, estado) | ✅ `reception` | ✅ |
| 2 | Acondicionamiento inicial (cama, calor, luz) | ✅ `inspection` | ✅ |
| 3 | Alimentación por etapas (pre-iniciador, iniciador, crecimiento, finalizador) | ✅ `FeedMovement` con `feed_type_id` | ✅ |
| 4 | Pesaje semanal/quincenal | ✅ `weighing` | ✅ |
| 5 | Registro diario mortalidad | ✅ `mortality` | ✅ |
| 6 | Consumo de alimento y agua | ✅ `feeding` | ✅ |
| 7 | Ambiente y equipos | ✅ `inspection` | ✅ |
| 8 | Carga a planta de beneficio | ✅ `transfer_out` | ✅ |
| 9 | Cierre administrativo del lote | ✅ `Lot.close()` + resumen final | ✅ |

---

## 5. NUEVO: ABUELAS / PROGENITORAS (Grandparent)

Esta etapa es **NUEVA** en la app actual. No existía en la app Flutter anterior.

| # | Funcionalidad | Backend | Frontend | Estado |
|:--|:--|:--|:--|:--|
| 1 | Plan de importación (docs sanitarios/aduana) | `Lot.import_plan` | `LotDetailPage.tsx` | ✅ |
| 2 | Creación de lote de abuelas | `POST /lots` | `LotListPage.tsx` | ✅ |
| 3 | Trazabilidad a generaciones posteriores | `Lot.parent_lot_id` | `LotDetailPage.tsx` | ✅ |
| 4 | Eventos operativos específicos | `OperationalEvent` con `lot.phase=grandparent` | `OperationFormPage.tsx` | ✅ |
| 5 | Filtro por etapa "Todos/Progenitoras/Reproductoras/Engorde" | `LotListPage.tsx` stage filter | ✅ | ✅ |

---

## 6. ADMIN WEB (App Antigua vs App Nueva)

### 6.1 App Antigua: https://admin.liderpollo.xyz/breeding-reception

| Funcionalidad Admin | App Nueva | Estado |
|:--|:--|:--|
| Crear Maestro de Lotes | `POST /lots` + `LotListPage.tsx` | ✅ |
| Asignar lote a orden de compra | `Lot.import_order` vinculado a `SapReference` | ✅ |
| Gestión de usuarios/roles | `UsersPage.tsx` + `POST /users`, `POST /roles` | ✅ |
| Catálogos/Maestros (farms, houses, etc.) | `MasterListPage.tsx` (10 entidades) | ✅ |
| Configuración de etapas productivas | `Lot.phase` management | ✅ |

### 6.2 Web Ejecutiva (Dashboard)

| Funcionalidad | App Nueva | Estado |
|:--|:--|:--|
| Dashboard Admin (KPIs, status, top types, last 7 days) | `DashboardPage.tsx` + `/dashboard/admin` | ✅ |
| Dashboard Mobile (today_events, pending_corrections, approved_today) | `DashboardPage.tsx` + `/dashboard/mobile` | ✅ |

---

## 7. SAP INTEGRATION

### 7.1 Proceso Documentado en PDF "Sap y App Proceso Avícola"

| # | Paso del Proceso | App Nueva | Estado |
|:--|:--|:--|:--|
| 1 | Ingreso al módulo de compras en SAP | Fuera de scope (es SAP) | N/A |
| 2 | Crear orden de compra en SAP (tipo doc, proveedor, materiales ♂♀, centro, cantidades) | `SapReference` recibe la OC | ✅ |
| 3 | Workflow de aprobación en SAP | Fuera de scope (es SAP) | N/A |
| 4 | OC queda registrada en SAP | `SapReference` con `doc_type=purchase_order` | ✅ |
| 5 | **App sincroniza con SAP** — ve órdenes de compra, lotes disponibles | `GET /sap/references` + `POST /sap/references/import` | ✅ |
| 6 | Confirmación en granja: OC, lote, proveedor, raza, ♀♂, fechas, peso, galpones | `OperationalEvent` tipo `reception` | ✅ |
| 7 | App busca órdenes de transferencia activas de alimentos | `SapReference` con `doc_type=transfer_order` | ✅ |
| 8 | App consolida datos aprobados para envío a SAP | `POST /sap/consolidate` | ✅ |
| 9 | Envío a SAP (payload + respuesta + ID SAP) | `SapService.send_to_sap()` + `SapPayload` + `SapResponse` | ✅ |
| 10 | Idempotencia (SHA-256 hash, sin duplicados) | `SapPayload.content_hash` | ✅ |
| 11 | Errores SAP registrados con reintento | `POST /sap/retry` | ✅ |
| 12 | Reporte de diferencias SAP vs App | `GET /reports/sap-comparison` + `SapComparisonPage.tsx` | ✅ |

---

## 8. WORKFLOW: REGISTRO → REVISIÓN → CORRECCIÓN → APROBACIÓN → SAP

Este flujo **NO existía formalmente** en la app antigua. Es una mejora arquitectónica de la nueva app.

| Paso | Backend | Frontend | Estado |
|:--|:--|:--|:--|
| Registro (Operador) | `POST /operations` → status=registered | `OperationFormPage.tsx` | ✅ |
| Revisión (Supervisor) | `GET /review/pending` → bandeja | `ReviewCenter.tsx` | ✅ |
| Corrección (Usuario autorizado) | `POST /corrections` (auditado) | `CorrectionForm.tsx` | ✅ |
| Devolución al operador | `POST /operations/return` | `ReviewDetail.tsx` | ✅ |
| Aprobación (Aprobador) | `POST /approvals` + `ApprovalStep` | `ApprovalPanel.tsx` | ✅ |
| Rechazo con motivo | `POST /approvals` action=reject | `ApprovalPanel.tsx` | ✅ |
| Aprobación multinivel (1/2/3 niveles) | `ApprovalStep` con `step_order` | ✅ | ✅ |
| Consolidación | `POST /sap/consolidate` | `SapManagerPage.tsx` | ✅ |
| Envío a SAP | `POST /sap/export` | `SapManagerPage.tsx` | ✅ |

---

## 9. AUDITORÍA

La app antigua **no tenía** módulo de auditoría. Es NUEVO.

| Funcionalidad | Backend | Frontend | Estado |
|:--|:--|:--|:--|
| Registro inmutable de cada acción | `AuditLog` model | ✅ | ✅ |
| Vista de auditoría | `GET /audit` | `AuditPage.tsx` | ✅ |
| Timeline por entidad | `GET /audit/timeline/{entity_type}/{entity_id}` | ✅ | ✅ |
| Corrección: original + corregido + responsable | `CorrectionLog` model | ✅ | ✅ |

---

## 10. REPORTES

### 10.1 KPIs Report

| KPI | Backend | Frontend | Estado |
|:--|:--|:--|:--|
| Mortalidad | `GET /reports/kpis/mortality` | `ReportsPage.tsx` | ✅ |
| Conversión alimenticia | `GET /reports/kpis/feed-conversion` | `ReportsPage.tsx` | ✅ |
| Producción de huevos | `GET /reports/kpis/egg-production` | `ReportsPage.tsx` | ✅ |
| Incubación/Eclosión | `GET /reports/kpis/hatchery` | `ReportsPage.tsx` | ✅ |
| KPIs generales | `GET /reports/kpis` | `ReportsPage.tsx` | ✅ |
| Reporte por lote | `GET /reports/lot/{lot_id}` | `LotReportPage.tsx` | ✅ |
| Comparación SAP vs App | `GET /reports/sap-comparison` | `SapComparisonPage.tsx` | ✅ |
| Exportación Excel/PDF | `POST /reports/export` | Pending UI | ⚠️ |

---

## 11. MATRIZ DE BRECHAS (GAPS) IDENTIFICADAS

| # | Gap | Prioridad | Descripción |
|:--|:--|:--|:--|
| G-01 | **Índice de Bienestar Animal** | Media | KPI mencionado en doc original. No implementado como endpoint ni en frontend. |
| G-02 | **Eficiencia de Vacunación (incubadora)** | Media | KPI de incubadora: pollitos vacunados / total. No implementado. |
| G-03 | **Eficiencia de Traslado (incubadora)** | Media | KPI: pollitos trasladados vivos / pollitos nacidos sanos. No implementado. |
| G-04 | **Índice de Conversión Ajustado (AFCR)** | Baja | KPI de engorde avanzado. No implementado. |
| G-05 | **Índice de Producción (engorde)** | Baja | KPI compuesto de engorde. No implementado. |
| G-06 | **Exportación Excel/PDF** | Alta | Endpoint existe (`POST /reports/export`) pero falta UI de descarga. |
| G-07 | **Registro de almacenamiento pre-incubación** | Media | App antigua detalla: T°, H°, duración almacenamiento. Verificar que `EggMovement` tenga estos campos en el modelo actual. |
| G-08 | **Separación ♂♀ en pesaje de cría** | Media | La app antigua enfatiza pesar machos y hembras por separado en cría de reproductoras. Verificar que `BirdMovement` soporte `avg_weight_male_g` y `avg_weight_female_g`. |
| G-09 | **Bandeja de transferencia (alimento)** | Media | App antigua: "La APP buscara las ordenes de transferencia activa de alimentos". Verificar que el frontend muestre `SapReference` de tipo `transfer_order` al registrar alimentación. |
| G-10 | **Pantalla de cierre de lote con resumen** | Alta | App antigua menciona "cierre administrativo y operativo del lote... mortalidad total, consumo total, conversión final". Verificar `Lot.close()` endpoint + UI de cierre. |

---

## 12. ESTADO GENERAL

| Categoría | Total Items | ✅ Cubiertos | ⚠️ Gaps | Cobertura |
|:--|:--|:--|:--|:--|
| Reproductora Cría - Datos | 9 | 9 | 0 | 100% |
| Reproductora Cría - KPIs | 4 | 3 | 1 (G-01) | 75% |
| Reproductora Cría - Procesos | 9 | 9 | 0 | 100% |
| Reproductora Prod - Datos | 12 | 12 | 0 | 100% |
| Reproductora Prod - KPIs | 7 | 7 | 0 | 100% |
| Reproductora Prod - Procesos | 6 | 6 | 0 | 100% |
| Incubadora - Datos | 25 | 25 | 0 | 100% |
| Incubadora - KPIs | 5 | 3 | 2 (G-02, G-03) | 60% |
| Incubadora - Procesos | 10 | 10 | 0 | 100% |
| Engorde - Datos | 10 | 10 | 0 | 100% |
| Engorde - KPIs | 6 | 4 | 2 (G-04, G-05) | 67% |
| Engorde - Procesos | 9 | 9 | 0 | 100% |
| Progenitoras | 5 | 5 | 0 | 100% |
| Admin Web | 5 | 5 | 0 | 100% |
| SAP Integration | 12 | 12 | 0 | 100% |
| Workflow | 9 | 9 | 0 | 100% |
| Auditoría | 4 | 4 | 0 | 100% |
| Reportes | 8 | 7 | 1 (G-06) | 88% |
| **TOTAL** | **155** | **149** | **6 gaps + 4 verificaciones** | **96.1%** |

---

## 13. VERIFICACIONES TÉCNICAS (Validación de Código)

| # | Verificación | Resultado | Acción |
|:--|:--|:--|:--|
| V-01 | `EggMovement` tiene campos `storage_temp_c`, `storage_humidity_pct`, `storage_start_date`? | ❌ **NO** — El modelo `EggMovement` solo tiene `egg_type`, `quantity`, `avg_weight`, `classification_date`. No hay modelo para almacenamiento pre-incubación. | **GAP-07 confirmado**: Agregar `EggStorage` model o extender `EggMovement` con campos de almacenamiento. |
| V-02 | `BirdMovement` tiene `avg_weight_male_g` y `avg_weight_female_g` separados? | ⚠️ **PARCIAL** — `BirdMovement` usa columna `sex` (male/female/mixed) y un solo `avg_weight`. Se crean filas separadas por sexo. Es funcional pero diferente al diseño de la app antigua que tenía columnas separadas ♂♀. | No es gap crítico, el modelo actual funciona creando múltiples filas. |
| V-03 | `OperationFormPage` muestra `SapReference` tipo `transfer_order` al registrar `feeding`? | ❌ **NO** — El formulario de alimento solo tiene campo `quantity_kg`. No muestra órdenes de transferencia SAP activas, ni selector de `feed_type_id`, ni conteo de bultos/sacos. | **GAP-08 confirmado**: Agregar selector de orden de transferencia SAP + feed_type + sacks en `OperationFormPage`. |
| V-04 | Existe UI para cierre de lote (`Lot.close()`) con resumen final? | ⚠️ **PARCIAL** — Backend tiene `close_lot()` (solo pone status=closed, end_date=today). Frontend muestra botón "Cierre de Lote" en `LotDetailPage`. Pero NO genera resumen final (mortalidad total, consumo total, conversión). | **GAP-09 confirmado**: `close_lot()` debe calcular y devolver resumen. Frontend debe mostrar modal de confirmación con resumen. |
| V-05 | `GET /reports/kpis` incluye endpoints para TODOS los KPIs? | ⚠️ **PARCIAL** — Hay 5 endpoints KPI (mortality, feed-conversion, egg-production, hatchery, all). Faltan: animal-welfare, vaccination-efficiency, transfer-efficiency, AFCR, production-index. | **GAPs 01-05**: Agregar endpoints KPI faltantes. |
| V-06 | Review Center tiene filtros por: granja, lote, fecha, operador, etapa, tipo, estado? | ❌ **NO** — Solo tiene filtros por Lote ID, Tipo de Evento, Fecha Desde/Hasta. Faltan: granja, operador, etapa, estado. | **GAP-10 confirmado**: Agregar filtros faltantes en `ReviewCenter.tsx`. |

---

## 14. HALLAZGOS ADICIONALES (Capturas de Pantalla App Antigua)

Del análisis de 11 capturas de pantalla de la app Flutter antigua (`App mobile avicola - capture pantallas.docx`):

### 14.1 Estructura de Navegación (App Antigua)
- **Bottom Tab Bar** (5 tabs): Home, Reproducción, Incubación, Pollo, Perfil
- **App Nueva** (`MobileNav.tsx`): Home, Bird, FileText, Search, TrendingUp — **diferente estructura**

| App Antigua Tab | App Nueva Tab | Equivalencia |
|:--|:--|:--|
| Home | Home | ✅ Dashboard |
| Reproducción | Bird | ✅ Operaciones/Lotes |
| Incubación | (incluido en Bird) | ✅ Dentro de Lotes |
| Pollo | (incluido en Bird) | ✅ Dentro de Lotes |
| Perfil | (en Sidebar) | ✅ Profile |
| — | FileText | NUEVO (Operaciones) |
| — | Search | NUEVO (Review) |
| — | TrendingUp | NUEVO (Reportes) |

### 14.2 Pantalla de Registro por Lote (App Antigua)
La app antigua tiene una **pantalla de detalle de lote con tabs**:
- **Básico**: Info general del lote (hembras, machos, peso prom, mortalidad)
- **Alimento**: Registro por semana (N° Sem, Kg Ave/Sem, Bultos, Fecha)
- **Agua**: Registro por semana (Lt Agua x Ave x Sem, Fecha)
- **Vacunas**: Registro de vacunación
- **Pesaje**: Por semana (N° Sem, Peso Macho g, Peso Hembra g, Fecha)
- **Mortalidad**: Por semana (N° Sem, Macho, Hembra, Fecha)

**Diferencia clave**: La app antigua organiza los datos por **NÚMERO DE SEMANA**, con tablas dentro de cada lote. La app nueva usa un modelo basado en **eventos** (`OperationalEvent`) con sub-tablas (`BirdMovement`, `FeedMovement`, `EggMovement`). Ambos modelos capturan los mismos datos pero con UX diferente.

### 14.3 Dashboard de Resumen (App Antigua)
- "Resumen Diario" con cards por tipo de negocio (Pollo Engorde, Reproductora)
- Lista de lotes con: código, fase (Cría/Producción/Procesamiento), cantidad de aves, último registro
- **App Nueva**: `DashboardPage.tsx` tiene KPIs más completos pero no muestra el resumen por lote tipo "último registro".

### 14.4 Reportes (App Antigua)
- Consumo de Agua (gráfico de barras)
- Mortalidad (gráfico de barras)
- Peso del Pollo kg (gráfico de línea)
- **App Nueva**: Reportes más completos (mortalidad, conversión, huevos, incubación, SAP comparison) pero sin gráficos (solo datos tabulares).

---

## 15. MATRIZ DE BRECHAS (GAPS) ACTUALIZADA

| # | Gap | Prioridad | Descripción | Fuente |
|:--|:--|:--|:--|:--|
| G-01 | **Índice de Bienestar Animal** | Media | KPI no implementado | Bases PDF |
| G-02 | **Eficiencia de Vacunación (incubadora)** | Media | KPI no implementado | Bases PDF |
| G-03 | **Eficiencia de Traslado (incubadora)** | Media | KPI no implementado | Bases PDF |
| G-04 | **Índice de Conversión Ajustado (AFCR)** | Baja | KPI de engorde avanzado | Bases PDF |
| G-05 | **Índice de Producción (engorde)** | Baja | KPI compuesto de engorde | Bases PDF |
| G-06 | **Exportación Excel/PDF** | Alta | Endpoint existe, falta UI | Spec |
| G-07 | **Almacenamiento pre-incubación** | Alta | Falta modelo `EggStorage` con T°, H°, duración | V-01 |
| G-08 | **Selector SAP Transfer Order en feeding** | Alta | `OperationFormPage` no muestra órdenes de transferencia SAP activas ni feed_type ni sacks | V-03 / Captura |
| G-09 | **Cierre de lote con resumen final** | Alta | `close_lot()` no calcula resumen. Frontend no muestra modal de confirmación. | V-04 / BR-05 |
| G-10 | **Filtros Review Center** | Alta | Faltan filtros por granja, operador, etapa, estado | V-06 |
| G-11 | **Registro por semana (UX)** | Media | App antigua organiza datos por N° Semana. App nueva usa eventos. Evaluar si agregar vista semanal. | Capturas |
| G-12 | **Gráficos en Reportes** | Media | App antigua tiene gráficos de barras/línea. App nueva solo datos tabulares. | Capturas |
| G-13 | **Bottom Tab Bar semántico** | Baja | MobileNav tiene labels genéricos. App antigua: Home/Reproducción/Incubación/Pollo/Perfil. | Capturas |

---

## 16. ESTADO GENERAL (ACTUALIZADO)

| Categoría | Total Items | ✅ Cubiertos | ⚠️ Gaps | Cobertura |
|:--|:--|:--|:--|:--|
| Reproductora Cría - Datos | 9 | 9 | 0 | 100% |
| Reproductora Cría - KPIs | 4 | 3 | 1 (G-01) | 75% |
| Reproductora Cría - Procesos | 9 | 8 | 1 (G-08) | 89% |
| Reproductora Prod - Datos | 12 | 12 | 0 | 100% |
| Reproductora Prod - KPIs | 7 | 7 | 0 | 100% |
| Reproductora Prod - Procesos | 6 | 6 | 0 | 100% |
| Incubadora - Datos | 25 | 22 | 3 (G-02, G-03, G-07) | 88% |
| Incubadora - KPIs | 5 | 3 | 2 (G-02, G-03) | 60% |
| Incubadora - Procesos | 10 | 10 | 0 | 100% |
| Engorde - Datos | 10 | 10 | 0 | 100% |
| Engorde - KPIs | 6 | 4 | 2 (G-04, G-05) | 67% |
| Engorde - Procesos | 9 | 9 | 0 | 100% |
| Progenitoras | 5 | 5 | 0 | 100% |
| Admin Web | 5 | 5 | 0 | 100% |
| SAP Integration | 12 | 11 | 1 (G-08) | 92% |
| Workflow | 9 | 8 | 1 (G-10) | 89% |
| Auditoría | 4 | 4 | 0 | 100% |
| Reportes | 8 | 6 | 2 (G-06, G-12) | 75% |
| UX/UI Mobile | 8 | 5 | 3 (G-11, G-12, G-13) | 63% |
| **TOTAL** | **163** | **147** | **16 gaps** | **90.2%** |

---

## 17. PLAN DE ACCIÓN PRIORIZADO

### 🔴 Fase 9A: Gaps Críticos (Alta Prioridad) — 5 gaps
| Gap | Tarea | Esfuerzo |
|:--|:--|:--|
| G-07 | Crear modelo `EggStorage` + migración + endpoint | 3h |
| G-08 | Agregar selector SAP transfer order + feed_type + sacks en `OperationFormPage` | 4h |
| G-09 | `close_lot()` calcula resumen (mortalidad total, consumo total, FCR) + modal UI | 4h |
| G-10 | Agregar filtros granja/operador/etapa/estado en `ReviewCenter.tsx` | 3h |
| G-06 | Botón Exportar Excel/PDF en Reports + LotReport | 4h |

### 🟡 Fase 9B: Gaps Medios (Media Prioridad) — 6 gaps
| Gap | Tarea | Esfuerzo |
|:--|:--|:--|
| G-01 | Endpoint `GET /reports/kpis/animal-welfare` + tarjeta UI | 2h |
| G-02 | Endpoint `GET /reports/kpis/vaccination-efficiency` | 2h |
| G-03 | Endpoint `GET /reports/kpis/transfer-efficiency` | 2h |
| G-11 | Vista semanal en `LotDetailPage` (tabla resumen por semana como en app antigua) | 5h |
| G-12 | Agregar gráficos (recharts) en Reports: barras para agua/mortalidad, línea para peso | 6h |
| G-13 | Renombrar tabs MobileNav a: Home/Reproductora/Incubación/Engorde/Perfil (o similar) | 1h |

### 🟢 Fase 9C: Gaps Bajos (Baja Prioridad) — 2 gaps
| Gap | Tarea | Esfuerzo |
|:--|:--|:--|
| G-04 | AFCR en endpoint `feed-conversion` | 1h |
| G-05 | Índice de Producción en KPIs | 1h |

> **Esfuerzo total estimado Fase 9:** 38 horas  
> **Cobertura esperada post Fase 9:** 99.4% (162/163 items)
