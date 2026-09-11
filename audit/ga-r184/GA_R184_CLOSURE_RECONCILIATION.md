# GA-R184 · RECONCILIACIÓN DE CIERRE

## Mapa de extremo a extremo

| Eslabón | Artefacto / Verdad |
|---|---|
| 500 original en runtime | `evidence/red/runtime-red.json` (ipe/35 y ipe/33 → 500; controles 200) |
| Causa raíz | `date.today() - lot.start_date` (date − datetime aware) ⇒ TypeError; repro en `evidence/red/typeerror-local.txt` |
| Fórmula canónica | Preservada e intacta (traza de negocio §1; diff C2 sin cambios de fórmula) |
| Semántica temporal canónica | Día de calendario con `_dia(...)` (R-75/GA-REM-028; misma convención de `lots/service.py:379`) |
| Implementación | C2 `3f88f94` — 1 archivo, +6/−1 (matriz en `GA_R184_BACKEND_EVIDENCE.md`) |
| Pruebas | Suite PG/CI (10 casos) + verificaciones locales + batería runtime 14/14 |
| Evidencia runtime | `GA_R184_AUTHENTICATED_RUNTIME_EVIDENCE.md` + `evidence/green/` |
| Evidencia de seguridad | E2E-09/10/11/12 + OD-16 verificado |
| Consumidor frontend | USER_VISIBLE (UI validada: 556.6 visible, desktop+móvil) |
| AC | `GA_R184_CHECKLIST.md` — **todos PASS** |
| Resultado final | R-184 **CLOSED** |

## Preguntas explícitas

| Pregunta | Respuesta |
|---|---|
| 500 original reproducido | **YES** (runtime pre-fix ×2 + repro determinista del TypeError) |
| Causa raíz confirmada | `date − datetime` en `get_kpi_ipe` (columna `DateTime(timezone=True)`); no era serialización ni `planned_close_date` |
| ¿Mismatch date/datetime? | **YES** (probado, no asumido) |
| ¿Fórmula de negocio cambiada? | **NO** (preservada; sin tocar términos, redondeos ni bandas) |
| Petición IPE válida | **PASS** (200; valor determinista exacto 556.6 / 37894.7) |
| Comportamiento con datos ausentes | **PASS** (controlado: 0.0 documentado, sin fabricar positivos, sin 500) |
| Lote ajeno | **DENY** (404 «Lote no encontrado») |
| BU OFF | **DENY** (404; incl. actor global — OD-16) |
| RBAC | **DENY** (403 exacto) |
| Residual | **1 candidato registrado (R-186: G-05 producción-index, misma clase) + 1 observación de negocio (escala fórmula vs bandas)** — ambos fuera de alcance por regla §4, sin implementar |

## Estados del programa (sin reaperturas)

R-184: **CLOSED** · R-181/R-182/R-185/OD-21: sin cambio (verificado) · OBS-UAT-01: `UX_ENHANCEMENT_ONLY_P2` · BU-D10: `PENDING_RATIFICATION` · Wave B `PAUSED` · Wave C/SAP `NOT_STARTED`.
