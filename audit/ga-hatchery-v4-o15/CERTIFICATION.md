# CERTIFICACIÓN LOCAL — GA-HATCHERY-V4-O15-PREVIEW-UNKNOWN

Residual de `specs/018-cutover-hatchery-v4-non-incubables/spec.md` §8. Baseline `main == develop == 0c26662`.
Implementación `19b547b` (+ test de cierre de B5 en el commit siguiente). Sin migración; fórmulas V4/V3, BR-03, no incubables y reconciliación **no se tocan**.

## 1. O-15
```text
O-15 = P2 DATA SEMANTICS / UX · FIX_REQUIRED → CLOSED
```
**Causa raíz.** `CutoverService.preview()` acumulaba `eggs_in_process += derivados.get("eggs_in_process") or 0` y `chicks_available += _entero(...)`: `None → 0`.
Una fila UNKNOWN aportaba 0 y el chip presentaba una suma parcial (900) como total. La reconciliación por lote ya conservaba UNKNOWN.
**Capa dueña:** backend (agregado del summary del preview). El frontend solo pintaba el número recibido (`Number(x ?? 0)`).

## 2. Antes / después
| | Antes | Después |
|---|---|---|
| `summary.eggs_in_process` con [900, UNKNOWN] | `900` | `null` + `eggs_in_process_status = UNKNOWN` + `eggs_in_process_unknown_rows = 1` |
| `summary.chicks_available` con una fila UNKNOWN | suma parcial | `null` + `UNKNOWN` |
| Chips de incubadora | `Number(x ?? 0).toLocaleString()` | `Metric` (UNKNOWN visible, 0 conocido visible) |
| Preview por fila | sin «Huevos en proceso» | columna derivada «Huevos en proceso (derivado)»: A = 900, B = UNKNOWN |
Un único helper puro `_agregar_con_unknown` concentra la regla; el patrón (`valor` + `_status` + `_unknown_rows`) es el que ya usaba `historical_mortality`.

## 3. Semántica UNKNOWN (helper) — O15-01..05
| ID | Entrada | Resultado |
|---|---|---|
| O15-01 | `[900, 800, 0]` | 1700 |
| O15-02 | `[900, UNKNOWN, 0]` | UNKNOWN (no 900) |
| O15-03 | `[UNKNOWN]` | UNKNOWN |
| O15-04 | `[0, 0]` | 0 |
| O15-05 | `[]` | 0 (semántica vigente de «sin filas»: los chips de conteo parten de 0; no se inventa UNKNOWN) |
`NOT_APPLICABLE` no es UNKNOWN: aporta 0 (cubierto por `test_o15_09`, que cerró el mutante B5).

## 4. E2E del residual
| Caso | Resultado |
|---|---|
| E2E-O15-01 dos procesos: A = 900, B = UNKNOWN (fosa vacía) | fila A 900 · fila B UNKNOWN · chip UNKNOWN (sin «900») · API `null/UNKNOWN/1` — PASS |
| E2E-O15-02 completar B con 0 conocido (re-subida al mismo batch) | B = 1000 · chip 1.900 · `KNOWN`, 0 filas UNKNOWN — PASS |
| E2E-O15-03 control de cero | chip 0 y fila 0 (ni UNKNOWN ni vacío) — PASS |

## 5. Regresión (código = `19b547b`)
| Gate | Resultado | Evidencia |
|---|---|---|
| Backend completo | **1965 passed, 0 failed, 59 skipped** | `evidence/40_backend_full.log` |
| Frontend completo | **750 passed, 1 skipped** (124 archivos) | `evidence/41_frontend_full.log` |
| TSC / Build | PASS / PASS | `42_tsc.log`, `43_build.log` |
| E2E hatchery (P16 + Spec 018 + H4-FOSA + O15) | 17 passed | `evidence/30_e2e_hatchery.log` |
| E2E completa `--workers=1` | **223 passed, 0 failed** (13,5 min) | `evidence/44_e2e_full.log` |
| Sensibilidad | B1–B6, F1–F3: **9/9 detectados**; B5 sobrevivió a la primera y se cerró con `test_o15_09` (cae con el mutante, pasa restaurado) | `evidence/50_mutation_campaign.md`, `51_b5_closure.log` |
| Post-mutación | backend 264 passed · frontend 27 passed | `52_`, `53_` |
H4-FOSA-01..07 y las fórmulas ratificadas siguen en verde dentro de las corridas completas (fórmula `set − transferred − fosa`, BR-03, no incubables y V3 sin cambios).

## 6. Observaciones
- **O-16 (nueva, otras BU, NO se toca):** el summary del preview de progenitoras/reproductoras/engorde suma `accumulated_feed_kg` solo de las filas KNOWN y presenta la suma parcial sin marca (misma clase de defecto). Decisión de la Owner si se corrige en un ciclo propio.
- `live_birds` del summary de incubadora (= `chicks_available`) no se muestra en el chip de incubadora; no se modificó.
- O-11, O-12, O-13, O-14 y OPERATIONAL_MODEL_GAP: sin cambios.
