# GA-R184 · EVIDENCIA BACKEND

## 1 · Cambio implementado (commit C2 `3f88f94`)

| Elemento | Valor |
|---|---|
| Archivo | `backend/app/reports/service.py` (**único**) |
| Diff | `+6 −1` (1 import + 1 expresión + 4 líneas de comentario) |
| Import añadido | `from ..lots.service import _dia` (normalización canónica R-75 / GA-REM-028; sin ciclos — verificado) |
| Expresión | `age_days = (date.today() - _dia(lot.start_date)).days if lot and lot.start_date else 30` |
| Fórmula IPE | **INTACTA** (ningún término, redondeo, banda ni guarda modificada) |
| G-05 `production-index` | **NO tocado** (misma clase; candidato R-186 registrado aparte) |
| Migraciones / permisos / endpoints / frontend | **0 / 0 / 0 / 0** |

## 2 · Verificaciones locales ejecutadas

| Verificación | Resultado |
|---|---|
| Import del servicio + `_dia.__module__ == app.lots.service` (sin ciclo) | PASS |
| Reproducción determinista pre-fix: `TypeError: unsupported operand type(s) for -: 'datetime.date' and 'datetime.datetime'` | `evidence/red/typeerror-local.txt` |
| Expresión post-fix con modelo real: edad 19 (con inicio a 19 días) y 30 (sin inicio) | PASS |
| Gate backend canónico (OD-16 boundary + migración BU, filtro canónico) | **7 passed · 2 deselected** |
| Suite nueva `tests/test_r184_ipe_date_semantics.py` (PG; CI) | **10 skipped locales** (declarado; mecanismo `test_credentials`/`GA_TEST_ADMIN_PASSWORD`, idéntico a las suites de lotes GA-FE-06/07) |

## 3 · Gates frontend (§45 — sin cambios de código frontend)

| Gate | Resultado |
|---|---|
| `npx tsc -b --noEmit` | **PASS** |
| `npm run build` | **PASS** (1.67 s; único warning = `INEFFECTIVE_DYNAMIC_IMPORT` preexistente) |
| `npx vitest run` | **280/280 PASS** |

## 4 · Contrato verificado por la suite (PG/CI)

Camino feliz determinista (esperado calculado a mano = 33333.3), estabilidad entre llamadas, clamp del mismo día (1), legado sin inicio (30), guarda `fcr > 0` sin división por cero, 404 inexistente/ajeno/sin concesión, 403 sin RBAC, BU-OFF 404 y actor global sin bypass de BU-OFF (OD-16).
