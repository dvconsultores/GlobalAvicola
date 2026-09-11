# GA-FE-06 · RECONCILIACIÓN DE CIERRE — R-182

Respuestas directas, con evidencia ligada.

| # | Pregunta | Respuesta | Evidencia |
|---|---|---|---|
| 1 | ¿La fecha prevista se perdía **en silencio** antes? | **SÍ** — se capturaba en el formulario y el payload de 8 claves no la incluía; `area_id` ni se capturaba. El alta respondía 201 y el dato no existía en ningún salto | RED: `red/vitest-red-summary.txt` (4 fallos objetivos) + `red/runtime-red.json` (lote 17: payload sin claves, fresh `null`) |
| 2 | ¿Se captura ahora en UI? | **SÍ** — control de fecha (ya existía, ahora conectado) + **selector de «Área» nuevo** alimentado por `/masters/areas?limit=100` | `ds-02b`, `en-01b`, `mb-01b`; `runtime-green.json` |
| 3 | ¿Viaja en el contrato HTTP? | **SÍ** — payload de 10 claves con `planned_close_date` (YYYY-MM-DD) y `area_id` (o `null` explícitos) | `GA_FE_06_NETWORK_EVIDENCE.md`; corrida E2E-01 |
| 4 | ¿Se **persiste** y se relee? | **SÍ** — fresh GET devuelve exactamente el valor (`2026-09-21T00:00:00Z` / `1` en lote 19); refresh/relogin idéntico | E2E-01, E2E-07; `final-verify.json` |
| 5 | ¿Sin corrimiento ±1 día? | **SÍ** — 4 valores de borde (+10/+3/+1/−1) exactos entre lo tecleado y el ISO releído (convención medianoche UTC, R-75) | `runtime-green.json` E2E-05; E2E-02 |
| 6 | ¿Visible en producto? | **SÍ** — fila «Fecha prevista de cierre» en el detalle (día del calendario, `slice(0,10)` del ISO) | `ds-01b`, `ds-01c`, `mb-02b` |
| 7 | ¿Opcional de verdad? | **SÍ** — sin fecha/área el payload envía `null` y el lote se crea; el SLA excluye NULL por contrato | E2E-04 (lote 23) |
| 8 | ¿El SLA queda alimentado? | **Fuente reparada**; aviso del escáner horario = `PENDING_SCAN_WINDOW` (relecturas 14:06/14:15 UTC → 0; ver §SLA) | E2E-10..13 datos ✓; `GA_FE_06_SLA_CONTRACT_MATRIX.md` capas 1–3 |
| 9 | ¿Cambios backend/migración/permisos? | **0 · NO · NINGUNO** (como se anticipó). Todo el cambio es frontend + i18n | `git show 23ca59a --stat` |
| 10 | ¿Regresiones? | Suite frontend **278/278** (36 archivos; incluye GA-FE-02/03/04/05), `tsc` 0, build OK, gate PG-libre 7/7; runtime: guard D fail-closed re-verificado (GA-FE-04) | salidas de gates; `ds-04b` |
| 11 | ¿Hallazgos nuevos? | **N-1 (R-183 candidato)**, **N-2 (R-184 candidato)** + observaciones N-3/N-4 — registrados con evidencia, **no corregidos** (alcance) | `GA_FE_06_FINDINGS.md` |
| 12 | ¿Higiene de datos? | BUs restauradas OFF, concesión revocada, usuarios/roles retirados, áreas dadas de baja lógica, credenciales destruidas | `GA_FE_06_TEST_DATA_LEDGER.md` + `GA_FE_06_HYGIENE_EVIDENCE.md` |
| 13 | ¿Generación certificada? | `index-DcqmSs-R.js` (LM 2026-09-11 13:57:59 GMT · ETag `"6aa408e7-13cfbd"`), desplegada desde `23ca59a` | corrida E2E-00; headers |

## Nota SLA (honestidad)

El aviso `lot_near_close` lo produce una tarea interna con ciclo horario; no existe disparador manual. La tranche certifica: (a) los datos de origen existen y son exactos (runtime), (b) la regla `0..3 / active / NOT NULL` está cubierta por la suite canónica del repo (CI), (c) relectura de notificaciones al cierre documentando el resultado real (aviso capturado o `PENDING_SCAN_WINDOW`). **No se reimplementó la regla ni se forzó el escáner.**

---

# ADDENDUM GA-FE-06-A (2026-09-11) — cierre de seguridad

El AC de pertenencia (ácron local AC11; **R182-AC20/R182-AC36** en la numeración del encargo) pasó de PARTIAL a **PASS**:

- Alta con área ajena: **400 `{"detail":"Área no encontrado","rule":"BR-07"}`**, sin persistencia, sin auditoría de éxito (runtime `69d0c95`).
- Edición a área ajena: íd.; fresh GET conserva el área propia.
- Misma-empresa y NULL: ALLOW (controles). Área inexistente: 400 BR-07 (antes 500).
- R-183: **absorbido en R-182** (subhallazgo de seguridad; `GA_FE_06_A_R183_DEDUP.md`). R-184: separate, non-blocking, sin cambios.

Con esto, **R-182 = CLOSED** (0 residuales de seguridad) y `GA-FE-06 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING`.
