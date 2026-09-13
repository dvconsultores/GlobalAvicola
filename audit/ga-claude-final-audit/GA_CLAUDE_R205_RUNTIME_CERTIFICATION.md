# GA-CLAUDE · R-205 — CERTIFICACIÓN (cuadre BR-20 alcanzable por la navegación real)

Fecha: 2026-09-14 · Hallazgo **R-205** (P1 · bloquea P-03 recepción · BR-20) · Paquete `specs/R-205/` · Clarificaciones C-01…C-08 (sin decisiones abiertas; C-06 nota de dominio) · Commits: C1 `fe3bd3d` · C2 `72aa7f4` · C2s `dbc782d`.

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | `evidence/red/vitest-r205.log` — **12F/2P**: helper `resolverStageDelAsistente` inexistente (9 unit) + 3 jsdom (deep link sin cuadre; `?stage=` sin paridad; cuadre incompleto viaja al POST); controles verdes (URL directa; lote broiler sin cuadre). **Control BR-20** `evidence/red/backend-r205-control.log` — `test_reception_reconciliation.py` **10/10** verde |
| **C2 · Implementación** | ✅ | `evidence/green/r205-green-final.log` — **29/29** (R-205 14 + R-190 11 + F-01e 4); `tsc` 0; **FE 360/360** (`evidence/green/fe-suite-360.log`); build OK · commit `72aa7f4` |
| **C2s · Sensibilidad** | ✅ S1·S2·S3 | **S1** (sin visibilidad por lote ni derivación): 4F · **S2** (sin soporte `?stage=`): 3F · **S3** (sin guarda cliente): 1F — `evidence/sensibilidad/`; mutaciones revertidas |
| **C3 · Runtime** | ⏸ **pendiente** | E2E-R205-01…06 (nube) + recertificación R-189 retry 7/7 + verificación cruzada `p03` — ventana de deploy/credenciales (misma clase que **G-06**) |

## 2 · Implementación

- `operationPayload.ts::resolverStageDelAsistente` — etapa derivada con prioridad `?stage=` → lote (`bird_type` + fase) → `null` (paso 1).
- `OperationFormPage.tsx` — `stageFinal = stage ?? stageDerivada`; cuadre **visible por lote** (`bird_reception` + `bird_type=breeder`, C-02) o por etapa; guarda cliente del cuadre (`received_total`/`dead_on_arrival`/`rejected_on_arrival` completos) con mensaje `operations.cuadreRequired` — sin petición si falta (C-03, patrón R-189).
- i18n ES/EN (`cuadreRequired`).
- Backend **sin cambio**: BR-20 intacta (control 10/10).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R205-01 (hub con deep link ⇒ cuadre visible + payload completo) | ✅ jsdom AC-01 · S1 |
| AC-R205-02 (deep link con `?stage=` ⇒ paridad) | ✅ jsdom AC-02 · S2 |
| AC-R205-03 (URL directa por pasos — control) | ✅ jsdom AC-03 |
| AC-R205-04 (lote broiler ⇒ sin cuadre — control) | ✅ jsdom AC-04 |
| AC-R205-05 (cuadre incompleto ⇒ sin POST + mensaje) | ✅ jsdom AC-05 · S3 |
| AC-R205-06 (BR-20 por API — control) | ✅ BE 10/10 |
| AC-R205-07 (sin migración/endpoint/permiso) | ✅ diff FE-only (helper+página+i18n) |
| AC-R205-08 (unit de derivación: `?stage=`/lote/null) | ✅ unit 9/9 · S2 |

## 4 · Veredicto

**R-205 = `CLOSED_TECHNICALLY`** — C1/C2/C2s completos; el cuadre de reproductoras queda alcanzable por **todas** las rutas del producto (hub, detalle, deep link) y obligatorio en cliente. **C3 runtime pendiente** (ventana de deploy/credenciales): habilita el verde de `p03/p04/p11` y la recertificación R-189.
