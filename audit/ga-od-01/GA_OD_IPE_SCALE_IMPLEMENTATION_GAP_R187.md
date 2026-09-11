# R-187 · P2 · OPEN — IPE G-06: ESCALA INFLADA (×100) vs REGLA RATIFICADA OD-22

## Identificación

- **Finding**: **R-187** (siguiente libre tras R-186 CLOSED; disponibilidad verificada, sin colisión).
- **Severidad**: **P2** — corrección de negocio visible en un KPI de decisión productiva; sin impacto de datos/seguridad; sin migración.
- **Tipo**: Brecha de implementación vs regla de negocio ratificada (no es un defecto de código nuevo: el código hace lo que su definición histórica dice).
- **Hogar de evidencia**: `audit/ga-od-01/` (este registro + paquete completo de decisión).
- **Dueño**: tranche técnica futura (no iniciada; spec → AC → implementación → UAT del propietario).

## Contexto

La fórmula actual `ipe = (viabilidad × ganancia_diaria × 100) / (fcr × 10)`, con la viabilidad ya en porcentaje (95.0), aplica un **×100 duplicado** (fracción→porcentaje ya convertida). Resultado: **números ~100× las bandas** ⇒ clasificación visual poco informativa (casi todo «Excelente»; caso flojo real: 21315.8 → 🟢).

Evidencia: `GA_OD_IPE_UNIT_ANALYSIS.md` (`CONFIRMED_100X_SCALE_CONFLICT`; ratio 100.0 exacto en 3 casos) y `GA_OD_IPE_SCALE_EVIDENCE.md` (ejemplos A/B/C).

## Decisión que lo gobierna

**OD-22** (2026-09-11, Opción A — elección explícita del propietario): alinear el valor a la escala estándar/bandas; **bandas sin cambios**; **sin migración**. Ver `GA_OD_IPE_SCALE_OWNER_DECISION.md`.

## Alcance del trabajo pendiente (NO ejecutado)

1. Spec + AC del ajuste G-06 (retirar el `×100` sobrante; `reference`/bandas sin cambio; redondeo a definir en AC).
2. Implementación **backend-only** (una expresión + tests; sin migración; fórmula contract-compatible).
3. **UAT del propietario** (cambia el número mostrado en tarjeta/reporte IPE ⇒ UAT propia requerida).
4. Actualización de suites/evidencia (nota: con el FCR placeholder actual, el fixture 556.6 pasaría a 5.6 — limitación independiente ya documentada).

## Dedup

- **Distinto** de **R-184** (500 / date-datetime en G-06; cerrado) y de **R-186** (500 / date-datetime en G-05; cerrado): aquí no hay error HTTP, es escala de negocio.
- **Distinto** de R-131 / `GA-REM-022` (meta-clase «FCR = feed/1000»): relación de contexto (afecta al FCR de ambas fórmulas), no duplicado.
- **Sin dueño previo** de esta brecha: la observación vivió como `OWNER_DECISION_REQUIRED` sin finding hasta la decisión; la secuencia OBS→OD→finding se completa aquí.

## Fuera de alcance

- R-184 (NO se reabre) · R-186 (NO se reutiliza; cerrado) · FCR real/pesaje (limitación aparte) · bandas/UI/textos (sin cambio con la opción A).

## Estado

**`CLOSED_OWNER_ACCEPTED`** (2026-09-11 — tranche R-187: C2 `f755baa`; runtime E2E-01…14 PASS; aceptación del propietario **GA-UAT-07 → A) «ACEPTO R-187»**; evidencia `audit/ga-r187/` + `audit/ga-uat-07/`).

*(Histórico: abierto como P2 `OPEN` al ratificarse OD-22; implementado en R-187; aceptado en GA-UAT-07.)*
