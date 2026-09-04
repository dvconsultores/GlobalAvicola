# 06 — MAPA DE PROCESOS DE NEGOCIO

Procesos reconstruidos **exclusivamente** desde `docs/02-functional-spec.md`, `specs/global-avicola/spec.md §4`, `frontend/src/data/processCatalog.ts` (`STAGE_FLOWS`) y el código. No se inventan procesos.

Clasificación: `CUBIERTO` (E2E completo) · `PARCIAL` · `MANUAL` (existe pero fuera del sistema) · `NO IMPLEMENTADO` · `NO DOCUMENTADO`.

---

## 1. Procesos identificados: 15

| ID | Proceso | Origen | Cobertura |
|---|---|---|---|
| P-01 | Progenitoras (Abuelas) — Cría | spec §4.4 / `STAGE_FLOWS.grandparent_rearing` | PARCIAL |
| P-02 | Progenitoras — Producción de huevo | spec §4.4 / `STAGE_FLOWS.grandparent_production` | PARCIAL |
| P-03 | Reproductoras — Cría | spec §4.5 | PARCIAL |
| P-04 | Reproductoras — Producción de huevo fértil | spec §4.6 | PARCIAL |
| P-05 | Incubación | spec §4.7 | PARCIAL |
| P-06 | Pollo de engorde | spec §4.8 | PARCIAL |
| P-07 | Revisión → Corrección → Aprobación | spec §4.10 / docs/12 | PARCIAL |
| P-08 | Consolidación y envío a SAP | spec §4.3/§4.10 / docs/10 | PARCIAL |
| P-09 | Auditoría interna | spec §4.11 / docs/13 | PARCIAL |
| P-10 | Trazabilidad generacional entre lotes | spec §4.9 (2ª) | PARCIAL |
| P-11 | Activación manual de lotes / saldos iniciales | spec §4.9 / func §3.9 | **MANUAL** |
| P-12 | Gestión de datos maestros | func §3.2 | PARCIAL |
| P-13 | Gestión de usuarios, roles y permisos | func §3.1 | PARCIAL |
| P-14 | Notificaciones y alertas | func §3.14 | **NO IMPLEMENTADO** |
| P-15 | Reportes y KPIs | spec §4.12 | PARCIAL |
| — | Registro contable/administrativo en SAP | fuera de alcance (SAP es el sistema principal) | **MANUAL** (por diseño) |

```
Procesos identificados ...........  15
Procesos 100 % cubiertos .........   0
Procesos parciales ...............  12
Procesos manuales ................   2   (P-11 y el posting real en SAP)
Procesos no implementados ........   1   (P-14)
```

---

## 2. Sección obligatoria (§27): procesos 100 % cubiertos

# NINGUNO

No existe ningún proceso de negocio que satisfaga la cadena completa `Entrada → ejecución → persistencia → salida → estado final` sin un defecto confirmado en alguno de sus pasos. La lista es deliberadamente vacía: incluir procesos parciales aquí falsearía el resultado.

**Procesos más cercanos a completarse** (y qué falta exactamente en cada uno):

| Proceso | Pasos correctos | Paso que lo bloquea |
|---|---|---|
| **P-07 Revisión → Aprobación** | 8 de 10 | El paso *Corrección* no aplica el valor corregido al evento (`corrections/service.py:52`); la segregación BR-14 se puede eludir por `POST /review/complete` |
| **P-06 Engorde** | 10 de 11 | `mortality_recording` devuelve 500 (`operations/service.py:242`); el cierre de lote vive en `LotDetailPage`, que está rota |
| **P-08 Consolidación → SAP** | 5 de 6 | El último paso escribe un JSON en `/tmp` y marca `sent_to_sap` con un id ficticio; no hay SAP real |
| **P-05 Incubación** | 7 de 8 | El eslabón de trazabilidad (`egg_reception_hatchery` → `EggBatch`) crea vínculos auto-referenciales |

---

## 3. Detalle por proceso

### P-01 · Progenitoras — Cría

```
INICIO
  ↓ grandparent_import        registrar importación (OC SAP, proveedor, docs)
  ↓ farm_inspection           inspeccionar granja antes de recibir
  ↓ bird_reception            recepcionar aves (multi-galpón, ±10 % vs OC)
  ↓ bird_distribution         distribuir a galpones
  ↓ ── ciclo diario/semanal ──────────────────────────
  │   feed_registration · weight_recording
  │   mortality_recording · cull_recording
  │   vaccination · medication
  ↓ bird_exit                 traslado a fase producción
FIN
```

