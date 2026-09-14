# R-195 · Evidencia de sensibilidad (mutación + restore desde SHA explícito)

Fecha: 2026-09-14 · Spec: `audit/ga-claude-final-audit/specs/R-195/` (AC-01…08)
`IMPLEMENTATION_COMMIT=bcfdebd` · `HEAD_VERIFIED=bcfdebd` (árbol limpio antes/después)

Restauración con `git restore --source=bcfdebd -- <archivo>` (SHA explícito).

| Mutación | Revert de | Rojo observado | Restore | Post-restore |
|---|---|---|---|---|
| S1 | payload de edición vuelve al formulario completo (`username`/`company_id`) | `× AC-01` — 1F/4P | ✓ | verde en S2 |
| S2 | guard sin `last_name` | `× AC-03` — 1F/4P | ✓ | verde en S3 |
| S3 | catch de baja vuelve a `alert` nativo | `× AC-05` — 1F/4P | ✓ | verde en S4 |
| S4 | guard notifica con `alert` nativo | `× AC-03 · × AC-06` — 2F/3P (clúster esperado: misma guarda) | ✓ | full FE 419/419 |

## Post-mutation green

- `r195.usersEdit.test.tsx` 5/5.
- Suite FE completa: **62 archivos / 419/419** (`fe-r195-post-mutation-full.log`).
- `npm run build` (`tsc -b && vite build`): exit 0.
- BE: **sin cambio** (SPEC §7/§10: contrato ya correcto; `UserUpdate` intacto) —
  regresión cubierta por la suite FE y por el control de contrato de C1.

## Notas

- **AC-02** ya estaba verde en C1 por R-215 (catch con `getErrorMessage`+toast):
  se conserva como regresión.
- **Harness r215** ajustado (test 05 rellena `last_name`): el guard nuevo de
  R-195 cortaba antes del 422 simulado — misma intención (render seguro del 422).
