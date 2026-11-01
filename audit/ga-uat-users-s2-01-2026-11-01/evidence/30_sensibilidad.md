# 30 — Sensibilidad / mutación (GA-UAT-USERS-S2-01)

**IMPL SHA (restauración):** `464bd998542e609615f66f2acc13a39751ce24d9` · restauración tras cada mutación con `git restore --source=464bd99 -- <archivo>` + `git diff --stat 464bd99 -- <archivo>` vacío. El ejecutor (DeepSeek, MCP) aplicó las ediciones; Claude revisó el informe (suite real + diffs vacíos finales).

## Frontend — suite `frontend/src/pages/users/__tests__` (baseline 57 passed)
| Mut. | Cambio en `UsersPage.tsx` | Resumen | Tests que la detectan | Veredicto |
|---|---|---|---|---|
| M1 | Campo de contraseña siempre presente en edición + POST `/password` si `form.password` (vuelve el defecto) | 8 failed · 49 passed | FE-01, FE-02, FE-03, FE-04, FE-05, FE-07a/b/c | **DETECTADA** |
| M2 | Se elimina la validación de longitud (<8) | 1 failed · 56 passed | FE-06a | **DETECTADA** |
| M3 | Se elimina la validación de confirmación | 1 failed · 56 passed | FE-06b | **DETECTADA** |
| M4 | Se quita `autoComplete="new-password"` del alta | 1 failed · 56 passed | FE-07d | **DETECTADA** |
| M5 | El POST de clave nunca se envía | 2 failed · 55 passed | FE-06c, FE-06d | **DETECTADA** |

## Backend — `test_uat_users_s2_role_only` + vecinos (baseline 32 passed)
| Mut. | Cambio | Resumen | Tests que la detectan | Veredicto |
|---|---|---|---|---|
| M6 | `UserUpdate.model_config extra="forbid"` → `"ignore"` (el PUT descarta `password` en silencio) | 1 failed · 31 passed | BE-03 | **DETECTADA** |
| M7 | `change_password`: se anula «nueva ≠ actual» | 2 failed · 30 passed | BE-05 + `test_ac_id_06` | **DETECTADA** |
| M8 | auditoría del cambio de clave con `entity_type="user"` en vez de `"user_password"` | 1 failed · 31 passed | BE-07 | **DETECTADA** |

**Resultado:** 8/8 DETECTADAS · 0 sobrevivientes · restauración final: `git diff --stat 464bd99 -- frontend/src backend/app` vacío; suites objetivo de nuevo verdes (57/57 y 32/32).

```
SENSIBILIDAD=8/8_DETECTADAS · DIFF_VS_IMPL_SHA=0
```