| Paso | Módulo | Pantalla | API | BE | DB | Cobertura | Spec | Gap |
|---|---|---|---|---|---|---|---|---|
| grandparent_import | operations | OperationFormPage | `POST /operations` | OperationsService | operational_events | PARCIAL | spec §4.4 | la OC SAP se guarda en `extra_data.sap_order_ref`, no en `sap_document_ref` → BR-11/BR-18 inertes |
| farm_inspection | operations | OperationFormPage | idem | idem | inspection_details | CUBIERTO | §4.4 | — |
| bird_reception | operations | OperationFormPage | idem | + `validate_house_capacity`, `validate_oc_limit` | bird_movements | PARCIAL | §4.4 | `validate_oc_limit` nunca se dispara (sin `sap_document_ref`) |
| bird_distribution | operations | OperationFormPage | idem | idem | bird_movements | CUBIERTO | §4.4 | — |
| feed_registration | operations | OperationFormPage | idem | idem | feed_movements | CUBIERTO | §4.4 | — |
| weight_recording | operations | OperationFormPage | idem | idem | bird_movements | CUBIERTO | §4.4 | sin alerta de peso fuera de curva (spec §4.5) |
| **mortality_recording** | operations | OperationFormPage | idem | `validate_mortality` + generador de alertas | bird_movements | **ROTO** | §4.4, BR-01 | `NameError` → HTTP 500 |
| cull_recording | operations | OperationFormPage | idem | idem | bird_movements | CUBIERTO | §4.4 | — |
| vaccination / medication | operations | OperationFormPage | idem | idem | operational_events | CUBIERTO | §4.4 | — |
| bird_exit | operations | OperationFormPage | idem | idem | bird_movements | CUBIERTO | §4.4 | — |
| *(spec)* egg_collection / egg_classification / egg_dispatch en GRANDPARENT | — | — | — | — | — | **NO IMPLEMENTADO en esta etapa** | §4.4 | el frontend los movió a `grandparent_production` |

**Cobertura P-01: 8 de 11 pasos correctos → PARCIAL.**

### P-02 · Progenitoras — Producción / P-04 · Reproductoras — Producción

Flujo idéntico salvo el destino del huevo.

```
farm_inspection → feed_registration → weight_recording → vaccination → medication
   → mortality_recording (ROTO) → cull_recording
   → egg_collection  (recolectar + clasificar: tipo, cantidad, peso)
   → egg_dispatch    (OC de transferencia SAP, incubadora destino, inspección de transporte)
   → bird_exit
```

| Gap | Detalle |
|---|---|
| `mortality_recording` roto | igual que P-01 |
| `egg_classification` | la spec lo exige como paso propio (§4.4/§4.6); se fusionó en `egg_collection` (`f379b7e`) sin actualizar la spec |
| `egg_dispatch` → EggBatch | la creación automática del lote de huevos busca la recepción **en el mismo `lot_id`**, lo que produce vínculos lote→sí mismo o ningún vínculo |
| KPI `% postura`, fertilidad | implementados (`/reports/kpis/egg-production`) pero solo cuentan eventos ya aprobados |

**Cobertura: 8 de 10 pasos → PARCIAL.**

### P-03 · Reproductoras — Cría

Idéntico a P-01 sin `grandparent_import`. Mismo bloqueo por `mortality_recording`. La transición Cría→Producción (`POST /lots/{id}/phases`) está implementada en backend y su UI vive en `LotDetailPage`, **rota**. **PARCIAL.**

### P-05 · Incubación

```
hatchery_inspection (por máquina, sin lote)
  → egg_reception_hatchery      recepción de huevo fértil (OC transferencia SAP)
  → egg_reception_classification  clasificar aptos / no aptos     ← SIN SPEC
  → incubation_load             carga a incubadora (temp/hum/CO2/volteo)   [BR-03 ✔]
  → ovoscopy                    infértiles, embriones muertos
  → transfer_to_hatcher         traslado a nacedora (día 18)
  → birth_registration          nacimiento + vacunación in ovo   [alimenta saldo de pollitos]
  → chick_dispatch              despacho a engorde               [BR-04 ✔]
```

| Gap | Detalle |
|---|---|
| `egg_reception_classification` | tipo de evento **sin ninguna spec** |
| Trazabilidad EggBatch/ChickBatch | auto-creación con lógica auto-referencial → no enlaza generaciones |
| KPI `% eclosión`, `% nacimiento` | implementados (`/reports/kpis/hatchery`) |
| Inspección sin lote | `i9j0k1l2m3n4` hizo `lot_id` nullable para permitirlo — cambio de esquema **sin spec** |

**Cobertura: 7 de 8 pasos → PARCIAL.**

### P-06 · Pollo de engorde

Igual que P-03 más `lot_closure`. BR-05 exige al menos un pesaje y un registro de alimento antes de cerrar — implementado (`validate_lot_closure`). El botón de cierre está en `LotDetailPage` (**rota**) y también existe `lot_closure` como tipo de evento.
**Cobertura: 10 de 11 pasos → PARCIAL.**

