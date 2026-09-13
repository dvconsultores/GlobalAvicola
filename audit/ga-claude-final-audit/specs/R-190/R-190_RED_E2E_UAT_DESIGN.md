# R-190 · DISEÑO DE PRUEBAS RED · E2E RUNTIME · UAT

HEAD `c0b4afc` · Sin implementación en este documento.

## 1 · Diseño RED (unit / integración)

### 1.1 `frontend/src/pages/operations/__tests__/r190.locationEventsHouse.test.tsx` (jsdom, camino real)

Arnés: copia del de `f01e.receptionHouse.test.tsx:16-94` (mock de `services/api` con `get`/`post`, mock de `react-i18next` devolviendo el fallback, `ToastProvider`, helpers `porNombre`, `cambio`, `elegirEnSelector`, `guardar`). Fixtures:

```ts
const LOTE_SIN_GALPON = { id: 7, lot_code: 'L-GP-2099-01', farm_id: 1, house_id: null, status: 'active', bird_type: 'grandparent', start_date: '2026-01-01' }
const LOTE_CON_GALPON = { id: 8, lot_code: 'L-GP-2099-02', farm_id: 1, house_id: 55, status: 'active', bird_type: 'grandparent', start_date: '2026-01-01' }
const GALPON_11 = { id: 11, name: 'Galpón 1', farm_id: 1, capacity: 5000 }
const GALPON_12 = { id: 12, name: 'Galpón 2', farm_id: 1, capacity: 5000 }
const GALPON_55 = { id: 55, name: 'Galpón 55', farm_id: 1, capacity: 5000 }
const FARM = { id: 1, name: 'Granja Norte', code: 'GN' }
const TRANSPORTE = { id: 1, name: 'Camión', plate: 'ABC-123' }
```

Navegación: `montar()` con `initialEntries=['/operations/new']`, paso 1 «Progenitoras — Cría» (o «Progenitoras — Producción» para recolección/despacho), paso 2 botón `/<event_type>/`.

| Nombre exacto del `it` | Pasos | Aserción que **falla en HEAD** |
|---|---|---|
| `AC-R190-01 · lote SIN galpón + bird_distribution con galpón destino en la fila ⇒ house_id del evento = galpón de la fila` | lote 7; `elegirEnSelector(/Seleccionar galpón/, /Galpón 1/)` en la fila 0 (destino); cantidad 40; guardar | `expect(payload.house_id).toBe(11)` — HEAD: `undefined` |
| `AC-R190-02 · lote SIN galpón + bird_exit ⇒ selector «Galpón del evento» y house_id en el payload` | lote 7; `elegirEnSelector(/Galpón del evento/, /Galpón 1/)`; cantidad ♂ 10; guardar | `await screen.findAllByRole('button', { name: /Galpón del evento/ })` — HEAD: no existe (timeout) |
| `AC-R190-03 · lote SIN galpón + egg_collection ⇒ house_id en el payload` | etapa producción; lote 7; galpón del evento; fértiles 100; guardar | `expect(payload.house_id).toBe(11)` — HEAD: `undefined` |
| `AC-R190-04a · farm_inspection sin granja ⇒ sin POST y mensaje operations.farmRequired` | evento `farm_inspection`; fila con galpón 11 y temperatura 25; guardar | `expect(post).not.toHaveBeenCalled()` y `screen.getByText('operations.farmRequired')` — HEAD: POST viaja sin `farm_id` |
| `AC-R190-04b · farm_inspection con granja y galpón de fila ⇒ farm_id y house_id` | granja «Granja Norte»; fila galpón 11; guardar | `expect(payload.farm_id).toBe(1)`; `expect(payload.house_id).toBe(11)` — HEAD: `house_id` 11 pero `farm_id` 1 sólo si se elige granja (verde/rojo según variante; se conserva como control) |
| `AC-R190-05 · lote CON galpón ⇒ house_id del lote en distribución y salida` | lote 8; fila galpón 12; guardar | `expect(payload.house_id).toBe(55)` — HEAD: verde (control) |
| `AC-R190-07 · bird_transfer: lote SIN galpón ⇒ house_id = galpón origen de la fila 0` | lote 7; origen 11; destino 12; ♂ 10; guardar | `expect(payload.house_id).toBe(11)` — HEAD: `undefined` |
| `AC-R190-08a · egg_dispatch ⇒ house_id del selector` / `AC-R190-08b · transport_inspection ⇒ house_id del selector` | etapa producción / cría; lote 7; selector; datos mínimos; guardar | `expect(payload.house_id).toBe(11)` — HEAD: `undefined` |
| `AC-R190-09 · lote SIN galpón y sin galpón elegido ⇒ sin POST y mensaje operations.eventHouseRequired` | lote 7; `bird_exit` sin selector; ♂ 10; guardar | `expect(post).not.toHaveBeenCalled()` — HEAD: POST viaja |
| `AC-R190-11 · i18n ES/EN: claves de ubicación presentes` | lectura de `public/locales/{es,en}/translation.json` | `expect(es.operations.eventHouseRequired).toBeTruthy()` — HEAD: `undefined` |

### 1.2 `frontend/src/pages/operations/__tests__/r190.resolverUbicacion.test.ts` (unit puro)

Importa `resolverUbicacionDelEvento` de `../operationPayload` (HEAD: **no existe** ⇒ el fichero falla al importar; RED válida). Tabla `it.each` con ≥ 12 filas: (tipo, lote {farm_id, house_id}, filas, houseSeleccionado, catálogo) ⇒ `{ farm_id, house_id }` esperado; incluye: lote con galpón manda; distribución sin lote-galpón ⇒ primera fila; traslado ⇒ origen; salida ⇒ selector; sin fuente ⇒ `{ farm_id: 1, house_id: undefined }`; lote sin granja + galpón 11 ⇒ `farm_id` = 1 (del catálogo); etapa incubadora ⇒ sin cambio (frontera).

