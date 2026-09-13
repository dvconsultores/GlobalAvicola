# GA-CLAUDE · PREPARACIÓN DE EVENTOS FUENTE PARA SAP (§55)

Auditoría independiente Claude · 2026-09-13 · HEAD `c0b4afc` · Runtime `avicola.globaldv.net`. **No se conecta SAP** (P-08 `BLOCKED_EXTERNAL`, §56): esta matriz evalúa si los **eventos de origen locales** son fiables y completos para iniciar la integración. Fuentes: `integrations/sap/{models.py,service.py,adapter.py}`, informes `D_security_tx.md`/`E_domain_ledger.md`, decisión `OD-12`, `GA-REM-017`.

## 0 · Arquitectura de la frontera (vigente)

`Frontend → FastAPI → (Integration Layer) → SAP` vía consolidación + payloads; nunca Frontend→SAP ni HANA directo. Entidades internas: `SapReference` (réplica OC/STO con `sap_code`, `quantity`, `unit`), `ConsolidatedMovement` (agrupa `event_ids` de eventos `approved` por lote/tipo/periodo; `total_quantity`, `unit`, `sap_reference`), `SapPayload` (`idempotency_key` SHA-256, `external_transaction_id` (G-R03), `source_system` default `APP_AVICOLA`, `sap_reference_item`, `payload_data`, estados `PREPARED/SENDING/CONFIRMED/FAILED/RETRYING`, `retry_count/max_retries/next_retry_at`, `sap_document_id`, `error_message`), `SapResponse` (confirmación entrante), `SapSyncJob`.

Contrato de retry: backoff 1/5/15 min (`service.py:344-373`); adaptador `manual`/`mock` **no** marca `SENT_TO_SAP`; `retry_failed` → `SAP_CONFIRMED` saltando `SENT_TO_SAP` y sin auditoría (E-25); `SAP_ERROR` sin productor; consolidación sin bloqueo (dup. concurrente P3, GAP-14).

## 1 · Matriz de eventos candidatos

Convención: **Ref** = documento SAP asociado; **Idem** = idempotencia interna; **Payload** = mapeabilidad del `payload_data`; **READY / PARTIAL / UNDEFINED / BLOCKED_EXTERNAL** según §55.

| # | Proceso | Evento (local) | Disparador | Estado aprobado | Registros fuente | Empresa | BU | Ref | `external_transaction_id` | `source_system` | `event_type` | Idem | Payload | Auditoría | Reverso | Retry/Fallo | **Readiness** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | P-01 | `grandparent_import` | UI asistente | `approved` (P-07) | evento + `extra_data.import_plan` + `bird_movements` + OC (`sap_document_ref` código ✔ F-01) | ✔ | grandparent | OC compra | post-éxito (R-145) | ✔ default | ✔ | payload SHA-256 (solo export) | ~ (P1-12) | no elegible (OD-19) | backoff; `failed` sin UI (R-217) | **PARTIAL** (mapping AOD-01 pendiente) |
| 2 | P-01/P-03/P-06 | `bird_reception` | UI asistente | `approved` | evento + `bird_movements` + cuadre (BR-20) + OC | ✔ | gp/breeder/broiler | OC | post-éxito | ✔ | ✔ | SHA-256 | ~ | **elegible** (R-193 neto pendiente) | backoff | **PARTIAL** (BR-18 tras reverso R-193; ref. correcta ✔) |
| 3 | P-04/P-05 | `egg_dispatch` | UI asistente | `approved` | evento + `egg_movements[fertile]` + STO + `EggBatch` | ✔ | breeder/gp → hatchery | STO | post-éxito | ✔ | ✔ | SHA-256 | ~ | no elegible (huevos) | backoff | **PARTIAL** (R-172 semántica; refs OK; incertidumbres UI R-194 aguas arriba) |
| 4 | P-05 | `egg_reception_hatchery` | UI (rota: R-194) | `approved` | evento + almacenamiento + fértiles (tras R-194) | ✔ | hatchery | STO | post-éxito | ✔ | ✔ | SHA-256 | ~ | no elegible | backoff | **UNDEFINED** (no registrable por UI hoy) |
| 5 | P-05 | `birth_registration` | UI (bloqueo silencioso: R-194) | `approved` | evento + `chicks_healthy/weak` + líneas | ✔ | hatchery | — | post-éxito | ✔ | ✔ | SHA-256 | ~ | no elegible | backoff | **UNDEFINED** (flujo roto; decisión AOD-23 pendiente) |
| 6 | P-05 | `chick_dispatch` | UI (400: R-194) | `approved` | evento + `ChickBatch` + destino | ✔ | hatchery → breeder/broiler | — / STO | post-éxito | ✔ | ✔ | SHA-256 | ~ | no elegible | backoff | **UNDEFINED** |
| 7 | P-06 | `feed_registration` | UI asistente | `approved` | evento + `feed_movements` + OT | ✔ | broiler/breeder | OT (`sap_order_id`) | post-éxito | ✔ | ✔ | SHA-256 | ~ | no elegible (alimento) | backoff | **PARTIAL** (ref. por **id** hoy: R-209; OT no validada: R-145) |
| 8 | P-06 | `bird_exit` | UI asistente | `approved` | evento + movimientos + planta/destino | ✔ | broiler/… | OC salida | post-éxito | ✔ | ✔ | SHA-256 | ~ | elegible | backoff | **PARTIAL** (ref. por **id** hoy: R-209) |
| 9 | P-06 | `lot_closure`/`POST /close` | UI detalle lote | estado lote `closed` (no evento) | `close_lot` resumen (sin filtro de estado: R-192) | ✔ | broiler/… | — | n/a | n/a | n/a | n/a | sin payload propio (resumen) | ✘ sin auditar (E-10) | — | — | **UNDEFINED** (semántica de cierre AOD-08) |
| 10 | P-07/OD-19 | reverso (par `reversed`) | UI (R-207) | `reversed` ×2 | original + contrapartida | ✔ | según origen | copia del original | n/a | n/a | `reversed` | n/a | ajuste post-SAP diferido (`R-136`) | ~ | — | — | **BLOCKED_EXTERNAL** (regla post-SAP diferida) |
| 11 | transversal | mortalidad/descarte/agua/peso/vacuna | UI asistente | `approved` | evento + movimientos | ✔ | por lote | — | post-éxito | ✔ | ✔ | SHA-256 | ~ | elegibles algunos | backoff | **PARTIAL** (¿eventos fuente SAP? decisión AOD-01/05 pendiente) |

