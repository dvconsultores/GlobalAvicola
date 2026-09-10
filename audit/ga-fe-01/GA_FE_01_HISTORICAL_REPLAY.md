# GA-FE-01 · HISTORICAL CAUSAL REPLAY

**2026-09-10** · worktrees temporales en `/tmp`, árbol principal intacto, sin modificar código en
los worktrees, dependencias reutilizadas por enlace simbólico (sin tocar lockfiles), worktrees
eliminados al terminar (`git worktree list` → solo el árbol principal).

Comando por SHA: `npx tsc -b --noEmit` (sin cachés: `tsconfig.*.tsbuildinfo` eliminado antes de
cada corrida) y `npm run build` donde es práctico.

---

## Resultados

| SHA | Fecha | Rol | `tsc -b --noEmit` | Errores | `npm run build` |
|---|---|---|---|---|---|
| **`f46cb13`** | 2026-09-05 16:08 | Commit del artefacto servido | **exit 0 — GREEN** (sin salida) | 0 | **exit 0 — GREEN** → `dist/assets/index-D5dwMXuP.js` (1 235,29 kB) |
| **`4386f87`** | 2026-09-06 03:36 | Primer RED | **exit 2** | **2** (`AuditPage.tsx` E1+E2) | **FAIL** — muere en `tsc` (no alcanza `vite`) |
| **`950bb21`** | 2026-09-07 13:06 | Segundo RED | **exit 2** | **6** (E1+E2 + E3–E6 `LotFormPage.tsx`) | (no re-ejecutado; mismo gate roto) |
| **`42108b0`** (baseline) | 2026-09-10 | HEAD de la tranche | **exit 2** | **6** | **FAIL** — muere en `tsc` |

## El eslabón que cierra la cadena por ambos extremos

```
El build GREEN de f46cb13 produce EXACTAMENTE el asset que sirve el runtime:

  f46cb13   npm run build → dist/assets/index-D5dwMXuP.js          (1 235,29 kB)
  runtime   GET /         → assets/index-D5dwMXuP.js  sha256 4eb822a5…  (1 235 292 bytes)

⇒ El artefacto servido (congelado desde 2026-09-05 14:09:27 GMT) salió de f46cb13.
⇒ El primer commit posterior (4386f87) ya es RED; desde entonces ningún build de imagen
  de frontend puede completar `RUN npm run build`.
```

Nota metodológica: en la corrida por lote los códigos de salida quedaron enmascarados por un `| tail`;
se repitieron **sin tubería** los dos SHAs rojos y se registraron los códigos reales
(`4386f87`: exit 2/2 errores · `950bb21`: exit 2/6 errores). El baseline se midió sin tubería
(exit 2/6 errores) y `vite build` aislado sin tubería (exit 0).

## Interpretación

```
GREEN BEFORE (f46cb13)
   ↓ 4386f87 retira pestañas de AuditPage (GA-REM-032 AC11) y deja el import viejo
FIRST RED (2 errores) — reproducible
   ↓ 950bb21 añade el scaffold de áreas sin cablear (4 errores más)
RED PERSISTS (6 errores) — reproducible
   ↓ Dockerfile: RUN npm run build → falla siempre en tsc → sin imagen nueva
FROZEN RUNTIME (index-D5dwMXuP.js servido desde 09-05)
```

La cadena no se apoya en `git diff`: se apoya en **ejecuciones del compilador y del build** en el
código de cada commit — exactamente lo que exige §17 del encargo.

## Reproducibilidad

| Comando | Dónde | Resultado esperado |
|---|---|---|
| `git worktree add /tmp/x f46cb13 && ln -s <repo>/frontend/node_modules /tmp/x/frontend/node_modules` | raíz | worktree detached |
| `rm -f node_modules/.tmp/tsconfig.*.tsbuildinfo && npx tsc -b --noEmit` | `/tmp/x/frontend` | exit 0 (f46cb13) · exit 2 (rojos) |
| `npm run build` | `/tmp/x/frontend` | GREEN en f46cb13 con `index-D5dwMXuP.js` · FAIL en 4386f87 |
| `git worktree remove --force /tmp/x` | raíz | árbol principal limpio |
