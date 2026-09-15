# T14 · CUTOVER OPERACIONAL (GA-REQ-061) — CERTIFICACIÓN DE TRANCHE

Fecha: 2026-09-15 · Estado: **CLOSED_TECHNICALLY** · Evidencia principal:
`specs/GA-REQ-061/GA_REQ_061_CERTIFICATION.md` +
`specs/GA-REQ-061/evidence/`.

## Resumen ejecutivo

Capacidad nueva transversal Pre-Go-Live para incorporar lotes ya en marcha sin
doble conteo y sin fabricar datos. Implementada por checkpoints C1–C9 con
gobernanza completa por checkpoint (SPEC→AC→RED→IMPL→GREEN→SENSIBILIDAD→
POST-MUTACIÓN→EVIDENCIA→COMMIT→PUSH→VERIFY):

- **BE**: 226 rutas `/api/` (crecimiento 214→226), tablas 60, cabeza alembic
  `c8d9e0f1a2b3`; guardias de conjunto 67/67; sensibilidad **S1–S10 completas**.
- **FE**: «Cargas Iniciales» en `/cutover` (i18n ES/EN; UNKNOWN≠0 visual;
  apply bloqueado con errores); FE **524/524**; build 0.
- **E2E**: corrida por BU (4/4) con journals; caso numérico de oro (9.965/535/
  UNKNOWN) y negativas (cross-company 404, re-apply 409, submit bloqueado).
- **Deficits reales cerrados en la tranche**: `MASTER_INACTIVE` (OD-21/AC52),
  alcance BU del actor no-super-admin (resuelto en BD), plantilla descargable
  versionada por BU.

## Commits (locales, empujados y verificados en cada checkpoint)

`cf03253` C1 · `3e138a1` C2 · `3e3f2cb` C3 · `fe5fe98` C4 · `4b8bc74` C5 ·
`02e0632` C6 · `69f5aa8` C7 · `a7ada1f` C8 · `1976011` C9 · cierre de trance:
pendiente del commit final.

## Gates

- BE full: **1428/0F/49S**.
- FE full 524/524 · build EXIT 0.
- E2E 4/4 (harness aislado).
- `REMOTE_SHA_MATCH = PASS` en cada checkpoint (política AOD-29 Clar. 01).
Además: primera corrida full detectó 9 fallos de gobernanza/contaminación de suite —
todos resueltos en `4b859b2` con re-verificación (161/161 dirigida y 1428/0F full).

## Siguiente

**T12** (orden canónico T11 → T14 → **T12** → T13). R-142 permanece diferida
(AOD-17).
