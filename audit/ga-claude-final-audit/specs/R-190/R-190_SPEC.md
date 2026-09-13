# R-190 · SPEC — GALPÓN Y GRANJA DEL EVENTO EN EL ASISTENTE PARA TODOS LOS EVENTOS DE UBICACIÓN (BR-08)

| Campo | Valor |
|---|---|
| **ID** | `R-190` · Tipo `REQUEST CONTRACT REMEDIATION SPEC` · Prioridad **P1** · Estado `SPEC_READY` (sin código) |
| **Hallazgo** | `R-190_FINDING.md` |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Fuente normativa** | `docs/02-functional-spec.md` §3.5 (recepción/distribución por galpón), §3.6 (recolección por galpón); BR-08 (`validators.py:822-839`); RR-02 (`GA-REM-005`: distribución/traslado intra-lote, neutros); OD-25 (B) (lote autocreado sin galpón) |
| **Decisiones intactas** | OD-16, OD-19, OD-23 = B, OD-25 = B, R-130, BR-08, BR-17, BR-18, BR-20; F-01e (`house_id` de la recepción) |
| **Decisión del propietario** | **requerida** sólo para C-03 (alternativa B: persistir galpón en el lote al aprobar la primera recepción); la remediación principal (alternativa A) no la necesita |
| **Migración** | ninguna · **Endpoint nuevo** ninguno · **Permiso nuevo** ninguno |
| **Interdependencias** | R-205 (misma tranche; `onSubmit`/`stage`), R-211 (galpón por fila), R-194 (etapa incubadora, excluida) |

## 1 · Contexto

El asistente `/operations/new` (`OperationFormPage.tsx`, único `onSubmit`, `POST /api/v1/operations`) construye `farm_id`/`house_id` del evento a partir del lote seleccionado. Desde `OD-25 (B)` los lotes de abuelas nacen sin galpón, y `LotFormPage` permite crear lotes sin galpón. F-01e (R-189) resolvió el caso de la recepción; el resto de eventos de ubicación sigue enviando el cuerpo sin `house_id` (o sin `farm_id` en la inspección de granja) y el backend, correctamente, responde `400 BR-08`.

## 2 · Evidencia

Véase `R-190_FINDING.md §1`. Resumen: runtime `evidence/runtime-gp-e2e.json` (`R-08-distribucion`, `R-08-salida`, `R-10-recoleccion`, `R-08-inspeccion`) y local `evidence/ui-e2e-local-pass2.json` (`GP2-14/15/17`); código `OperationFormPage.tsx:385-394,438` y `validators.py:822-839`.

## 3 · Causa raíz

1. `derivedHouseId` (`OperationFormPage.tsx:387-394`) sólo resuelve galpón alternativo para `farm_inspection` y `bird_reception`.
2. Cuatro tipos de `location_events` no capturan galpón en la UI (`bird_exit`, `egg_collection`, `egg_dispatch`, `transport_inspection`).
3. Dos tipos lo capturan por fila y no lo mapean (`bird_distribution`, `bird_transfer`).
4. `farm_id` de `farm_inspection` depende del selector de granja no obligatorio (`:386,438,2060-2071`).
5. No hay validación en cliente: el `superRefine` (`:178-187`) sólo exige `lot_id`.

## 4 · Impacto de negocio

Cadena P-01/P-02 cortada tras la recepción para los lotes canónicos `OD-25 (B)`; P-03/P-04/P-06 afectados para lotes creados sin galpón. Sin rodeo dentro del producto. Datos de SAP incompletos (P-08).

## 5 · Comportamiento actual

| Evento | Fuente de `house_id` hoy | Fuente de `farm_id` hoy | Resultado con lote sin galpón |
|---|---|---|---|
| `bird_reception` | lote → primer `target_house_id` (F-01e) | selector granja → lote | 201 (F-01e) |
| `bird_distribution` | lote | selector granja → lote | **400 BR-08** |
| `bird_transfer` | lote | ídem | **400 BR-08** |
| `bird_exit` | lote | ídem | **400 BR-08** |
| `egg_collection` | lote | ídem | **400 BR-08** |
| `egg_dispatch` | lote | ídem | **400 BR-08** |
| `transport_inspection` | lote | ídem | **400 BR-08** |
| `farm_inspection` | primera fila inspeccionada → lote | selector granja (no exigido) | **400 BR-08** «requiere una granja» si el selector queda vacío |
| `egg_reception_hatchery`, `chick_dispatch` | lote | `undefined` (etapa incubadora, `:438`) | 400 BR-08 — **R-194** |

