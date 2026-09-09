# AUDITORÍA DE PREPARACIÓN PARA LA INTEGRACIÓN SAP

**Auditoría 360°** · 2026-09-09 · base `7310adb` · **AUDIT ONLY** · **no se conecta SAP**

Marco: Recomendación central §3 (módulos), §14 (activaciones), §15/§16 (qué consume y envía),
§19 (id externo), §22 (matriz final), §23 (arquitectura), §25 (5 decisiones) ·
`docs/10-sap-integration-strategy.md` · `spec.md §4.3, §14` · `OD-12` · `GA-REM-010` (estados) ·
`GA-REM-017` (`BLOCKED_EXTERNAL`) · `P-08` (`PARTIAL`, **no tocado**).

---

## 1. Arquitectura y modos — comprobado

| Requisito | Evidencia | Estado |
|---|---|---|
| React → Backend → Integration Layer → SAP; nunca React → SAP ni App → tablas HANA (Rec. §23) | el frontend solo llama `/api/v1/*`; el backend no tiene driver ni URL de HANA; `SapIntegrationAdapter` es la única frontera (`adapter.py:51`) | ✓ |
| Adaptador seleccionable | `SAP_ADAPTER` ∈ {`manual`, `mock`}; `real` → `NO IMPLEMENTADO (GA-REM-017)` (`config.py:125-131`, `service.py:39-56`) | ✓ honesto |
| Rutas SAP tras bandera | `FEATURE_SAP_ENABLED` monta el router (`main.py:146,165`); `.env` local `true` | ✓ |
| Estados honestos | manual/mock **no** producen `sent_to_sap`; payload queda `PREPARED` (`GA-REM-010 AC01-AC06`) | ✓ |
| `connection-check` | `ManualSapAdapter.check_connection() → False` | ✓ |
| Artefacto manual persistente | `SAP_EXPORT_DIR` dentro del volumen `avicola-media` (`GA-REM-009/010`) | ✓ |

## 2. Outbox, idempotencia y errores

| Elemento | Implementación | Fuente | Estado | ID |
|---|---|---|---|---|
| Consolidación | `POST /sap/consolidate`: `APPROVED` → agrupa por `(lot_id, event_type)` → `consolidated_movements(total_quantity, unit, sap_reference=primer sap_document_ref)` → evento `CONSOLIDATED` (`service.py:151-231`) | `docs/12 §10` | ✓ agrupación; **la «validación de integridad» de `docs/12 §10.3` (totales cuadran, referencias existen, sin huérfanos) no existe** | `H360-S10` P2 |
| Outbox | `sap_payloads` con `status`, `retry_count`, `next_retry_at`, `error_message`; **disparo manual** (`POST /sap/export`, `POST /sap/retry`); sin worker/cron | `spec §4.3` bitácora | patrón outbox **pasivo** — aceptable en modo manual; insuficiente para real | `H360-S11` P2 (WAVE D) |
| Idempotencia del payload | `idempotency_key` SHA-256 único; se omite si ya `CONFIRMED` (`:284-290`) | `docs/10 §5`, `BR-12` | ✓ |
| Idempotencia del evento | `operational_events.idempotency_key` **opcional**, generado por el cliente (`schemas.py:106`); el frontend móvil no lo envía (`grep idempotency frontend/src` → 0) | Rec. §17 «duplicidad de envío» | reenvíos móviles duplican registros → `H360-S12` P2 |
| Id externo (Rec. §19) | `external_transaction_id = AVICOLA-{EVENT_TYPE}-{idem[:16]}`, `source_system=APP_AVICOLA` (`:337-341`) **solo tras éxito**; `sap_reference_item` nunca se puebla | Rec. §19 exige el id **antes** del envío (es lo que evita el duplicado en reproceso) | `PARCIAL` → `H360-S13` P2 |
| Reintentos | `retry_failed`: `max_retries=3`, respeta `next_retry_at`; **backoff fijo 1 min** (`:373`), sin progresión 1/5/15 | `docs/10 §6.2` | **`DEFECTO`** → `H360-S07` P2 |
| Estados de error | `PayloadStatus.FAILED/RETRYING`, `SapSyncJob.FAILED`, notificación `sap_send_failed` (`GA-REM-038`) | `docs/10 §6` | ✓ |
| Confirmación entrante (SAP → app) | **no existe** endpoint ni job que lea respuesta asíncrona; `SAP_CONFIRMED`/`SAP_ERROR`/`REPROCESADO` no tienen productor | Rec. §18, §26 «recibir documento SAP generado» | ✗ → `H360-S09` P1 (WAVE D) |
| Conciliación | `GET /reports/sap-comparison` no lee SAP | Rec. §24, §26 | ✗ G-R10 |

