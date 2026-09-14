# GA-CLAUDE · R-210 — CERTIFICACIÓN (unidad única de peso: gramos)

Fecha: 2026-09-14 · Hallazgo **R-210** (P2 · integridad de dato) · Paquete `specs/R-210/` · Commits: C1 `6da1b3c` · C2 `5c1b5af` · C2s `0f587b1` · C-01 confirmatoria encolada (A=g por defecto).

## 1 · Fases

| Fase | Estado | Evidencia |
|---|---|---|
| **C1 · RED** | ✅ | FE `evidence/red/vitest-r210.log` — **3F/2P**: rótulos «(kg)» en pesaje y cierre, `step="0.001"`; controles verdes (sin conversión 2150 g; i18n sin kg). BE control `evidence/red/backend-r210-control.log` — **4/4** (curva en gramos, bordes inclusivos) |
| **C2 · Implementación** | ✅ | `evidence/green/` — FE **14/14** dirigidas; FE completa **380/380**; `tsc` 0 · commit `5c1b5af` |
| **C2s · Sensibilidad** | ✅ S1·S2 | S1 (rótulos a kg): 2F · S2 (`step 0.001`): 1F — `evidence/sensibilidad/` |
| **C3 · Runtime** | ⏸ pendiente | R210-RT-01/03 (etiqueta «(g)» y detalle en g en móvil/escritorio) — ventana de deploy |
| **UAT** | ⏸ | UAT-R210-01 (C-01 confirmatoria «la captura es en gramos») — cola del propietario |

## 2 · Implementación

- Rótulos: `Peso prom. (g)` (pesaje) y `Peso final prom. (g)` (cierre) — fallbacks realineados con la clave i18n que ya decía «(g)».
- `step="1"` en los inputs de `avg_weight` de pesaje y cierre (era `0.001`, herencia kg).
- Sin cambios de backend: curva/evaluación ya operan en gramos (control `evaluar` 4/4, bordes inclusivos).

## 3 · AC

| AC | Estado |
|---|---|
| AC-R210-01 (rótulos en g) | ✅ jsdom 01/01b · S1 |
| AC-R210-02 (step coherente) | ✅ jsdom 02 · S2 |
| AC-R210-03 (serialización sin conversión) | ✅ jsdom 03 (2150 → 2150) |
| AC-R210-04 (i18n sin «kg» en claves de peso) | ✅ jsdom 04 |
| AC-R210-05 (evaluación en g — control) | ✅ BE 4/4 |

## 4 · Veredicto

**R-210 = `CLOSED_TECHNICALLY`** — una sola unidad (gramos) en captura, etiqueta y evaluación; sin conversiones silenciosas. C3 runtime y confirmación C-01 en cola (no bloquean).
