# SAP-HANA-CLOUD · 06_RAW_STAGING_MAPPING

Fecha: 2026-10-06 · SPEC 005 · Evoluciona `audit/sap0/SAP_RAW_STAGING_SPEC.md` y `audit/sap-soap/10_…` sin romperlos · Modelo físico en `specs/005-…/data-model.md`

---

## 1 · Flujo obligatorio

```text
HANA (SELECT) → RAW → VALIDATION → MAPPING → STAGING → CONTROLLED PROMOTION → sap_references
```

**Nunca** `HANA → DOMAIN`. El conector no conoce tablas del producto; la única escritura hacia algo que el dominio lee es el upsert de `sap_references` en `inbound/promotion.py`.

## 2 · RAW (`sap_inbound_records`)

Una fila del origen = una fila RAW, con `payload_json` (la respuesta normalizada a JSON), `payload_hash` (SHA-256 del JSON canónico), `source_key`, `version` e `is_current`.

| Regla | Implementación |
|---|---|
| Inmutable | el payload de una versión no se modifica; un cambio entra como versión nueva |
| Idempotente | misma clave + mismo hash = no-op (ni fila ni `UPDATE`) |
| Sin duplicados | índice único parcial `(company_id, source_system, object_type, source_key) WHERE is_current` |
| Sin secretos | solo datos de negocio de SAP |
| Aislado | `company_id` = empresa en cuyo contexto se extrajo; `client`, `company_code`, `plant_code` desnormalizados |

## 3 · VALIDATION (`inbound/staging.py`)

| Comprobación | Resultado si falla |
|---|---|
| Columna obligatoria ausente en la respuesta | el job falla con `SAP_SCHEMA_MISMATCH`; no se rellena con `NULL` |
| Campo obligatorio sin valor en una fila | la fila queda `INVALID` con `SAP_VALIDATION_ERROR`, visible en `/errors` |
| Fecha que no es `AAAAMMDD` | `INVALID` |
| Cantidad no numérica o negativa | `INVALID` |
| `SHKZG` fuera de `S`/`H` | `INVALID` |

Una fila inválida no se descarta ni se repara: queda a la vista hasta que el origen la corrija (nueva versión).

## 4 · MAPPING (`inbound/mapping.py`)

```text
SAP SYSTEM → MANDT → BUKRS → WERKS → GA COMPANY
```

| Resultado | Condición | Efecto |
|---|---|---|
| `MAPPED` | la sociedad y **todos** los centros que la fila referencia son de la empresa efectiva | continúa |
| `PENDING_MAPPING` | falta resolver la sociedad o algún centro | se retiene con `SAP_MAPPING_PENDING`; sin promoción |
| ajena | la sociedad pertenece a **otra** empresa GA | la fila no se persiste (`rows_rejected`) |

Sin fallback transversal, sin «primera empresa», sin atajo para la autoridad global. El mapping se re-evalúa en cada pasada: añadir un centro libera sus filas aunque el hash no haya cambiado.

`sap_entity_mappings` es único por `(sistema, mandante, tipo, clave)`: una sociedad o un centro pertenece a una sola empresa.

| Tipo | Clave | Quién lo declara |
|---|---|---|
| `COMPANY_CODE` | `BUKRS` | autoridad global situada en la empresa |
| `PLANT` | `WERKS` (padre: `BUKRS` de la misma empresa) | `sap:send_sap` |
| `STORAGE_LOCATION` | `WERKS/LGORT` (padre: `WERKS`) | `sap:send_sap` |

### OD-24

- `Company ↔ BUKRS` y `Plant ↔ Farm`: el vínculo con una granja (`farm_id`) existe solo si alguien lo declara en el mapping.
- `LGORT ≠ galpón`: `house_id` solo por mapping expreso de `STORAGE_LOCATION`.
- Ningún maestro local se crea, modifica ni borra. La convergencia de maestros sigue fuera de alcance.
- `business_unit_code` es informativo: no habilita unidades ni concede acceso (OD-16.c).

## 5 · STAGING

Capa lógica sobre el mismo registro: `staged_json` (DTO de negocio tipado, ver `05_OBJECT_FIELD_MAPPING.md`) más los estados.

| Estado | Valores |
|---|---|
| `validation_status` | `PENDING` · `VALID` · `INVALID` |
| `mapping_status` | `PENDING` · `MAPPED` · `PENDING_MAPPING` |
| `promotion_status` | `PENDING` · `READY_FOR_PROMOTION` · `PROMOTED` · `STAGED_ONLY` · `BLOCKED` · `SUPERSEDED` |

## 6 · PROMOTION

| Objeto | Regla |
|---|---|
| `plant`, `storage_location`, `vendor`, `material`, `batch` | upsert fila a fila por `(empresa, tipo, código)` |
| `purchase_order` | se compone con sus posiciones e historial; ver §7 |
| `transfer_order` | se compone por documento; se retiene entera si alguna posición activa no está mapeada |
| `company`, `movement_type`, `purchase_order_history`, `production_order`, `outbound_order`, `material_movement` | `STAGED_ONLY`: no tienen tipo de referencia y **no** se guardan como `OTHER` |

Referencia previa duplicada con la misma clave ⇒ `BLOCKED`: no se elige una ni se sobrescribe. Una referencia manual única con la misma clave se adopta (se actualiza en sitio).

## 7 · Órdenes de compra y BR-18

`validate_oc_limit` no cambia. Compara lo recibido en GA contra `SapReference.quantity`, así que la promoción solo afirma una cantidad cuando puede sostenerla:

| Situación | Resultado |
|---|---|
| posiciones activas con la misma unidad | `quantity` = Σ `MENGE`; `unit` = esa unidad |
| posición borrada (`LOEKZ`) | excluida de la suma; conservada en `items[]` con `deleted: true` |
| unidades distintas | `BLOCKED` · `SAP_VALIDATION_ERROR` (una OC sin cantidad dejaría BR-18 inaplicable) |
| posición activa en un centro sin mapping | `BLOCKED` · `SAP_MAPPING_PENDING` |
| sin posiciones todavía | `READY_FOR_PROMOTION` (espera) |
| cabecera anulada o todas las posiciones borradas | referencia inactiva, `status: CANCELLED`; el total histórico se conserva |

`received_quantity` = entradas (`VGABE=1`, `S`) − reversos (`VGABE=1`, `H`) del historial: es informativo y sirve a la reconciliación. El límite de BR-18 sigue siendo lo ordenado.

## 8 · Reversos

| Objeto | Campos conservados |
|---|---|
| `material_movement` | `reversal_flag`, `original_document`, `reversal_reference` (`SMBLN/SJAHR/SMBLP`), `debit_credit` |
| `purchase_order_history` | `debit_credit`, `reversal`, `reference_document` (`LFBNR`), `movement_type` |
| `purchase_order`, `transfer_order` | `deleted`, `status` (`CANCELLED`), `delivery_completed` |
| `production_order` | `status` (`DELETED`/`CLOSED`/`COMPLETED`/`RELEASED`/`CREATED`) |

## 9 · Auditoría

Cada job guarda petición, actor (nulo si es el scheduler), empresa, objeto, `query_id`, filtros saneados, ventana, contadores y error. Además se escribe un `audit_log` (`IMPORT` · `sap_inbound_sync`) por petición y uno (`CONFIG_CHANGE` · `sap_entity_mapping`) por cambio de mapping.
