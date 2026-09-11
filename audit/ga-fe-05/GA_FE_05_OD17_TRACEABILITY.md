# GA-FE-05 · TRAZABILIDAD OD-17

Fuente: `OD-17` (decisión del propietario, citada por `REMEDIATION_BACKLOG.md`, `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md` y `R135_R143_STATE_CORRECTION_MATRIX.md`) + `docs/12-approval-workflow.md §2/§4` + `spec §4.10` + implementación backend vigente.

| Cláusula | Texto/semántica canónica | Implementación backend (verificada) | Decisión UI GA-FE-05 |
|---|---|---|---|
| `OD-17.a` | `REJECTED` **no es terminal**: se actualiza, se reenvía y se corrige | `REENVIABLES` incluye `rejected`; `EDITABLES` no lo excluye; `NO_CANCELABLES` no lo incluye | CTA «Reenviar a revisión» visible en `rejected` |
| `OD-17.b` | `RETURNED` se **reenvía** por el mismo acto explícito (`POST /operations/{id}/submit`); quien rechazó no aprueba el reenvío si la configuración lo exige (`R-143`) | `submit_to_review` acepta `returned` y `rejected` → `pending_review`; segregación interna (no UI) | CTA «Reenviar a revisión» visible en `returned`; sin lógica de segregación en UI (backend decide) |
| `OD-17.c` | Ciclo SAP diferido (`consolidate→…→sap_confirmed`), sin cambios | Estados SAP presentes en el enum; no tocados | Ninguna acción nueva SAP (fuera de alcance) |
| `docs/12 §2` | «Devuelto → Operador reenvía» · «Rechazado → Operador reenvía (corregido)» | Igual que arriba | Wording ES/EN: «Reenviar a revisión» / “Resubmit for review” |
| `spec §4.10` | Envío explícito a revisión desde `registered` | `submit_to_review` acepta `registered` | CTA «Enviar a revisión» / “Submit for review” |
| `R-135` | Cerró el backend de la máquina de estados (no es trabajo pendiente) | Confirmado en código | Nada del backend se modifica |

## Matriz de decisión UI ↔ ciclo de vida (citas obligatorias)

| Estado | Transición submit | ¿Permitida? | Cita | Decisión UI |
|---|---|---|---|---|
| `draft` | submit | NO | `REENVIABLES` (código) | Sin CTA |
| `registered` | submit → `pending_review` | SÍ | `docs/12 §2` · `spec §4.10` | CTA «Enviar a revisión» |
| `pending_review` | submit | NO | `REENVIABLES` | Sin CTA |
| `in_review` | submit | NO | `REENVIABLES` | Sin CTA |
| `returned` | resubmit → `pending_review` | SÍ | `OD-17.b` · `docs/12 §2` | CTA «Reenviar a revisión» |
| `corrected` | submit | NO (espera aprobador) | `REENVIABLES` | Sin CTA |
| `approved` | resubmit | NO (terminal de ciclo) | `OD-17.a` (terminales) | Sin CTA |
| `rejected` | resubmit → `pending_review` | SÍ | `OD-17.a` (no terminal) | CTA «Reenviar a revisión» |
| `consolidated`/`sent_to_sap`/`sap_confirmed`/`sap_error`/`cancelled`/`reversed` | submit | NO | `OD-17.a/c` | Sin CTA |

**Invariante**: ninguna decisión de UI introduce transiciones nuevas; la tabla anterior es un reflejo 1:1 de `REENVIABLES` + `OD-17`. La autoridad final permanece en el backend (400/403 verificables).