### P-07 · Revisión → Corrección → Aprobación

```
Operador registra                      status = registered
  ↓ POST /operations/{id}/submit       status = pending_review
  ↓ POST /review/batches   (opcional)  status = pending_review + ReviewBatch
  ↓ POST /review/start/{id}            status = in_review
  ↓ ¿correcto?
  ├── NO → POST /review/return         status = returned        → vuelve al operador ✔
  ├── CORREGIR → POST /corrections     status = corrected  ⚠ EL VALOR NO SE APLICA
  └── SÍ → POST /review/complete
            ├── approval_levels ≤ 1 → status = approved   ⚠ SIN VALIDAR BR-14
            └── approval_levels > 1 → status = corrected
                  ↓ POST /approvals/approve   [BR-14 ✔] → approved
                  ↓ POST /approvals/reject    (motivo obligatorio ✔) → rejected
FIN
```

| Gap | Severidad | Evidencia |
|---|---|---|
| La corrección no modifica el evento | **P0** | `backend/app/corrections/service.py:37-58` — crea `CorrectionLog`, cambia estado, nunca hace `setattr` sobre el campo |
| BR-14 eludible | **P0** | `review/service.py:196-234` `complete_review()` aprueba sin `validate_segregation` |
| Multinivel no secuencia | P1 | `ApprovalStep` nunca se consulta; solo se distingue 1 vs >1 nivel |
| Filtros de la bandeja ignorados | P1 | `ReviewCenter` envía `status` y `operator_id`; `GET /review/pending` no los acepta |
| Detalle de revisión roto | P0 | `ReviewDetail` pide `/operations?limit=200` → 422 |
| Formulario de corrección roto | P0 | `CorrectionForm` pide `/operations?limit=200` → 422 |

**Cobertura: 8 de 10 pasos → PARCIAL** (el proceso mejor construido del sistema, bloqueado por dos defectos puntuales).

### P-08 · Consolidación y envío a SAP

```
POST /sap/consolidate   agrupa eventos approved → consolidated_movements, status = consolidated ✔
  ↓ POST /sap/export
      genera idempotency_key SHA-256 (lot|type|fecha|ref|event_ids) ✔
      comprueba SapPayload CONFIRMED previo (idempotencia) ✔
      crea SapPayload SENDING ✔
      adapter.export_consolidated()  → ManualSapAdapter  ⚠ escribe /tmp/sap_exports/<key>.json
      crea SapResponse ✔
      marca eventos status = sent_to_sap y sap_document_ref = "MANUAL-xxxxxxxx" ⚠
  ↓ POST /sap/retry   reintento con backoff  ⚠ backoff (minuto+1)%60 puede producir fecha pasada
FIN
```

| Gap | Severidad | Evidencia |
|---|---|---|
| No existe `RealSapAdapter` | **P0** | `sap/service.py:34-38` `# TODO: read from config/env which adapter to use`; T-085 pendiente |
| El archivo generado es efímero | **P0** | `/tmp` en contenedor sin volumen |
| Marca `sent_to_sap` sin confirmación real | **P0** | BR-15 bloquea después la edición de registros que nunca llegaron a SAP |
| `FEATURE_SAP_ENABLED=true` en producción | **P0** | `docker-compose.yml:28`, commit `bfccdfb` |
| Import de referencias SAP sin UI de carga | P2 | `SapManagerPage` lista referencias pero no ofrece importación de CSV/JSON |
| Comparativo SAP vs App siempre vacío | P1 | filtra por `sap_document_ref != NULL`, que solo se puebla tras exportar |

**Cobertura: 5 de 6 pasos internos → PARCIAL. El proceso de negocio real (dato en SAP) sigue siendo MANUAL.**

### P-09 · Auditoría interna

| Elemento | Estado | Evidencia |
|---|---|---|
| Registro automático de creación de evento | ✔ **duplicado** | listener `after_flush` + `audit_event_created()` en el servicio |
| Transiciones de estado | ✔ duplicado | `_audit_event_modified` + `audit_state_transition()` |
| Correcciones | ✔ duplicado | `_audit_correction` + `audit_correction()` |
| Acciones de aprobación | ✔ duplicado | `_audit_approval_action` + `ApprovalAction` |
| Login / logout / login fallido | ✘ **no se registra** | `AuditAction.LOGIN/LOGOUT/LOGIN_FAILED` definidos y nunca usados |
| Cambios de maestros y lotes | ✘ | los listeners solo observan `OperationalEvent`, `CorrectionLog`, `ApprovalAction` |
| Cambios de permisos | ✘ | `AuditAction.PERMISSION_CHANGE` definido y nunca usado |
| Import / export SAP | ✘ | `AuditAction.IMPORT/EXPORT` definidos y nunca usados |
| Inmutabilidad | ✔ | no hay UPDATE/DELETE sobre `audit_logs` |
| Visor + timeline | ⚠ | `AuditPage` envía `search`, `action_contains`, `group_by`: **ninguno existe en el backend** |