## 3. Qué lleva hoy el payload frente a lo que SAP necesita (Rec. §16, §22)

`SapExportPayload` (`sap/schemas.py:60-75`): `lot_id, event_type, period_start/end,
total_quantity, unit, sap_reference, idempotency_key`. **No lleva**: material SAP, centro,
almacén, objeto de costo (centro de costo / orden interna / lote productivo SAP), tipo de
movimiento, posición de documento, detalle por galpón/sexo, referencia de evidencia.

| Proceso (Rec. §22) | SAP debe recibir | ¿El payload lo permite? | Bloqueo |
|---|---|---|---|
| Compra/recepción de aves | entrada contra OC por cantidad real + resumen operativo + diferencias | cantidad y OC sí; material, centro, almacén, diferencias, lote SAP **no** | `H360-S02`, `S05`, `S08` |
| Distribución por galpón | objeto custom / referencia operativa | detalle por galpón no viaja | `AOD-02` |
| Consumo de alimento | documento de material contra lote/costo | material y objeto de costo **no** | `H360-S01`, `S08` |
| Recepción de transferencia | confirmación de traslado | OT no validada ni referenciada de forma tipada (`H360-S04`) | — |
| Mortalidad | evento productivo o baja | depende de `AOD-04` (`RC-07`) | decisión |
| Vacuna / medicina | consumo sanitario + evento | material sanitario **no** | `H360-S01` |
| Producción de huevos | entrada/producción/indicador según diseño | material huevo fértil **no** | `H360-S02` |
| Incubadora | producción de pollitos / merma | ídem | `H360-S02` |
| Engorde (salida, cierre) | transferencia/salida/cierre y costos | sin documento de cierre ni objeto de costo | `AOD-08` |
| Inspección crítica | notificación PM/QM o alerta custom | alertas existen; sin envío | `AOD-05` |

→ **`H360-S08` · P1 (WAVE D)**: el payload es un **resumen contable de cantidades**, no un
evento mapeable a un documento SAP; el mapeo por proceso (Rec. §24: mandante, documento origen,
documento destino, API, reverso, conciliación, evidencia, responsable) **no existe para ninguno
de los 10 procesos**.

## 4. Las cinco decisiones (Rec. §25) — estado

| # | Decisión | Dónde consta | Estado |
|---|---|---|---|
| 1 | ave viva = inventario valorizado o población productiva | nadie | **PENDIENTE** → `AOD-01` |
| 2 | galpón = almacén, ubicación técnica o dimensión operativa | nadie | **PENDIENTE** → `AOD-02` |
| 3 | lote productivo = batch, orden interna, orden de producción o custom | nadie; `lots` sin clave SAP (`H360-S05`) | **PENDIENTE** → `AOD-03` |
| 4 | mortalidad = movimiento de inventario o indicador/costo | `RC-07_BUSINESS_DECISION_DOSSIER.md` · `REQUIREMENT_CONFLICT_RESOLUTION RC-07` | **PENDIENTE** (`OWNER_DECISION_REQUIRED` desde Wave 1.5) → `AOD-04` |
| 5 | bioseguridad = SAP QM/custom o app + resumen | nadie | **PENDIENTE** → `AOD-05` |

