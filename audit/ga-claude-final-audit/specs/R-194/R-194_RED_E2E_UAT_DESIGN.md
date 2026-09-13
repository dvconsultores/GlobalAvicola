# R-194 · DISEÑO DE PRUEBAS RED · E2E RUNTIME · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED

### 1.1 `frontend/src/pages/operations/__tests__/r194.hatcheryChain.test.tsx` (jsdom)

Arnés del asistente; lote incubadora `LOTE_HAT = {id:30, bird_type:'hatchery', farm_id:1, house_id:80, status:'active'}`; planta/granja/galpón/incubadora de fixture.

| Nombre exacto | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R194-01 · recepción sin BR-08 ni 422` | etapa incubadora; `egg_reception_hatchery`; rellenar recibidos 1000; guardar | `post` llamado y sin claves prohibidas; payload con ubicación/`arrival_date` — HEAD: 422 (arrival_date) / POST sin `farm_id` |
| `AC-R194-02 · fértiles en egg_movements` | ídem | `payload.egg_movements` contiene `{egg_type:'fertile', quantity:1000}` — HEAD: `[]` |
| `AC-R194-03 · carga con saldo` | `incubation_load` con 500 | `post` llamado — HEAD: sin petición |
| `AC-R194-04 · dosis válida envía; inválida muestra error` | `birth_registration`; dosis «0.2» ⇒ guardar; dosis «abc» ⇒ guardar | primer caso: POST; segundo: error visible y sin POST — HEAD: nunca POST |
| `AC-R194-06 · hatchery_id en filas` | seleccionar incubadora; guardar | `payload.hatchery_params[0].hatchery_id == 1` — HEAD: ausente |

### 1.2 Controles backend — `backend/tests/test_r194_hatchery_controls.py` (verde en HEAD)

- BR-03: recepción con fértiles 1000 + carga 1000 ⇒ 201; carga 1001 ⇒ 400 BR-03.
- BR-04: despacho ≤ viables ⇒ 201; exceso ⇒ 400.
- BR-08: según C-01 (A: sin granja ⇒ 400; B: exento).
- BR-21: nacimiento con sanos/débiles ⇒ 201.

Ejecución: `npx vitest run …/r194.*` ⇒ 5 rojos exactos; backend control verde; salida a `evidence/red/`.

## 2 · Diseño E2E runtime (C3)

Entorno nube o local estable; lote incubadora real (`HAT2-00` de la pila local o nuevo en nube).

| Caso | Pasos | Esperado |
|---|---|---|
| E2E-R194-01 | recepción de huevos por UI (1000) | 201; saldo fértil visible en carga |
| E2E-R194-02 | clasificación | 201 |
| E2E-R194-03 | carga 500 | 201 |
| E2E-R194-04 | ovoscopía + transferencia | 201 ×2 |
| E2E-R194-05 | nacimiento con sanos/débiles y dosis | 201; 0 bloqueos silenciosos |
| E2E-R194-06 | despacho de pollitos | 201; `ChickBatch` creado |
| E2E-R194-07 | verificación X-BU: vínculos en `TraceabilityTree` | `EggBatch`/`ChickBatch` completados |
| E2E-R194-07m/07en | repetición móvil/EN de recepción+despacho | usable; sin overflow |

Invariantes: `pageerror` 0; `5xx` 0; poblaciones/saldos coherentes con BR-02/03/04 (sondas). Artefactos: `evidence/runtime-c3/journal.json`, `R194-0x.png`, `payloads/`.

## 3 · Plan UAT del propietario (C4)

Guion ES, 25 min; rol operador de incubadora (escritorio + móvil); agrupable con R-190/R-205.

| Caso | Acción | Esperado |
|---|---|---|
| UAT-R194-01 | Registrar la recepción de huevos de una orden con fecha de llegada | Guardado sin error; la carga del día siguiente ve el saldo |
| UAT-R194-02 | Cargar una incubadora | Guardado; el saldo baja |
| UAT-R194-03 | Registrar un nacimiento (sanos/débiles) con dosis | Guardado; sin bloqueos |
| UAT-R194-04 | Despachar pollitos a una granja | Guardado; el vínculo aparece en trazabilidad |
| UAT-R194-05 | Repetir recepción y despacho en móvil/EN | Usable; etiquetas EN |

Criterio: 5/5, sin errores rojos.