### 1.3 `backend/tests/test_r190_br08_contract.py` (control, verde en HEAD)

Patrón `esc` de `tests/test_reception_reconciliation.py` (empresa con `grandparent` ON, operador, granja, galpón, lote sin galpón). Casos: `test_r190_01_distribucion_sin_house_id_es_400_br08`, `test_r190_02_salida_sin_house_id_es_400_br08`, `test_r190_03_recoleccion_sin_house_id_es_400_br08`, `test_r190_04_con_house_id_declarado_es_201` (previa recepción de saldo). Aserción: `r.status_code == 400 and r.json()["rule"] == "BR-08"`; cero filas en `operational_events` para el lote tras el rechazo. Su función: probar que R-190 **no** debilita BR-08.

### 1.4 Ejecución de la RED

`cd frontend && npx vitest run src/pages/operations/__tests__/r190.*` ⇒ fallos exactamente en los `it` marcados «rojo»; salida completa a `evidence/red/vitest-r190.log`. `bash backend/scripts/run_tests.sh tests/test_r190_br08_contract.py` ⇒ 4/4 verde; salida a `evidence/red/backend-r190-control.log`.

## 2 · Diseño E2E runtime (C3)

Entorno: `https://avicola.globaldv.net` sobre la generación C2 (paridad bundle/backend verificada primero). Actores: operador de abuelas y aprobador de UAT-09 (credenciales en `~/ga_uat09_credentials.txt`, nunca en logs). Runner: extensión de `scripts_e2e_f01_retry.mjs` (Playwright, journal JSON, capturas, intercepción de `POST /api/v1/operations` para guardar payload y respuesta). Datos: lote autocreado más reciente sin galpón (o uno nuevo vía UAT-01…05 del retry) con saldo ≥ 100 aves tras recepción aprobada; galpones 1 y 2 de la granja 1; OC `PO-C001-GPR-0001`.

| Caso | Actor | Pasos | Resultado esperado (HTTP/UI) | Limpieza |
|---|---|---|---|---|
| E2E-R190-01 | operador | hub → Progenitoras cría → «Distribución de aves» → lote autocreado → fila galpón 1, ♂ 40 → guardar | `POST /operations` **201**; toast «Guardado»; payload con `house_id: 1`, `farm_id: 1` | evento queda `registered`; se anula al final (`POST /operations/{id}/cancel`) o se aprueba según ledger |
| E2E-R190-01m | operador | mismo caso a 390×844 | 201; sin overflow (`document.documentElement.scrollWidth <= 390`) | ídem |
| E2E-R190-02 | operador | «Salida de aves» → lote → «Galpón del evento» = Galpón 1 → ♂ 10 (sin transporte) → guardar | **201** (BR-01: 10 ≤ saldo) | anular al final |
| E2E-R190-03 | operador | Progenitoras producción → «Recolección de huevos» → lote → galpón → fértiles 100 → guardar | **201** | anular |
| E2E-R190-04 | operador | «Inspección de granja» sin elegir granja → fila galpón 1, T 25 → guardar | **sin petición**; mensaje «Este evento requiere una granja»; luego elegir granja → **201** | anular |
| E2E-R190-05 | operador | «Traslado de aves» → lote → origen 1, destino 2, ♂ 10 → guardar | **201**, `house_id: 1` | anular |
| E2E-R190-06 | operador | «Despacho de huevos» (tras E2E-R190-03 aprobado por el aprobador para tener saldo) → galpón → fértiles 50 → guardar; «Inspección de transporte» → galpón → guardar | **201** ×2 | anular |
| E2E-R190-07 | operador | control: lote 62 (con galpón) → distribución con fila galpón 2 | **201**, `house_id` = galpón del lote | anular |
| E2E-R190-08 | sonda API (token operador) | `POST /operations` `bird_distribution` sin `house_id` | **400** `rule: BR-08`; UI (repetición por UI con cliente actual) muestra texto | — |

Invariantes del run: `pageerror` = 0; respuestas `5xx` = 0; población del lote invariable tras anulaciones (control `GET /reports/kpis?lot_id`). Artefactos: `evidence/runtime-c3/journal.json`, `R190-0x.png`, `payloads/*.json`, `sonda-br08.json`.

## 3 · Plan UAT del propietario (C4)

Guion en español, 20 min, sobre la misma generación certificada en C3. Rol: operador de abuelas (móvil y escritorio).

| Caso | Acción del propietario | Resultado visible esperado |
|---|---|---|
| UAT-R190-01 | Desde el lote de abuelas creado por la importación, registrar una **distribución** eligiendo el galpón en la fila | «Operación guardada»; el evento aparece en el detalle del lote con el galpón |
| UAT-R190-02 | Registrar una **salida de aves** eligiendo «Galpón del evento» | Guardado sin error; el saldo del lote baja tras aprobar |
| UAT-R190-03 | Registrar una **recolección de huevos** eligiendo galpón | Guardado sin error |
| UAT-R190-04 | Intentar guardar una **inspección de granja** sin granja / una salida sin galpón | Mensaje claro bajo el control; nada se envía; tras completar, se guarda |
| UAT-R190-05 | Cambiar idioma a EN y repetir UAT-R190-02 en el móvil | Etiquetas en inglés; formulario usable; sin desplazamiento horizontal |

Criterio de aceptación UAT: 5/5 en verde, sin errores rojos del servidor, y confirmación del propietario sobre C-03 (A por defecto o B como anexo).
