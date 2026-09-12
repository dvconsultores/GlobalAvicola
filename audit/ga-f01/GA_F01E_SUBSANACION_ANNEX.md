# GA-F01e · SUBSANACIÓN ANEXA — R-189 (galpón de la recepción: `house_id` del evento desde la fila declarada)

Fecha: 2026-09-13 · Tranche: remediación F-01 (retry GA-UAT-09) · Autoridad: mandato del propietario
«REMEDIATE F-01 COMPLETELY AND REPEAT GA-UAT-09» + directiva de continuación (§6: un AC fallido ⇒
FINDING → SPEC → AC → RED → IMPLEMENTACIÓN; sin hotfix).
Entrada: retry de certificación runtime sobre la generación C2d (`index-BwuucRxo.js`) —
lote autocreado `L-GP-2026-10` (id 64), recepción por UI ⇒ **400 BR-08**.

## 1 · Hecho observado (runtime, generación C2d)

- El recorrido completo UAT-01…05/07 es **verde** (29/29 asserts; F-01 certificado por UI; 0 pageerror; 0 respuestas 5xx). Artefactos: `evidence/runtime-c2d/`.
- **UAT-06 (recepción por UI) contra el lote autocreado `L-GP-2026-10` (`house_id` NULL)**:
  `POST /api/v1/operations` ⇒ **400** `{"detail":"El evento 'bird_reception' requiere un galpón asignado","rule":"BR-08"}`.
- Payload real capturado (mismo run):

```json
{"lot_id": 64, "event_type": "bird_reception", "farm_id": 1,
 "sap_document_ref": "PO-C001-GPR-0001",
 "bird_movements": [{"sex":"male","quantity":40,"avg_weight":3800,"target_house_id":1,"week_number":0},
                    {"sex":"female","quantity":60,"avg_weight":3600,"target_house_id":1,"week_number":0}],
 "egg_movements": [], "feed_movements": [], "hatchery_params": [], "inspection_details": [], "egg_storage_records": []}
```

  ⇒ **`house_id` ausente**, aunque el operador **sí eligió galpón** («Galpón 1 (cap. 5000)», `target_house_id: 1` en ambas filas).
- Controles: (a) sonda API con la misma forma ⇒ mismo 400; (b) calibración contra el lote 62 (`house_id=1`) ⇒ el payload UI **sí** lleva `house_id: 1` ⇒ el defecto es de **mapeo del formulario**, no del backend; (c) el backend sigue rechazando (no se debilita validación).

## 2 · Causa raíz

`OperationFormPage.onSubmit` · `derivedHouseId` (rama no-inspección) = `selectedLot?.house_id ?? undefined`:
el galpón capturado por fila (`bird_movements[i].target_house_id`, sección «Distribución por galpón») **nunca se mapea** al `house_id` del evento que `BR-08` exige y que `BR-17` (capacidad) evalúa.

Los lotes autocreados por `OD-25 (B)` **no tienen galpón** (mapa de campos R-153: `house_id = event.house_id`; la importación por UI no captura galpón) ⇒ el camino canónico «importar sin lote → aprobar → **recepcionar**» queda **inalcanzable por UI**.

Clase: misma familia R-189 («valor capturado que no llega al campo tipado que el dominio valida» — análoga a S2). Preexistente al tranche: el mapeo es anterior a C2/C2d; quedó oculto porque GA-UAT-09 se bloqueó en UAT-01 y UAT-06 nunca se ejecutó hasta este retry.

## 3 · Alcance de la subsanación (D1)

- `derivedHouseId` rama no-inspección, **solo `bird_reception`**:
  `selectedLot?.house_id ?? (primer `target_house_id` declarado en `bird_movements`) ?? undefined`.
- Frontera explícita: los demás tipos de evento **conservan su mapeo actual** (distribución/traslado no se reabren sin hallazgo propio).
- Nada más: **sin backend, sin migración, sin endpoint, sin permiso, sin UI nueva** (el galpón ya se captura y ya se muestra).

## 4 · Compatibilidad

- Lote CON galpón ⇒ el galpón del lote manda (idéntico a hoy) — AC-F01E-02.
- Sin galpón en lote ni en filas ⇒ ausencia (no se inventa) — AC-F01E-03.
- Importación (y demás tipos) sin cambio — AC-F01E-04.
- `BR-17` (capacidad) pasa a evaluar el galpón realmente elegido por el operador (semántica correcta de «alojar»).

## 5 · Criterios de aceptación (AC-F01E)

- **AC-F01E-01** recepción contra lote sin galpón: `house_id` del evento = primer galpón declarado en las filas (unit).
- **AC-F01E-02** lote con galpón: sin regresión (unit).
- **AC-F01E-03** sin galpón en ninguno: `house_id` ausente, sin inventar (unit).
- **AC-F01E-04** frontera: importación sin cambio (unit).
- **AC-F01E-05** runtime post-fix: recepción por UI contra lote nuevo ⇒ **201**; aprobación; población entra **una sola vez** (brackets 100/101).
- **AC-F01E-06** UAT-01…07 **7/7 en verde** en el retry (recorrido completo) + 0 fatales.
- **AC-F01E-07** suites verdes: vitest (310 + 4 nuevos), tsc, build.
- **AC-F01E-08** sin migración / endpoint / permiso nuevos (diff).

## 6 · Pruebas

- Unit: `frontend/src/pages/operations/__tests__/f01e.receptionHouse.test.tsx` — RED capturado (1×: `expected undefined to be 11`; `RED_frontend_f01e_raw.txt`) y GREEN tras D1.
- Runtime: re-ejecución del recorrido (`scripts_e2e_f01_retry.mjs`, modo live) sobre la generación post-fix → `evidence/runtime-c2f/`.

## 7 · Fuera de alcance

F-01b, F-01c · distribución/traslado (derivación de galpón) · OBS-2/3 · cualquier otro residual, AOD-06/AOD-24, Wave B/C, SAP.
