# GA-R187 · EVIDENCIA DE RED (sanitizada)

Sin tokens, sin cabeceras `Authorization`, sin cookies. Fuente: `evidence/green/runtime-api.json` (statuses/paths/bodies) y `runtime-ui.json` (texto visible).

## 1 · Generación observada

| Momento | Observación |
|---|---|
| Pre-fix (committed R-184) | `GET /api/v1/reports/kpi/ipe/11` → **200** · `ipe 556.6` (régimen ×100) |
| Probe post-deploy (hoy) | `GET /api/v1/reports/kpi/ipe/11` → **200** · `ipe 5.6` ⇒ **generación nueva (f755baa) confirmada** |
| Bundle | `index-BUthrUt9.js` (sin cambio; frontend no tocado) |

## 2 · Peticiones representativas (empresa 1, BU ON durante la ventana)

```
GET  /api/v1/reports/kpi/ipe/54   → 200 {"lot_id":54,"viabilidad_pct":95.0,"avg_weight_g":2000.0,
                                       "ganancia_diaria_g":105.26,"age_days":19,"fcr":3.0,
                                       "ipe":333.3,"reference":{"excellent":">300","good":"250-300","average":"200-250"}}
GET  /api/v1/reports/kpi/ipe/11   → 200 {...,"ipe":5.6,...}      (antes: 556.6)
GET  /api/v1/reports/kpi/ipe/53   → 200 {...,"ipe":378.9,...}    (antes: 37894.7)
GET  /api/v1/reports/kpi/ipe/58   → 200 {...,"ipe":250.0,...}    (frontera 250 → 🟡 en UI)
GET  /api/v1/reports/kpi/ipe/59   → 200 {...,"ipe":300.0,...}    (frontera 300 → 🟢 en UI)
GET  /api/v1/reports/kpis/production-index?lot_id=11
                                  → 200 {"production_index":5.1,...}   (G-05 intacto)
```

## 3 · Negativos (gobernados)

```
GET /api/v1/reports/kpi/ipe/14          (empresa 3, actor empresa 1)      → 404 {"detail":"Lote no encontrado"}
GET /api/v1/reports/kpi/ipe/999999999                                     → 404 {"detail":"Lote no encontrado"}
GET /api/v1/reports/kpi/ipe/54          (sin concesión BU)                → 404 {"detail":"Lote no encontrado"}
GET /api/v1/reports/kpi/ipe/54          (sin reports:read)                → 403 {"detail":"Permiso requerido: reports:read"}
GET /api/v1/reports/kpi/ipe/54          (BU OFF, actor empresa)           → 404
GET /api/v1/reports/kpi/ipe/54          (BU OFF, actor global)            → 404
PUT /api/v1/lots/54 {"area_id":16}      (área inactiva, GA-FE-07)         → 400 {"detail":"Área inactiva","rule":"BR-07"}
```

## 4 · UI (texto visible observado)

- Detalle/reporte/refresh/relogin/móvil: contienen `333.3` junto a la tarjeta IPE; sin «Internal Server Error», sin `NaN`, sin `Infinity`.
- Móvil: `document.documentElement.scrollWidth − innerWidth = 0`.
