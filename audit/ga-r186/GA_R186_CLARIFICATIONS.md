# GA-R186 · CLARIFICACIONES (C01–C20)

| # | Pregunta | Respuesta canónica | Fuente |
|---|---|---|---|
| C01 | Ruta exacta | `GET /api/v1/reports/kpis/production-index` (`lot_id` requerido) | `reports/router.py:106` |
| C02 | Permiso exacto | `reports:read` (0 permisos nuevos) | íd. |
| C03 | Esquema de respuesta | 7 claves + `unit:"index"` (ver spec §7) | `service.py:610-617` |
| C04 | Fórmula G-05 | `(avg_weight_g × viability_pct) / (age_days × FCR × 10)` (contrato ejecutable) | docstring+implementación; nota `×10` registrada |
| C05 | Distinción G-05/G-06 | Distinta fórmula, distinto filtro de peso, distinto fallback de FCR, distinto clamp | traza de negocio §2 |
| C06 | Entradas de fecha | `Lot.start_date` + `date.today()` | traza temporal |
| C07 | Operandos exactos del fallo | `date` − `datetime` aware (línea 604) | repro local + runtime |
| C08 | Dominio DATE/DATETIME | **DATE** (día de calendario) | R-75/GA-REM-028; convención del repositorio |
| C09 | Regla de conteo | `(hoy − día_inicio).days`; sin inicio → 30 | contrato vigente preservado |
| C10 | Mismo día | 0 días ⇒ guarda ⇒ PI 0 (**sin clamp**) | contrato vigente |
| C11 | Sin `start_date` | fallback 30 (legado) | contrato vigente |
| C12 | Agregación vacía | N/A — endpoint de un solo lote (Query requerido) | router |
| C13 | Lote inválido en colección | N/A (no hay colección); lote único con datos ausentes ⇒ controlado | matriz |
| C14 | Denominador cero | guarda `(age_days × fcr) > 0`; FCR 0 ⇒ `or 1` | contrato vigente |
| C15 | Redondeo | avg 1d · viab 1d · fcr 2d · PI 1d | contrato |
| C16 | Filtrado tenant | `company_id` del actor + `_exigir_lote` | service |
| C17 | Filtrado BU | `lotes_alcanzables` (habilitada∧concedida; global por habilitadas — OD-16) | scope |
| C18 | Consumidor frontend | **API_ONLY** (solo campo de tipo sin usar) | grep FE |
| C19 | Owner UAT | **NOT REQUIRED** (nada user-visible cambia) | auditoría §18 |
| C20 | Criterio de cierre | 500 resuelto + fórmula preservada + determinista + seguridad + R-184 sin regresión | cierre |

Sin preguntas al propietario: ninguna ambigüedad de negocio nueva (la única pendiente —escala IPE— pertenece a G-06 y permanece intacta).
