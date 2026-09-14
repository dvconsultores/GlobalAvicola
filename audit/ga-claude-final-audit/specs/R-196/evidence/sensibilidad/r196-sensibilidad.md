# R-196 · Evidencia de sensibilidad (mutación + restore desde SHA explícito)

Fecha: 2026-09-14 · Spec: `audit/ga-claude-final-audit/specs/R-196/` (AC-01…10)
`IMPLEMENTATION_COMMIT=571b4d5` · `HEAD_VERIFIED=571b4d5` (árbol limpio antes de cada mutación)

Restauración SIEMPRE con `git restore --source=571b4d5 -- <archivo>` (SHA
explícito; nunca `checkout` implícito — lección AE-42).

| Mutación | Archivo | Revert de | Rojo observado | Restore | Post-restore |
|---|---|---|---|---|---|
| S1 | `pages/masters/MasterListPage.tsx` | selector padre (`PADRE_DE`) desactivado | `× AC-02 · × AC-03a · × AC-03b · × AC-04` — 4F/5P (clúster de la única ruta del selector) | `--source=571b4d5` ✓ | re-run verde en S2 |
| S2 | `pages/masters/MasterListPage.tsx` | conversión numéricos vacíos ⇒ `null` desactivada | `× AC-04` — 1F/8P (tras **reforzar el guard**: limpiar el campo deja `''`, el caso real) | ✓ | re-run verde en S3 |
| S3 | `pages/masters/MasterListPage.tsx` | botón «Activar» oculto | `× AC-05` — 1F/8P | ✓ | re-run verde en S4 |
| S4 | `pages/masters/MastersHubPage.tsx` | `Link` → `span` (sin navegación) | `× AC-07` — 1F/8P | ✓ | re-run verde final |
| S5 | `app/masters/service.py` | override de empresa desactivado (la del cliente se impone) | `× be_02 (ignora company ajena)` — 1F/2P | ✓ | be_03 pasa en S6 |
| S6 | `app/masters/schemas.py` | `FarmCreate.company_id` vuelve a obligatorio | `× be_01 (sin company en cuerpo)` — 1F/2P | ✓ | árbol limpio |

## Notas

- **AC-04 reforzado durante sensibilidad** (harness, no spec): el test original
  dejaba `capacity` *sin tocar* (`undefined`, que el contrato ya acepta) y la
  mutación S2 no teñía; ahora el test **limpia** el campo (`''`, el caso real del
  “422 por cadena vacía”) y S2 lo tiñe quirúrgicamente. Commit C2b.
- **S1** tiñe 4 tests (AC-02/03a/03b/04): una sola ruta de código (el selector
  del padre) — clúster esperado y documentado; cada test tiene además su propia
  mutación exclusiva (S2-S4) para el resto de sus asserts.
- Los 5 setups de áreas (tests de BE) adaptados a `switch-company` durante C2
  quedan cubiertos por la suite BE completa post-mutation.

## Post-mutation green

- `r196.mastersCreate.test.tsx` 9/9.
- Suite FE completa: **61 archivos / 414/414** (`fe-r196-post-mutation-full.log`).
- `npm run build` (`tsc -b && vite build`): exit 0 (`fe-r196-post-mutation-build.log`).
- Suite BE completa: **1367 passed / 0 failed / 49 skipped** (21:47;
  `be-r196-post-mutation-full-1367-0-49.log`; 1364 de T8 + 3 nuevos de R-196).