## 6 · Comportamiento esperado

Regla única de derivación en el asistente para todo `event_type ∈ location_events` (excluida la etapa incubadora, R-194):

1. **`house_id` del evento** = `lot.house_id` si el lote lo declara (el lote manda, como en F-01e); si no:
   - `bird_reception`, `bird_distribution`: primer `target_house_id` declarado en las filas de distribución;
   - `bird_transfer`: `source_house_id` de la fila 0, o en su defecto `target_house_id` (C-04);
   - `bird_exit`, `egg_collection`, `egg_dispatch`, `transport_inspection`: nuevo selector **«Galpón del evento»** (`house_id` del formulario, ya declarado en el esquema `:88`), alimentado con `farmHouses` (`:291-298`);
   - `farm_inspection`: primera fila inspeccionada (sin cambio).
2. **`farm_id` del evento** = `selectedFarmId` ?? `lot.farm_id` ?? `farm_id` del galpón resuelto (catálogo `houses` ya cargado, `:364`).
3. **Bloqueo en cliente** (`superRefine`): si tras la derivación faltan `farm_id` o `house_id` para un evento de ubicación, el envío no viaja y se muestra el mensaje `operations.eventHouseRequired` / `operations.farmRequired` junto al control correspondiente. El `400 BR-08` del servidor sigue existiendo y sigue mostrándose de forma segura si un cliente antiguo lo provoca.
4. El backend **no cambia** (BR-08 intacta; RR-02 intacta; BR-17 según R-211).
5. Alternativa B (C-03, decisión del propietario): además de lo anterior, persistir `house_id` en el lote al aprobar la primera recepción cuando el lote no lo tenga. **No forma parte del alcance por defecto**.

## 7 · Alcance

- `OperationFormPage.tsx`: derivación unificada (`derivedHouseId`/`derivedFarmId`), selector «Galpón del evento» en cuatro tipos, `superRefine` de ubicación, mensajes.
- `operationPayload.ts`: helper puro `resolverUbicacionDelEvento(eventType, lote, filas, houseSeleccionado, catálogoGalpones)` (testeable en unit sin DOM).
- i18n ES/EN: tres claves nuevas.
- Pruebas RED/GREEN (unit jsdom camino real, unit del helper), E2E runtime, UAT.

## 8 · Fuera de alcance

Etapa incubadora (`egg_reception_hatchery`, `chick_dispatch`, `egg_reception_classification`…) → **R-194**. Capacidad por galpón → **R-211**. Cuadre BR-20 y `stage` → **R-205**. Persistir galpón en el lote (C-03) salvo decisión. Cambios en BR-08, RR-02, OD-25. Edición (`PUT /operations/{id}`) de galpón: sin pantalla de edición de ubicación en el alcance (residual R-220). SAP.

## 9 · Impacto frontend

- `OperationFormPage.tsx:385-394` (derivación), `:436-451` (payload), `:178-187` (`superRefine`), casos `bird_exit` (`:869-989`), `egg_collection` (`:1046-1081`), `egg_dispatch` (`:1083-1185`), `transport_inspection` (`:1352-…`): añadir el selector.
- `operationPayload.ts`: nuevo helper puro.
- `public/locales/{es,en}/translation.json`: `operations.eventHouse`, `operations.eventHouseRequired`, `operations.farmRequired`.
- Sin rediseño; sin nuevas rutas.

## 10 · Impacto backend

Ninguno en producto. Sólo pruebas de control (BR-08 sigue devolviendo 400 por API sin `house_id`).

## 11 · Contrato frontend↔backend

Petición `POST /api/v1/operations` (`OperationalEventCreate`, `schemas.py:186-192`), campos relevantes:

| Campo | Tipo | Regla R-190 |
|---|---|---|
| `event_type` | str | uno de `location_events` (`validators.py:828-832`) |
| `lot_id` | int | obligatorio salvo inspecciones (`service.py:828-830`) |
| `farm_id` | int | **siempre presente** para eventos de ubicación (derivado según §6.2) |
| `house_id` | int | **siempre presente** para eventos de ubicación (derivado según §6.1) |
| `bird_movements[i].target_house_id` / `source_house_id` | int | se conservan tal cual (detalle por fila; tenencia `service.py:863-867`) |

