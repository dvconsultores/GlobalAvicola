# GA-R186 · EVIDENCIA RUNTIME AUTENTICADA (E2E-01…13 + R-184)

Generación congelada: backend con el fix **`0309225`** · bundle frontend sin cambio `index-BUthrUt9.js`. Actor principal: autoridad global (empresa 1) + actor autorizado `r186.kpi` (reports:read + concesión broiler); ventana BU ON durante la batería (restaurada OFF en limpieza). Evidencia cruda: `audit/ga-r186/evidence/green/runtime-e2e.json`.

## 1 · Batería (14/14 PASS)

| Caso | Petición | Resultado | Veredicto |
|---|---|---|---|
| E2E-01 | `production-index?lot_id=35` (daba 500) | **200** | PASS |
| E2E-01b | `production-index?lot_id=33` (daba 500) | **200** | PASS |
| E2E-02 | `?lot_id=11` determinista | esperado **{pesos_n 19, avg_raw 1363.157…, avg_round1 1363.2, age 110, viab 100.0, fcr 24.5, pi 5.1}** == actual exacto (esquema + `unit:index`) | PASS |
| E2E-02b | 2ª llamada | JSON idéntico | PASS |
| E2E-03 | semántica temporal | `start 2026-05-24` · edad real 110 == `age_days` (sin ±1) | PASS |
| E2E-04 | **mismo día** (lote 35, start hoy) | 200 · `age_days 0` · `production_index 0` (guarda; sin clamp — contrato G-05) | PASS |
| E2E-05 | sin `start_date` | **N/A probado**: no existen lotes sin inicio (el alta lo fija); cubierto por suite PG (edad 30) | N/A |
| E2E-06/07 | vacío / colección | **N/A probado**: endpoint de un solo lote (`lot_id` requerido) | N/A |
| E2E-08 | lote incompleto (sin datos) | 200 · `avg 0` · `viab 100.0` · `fcr 1` (`or 1`) · `pi 0` — controlado, sin NaN/∞ | PASS |
| E2E-09 | lote empresa ajena (c3, id 14) | **404** «Lote no encontrado» | PASS |
| E2E-10 | BU c1 OFF (actor concesionado) | **404** · restaurada ON ⇒ 200 | PASS |
| E2E-11 | sin concesión de unidad | **404** | PASS |
| E2E-12 | sin `reports:read` | **403** «Permiso requerido: reports:read» | PASS |
| E2E-13 | **global + BU OFF** | **404** (OD-16 absoluto) | PASS |
| E2E-R184 | `kpi/ipe/11` | **556.6** · edad 110 · esquema intacto — **G-06 preservado** | PASS |
| E2E-R184b | `kpi/ipe/35` | 200 (fix R-184 intacto) | PASS |

**Cálculo independiente de E2E-02**: media de `avg_weight` sobre **todos** los movimientos con peso de todos los eventos del lote (19 filas — semántica G-05 sin filtro de tipo de evento), mortalidad/feed desde `/reports/kpis`, edad desde `start_date`; fórmula documentada evaluada a mano — nunca derivada del código bajo prueba.

## 2 · Verificaciones transversales

- **Sin NaN/∞** en ningún caso; ningún 500 post-deploy.
- **Sin datos ajenos** en respuestas (404 anti-enumeración en todos los negativos).
- **Auditoría**: lectura pura sin efectos de escritura.
- **Rendimiento**: mismo SQL; el fix solo normaliza en Python.
- **Blip de deploy**: no observado en la ventana de captura (batería ejecutada con la generación nueva ya estable).
