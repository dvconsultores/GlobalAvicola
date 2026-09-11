# GA-R187 · EVIDENCIA FRONTEND

Fecha: 2026-09-11 · Producto frontend: **sin cambios (0 archivos)** · Bundle desplegado: `index-BUthrUt9.js` (idéntico a la línea base).

## 1 · Gates

| Gate | Resultado |
|---|---|
| `npx tsc -b --noEmit` | **PASS** (exit 0) |
| `npm run build` | **PASS** (`✓ built`) |
| `npx vitest run` | **280/280** (37 files) |
| `git diff -- frontend/` | **0 archivos** |

## 2 · Propiedad de la clasificación (recordatorio probado)

Frontend solo **muestra** `kpiIpe.ipe` y clasifica con los comparadores propios (`LotDetailPage.tsx:396-397` · `LotReportPage.tsx:167-168`, `>=300 🟢 / >=250 🟡 / resto 🔴`); **no recalcula** IPE ni duplica la fórmula (grep `ipe` en `frontend/src` = display + imports). Por eso OD-22 no toca frontend y las bandas permanecen idénticas.

## 3 · Verificación UI (resumen; detalle en evidencia runtime)

- Detalle del lote DET: tarjeta IPE visible con **333.3** · sin error crudo.
- Reporte del lote: **333.3** (consistente con detalle).
- Refresh y relogin: **333.3** estable (sin valor viejo de escala).
- Móvil 390×844: **333.3** legible; `scrollWidth−innerWidth = 0` (sin overflow); sin errores.
- Lista de lotes navegable (spot GA-FE-03).
- Capturas: `evidence/green/UI-desktop-lista-lotes.png` · `UI-desktop-detalle-DET.png` · `UI-desktop-reporte-DET.png` · `UI-mobile-detalle-DET.png`.