Respuesta: `201` `OperationalEventRead` (`schemas.py:256-266`) sin cambio. Errores: `400` `{"detail": "...", "rule": "BR-08"}` sólo alcanzable por clientes que omitan la derivación.

## 12 · Impacto en datos

Ninguna columna nueva. Los eventos nuevos llevarán `house_id` poblado donde hoy fallaban; no se alteran eventos históricos. El lote no cambia (salvo C-03 = B).

## 13 · Seguridad

Sin cambio de superficie. La tenencia de `farm_id`/`house_id` y de los galpones por fila la sigue verificando el servidor (`service.py:844-848,863-867`, GA-REM-002). El cliente sólo filtra el catálogo por granja del lote (`farmHouses`); un galpón ajeno enviado por API se comporta como inexistente (BR-07).

## 14 · Inquilino

El catálogo de galpones proviene de `GET /masters/houses?limit=100` acotado a la empresa efectiva; nada nuevo. Sin autorización en el frontend.

## 15 · Unidad de negocio

Sin cambio: la unidad la deriva el servidor del lote (`_tipo_de_lote`, `exigir_unidad_operativa`). OD-16 y OD-23 = B intactas.

## 16 · RBAC

`operations:create` (ruta `/operations/new`, `App.tsx:260`, y `router.py:70-74`). Sin permiso nuevo.

## 17 · Transacciones

Sin cambio: una petición, una transacción (`RutaTransaccional`); el rechazo en cliente no genera petición.

## 18 · Auditoría

Sin cambio: el alta audita `created:registered` como hoy (duplicidad del listener → P1-12 REAPERTURA, no aquí).

## 19 · i18n (ES/EN)

| Clave | ES | EN |
|---|---|---|
| `operations.eventHouse` | Galpón del evento | Event house |
| `operations.eventHouseRequired` | Este evento requiere un galpón: elija uno o asígnelo al lote | This event requires a house: choose one or assign it to the lot |
| `operations.farmRequired` | Este evento requiere una granja | This event requires a farm |

Los mensajes del servidor (`detail`) se muestran tal cual (R-189). Sin texto fijo nuevo fuera de las claves.

## 20 · Escritorio

Selector «Galpón del evento» en la columna de contexto (junto a granja/lote) para los cuatro tipos; mensajes bajo el control; sin overflow horizontal a 1280×800.

## 21 · Móvil

Verificación 390×844: selector alcanzable con el teclado táctil cerrado, mensajes visibles sin desplazamiento horizontal; `SearchSelect` ya es táctil (`SearchSelect.tsx`).

## 22 · Manejo de errores

| Código | Situación | Comportamiento |
|---|---|---|
| bloqueo cliente | falta galpón/granja tras derivación | sin petición; mensaje junto al control |
| 400 | `BR-08` (cliente antiguo), `BR-07`, `BR-17` (R-211), `BR-18` | `getErrorMessage` → texto; sin React #31 |
| 401 | sesión expirada | flujo existente (GA-REM-003) |
| 403 | sin `operations:create` | ruta protegida (`CapabilityRoute`) + toast |
| 404 | lote/galpón inexistente para la empresa | se muestra `detail` (BR-07 «Lote no encontrado») |
| 409 | idempotencia (`idempotency_key`) | se muestra `detail` |
| 422 | cuerpo inválido (cliente antiguo) | lista FastAPI → texto (R-189) |

## 23 · Impacto de migración

Ninguno.

## 24 · Impacto SAP

Ninguna llamada. Los eventos aprobados con ubicación completa alimentan consolidación/exportación futura (P-08) con `farm_id`/`house_id` coherentes. SAP sigue siendo la fuente de registro futura.

## 25 · Compatibilidad hacia atrás

