# R-207 · DISEÑO DE PRUEBAS RED · E2E · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

`frontend/src/pages/operations/__tests__/r207.reversalSurface.test.tsx` (jsdom; mock api).

| Nombre | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R207-01 · gate` | detalle de evento `approved`; sesión con/sin `reversals:create` | botón visible solo con permiso — HEAD: no existe |
| `AC-R207-02 · solicitar` | rellenar motivo ≥5; confirmar | POST `/reversals` con `{event_id, reason}`; estado muestra contrapartida — HEAD: sin acción |
| `AC-R207-03 · badge reversed` | evento `reversed` | badge con clase/estado `reversed` — HEAD: gris |
| `AC-R207-04 · motivo corto` | motivo «ok» | sin POST; mensaje — HEAD: n/a |

Ejecución: `npx vitest run …/r207.*` ⇒ rojos exactos; salida a `evidence/red/`.

## 2 · Diseño E2E (C3)

Pila local (motor P-07 de un nivel) o nube con el actor adecuado.

| Caso | Pasos | Esperado |
|---|---|---|
| RT-01 | detalle aprobado con/sin permiso | botón / sin botón; sonda API 403 sin permiso |
| RT-02 | solicitar reverso (motivo ≥5) | 201; contrapartida `pending_review` visible en `/review`; enlace |
| RT-03 | aprobar contrapartida | ambos `reversed`; badges y detalle; enlace bidireccional; móvil |
| RT-04 | motivo corto | validación; sin POST |
| RT-05 | solicitar sobre evento con contrapartida activa | 409 con mensaje claro |

Artefactos: `evidence/r207/runtime-{red,c3}.json` + PNG. Invariantes: 0 `5xx`; verificación de R-192 (cierre del lote tras el reverso) y R-193 (BR-18) documentada aquí o en sus paquetes.

## 3 · Plan UAT

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R207-01 | Intentar solicitar un reverso (con permiso) desde un registro aprobado | Botón disponible; modal claro |
| UAT-R207-02 | Completar la solicitud con motivo | Contrapartida visible en revisión |
| UAT-R207-03 | Aprobarla | Estado «Revertido» visible en listas y detalle; enlace al original |
| UAT-R207-04 | Repetir en móvil/EN | Usable; etiquetas EN |

Criterio: 4/4.
