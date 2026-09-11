# GA-FE-05 · MATRIZ DE FIXTURES DE OPERACIÓN

Todos los estados se producen **por flujo oficial** (API de producto con actores sintéticos autorizados; la UI se usa en los E2E). Sin SQL crudo.

| Fixture | Estado objetivo | Cómo se produce | Actor | Datos | Uso E2E | Estado final |
|---|---|---|---|---|---|---|
| `OP-DRAFT` | `registered` | `POST /operations` (nace `registered`) sobre lote productivo del actor C | C | event_type `weight_recording`, fecha del día, lote `L-BO-2026-05` (o lote broiler vigente) | E2E-01, E2E-09, E2E-10 | tras submit ⇒ `pending_review` (evidencia) |
| `OP-RETURNED` | `returned` | `OP-PENDING-A` ⇒ `POST /review/start` ⇒ `POST /review/return` con motivo (≥10) por V | C + V | mismo lote | E2E-06, E2E-07 | tras resubmit ⇒ `pending_review` (evidencia) |
| `OP-PENDING` | `pending_review` | `POST /operations` + `POST /submit` (actor C) | C | mismo lote | E2E-05 (estado no reenviable) | se conserva como evidencia (no se aprueba) |
| `OP-APPROVED` | `approved` | `OP-PENDING-B` ⇒ start ⇒ complete (V) ⇒ approve (V con `approvals:approve`) | C + V | mismo lote | E2E-08 (inmutable) | se conserva como evidencia |
| `OP-CROSS` | (cross-company) | operation existente de Empresa 3 si hay; si no, se documenta ausencia y el caso se cubre con candidato externo | — | — | E2E negativo cross | — |

Reglas:
- Un fixture por caso, sin reutilizar el mismo evento entre casos mutantes (evita interferencia).
- Los eventos de fixtura quedan en estados finales legítimos (`pending_review`/`approved`) — no se borran estados aprobados (auditoría append-only); se documentan en el ledger como evidencia retenida.
- El lote usado pertenece a la Empresa 1 (segura) y a la unidad `broiler` (ventana ON solo durante preparación de fixtures).
- PROHIBIDO forzar estados por SQL/DB (`§35`) — si un estado no puede lograrse por flujo oficial, el caso se documenta como no logrado y no se simula.
