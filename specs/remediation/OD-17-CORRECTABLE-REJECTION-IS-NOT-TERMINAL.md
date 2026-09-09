# `OD-17` · UN RECHAZO CORREGIBLE NO ES TERMINAL

Decisión de propietario · resuelve `AOD-09` (`H360-P03`, `H360-D09`) · 2026-09-09 · **VIGENTE**
Alias: **`AOD-09 → OD-17`** (el artefacto de auditoría conserva su numeración).

```
RECHAZAR UN REGISTRO CORREGIBLE   ≠   TERMINARLO
```

---

## 1. El conflicto que resuelve

`docs/12 §4` fila 8: «Rechazado → Operador reenvía (corregido)». El código: `REJECTED` no es
editable (`operations/service.py:893`), no es corregible (`corrections/service.py:34`) y no es
reenviable (`:910`); y `RETURNED` es editable pero **no reenviable** por el operador (solo sale
por `corrections` → `CORRECTED`). `spec.md §4.10` callaba. Dos niveles discrepaban y el nivel 4
no se pronunciaba: `REQUIREMENT_CONFLICT` → decisión del propietario.

## 2. `OD-17.a` · la decisión

**Un rechazo corregible no es terminal.** Se distinguen tres clases de estado que hoy el
vocabulario mezcla:

| Clase | Estados | Naturaleza |
|---|---|---|
| **Devolución interna** (observado, rechazado por revisión administrativa) | `RETURNED`, `REJECTED` | el registro sigue vivo: se corrige y vuelve a revisión |
| **Rechazo futuro por SAP** | `SAP_ERROR` (hoy sin productor) | el registro aprobado no fue aceptado por el mandante: se corrige o reprocesa y se **reenvía explícitamente** |
| **Terminal** | `CANCELLED`, reverso (`BR-16`), cierre final del lote | no vuelve al flujo; solo por reverso o nuevo movimiento autorizado |

## 3. `OD-17.b` · el ciclo interno

```
REGISTERED → (submit) → PENDING_REVIEW → IN_REVIEW
                                          ├─ return  → RETURNED  → correct → CORRECTED → (review) → APPROVED
                                          └─ reject  → REJECTED  → correct → CORRECTED → (review) → APPROVED
```

- `RETURNED` y `REJECTED` admiten **corrección auditada** (`RR-01`: valor original conservado) y **reenvío**; quién reenvía (el operador que registró, o quien tenga `corrections:correct`) lo fija la spec que lo implemente, sin inventar permisos ni nombres de rol.
- El motivo del rechazo sigue siendo obligatorio (`docs/12 R3`); el reenvío conserva la historia (`audit_logs`, `correction_logs`).
- Segregación: quien rechazó no aprueba el reenvío si la configuración lo exige (`RC-03`, `docs/12 R2`).

## 4. `OD-17.c` · el ciclo futuro con SAP

```
APPROVED → CONSOLIDATED → SENT_TO_SAP → SAP_CONFIRMED            (final)
                                     └→ SAP_ERROR → correct / reprocess → REENVÍO EXPLÍCITO
```

- **Ningún reenvío automático.** Un error de SAP exige acto humano autorizado (`sap:send_sap`), auditado y con `external_transaction_id` nuevo o reprocesado según la regla de idempotencia (`BR-12`, Recomendación §19).
- Nada de esto se construye ahora (`GA-REM-017 BLOCKED_EXTERNAL`); se declara para que el vocabulario de estados no vuelva a cerrarse.

## 5. Lo que esta decisión **no** hace

- **No implementa `H360-P03`.** La spec, los AC y el código llegan en `WAVE B`.
- No añade estados nuevos ni renombra los existentes; `REPROCESADO` (Recomendación §18) queda para la spec de `WAVE B`/`D`.
- No cambia `CANCELLED` ni el reverso (`H360-P04`, `H360-P05`).

## 6. Trazabilidad

| Fuente | Relación |
|---|---|
| `docs/12 §4` fila 8, `§6 R2-R4` | se ratifica |
| Recomendación central §18 (`OBSERVADO → CORREGIDO → APROBADO`; `RECHAZADO_POR_SAP → REPROCESADO`) | se ratifica |
| `spec.md §4.10` | pendiente de enmienda en `WAVE B` |
| `OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX.md §1-§2` | evidencia del conflicto |
