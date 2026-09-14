# GA-CLAUDE · R-191 — CERTIFICACIÓN (transición de fase del lote por la UI)

Fecha: 2026-09-14 · Hallazgo **R-191** (P1 · bloquea P-02/P-04) · Paquete `specs/R-191/` · Commits: C1 `921a3a0` · C2 `d330ae5` · C2s `1f8dfb6`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | BE `evidence/red/backend-r191.log` — **7F/2P**: 2 fases activas, sin `phase` en la lectura (KeyError), poblaciones 0/0, transiciones inválidas 201, concurrencia 2×201; controles verdes (contrato `phase_id`; 422 del cuerpo antiguo). FE `evidence/red/vitest-r191.log` — **4F/4**: POST con `phase_code`, sin toast, badge ausente, i18n ausente |
| **C2 · Implementación** | ✅ | `evidence/green/` — BE **9/9** · FE **4/4** (regresión `gaFe04`/`gaFe06` verde); `tsc` 0; FE completa **364/364**; build OK · commit `d330ae5` |
| **C2s · Sensibilidad** | ✅ S1·S2·S3·S4 | S1 (cuerpo `phase_code`): 1F · S2 (catch sin toast): 1F · S3 (sin cierre de la activa): 3F · S4 (sin derivación de poblaciones): 1F — `evidence/sensibilidad/` |
| **C3 · Runtime** | ⏸ pendiente | E2E-R191-01…05 (nube; transición irreversible — lote de pruebas UAT-09) + consulta C-06 de activas múltiples |

## 2 · Implementación

- `lots/service.py::add_phase`: **bloqueo del lote** (`with_for_update`) + cierre de la fase activa (`end_date = start_date`); guardas `BR-23` (lote no activo · misma fase · fecha anterior); poblaciones ausentes (0/0) derivadas del **saldo por sexo** (nuevo `get_current_bird_balance_by_sex`, misma taxonomía/contrapartidas); lectura con `phase` (`LotPhaseRead.phase`).
- `LotDetailPage`: resuelve `phase_id` por **código** contra `masters/productive-phases`; POST `{lot_id, phase_id, start_date}`; toast de éxito y `getErrorMessage` en error; refetch de fases → badge «Producción» y botón fuera.
- i18n: `transitionSuccess`, `phaseAlreadyActive`. Sin migración/endpoint/permiso (AC-08).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R191-01 (cierra anterior; una sola activa) | ✅ BE 01 · S3 |
| AC-R191-02 (lectura incluye `phase.code`) | ✅ BE 02 |
| AC-R191-03 (poblaciones derivadas 35/60) | ✅ BE 03 · S4 |
| AC-R191-04a/b/c (lote no activo · misma fase · fecha anterior ⇒ 400 sin rastro) | ✅ BE 04a/b/c |
| AC-R191-05 (control `phase_id` explícito) | ✅ BE 05 |
| AC-R191-06 (concurrencia ⇒ {201,400}, una activa) | ✅ BE 06 · S3 |
| AC-R191-07 (422 del cuerpo antiguo — contrato vigente) | ✅ BE 07 |
| AC-R191-08…10 (FE: ids, toast, badge, i18n) | ✅ FE 01/02/03/10 · S1 · S2 |

## 4 · Veredicto

**R-191 = `CLOSED_TECHNICALLY`** — C1/C2/C2s completos; **C3 runtime** pendiente (ventana). El camino de fase queda íntegro por UI y por API, con una sola activa garantizada incluso en concurrencia, sin migración.