- Lotes con galpón: comportamiento idéntico (el lote manda).
- Clientes API que ya envían `house_id`: sin cambio.
- Eventos históricos: intactos.
- F-01e (`bird_reception`): intacta por construcción (misma regla, ampliada).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| **AC-R190-01** | Lote sin galpón + `bird_distribution` por UI con galpón destino en la fila ⇒ `POST` con `house_id` = galpón de la fila ⇒ `201` |
| **AC-R190-02** | Lote sin galpón + `bird_exit` por UI con «Galpón del evento» elegido ⇒ `house_id` presente ⇒ `201` |
| **AC-R190-03** | Lote sin galpón + `egg_collection` por UI con «Galpón del evento» ⇒ `201` |
| **AC-R190-04** | `farm_inspection` sin granja ⇒ **sin petición** y mensaje `operations.farmRequired`; con granja y galpón de fila ⇒ `201` con `farm_id` y `house_id` |
| **AC-R190-05** | Lote con galpón ⇒ `house_id` del evento = galpón del lote en todos los tipos (sin regresión; `f01e.receptionHouse` 4/4; R-189 29/29) |
| **AC-R190-06** | API sin `house_id` para un evento de ubicación ⇒ `400 BR-08` (backend intacto; `test_r26_error_contract.py` BR-08) |
| **AC-R190-07** | `bird_transfer` sin galpón en el lote ⇒ `house_id` = galpón origen de la fila 0 (C-04) ⇒ `201` |
| **AC-R190-08** | `egg_dispatch` y `transport_inspection` con «Galpón del evento» ⇒ `201` |
| **AC-R190-09** | Evento de ubicación sin ninguna fuente de galpón ⇒ **sin petición** y mensaje `operations.eventHouseRequired` (no se depende del 400) |
| **AC-R190-10** | `farm_id` derivado del galpón resuelto cuando el lote no declara granja y no hay selector (catálogo `houses`); nunca se inventa |
| **AC-R190-11** | ES/EN: claves nuevas presentes en ambos recursos; sin texto fijo |
| **AC-R190-12** | Móvil 390×844: selector y mensajes usables; overflow horizontal 0 |
| **AC-R190-13** | Sin migración, sin endpoint, sin permiso nuevo (diff) |
| **AC-R190-14** | Helper `resolverUbicacionDelEvento` cubierto por unit puro (tabla de tipos × fuentes) |
| **AC-R190-15** | Runtime: recorrido completo sobre lote autocreado (distribución → salida → recolección → despacho → inspección) `201` ×5, 0 fatales, 0 `5xx` |
| **AC-R190-16** | Errores 400/422 residuales siguen renderizándose como texto (regresión `f01.errorRendering`) |

## 27 · Pruebas (RED → GREEN)

- **Unit jsdom (camino real del formulario)**: `frontend/src/pages/operations/__tests__/r190.locationEventsHouse.test.tsx` (arnés de `f01e.receptionHouse.test.tsx`). RED en HEAD: `payload.house_id` `undefined`; selector «Galpón del evento» inexistente; `POST` disparado sin ubicación (AC-04/09).
- **Unit puro**: `frontend/src/pages/operations/__tests__/r190.resolverUbicacion.test.ts` (helper; RED: módulo/función inexistente).
- **Backend control (verde en HEAD, guarda de no-regresión)**: `backend/tests/test_r190_br08_contract.py` — BR-08 por API para `bird_distribution`/`bird_exit`/`egg_collection` sin `house_id` ⇒ 400; con `house_id` ⇒ 201.
- **Regresión**: `f01e.receptionHouse`, `f01.payloadContract`, `f01.errorRendering`, `receptionFormContract`, `f01d.serializers`; vitest completa (≥ 314), `tsc`, `build`; backend `test_r26_error_contract.py`, `test_edit_validation_parity.py::AC-R176-05b`, `test_submovement_structural_tenancy.py`.
- Diseño detallado: `R-190_RED_E2E_UAT_DESIGN.md`.

## 28 · E2E

Runtime nube (actores UAT-09, empresa 1) sobre el lote autocreado más reciente y sobre un lote con galpón (control): `E2E-R190-01…08` en `R-190_RED_E2E_UAT_DESIGN.md §2`. Artefactos en `audit/ga-claude-final-audit/specs/R-190/evidence/runtime-c3/` (journal JSON + PNG + payloads).

## 29 · UAT

`UAT-R190-01…05` (propietario) en `R-190_RED_E2E_UAT_DESIGN.md §3`.

## 30 · Criterios de cierre

AC-R190-01…16 verdes · RED leída en `c0b4afc` (o HEAD de C1) · GREEN local (vitest/tsc/build) · runtime C3 con artefactos · UAT 5/5 · R-189 recertificada (retry 7/7) · sin migración/endpoint/permiso · C-03 resuelta o explícitamente diferida por el propietario · finding R-190 → `CLOSED` en el backlog con el GA-REM asignado.
