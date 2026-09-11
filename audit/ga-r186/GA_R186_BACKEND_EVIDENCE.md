# GA-R186 · EVIDENCIA BACKEND

## 1 · Cambio implementado (commit C2 `0309225`)

| Elemento | Valor |
|---|---|
| Archivo | `backend/app/reports/service.py` (**único**) |
| Diff | `+4 −1` (1 expresión + 3 líneas de comentario) |
| Expresión | `age_days = (date.today() - _dia(lot.start_date)).days if lot and lot.start_date else 30` (en `get_kpi_production_index`) |
| Helper | `_dia` — **reutilizado** (canónico R-75/GA-REM-028; ya importado desde R-184). Sin `_dia2`/normalizadores nuevos |
| Expresiones sin normalizar restantes en el módulo | **0** (`grep "date.today() - lot.start_date"` = 0) |
| Fórmula G-05 | **INTACTA** (términos, divisores, guarda, `or 1`, fallbacks y redondeos sin tocar) |
| G-06 / R-184 | **NO tocados** (diff limitado a la línea 602) |
| Migraciones / permisos / endpoints / frontend | 0 / 0 / 0 / 0 |

## 2 · Verificaciones locales ejecutadas

| Verificación | Resultado |
|---|---|
| Repro determinista: `TypeError` pre-fix / edad 19 post-fix / PI esperado 400.0 | `evidence/red/typeerror-local.txt` |
| Import del servicio + expresión normalizada | PASS |
| Gate backend canónico (OD-16 + migración BU) | **7 passed** |
| Suite nueva `tests/test_r186_g05_date_semantics.py` (PG; CI) | **11 skipped locales** (declarado; mecanismo `test_credentials`) |
| `test_kpi_scope.py` (PG) | errores locales de conexión (preexistente; corre en CI) — sin relación con el cambio |

## 3 · Gates frontend (§48 — sin cambios de código)

| Gate | Resultado |
|---|---|
| `npx tsc -b --noEmit` | **PASS** |
| `npm run build` | **PASS** |
| `npx vitest run` | **280/280 PASS** |

## 4 · Contrato cubierto por la suite (PG/CI)

Determinista (400.0 exacto + esquema + `unit`), estabilidad, mismo día (edad 0 ⇒ PI 0, **sin clamp** y `fcr or 1`), sin inicio (edad 30), ausencia de datos (PI 0), 404 inexistente/ajeno/sin concesión, 403 sin RBAC, BU-OFF 404 y actor global sin bypass de BU-OFF (OD-16).
