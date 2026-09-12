# GA-F01e · RED — RECEPCIÓN POR UI BLOQUEADA (BR-08) EN LOTES AUTOCREADOS

Fecha: 2026-09-13 · Generación: `index-BwuucRxo.js` (C2d) · Run: `evidence/runtime-c2d/retry-walkthrough.json`

## 1 · Observación (runtime, UI real — uat09-op)

| Paso | Resultado |
|---|---|
| Importación de abuelas por UI (sin lote) | **201** (evento 120) — F-01 verde |
| Aprobación P-07 (uat09-ap) | **approved**; lote autocreado **L-GP-2026-10** (id 64, `farm_id:1`, **`house_id: null`**) |
| Antes de recepcionar: mortalidad ×1 (sonda BR-01) | **400** «Mortalidad (1) excede el saldo de aves disponibles (0)» ⇒ aprobación no pobló |
| **Recepción por UI** (lote 64, granja/galpón elegidos: «Galpón 1 (cap. 5000)», ♂40 ♀60) | **400** `{"detail":"El evento 'bird_reception' requiere un galpón asignado","rule":"BR-08"}` |
| Formulario tras el 400 | Permanece montado; mensaje legible; **0 errores fatales** (F-01 S3 corregido) — `F03-recepcion-bloqueada.png` |

## 2 · Payload real capturado (POST /operations, recepción)

```json
{"lot_id": 64, "farm_id": 1, "sap_document_ref": "PO-C001-GPR-0001",
 "bird_movements": [{"sex":"male","quantity":40,"avg_weight":3800,"target_house_id":1,"week_number":0},
                    {"sex":"female","quantity":60,"avg_weight":3600,"target_house_id":1,"week_number":0}],
 "egg_movements": [], "feed_movements": [], "hatchery_params": [], "inspection_details": [], "egg_storage_records": []}
```

`house_id`: **ausente** (clave no enviada). El galpón elegido viaja solo como `target_house_id` por fila.

## 3 · Controles

- **Sonda API** (misma forma, sin `house_id`) ⇒ 400 BR-08 (idéntico).
- **Calibración** contra el lote 62 (`house_id=1`, autocreado por API con galpón) ⇒ el payload UI **sí** lleva `house_id: 1` (`/tmp/f01-calib/calib-walkthrough.json`) ⇒ defecto de mapeo del formulario, no del backend.
- El backend **sigue rechazando** (validación no debilitada); ningún dato se persiste con el 400.

## 4 · Artefactos

`evidence/runtime-c2d/`: `F03-recepcion-bloqueada.png`, `C06a-recepcion-formulario.png`, `retry-walkthrough.json` (POSTs sanitizados, asserts, errores) · unit RED: `evidence/f01e/RED_frontend_f01e_v2_raw.txt` (1× `expected undefined to be 11`).

**Corrección declarada (RED v1 → v2)**: la primera captura unit usó un arnés que pulsaba la etiqueta de fila «Galpón N» (`<span>`) en vez de la opción del desplegable (`<button>`), de modo que el galpón no llegaba a fijarse y la falla no aislaba el defecto. Arnés corregido; **RED v2 recapturado con el componente sin el arreglo**: la fila 105 (`target_house_id = 11`) pasa y la 106 (`house_id`) falla — exactamente el defecto. v1 se conserva (`RED_frontend_f01e_raw.txt`); v2 en `RED_frontend_f01e_v2_raw.txt`. No se reescribe el histórico.

## 5 · Lectura

Camino canónico `OD-25 (B)` (importar sin lote → aprobar → recepcionar) **inalcanzable por UI** en su último paso.
Causa: `derivedHouseId` no considera el galpón capturado por fila cuando el lote no declara uno (ver anexo `GA_F01E_SUBSANACION_ANNEX.md` §2). Sin tratamiento de hotfix: ciclo FINDING → SPEC → AC → RED → IMPLEMENTACIÓN.
