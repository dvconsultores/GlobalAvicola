# R-209 · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

### 1.1 `frontend/src/pages/operations/__tests__/r209.sapCodeSelectors.test.tsx` (jsdom)

Arnés del asistente; catálogo `SapReference {id:12, sap_code:'4500001234', doc_number:'4500001234'}`.

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R209-01 · bird_exit guarda el código de la OC` | paso a `bird_exit`; elegir OC en el selector interno; guardar | `payload.sap_document_ref == '4500001234'` — HEAD: `'12'` |
| `AC-R209-02 · feed_registration guarda el código de la OT` | `feed_registration`; elegir OT; guardar | `payload.feed_movements[0].sap_order_id == '4500009'` — HEAD: `'9'` |
| `AC-R209-03 · fallback sin código ⇒ ausente` | referencia `{id:5, sap_code:null, doc_number:null, ref_id:null}` | clave ausente/undefined — HEAD: `'5'` |

### 1.2 Backend control

`backend/tests/test_r209_sap_document_ref_contract.py`: crear recepción/salida con `sap_document_ref` código y verificar que `GET /reports/sap-comparison` la marca como matched por `sap_code` (verde en HEAD; guarda de contrato).

Ejecución: `npx vitest run src/pages/operations/__tests__/r209.*` ⇒ 2-3 rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E (C3)

Runtime o local UI; registro real de salida con OC y alimento con OT; captura del detalle mostrando la referencia; sonda API del comparativo.

| Caso | Pasos | Esperado |
|---|---|---|
| R209-RT-01 | salida de aves por UI con OC | payload con código; detalle muestra código |
| R209-RT-02 | alimento por UI con OT | ídem |
| R209-RT-03 | referencia sin código | campo ausente; sin id |
| R209-RT-04 | comparativo API | casa por código |

Artefactos: `evidence/r209/runtime-{red,c3}.json`, payloads, `inventory.txt` (históricos con id; consulta de lectura `sap_document_ref ~ '^\d+$'` acotada a la empresa de prueba).

## 3 · Plan UAT

**No requerida.** Verificación técnica informativa en la certificación (payload + comparativo + captura del detalle).
