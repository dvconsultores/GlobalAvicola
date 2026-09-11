# GA-OD-01 · TRAZA DE LAS BANDAS DE CLASIFICACIÓN ACTUALES

## 1 · Dónde viven las bandas (tres capas)

| Capa | Fuente | Contenido |
|---|---|---|
| Backend (contrato de respuesta) | `app/reports/service.py::get_kpi_ipe` → ``"reference": {"excellent": ">300", "good": "250-300", "average": "200-250"}`` | Bandas informativas (texto) |
| Frontend (cálculo de la insignia) | `LotDetailPage.tsx:396-397` y `LotReportPage.tsx:167-168` | Umbrales hardcodeados: `ipe >= 300` ⇒ 🟢 · `ipe >= 250` ⇒ 🟡 · resto ⇒ 🔴 |
| i18n (etiquetas visibles) | `frontend/public/locales/es|en/translation.json` → `kpi.excellent` = «Excelente/Excellent» · `kpi.good` = «Bueno/Good» · `kpi.average` = «Regular» | Textos |

## 2 · Estructura real de clasificación

```
IPE > 300        → 🟢 «Excelente»
IPE 250 – 300    → 🟡 «Bueno»
IPE 200 – 250    → 🔴 «Regular»   (la rama «average» del contrato)
IPE < 200        → 🔴 «Regular»   (mismo texto visible; el frontend solo tiene 3 ramas)
```

## 3 · Interpretación de la escala

Las bandas (200/250/300) corresponden a la **escala EPEF convencional** del Índice de Producción Europeo (valores típicos del sector ~200-400). El propio texto de referencia del contrato usa esa escala.

## 4 · Coherencia con la fórmula

Ver `GA_OD_IPE_CURRENT_FORMULA_TRACE.md` §4: la fórmula implementada opera ~×100 por encima de esa escala ⇒ **las dos capas no comparten unidad**. Con datos reales, casi todo valor cae por encima de 300 ⇒ clasificación sistemáticamente «Excelente» (véase ejemplo C en la evidencia).

## 5 · Propiedad y cambios futuros implicados

- Opción A (alinear valor a las bandas): **solo cambia la fórmula**; back-end reference, umbrales del FE y traducciones **no se tocan**.
- Opción B (reescalar bandas ×100): requiere cambiar **backend reference + umbrales FE (300→30000, 250→25000) + textos** (o dejar textos pero con nuevos números) — tres capas.