Sin ellas «la integración puede funcionar técnicamente, pero quedará débil para costeo,
trazabilidad y auditoría» (Rec. §25). Son **previas** a `WAVE D`, no a `WAVE A–C`.

## 5. Datos que la app debe consumir de SAP (Rec. §15) — cobertura del espejo

| Dato | `SapReferenceType` | ¿Algún flujo lo usa? |
|---|---|---|
| OC | `PURCHASE_ORDER` (+`quantity`) | sí: `BR-18` |
| OT | `TRANSFER_ORDER` | **no** (solo listado) |
| Materiales | `MATERIAL` | **no** |
| Proveedores | `VENDOR` | **no** (los eventos usan `suppliers`) |
| Centros | `PLANT` | **no** |
| Almacenes | `STORAGE_LOCATION` | **no** |
| Centros de costo | `COST_CENTER` | **no** |
| Lotes/batch | `SAP_BATCH` | **no** |
| Granjas, galpones, capacidad, equipos, silos, inventario, lotes productivos, períodos, usuarios | sin tipo | — |

El espejo existe para 8 tipos y **solo uno se consume**. Importar sin consumir es inventario
muerto: no rompe nada, pero no acerca a `WAVE G`.

## 6. Pruebas

| Aspecto | Evidencia | Estado | ID |
|---|---|---|---|
| Suite local | `.env` `FEATURE_SAP_ENABLED=true` → `test_sap.py` (9) y `test_sap_transversal.py` se ejecutan; regresión de hoy 784 passed / 49 skipped (los 49 son `test_upgrade_path` y `test_runtime_startup`, que exigen `upgrade_test.sh` / `runtime_test.sh`) | ✓ |
| CI | `.github/workflows/backend-ci.yml:40-45` no define `FEATURE_SAP_ENABLED` → por defecto `False` → los 9 tests de `test_sap.py` **se saltan en CI** y el router SAP no se monta | **defecto de validez** | `H360-T01` P2 |
| Adaptador real | sin test posible (`BLOCKED_EXTERNAL`) | — | — |
| Reintento con backoff | test existente cubre `retry` pero no la progresión (no hay progresión que cubrir) | — | `H360-S07` |

## 7. Seguridad de la integración

- Credenciales SAP: no hay variables `SAP_URL/SAP_USER/...` en `config.py`; `Company.sap_config`
  (`String`, `R-127`) es el único lugar previsto y hoy no es escribible por API sin error. Cuando
  llegue `GA-REM-017` habrá que decidir **dónde** viven (por empresa vs entorno) → `AOD-12`.
- Roles técnicos y *communication arrangements* (Rec. §14, §23): n/a hasta SAP real.
- Permisos: `sap:read` / `sap:send_sap`; transversalidad acotada por `OD-12` ✓.

## 8. Veredicto de preparación

```
SAP_INTEGRATION_READINESS = NOT READY

  arquitectura y honestidad de estados ........ LISTO       (GA-REM-010, adaptador, flags)
  outbox / idempotencia / errores ............. PARCIAL     (S07 backoff · S09 sin confirmación entrante · S11 sin worker · S13 id externo tardío)
  identidad de maestros hacia SAP ............. NO LISTO    (S01 materiales · S05 lote · R-124 granja/empresa · S08 payload)
  decisiones de negocio (Rec. §25) ............ 0 de 5
  validez de pruebas en CI .................... DEFECTO     (T01)
  entrega real ................................ BLOCKED_EXTERNAL (GA-REM-017 · P-08, no tocado)
```

Nada de lo anterior contradice `GA-REM-010`: la app **no simula** integración y eso es
correcto. Lo que falta es lo que la Recomendación llama «matriz formal por proceso» (§24), y esa
matriz depende de `AOD-01…05`.
