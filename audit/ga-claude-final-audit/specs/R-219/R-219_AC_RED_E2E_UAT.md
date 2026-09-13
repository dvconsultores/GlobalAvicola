# R-219 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-219/evidence/`.

## 1 · Criterios de aceptación

| AC | Criterio | Test (RED) |
|---|---|---|
| AC-R219-01 | La tabla muestra el **nombre** de usuario (o id resoluble) y no campos inexistentes | unit (rojo) |
| AC-R219-02 | La pestaña «Correcciones» muestra el diff (`previous_values→new_values`) | unit (rojo) |
| AC-R219-03 | `change_reason`/`comments` visibles cuando existen | unit (rojo) |
| AC-R219-04 | Paginación funcional (50/página con total) | unit (rojo) |
| AC-R219-05 | Acciones/módulos traducidos ES/EN (sin crudos) | unit locales (rojo) |
| AC-R219-06 | Sin migración; opcional BE `user_name` (C-01) sin migración | revisión |
| AC-R219-07 | Regresión: `test_audit_query.py`, vitest, tsc, build | suites |

## 2 · Diseño RED

Unit jsdom `r219.auditPage.test.tsx` con logs de fixture (created/corrected/approved) ⇒ rojos por campos inexistentes/paginación/i18n. Salida `evidence/red/`.

## 3 · E2E

`R219-RT-01…03`: `/audit` con datos reales (nombre, diff, paginación) — captura. Artefacto `evidence/r219/runtime-{red,c3}.json`.

## 4 · UAT

**No requerida.** Verificación informativa: pestaña Correcciones con diff visible.
