# R-215 · Evidencia de sensibilidad (mutación + restore desde SHA explícito)

Fecha: 2026-09-14 · Spec: `audit/ga-claude-final-audit/specs/R-215/` (AC-01…04)
`IMPLEMENTATION_COMMIT=cd2e7bc` · `HEAD_VERIFIED=cd2e7bc` (árbol limpio antes/después)

Cada mutación revierte **exactamente el fix de un test** y se restaura con
`git restore --source=cd2e7bc -- <archivo>` (SHA explícito, nunca `checkout --`;
ver lección AE-42). El rojo debe ser **quirúrgico**: 1F/5P con el test que
protege ese fix.

| Mutación | Archivo | Revert de | Rojo observado | Restore | Verificación posterior |
|---|---|---|---|---|---|
| S1 | `pages/masters/MasterListPage.tsx` | `getErrorMessage` → `detail` crudo | `× 01` (React #31) — 1F/5P | `restore --source=cd2e7bc` ✓ `RESTORE_VERIF=2` | re-run 6P |
| S2 | `components/TraceabilityTree.tsx` (catch pollitos) | `getErrorMessage` → `detail` crudo | `× 03` (React #31) — 1F/5P | ✓ `RESTORE_VERIF=3` | re-run 6P |
| S3 | `pages/users/UsersPage.tsx` | `toast.error(getErrorMessage)` → `alert(detail)` | `× 05` («alert con detalle no-string: expected 1 to be 0») — 1F/5P | ✓ `RESTORE_VERIF=1` | S4 run: 05 pasa |
| S4 | `components/ErrorBoundary.tsx` | fallback de recuperación (`hasError && false`) | `× 06` — 1F/5P | ✓ `RESTORE_VERIF=0` | S5 run: 06 pasa |
| S5 | `pages/lots/LotFormPage.tsx` | `getErrorMessage` → `detail` crudo en toast | `× 02` (toast con objeto) — 1F/5P | ✓ `RESTORE_VERIF=2` | S6 run: 02 pasa |
| S6 | `pages/users/ProfilePage.tsx` | `getErrorMessage` → `detail` crudo | `× 04` (React #31) — 1F/5P | ✓ `RESTORE_VERIF=2` | full FE 405/405 |

## Post-mutation GREEN (estado final = cd2e7bc, árbol limpio)

- `r215.errorRendering.test.tsx` 6/6.
- Suite FE completa: **60 archivos / 405/405 pass** (`fe-r215-post-mutation-full.log`).
- Gates previos del commit de implementación: targeted 28/28, full 405/405,
  `npm run build` (tsc -b + vite) exit 0.

## Logs crudos

- `fe-r215-s1.log` … `fe-r215-s6.log` (rojos por mutación).
- `fe-r215-post-mutation-full.log` (405/405 tras restaurar todo).

## Cobertura 1:1

Cada consumidor y el boundary tienen una mutación que exclusively lo tiñe:
01↔S1, 02↔S5, 03↔S2, 04↔S6, 05↔S3, 06↔S4. Sin rojos colaterales en ninguna.
