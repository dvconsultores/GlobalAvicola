# R-206 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-206/evidence/`.

## 1 · Criterios de aceptación

| AC | Criterio | Test (RED) |
|---|---|---|
| AC-R206-01 | Importación con «Cuarentena» en blanco ⇒ **201** (campo omitido en el payload) | `r206.emptyOptional › quarantine` (rojo: `''` enviado) |
| AC-R206-02 | Importación con fecha ⇒ 201 (regresión, control) | `f01.payloadContract` (verde) |
| AC-R206-03 | `extra_data` numéricos ⇒ número o ausente (nunca cadena `''`) | `r206.serializer › numbers` (rojo) |
| AC-R206-04 | `sap_document_ref`/`vaccination_route` sin elegir ⇒ ausente (no `''`) | `r206.serializer › strings` (rojo) |
| AC-R206-05 | (Si C-02=A) API con `''` en opcional ⇒ 400/201 decidido y documentado | `test_r206_optional_tolerance` |
| AC-R206-06 | Sin migración/endpoint/permiso | revisión |
| AC-R206-07 | Regresión: `f01d.serializers`, `f01.payloadContract`, vitest completa, tsc, build | suites |

## 2 · Diseño RED

- Unit puro del serializador: `frontend/src/pages/operations/__tests__/r206.emptyOptional.test.ts` (tabla: entrada `''`/`'abc'`/número ⇒ salida canónica).
- jsdom: importación sin fecha de cuarentena ⇒ `post` con payload sin la clave (rojo en HEAD: `''`).
- Backend (si C-02=A): `test_r206_optional_tolerance.py`.
Ejecución: `npx vitest run …/r206.*`; salida a `evidence/red/`.

## 3 · E2E

`R206-RT-01…02` (UI local): importación con/sin fecha ⇒ 201; sonda API con `''` ⇒ comportamiento decidido. Artefacto `evidence/r206/runtime-{red,c3}.json`.

## 4 · UAT

`UAT-R206-01`: registrar una importación dejando la fecha de cuarentena en blanco ⇒ Guardado sin error (visible; 3 min).
