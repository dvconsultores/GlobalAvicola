# R-207 · CERTIFICACIÓN TÉCNICA LOCAL — Superficie de reverso (solicitar, seguir, mostrar)

Fecha: 2026-09-14 · Programa: GA PRE-SAP (T10) · Política: **AOD-29 Clarification 01**
(certificación local con gates reproducibles; **GitHub Actions retirado**; **push requerido**
a `origin/main` con verificación de SHA remoto).

## 1 · Paquetes y commits

| Fase | SHA | Contenido |
|---|---|---|
| C1 · RED | **`3eb1193`** | `r207.reversalSurface` FE 4F por causa exacta (botón/modal inexistentes con permiso; `STATUS_STYLES` sin `reversed`; flujo corto sin validar) |
| C2 · Implementación | **`4e8d999`** | `reversals.service` (contrato `POST /reversals {event_id, reason}`); botón «Solicitar reverso» en el detalle aprobado (gate `reversals:create`); modal sin diálogos nativos con motivo ≥5 (validación cliente + `role=alert`); contrapartida enlazada desde la respuesta 201; guard de vuelo; banner original ↔ contrapartida; `reversed` en mapa central (`STATUS_STYLES`/`STATUS_ALIASES`/`StatusKey`), `EventStatus`, y mapas locales (detalle, listas, bandejas, aprobaciones); i18n ES/EN (`reversals.*`) |

**Sin cambio backend** (SPEC §10: contrato existente) · **sin migración** · **sin endpoint ni
permiso nuevos** · diff FE + tests (AC-R207-08).

## 2 · Gates locales (PASS)

| Gate | Resultado | Evidencia |
|---|---|---|
| FE targeted R-207 | **4/4** | `evidence/green/fe-r207-green-targeted.log` |
| FE suite completa | **433/433** (baseline 429 + 4) | `evidence/green/fe-r207-green-full.log` |
| `npm run build` (`tsc -b && vite build`) | **EXIT 0** | `evidence/green/fe-r207-build.log` |
| BE | **no requerida**: `BACKEND_DIFF = 0` (la última suite completa BE 1373/0/49 corresponde al mismo árbol backend; R-207 no toca `backend/`) | — (justificación SPEC §10) |

## 3 · Sensibilidad (mutación → RED quirúrgica → restore desde `4e8d999`)

| ID | Mutación | Rojo observado | Log |
|---|---|---|---|
| R1 | retirar gate `reversals:create` | AC-R207-01 únicamente | `sensibilidad/fe-r1-…` |
| R2 | retirar validación de motivo <5 | AC-R207-04 únicamente | `sensibilidad/fe-r2-…` |
| R3 | descartar `reversal_event_id` de la respuesta 201 | AC-R207-02 únicamente | `sensibilidad/fe-r3-…` |
| R4 | quitar `reversed` del mapa central | AC-R207-03 únicamente | `sensibilidad/fe-r4-…` |
| R5 | romper el payload (`reason`→`observations`) | AC-R207-02 únicamente | `sensibilidad/fe-r5-…` |

**Post-mutación** (restauración verificada): FE targeted **4/4** (`evidence/post-mutation/`).

## 4 · Dependencias y ventana

- **R-192/R-193**: cerrados técnicamente en T7 (`e30178b`) ⇒ dependencia de orden del
  SPEC §8 **satisfecha**; la superficie de reverso no se libera antes del cierre tras
  reverso ni de BR-18.
- **R-208** (aprobación del lote de reversos) sigue su propio paquete; esta UI no lo
  adelanta (la contrapartida entra por el motor existente y se aprueba donde ya se
  aprueba).
- Reverso post-SAP permanece `SAP_DEFERRED` (fuera de alcance, SPEC §8).

## 5 · Explícitos de política

- `GITHUB_ACTIONS = NOT_APPLICABLE_BY_OWNER_DECISION` (nunca PASS).
- `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION`; publicación con `REMOTE_SHA_VERIFICATION`.
- `PUSH != DEPLOY`.

## 6 · UAT

Pendiente **acumulable** (SPEC §29, 4 casos: solicitar con motivo · contrapartida ·
aprobarla · estado/enlace; móvil/EN). Se agrupa en el gate PRE-SAP.

## 7 · Estado

- **R-207 = `CLOSED_TECHNICALLY`** (local) · KPI de procesos sin cambio (**0/17**).
- T10: R-197 ✓ · R-207 ✓ · siguiente evaluación: **R-142 según AOD-17** (si no procede, T10 cierra).