## 2 · Brechas que condicionan la integración (ya con paquete)

| Brecha | Impacto en la frontera | Spec |
|---|---|---|
| R-201 | Autoridad global sin contexto lee/reintenta payloads de todas las empresas (fail-open) | `specs/R-201/` |
| R-209 | Referencias SAP por **id interno** en salida de aves y alimento (`payload_data` y evento) | `specs/R-209/` |
| R-193 | Acumulado BR-18 tras reverso (2n) | `specs/R-193/` |
| R-192 | Cierre de lote imposible tras reverso efectivo | `specs/R-192/` |
| P1-12 | Transiciones SAP (`CONSOLIDATED`/`SENT_TO_SAP`/`SAP_CONFIRMED`) sin auditoría única | `specs/P1-12-REOPEN/` |
| R-217 | Panel SAP con estados inexistentes, sin retry/refetch | `specs/R-217/` |
| R-112 | 8/9 rutas `/sap/*` sin `response_model` | registro/`GA-REM-011` |
| GAP-14 | Doble consumo del `Result` en re-enlace idempotente; consolidación concurrente duplicable | `D_security_tx.md` (P3; fase SAP) |
| R-157/AOD-01…05 | Payload no mapeable a documento SAP (material, centro, almacén, objeto de costo, tipo de movimiento) | `GA-REM-017` (fase SAP) |
| R-145 | Backoff fijo 1 min en cola real, outbox pasivo, `external_transaction_id` solo post-éxito | `GA-REM-010` |

## 3 · Veredicto §55

```
Eventos candidatos evaluados ....... 11
READY ..............................  0
PARTIAL ............................  5  (importación, recepción aves, despacho huevo, alimento, salida)
UNDEFINED ..........................  5  (recepción incubadora, nacimiento, despacho pollitos, cierre, KPI-varios)
BLOCKED_EXTERNAL ...................  1  (post-SAP: reverso consolidado)
```

**Lectura**: la **infraestructura interna** de la frontera (consolidación → payload → idempotencia → retry) está construida y probada por API, pero (a) los eventos de incubadora no pueden registrarse por UI (R-194), (b) hay referencias contaminadas (R-209/R-193), (c) falta el **mapeo SAP** (material/centro/almacén/tipo de movimiento) que pertenece a la fase siguiente (§54) y (d) la gobernanza de pruebas no permite certificar. Conclusión: **«SAP source events sufficiently defined» no se cumple todavía**; la preparación es **insuficiente para GO**, suficiente para iniciar **discovery de contratos** tras cerrar la cola local (§69.B considerada pero no aplicable: la app local aún no está certificada).
