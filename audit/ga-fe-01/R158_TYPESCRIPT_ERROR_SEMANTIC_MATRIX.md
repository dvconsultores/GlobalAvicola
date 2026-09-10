# R-158 · TYPESCRIPT ERROR SEMANTIC MATRIX

**2026-09-10** · HEAD `42108b0` · comando: `npx tsc -b --noEmit` desde `frontend/` · salida cruda en evidencia.

```
NOTA DE CONTEO: el compilador reporta 6 diagnósticos en total — 5 × TS6133 + 1 × TS2493 —
sobre 5 símbolos (TS2493 y TS6133 comparten el mismo símbolo `areaRes` en la misma línea).
Se mantienen las 6 filas del encargo (§15 del prompt: «6 filas exactas si siguen siendo 6»).
```

| # | ERROR_ID | TS_CODE | FILE | LINE:COL | SYMBOL | EXACT_MESSAGE | INTRODUCED_BY | FEATURE_CONTEXT | SOURCE_REQUIREMENT | SHOULD_EXIST? | SHOULD_BE_USED? | ROOT_CAUSE_CLASS | CURRENT_RUNTIME_IMPACT | MINIMAL_CORRECT_FIX | TEST_PROTECTING_BEHAVIOR | OWNER_DECISION? | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | E1 | TS6133 | `frontend/src/pages/audit/AuditPage.tsx` | 3:18 | `User` (import) | `'User' is declared but its value is never read.` | `4386f87` (2026-09-06) | Rework de filtros de auditoría: pestañas «por usuario» retiradas | `GA-REM-032 AC11` (retiro gobernado; `R-82` CERTIFIED) | NO | NO | `STALE_IMPORT_AFTER_INTENTIONAL_REMOVAL` | Ninguno en runtime (nunca llega a construir imagen) | Quitar `User` del import de `lucide-react` | Typecheck + Vitest completo; sin suite dedicada de AuditPage (no existe) | NO | FIXED |
| 2 | E2 | TS6133 | `frontend/src/pages/audit/AuditPage.tsx` | 3:24 | `Database` (import) | `'Database' is declared but its value is never read.` | `4386f87` | ídem 1 (pestaña «por lote») | ídem 1 | NO | NO | `STALE_IMPORT_AFTER_INTENTIONAL_REMOVAL` | ídem 1 | Quitar `Database` del import | ídem 1 | NO | FIXED |
| 3 | E3 | TS6133 | `frontend/src/pages/lots/LotFormPage.tsx` | 47:9 | `areas` (estado) | `'areas' is declared but its value is never read.` | `950bb21` (2026-09-07) | Scaffold de áreas a medio cablear (GA-REM-039): petición 5.ª nunca añadida, setter nunca llamado, control nunca renderizado | `GA-REM-039` gobierna maestros y área de USUARIO (`AC-A11`, implementado en `UsersPage`); **ningún AC gobierna área en el alta de lote** | NO (como local muerto; la captura de área del lote no está especificada para esta superficie) | NO | `INCOMPLETE_EXISTING_FEATURE` (wiring abandonado; parte no gobernada) | Ninguno en runtime; feature jamás funcionó | Eliminar la línea de estado muerta; `area_id` del esquema se conserva (traza); finding `R-182` registrado para la captura gobernada futura | Typecheck + Vitest; sin suite dedicada (no existe); comportamiento idéntico verificable (símbolo no leído) | NO | FIXED |
| 4 | E4 | TS6133 | `frontend/src/pages/lots/LotFormPage.tsx` | 47:16 | `setAreas` | `'setAreas' is declared but its value is never read.` | `950bb21` | ídem 3 (mismo estado) | ídem 3 | NO | NO | `INCOMPLETE_EXISTING_FEATURE` | ídem 3 | Ídem 3 (misma línea) | ídem 3 | NO | FIXED |
| 5 | E5 | TS2493 | `frontend/src/pages/lots/LotFormPage.tsx` | 85:47 | `areaRes` | `Tuple type '[PromiseSettledResult<…>, PromiseSettledResult<…>, PromiseSettledResult<…>, PromiseSettledResult<…>]' of length '4' has no element at index '4'.` | `950bb21` | El destructuring pide 5 resultados; el array tiene 4 peticiones (farms/houses/genetic-lines/breeds) | ídem 3 | NO | NO | `INVALID_DESTRUCTURING` | Ninguno (bloquea el build) | Destructuring a 4 elementos | Typecheck + Vitest | NO | FIXED |
| 6 | E6 | TS6133 | `frontend/src/pages/lots/LotFormPage.tsx` | 85:47 | `areaRes` | `'areaRes' is declared but its value is never read.` | `950bb21` | ídem 5 | ídem 3 | NO | NO | `INVALID_DESTRUCTURING` | ídem 5 | Ídem 5 | ídem 5 | NO | FIXED |

## Lectura de conjunto

- **AuditPage (E1–E2)**: una remoción **gobernada** dejó dos imports sin uso. La corrección no
  cambia ninguna funcionalidad: las pestañas vigentes (`all`, `corrections`) y los filtros reales
  (acción/módulo/fecha) permanecen; las retiradas **no** se restauran.
- **LotFormPage (E3–E6)**: un scaffold de «áreas» **nunca cableado** en un commit de feature.
  No hay AC para esa superficie; completarlo sería UX nueva (prohibido en esta tranche). Se retira
  lo mínimo que rompe el compilador y se registra la feature incompleta (`R-182`).
- **Clases usadas**: `STALE_IMPORT_AFTER_INTENTIONAL_REMOVAL` (×2) ·
  `INCOMPLETE_EXISTING_FEATURE` (×2) · `INVALID_DESTRUCTURING` (×2). Ninguna otra.
- **OWNER_DECISION_REQUIRED**: ninguno.
- **Cero** `any` nuevos, cero `ts-ignore`/`ts-expect-error`, cero casts, cero renombrados `_`,
  cero `void`-falsos, cero relajación de compiler options.

## Evidencia de soporte

- Salida cruda del compilador: capturada en esta sesión (6 diagnósticos, exit 2).
- Historia: `4386f87` (2 errores) · `950bb21` (6 errores) — `GA_FE_01_HISTORICAL_REPLAY.md`.
- Gobernanza: `GA-REM-032 AC11` (comentario en el propio código) · `GA-REM-039 AC-A11` y §7–§9 de
  su spec · ausencia de «área» en `docs/02` · payload del alta verificado campo a campo.
