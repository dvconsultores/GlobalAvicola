# GA-FE-06 · EVIDENCIA RED (pre-implementación)

Generación auditada (bundle de entrada, congelado): **`index-WUv1-F9o.js`** (LM 2026-09-11 13:07:24 GMT, ETag `"6aa3fd0c-322"`) — confirmado también en la corrida (`result.bundle`).

## 1. RED de contrato (vitest)

`frontend/src/pages/lots/__tests__/gaFe06.lotFormContract.test.tsx` — ejecutado contra el código actual:

| Caso | Resultado | Fallo objetivo |
|---|---|---|
| PLD capturada ⇒ viaja como `planned_close_date` | ❌ | `expected undefined to be '2026-10-01'` |
| Selector «Área» desde `/masters/areas` (sin IDs crudos) | ❌ | `Unable to find a label with the text of: Área` |
| Área elegida ⇒ `area_id` en payload | ❌ | íd. (no existe control) |
| Sin fecha/área ⇒ `null` explícito | ❌ | payload sin las claves (`{ lot_code: 'GA6-T1', …(7) }`) |
| **Control** · alta mínima intacta | ✅ | pasa (refleja el comportamiento actual correcto) |

Resumen: **4 failed / 1 passed** — salida íntegra en `evidence/red/vitest-red-summary.txt`.

## 2. RED runtime autenticado (bundle desplegado de entrada)

Actor **C** `ga6.operador` (empresa 1 · rol 52 · BU `broiler` efectiva), desktop 1440×900, alta real por UI con **«Fecha prevista de cierre» = 2026-12-01** rellenada en el formulario:

| Observación | Valor capturado |
|---|---|
| POST `/api/v1/lots` | **201** (el backend acepta; no valida lo que no le llega) |
| Claves del payload enviado | `bird_type, breed_id, farm_id, genetic_line_id, house_id, lot_code, sap_reference, start_date` — **sin `planned_close_date`, sin `area_id`** |
| Fresh GET `/api/v1/lots/17` | `planned_close_date: null` · `area_id: null` |
| Controles presentes (`<select>`) | `bird_type, farm_id, house_id, genetic_line_id, breed_id` — **sin área** |
| Consola | 0 errores |
| Lote testigo | id **17** `GA6-RED-2026091113:55` (queda registrado en el ledger; PLD nunca persistida) |

Artefacto: `evidence/red/runtime-red.json`.

## 3. Lectura (reconciliación)

**La pérdida es real, silenciosa y del frontend**: el usuario rellena la fecha, el formulario responde 201 y la fecha no existe en ningún salto posterior. `area_id` ni siquiera alcanza a capturarse. El SLA «lote próximo a cierre» queda por tanto sin datos de origen — exactamente el hallazgo R-182. Backend/esquema/migración/evaluador: correctos (trazas GA_FE_06_LOT_DATA_MODEL_TRACE.md y GA_FE_06_SLA_TRACEABILITY.md).

## 4. Qué debe cambiar el GREEN (mapeo 1:1)

1. Payload del alta: +`planned_close_date`, +`area_id` (valores o `null`).
2. Formulario: control «Área» alimentado por `/masters/areas?limit=100` (nombres; sin IDs crudos).
3. Detalle: fila «Cierre previsto» con el día ISO (`slice(0,10)`) cuando exista.
4. i18n: clave `lots.area` (ES/EN).
5. Sin cambios backend/migración/SLA/permisos.