**Cobertura: PARCIAL con doble registro.** 6 de las 21 acciones del enum `AuditAction` se escriben.

### P-10 · Trazabilidad generacional

```
Reproductoras Producción --egg_dispatch--> [EggBatch] --egg_reception_hatchery--> Incubadora
Incubadora --chick_dispatch--> [ChickBatch] --bird_reception--> Engorde
```

**ROTO en el modo automático.** `_auto_create_traceability_batches` busca el evento complementario **con el mismo `lot_id`**:

- `EGG_DISPATCH` busca `EGG_RECEPTION_HATCHERY` con `lot_id == data.lot_id`, y luego asigna `hatchery_lot_id = reception.lot_id` — es decir, **el mismo lote**.
- `CHICK_DISPATCH` busca `BIRD_RECEPTION` con el mismo `lot_id` y asigna `destination_lot_id = reception.lot_id` — otra vez el mismo lote.

En operación normal el despacho se registra en el lote origen y la recepción en el lote destino, que son distintos: la coincidencia **nunca ocurre** y no se crea ningún lote de trazabilidad; si por accidente coincidieran, se crearía un vínculo del lote consigo mismo.
Evidencia: `backend/app/operations/service.py:127-176` y `:190-228`.

El **enlace manual sí funciona**: `POST /lots/egg-batches` y `POST /lots/chick-batches` desde `TraceabilityTree.tsx:86,105`. El árbol se muestra en `LotDetailPage`, que está rota.

**Cobertura: PARCIAL (solo manual, en pantalla inaccesible).**

### P-11 · Activación manual de lotes / saldos iniciales

Endpoint `POST /lots/activate-manual` implementado con 22 columnas en `opening_balances`. **No existe ninguna pantalla ni ruta que lo invoque**; `lots.service.ts:55` lo declara pero el servicio está muerto.
**Clasificación: MANUAL** — hoy solo puede ejecutarse llamando la API directamente o por SQL. Es un requisito de implantación crítico (migrar lotes en curso).

### P-12 · Gestión de datos maestros

19 catálogos en backend, **12** con pantalla. Sin pantalla: `incubators`, `hatchers`, `productive-phases`, `medications`, `cull-causes`, `rejection-reasons`, `correction-types` (7).
De las 12 con pantalla, **8 no pueden editarse**: el backend solo registró `PUT` para `companies`, `farms`, `houses` y `hatcheries`; `MasterListPage` emite `PUT` para todas → **405 Method Not Allowed** en suppliers, genetic-lines, breeds, feed-types, vaccines, mortality-causes, transports y processing-plants.
Además el contador de resultados es incorrecto: `setTotal(response.data.length)` usa el tamaño de la página porque el endpoint devuelve una lista plana sin total.
**PARCIAL.**

### P-13 · Gestión de usuarios, roles y permisos

- Usuarios: pantalla **rota** (`limit=200` → 422 aborta el `Promise.all`).
- Roles: 3 endpoints, **sin pantalla**.
- Permisos: modelo completo, **sin pantalla y sin enforcement**.
**PARCIAL / mayoritariamente inoperante.**

### P-14 · Notificaciones y alertas

| Tipo exigido (`docs/02 §3.14`) | Estado |
|---|---|
| Registro pendiente de revisión > 24 h | **NO IMPLEMENTADO** |
| Registro rechazado → notificar al operador | **NO IMPLEMENTADO** |
| Mortalidad > umbral configurable | implementado con umbral **fijo** 3 % / 8 % en código, y el generador **falla con 500** |
| Peso fuera de estándar | **NO IMPLEMENTADO** |
| Error de envío SAP | **NO IMPLEMENTADO** (hay estado en BD, sin notificación) |
| Lote próximo a cierre | **NO IMPLEMENTADO** |

Sí existen dos alertas ambientales no especificadas: temperatura y humedad fuera de rango en `farm_inspection`.
**NO IMPLEMENTADO** como proceso. No hay canal de notificación (email/push/Telegram) en ninguna parte del código.

### P-15 · Reportes y KPIs

14 endpoints de KPI. 4 huérfanos (`animal-welfare`, `production-index`, `transfer-efficiency`, `vaccination-efficiency`). Todos los cálculos filtran por `status IN (approved, consolidated, sent_to_sap, sap_confirmed)` — correcto conceptualmente, pero implica que **los KPIs son cero hasta que se aprueban los registros**, sin que la UI lo explique.
`ReportsPage` selecciona el lote escribiendo su **ID numérico** en un `<input type=number>` con valor por defecto **2** codificado. Las gráficas fallan (`limit=200` → 422). `SapComparisonPage` siempre vacío.
**PARCIAL.**
