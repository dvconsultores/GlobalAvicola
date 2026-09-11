# GA-FE-05 · MATRIZ DE ESTADOS DE OPERACIÓN (verdad del repositorio)

Fuente única: `backend/app/operations/models.py::EventStatus` + `service.py` (`EDITABLES`, `REENVIABLES`, `NO_CANCELABLES`) + `OD-17`/`docs/12`. Sin estados especulativos.

| Estado real | Significado | Editable* | Submit/Reenviar | Corregir | Revisar | Aprobar | CTA esperada (R-181) | Contrato backend del envío |
|---|---|---|---|---|---|---|---|---|
| `draft` | borrador (R-154; UI no lo produce hoy) | SÍ | NO | — | — | — | ninguna | `submit` ⇒ 400 |
| `registered` | registrado por operador | SÍ | **SÍ (envío)** | — | — | — | **«Enviar a revisión»** | `POST /submit` ⇒ `pending_review` |
| `pending_review` | en cola de revisión | NO | NO | — | inicio | — | ninguna | `submit` ⇒ 400 |
| `in_review` | revisión en curso | NO | NO | — | completar/devolver | aprobar/rechazar | ninguna | `submit` ⇒ 400 |
| `returned` | devuelto con motivo | SÍ | **SÍ (reenvío)** | SÍ (→`corrected`) | — | — | **«Reenviar a revisión»** | `POST /submit` ⇒ `pending_review` |
| `corrected` | corregido, espera aprobador | NO | NO | — | — | aprobar | ninguna | `submit` ⇒ 400 |
| `approved` | aprobado | NO | NO | — | — | — | ninguna | `submit` ⇒ 400 |
| `rejected` | rechazado (**no terminal**) | SÍ | **SÍ (reenvío)** | SÍ | — | — | **«Reenviar a revisión»** | `POST /submit` ⇒ `pending_review` |
| `consolidated` | consolidado | NO | NO | — | — | — | ninguna | `submit` ⇒ 400 |
| `sent_to_sap` | enviado a SAP | NO | NO | — | — | — | ninguna | `submit` ⇒ 400 |
| `sap_confirmed` | confirmado por SAP | NO | NO | — | — | — | ninguna | `submit` ⇒ 400 |
| `sap_error` | error SAP | NO | NO | — | — | — | ninguna | `submit` ⇒ 400 |
| `cancelled` | anulado | NO | NO | — | — | — | ninguna | `submit` ⇒ 400 |
| `reversed` | aprobado y neutralizado (OD-19) | NO | NO | — | — | — | ninguna | `submit` ⇒ 400 |

\* Editabilidad según `EDITABLES` (backend); no se modifica en GA-FE-05.

**Conjunto canónico del CTA**: exactamente `{registered → Enviar} ∪ {returned, rejected → Reenviar}` — igual a `REENVIABLES` y a `OD-17.a/b`. El resto: sin acción.

**Regla adicional de UI (GA-FE-04, no nueva)**: el CTA además exige permiso `operations:create` ∧ unidad disponible (`requiresUnits`: efectiva normal / habilitada+contexto global). `draft` queda sin CTA (el backend lo rechaza; no hay flujo UI de borrador en R-181).
