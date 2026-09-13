# R-191 · SPEC — TRANSICIÓN DE FASE DEL LOTE POR UI (CRÍA → PRODUCCIÓN) CON CONTRATO REAL, ERROR VISIBLE Y ESTADO REFLEJADO

| Campo | Valor |
|---|---|
| **ID** | `R-191` · Tipo `FE↔BE CONTRACT + ERROR HANDLING REMEDIATION SPEC` · Prioridad **P1** · Estado `SPEC_READY` |
| **Hallazgo** | `R-191_FINDING.md` |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Fuente normativa** | `docs/02-functional-spec.md` §3.5 (fases cría/producción de reproductoras) y §3.4 (abuelas); `docs/03-domain-model.md` (`lot_phases`, `productive_phases`); `frontend/src/data/processCatalog.ts:312-321` (`resolveStageKey`) |
| **Decisiones intactas** | OD-16 (autoridad global fail-closed sobre unidad apagada: `_exigir_unidad_operativa`), OD-19, OD-23 = B, OD-25 = B, R-130 (saldo: única fuente `bird_movements`), BR-05/BR-07 |
| **Decisión del propietario** | **no requerida** para el núcleo; C-05 (poblaciones de inicio de fase derivadas del saldo por sexo) se propone con supuesto por defecto y se ratifica en UAT |
| **Migración** | ninguna (`lot_phases.is_active`/`end_date` existen; `productive_phases.code` existe) · **Endpoint nuevo** ninguno · **Permiso nuevo** ninguno |
| **Interdependencias** | P1-12 REAPERTURA (auditoría de `add_phase`), GA-GOV-03 (`test_l08_phases_*`), R-218/R-220 (consumidores de `phases`) |

## 1 · Contexto

`LotDetailPage` ofrece «Iniciar Producción» a lotes `breeder`/`grandparent` activos en cría (`:103-105,174-182`, permiso `lots:create`). La acción llama a `POST /lots/{id}/phases` (`router.py:136-147`, `LotPhaseCreate`). El cuerpo enviado no cumple el contrato; el error se silencia; la lectura de fases no permite saber en qué fase está el lote.

## 2 · Evidencia

`evidence/runtime-gp-e2e.json` `R-09-transicion-ui` (422 `lot_id`/`phase_id` missing; `toasts: []`); `evidence/ui-e2e-local-pass2.json` `GP2-16`; código en `R-191_FINDING.md §1.2`.

## 3 · Causa raíz

1. Cuerpo: `phase_code` (inexistente) y sin `lot_id` (`LotDetailPage.tsx:125-130`) vs `LotPhaseCreate` (`lots/schemas.py:98-109`).
2. Sin resolución de `phase_id`: no se consulta `GET /masters/productive-phases`.
3. `catch` ⇒ `console.error` (`:133-135`).
4. `LotPhaseRead` sin `phase {code,name}` (`lots/schemas.py:112-116`) ⇒ `activePhaseName` siempre `null` (`:90`) ⇒ etapa siempre cría.
5. `add_phase` no cierra la fase activa anterior (`lots/service.py:685-697`; `models.py:26`).

## 4 · Impacto de negocio

P-02/P-04 inalcanzables por UI; operador sin señal; historia de fases inconsistente para cierre e indicadores; datos de fase incorrectos para la fuente futura SAP.

## 5 · Comportamiento actual

Clic → modal → confirmar → `POST` con cuerpo inválido → 422 → nada visible → botón sigue → si (por API) se añadiera la fase `PROD`, la UI seguiría mostrando «Cría» (sin código de fase en la lectura; dos fases activas).

## 6 · Comportamiento esperado

1. Al abrir el detalle, la UI carga `GET /masters/productive-phases?limit=100` (una vez; `masters:read`, que el rol con `lots:create` posee en los catálogos de semillas `seeds/test_seeds.py:126-134`; verificación en C1, C-02) y construye `fasePorCodigo`.
2. Al confirmar: `POST /lots/{id}/phases` con `{ lot_id, phase_id: fasePorCodigo('PROD').id, start_date, start_population_male?, start_population_female? }` — las poblaciones sólo viajan si el operador las escribió; si no, **se omiten** y el servidor las deriva (C-05).
3. Backend `add_phase`: en la misma transacción, cierra la fase activa anterior (`is_active = False`, `end_date = start_date` si estaba vacío) y crea la nueva activa; si el cuerpo omite poblaciones (o envía 0 en ambas), las deriva del saldo neto por sexo del lote (`Σ bird_movements` de entradas − salidas por `sex`, con la semántica `_suma_neta` de `validators.py:21-46`); rechaza `400` si el lote no está activo (BR-07) o si la fase pedida es la ya activa.
4. Respuesta `201 LotPhaseRead` **ampliada** (aditiva) con `phase: { id, code, name }`; `GET /lots/{id}/phases` igual.
5. UI: `toast.success`, refetch de `phases` **y** del lote; badge «Producción»; botón «Iniciar Producción» oculto (`canTransition` falso); acciones rápidas del catálogo de producción (`STAGE_OPERATIONS.grandparent_production` / `breeder_production`).
6. Error (400/403/404/422): `toast.error(getErrorMessage(err, t('lots.transitionError')))`; modal cerrado; botón habilitado de nuevo.
7. `resolveStageKey` recibe `activePhase.phase.code` (`PROD`) además del nombre; la expresión regular existente sigue admitiendo nombres.

## 7 · Alcance

`LotDetailPage.tsx` (carga de fases maestras, cuerpo, toasts, refetch, `activePhaseName` por código), `lots/schemas.py` (`ProductivePhaseRef`, `LotPhaseRead.phase`), `lots/service.py::add_phase` (cierre de fase anterior, derivación de poblaciones, guardas), `lots/router.py` (sin cambio de ruta; `response_model` ya `LotPhaseRead`), i18n, pruebas RED/GREEN, E2E, UAT.

## 8 · Fuera de alcance

Transiciones distintas de cría → producción (engorde/incubación no tienen botón); edición/borrado de fases; auditoría de `add_phase` (P1-12 REAPERTURA); `test_l08_phases_*` (GA-GOV-03); homogeneización de códigos `ENG/INC` vs `ENGORDE/INCUB` en semillas (residual documentado, C-07); vista semanal (R-218); cierre de lote (R-192).

## 9 · Impacto frontend

`frontend/src/pages/lots/LotDetailPage.tsx`: `:44-73` (carga adicional de `productive-phases`), `:88-93` (código de fase), `:121-138` (cuerpo, toasts, refetch de lote), `:466-507` (modal: placeholders desde poblaciones derivadas si se desea mostrar). Claves i18n: reutiliza `lots.transitionError`, `lots.transitionToProduction`; nueva `lots.transitionSuccess`. Sin nuevas rutas.

## 10 · Impacto backend

- `backend/app/lots/schemas.py`: `class ProductivePhaseRef(BaseModel): id:int; code:Optional[str]; name:str` (+`from_attributes`); `LotPhaseRead.phase: Optional[ProductivePhaseRef] = None`.
- `backend/app/lots/service.py::add_phase` (`:685-697`): cierre de la anterior; derivación de poblaciones; guardas (`lot.status == ACTIVE`, fase distinta de la activa).
- Helper nuevo en `lots/service.py` (o `operations/validators.py`): `saldo_por_sexo(db, lot_id) -> dict[str,int]` reutilizando `_suma_neta` por columna con filtro `BirdMovement.sex`.
- Sin cambio en `router.py` salvo, si procede, docstring.

## 11 · Contrato frontend↔backend

**Petición** `POST /api/v1/lots/{lot_id}/phases` (`lots:create`):

| Campo | Tipo | Obligatorio | Nota |
|---|---|---|---|
| `lot_id` | int | sí | debe coincidir con la ruta (`router.py:143-145`) |
| `phase_id` | int | sí | id de `productive_phases` (resuelto en cliente por `code == 'PROD'`) |
| `start_date` | date (YYYY-MM-DD) | sí | ≥ `lot.start_date` (guarda nueva, 400) |
| `start_population_male` / `_female` | int ≥ 0 | no | si ambos ausentes o 0 ⇒ derivados del saldo por sexo |
| `start_weight_avg` | float | no | sin cambio |

**Respuesta** `201`:

```json
{ "id": 12, "lot_id": 66, "phase_id": 2, "start_date": "2026-09-13", "end_date": null,
  "start_population_male": 40, "start_population_female": 60, "start_weight_avg": null,
  "is_active": true, "created_at": "…", "phase": { "id": 2, "code": "PROD", "name": "Producción" } }
```

`GET /api/v1/lots/{lot_id}/phases` devuelve la lista con el mismo objeto (la fase anterior con `is_active: false` y `end_date` fijado). **Errores**: `400 {"detail": "…"}` (lote no activo; fase ya activa; fecha anterior al inicio; `lot_id mismatch`), `403` (sin permiso / unidad apagada para autoridad global, OD-16), `404` (lote no alcanzable), `422` (cuerpo inválido).

## 12 · Impacto en datos

Filas nuevas en `lot_phases`; actualización de `is_active`/`end_date` de la fase anterior **sólo** al crear una nueva. Sin migración. Lotes que hoy tengan dos fases activas por altas históricas vía API: se documentan (consulta de reconciliación en C3) y no se corrigen automáticamente (C-06).

## 13 · Seguridad

Sin nueva superficie. `add_phase` ya exige lote alcanzable y unidad operativa (`service.py:692`); las guardas nuevas sólo restringen.

## 14 · Inquilino

`get_lot` acota a la empresa efectiva; `productive_phases` es catálogo global (`masters`). Sin cambio.

## 15 · Unidad de negocio

`_exigir_unidad_operativa` intacta (OD-16 fail-closed; `test_l08`/`l09` semántica vigente).

## 16 · RBAC

`lots:create` (ruta y botón, `LotDetailPage.tsx:174`); lectura de catálogo `masters:read` (C-02: si algún rol real con `lots:create` careciera de `masters:read`, alternativa B sin permiso nuevo: `LotPhaseCreate.phase_code` opcional resuelto en servidor). Sin permiso nuevo.

## 17 · Transacciones

Cierre de la fase anterior + alta de la nueva + derivación del saldo en **una** transacción de petición (`RutaTransaccional`); bloqueo de la fila del lote (`bloquear_saldo_del_lote`) antes de leer el saldo por sexo para evitar carreras con altas concurrentes.

## 18 · Auditoría

Sin cambio en este paquete: `add_phase` no audita hoy (E-10) y su cobertura se resuelve en **P1-12 (REAPERTURA)** con un único productor. R-191 deja el punto de extensión (`AuditService.log(... "PHASE_STARTED")`) documentado en el código sin activarlo, para no duplicar filas mientras el listener `after_flush` siga activo.

## 19 · i18n (ES/EN)

| Clave | ES | EN |
|---|---|---|
| `lots.transitionSuccess` (nueva) | Fase de producción iniciada | Production phase started |
| `lots.transitionError` (existente, `translation.json:890`) | Error al transicionar fase | Error transitioning phase |
| `lots.phaseAlreadyActive` (nueva, fallback del 400) | El lote ya está en esa fase | The lot is already in that phase |

Mensajes del servidor mostrados tal cual (`detail` string); listas 422 normalizadas por `getErrorMessage`.

## 20 · Escritorio

Modal existente; tras éxito, badge «Producción» en cabecera y en «Registrar operación»; botón desaparece; sin recarga completa.

## 21 · Móvil

390×844: modal y toasts visibles; sin overflow; verificación en C3 (`R191-01m.png`).

## 22 · Manejo de errores

| Código | Situación | Comportamiento UI |
|---|---|---|
| 400 | lote no activo · fase ya activa · fecha < inicio · `lot_id mismatch` | `toast.error(detail)`; modal cerrado; botón habilitado |
| 401 | sesión | flujo global |
| 403 | sin `lots:create` (no debería llegar: botón oculto) · unidad apagada (global) | toast «sin permiso» (`getErrorMessage`) |
| 404 | lote no alcanzable | toast |
| 409 | (no aplica) | — |
| 422 | cuerpo inválido (imposible por construcción; cliente antiguo) | lista → texto |

## 23 · Impacto de migración

Ninguno.

## 24 · Impacto SAP

Ninguna llamada. La fase real del lote quedará disponible para consolidación por periodo/fase (P-08 futuro).

## 25 · Compatibilidad hacia atrás

- Clientes API que envían `lot_id`+`phase_id`+poblaciones: sin cambio (poblaciones explícitas se respetan).
- `LotPhaseRead` ampliado de forma aditiva (`phase` opcional): consumidores actuales (`LotDetailRead.phases`, `LotDetailPage`) no se rompen.
- Cierre de la fase anterior: nuevo efecto sólo al añadir fase (comportamiento correcto esperado por `is_active`).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| **AC-R191-01** | Lote `breeder` (y `grandparent`) activo en cría: «Iniciar Producción» por UI ⇒ `POST` con `lot_id` y `phase_id` de `PROD` ⇒ `201`; badge «Producción»; botón oculto; acciones rápidas de producción |
| **AC-R191-02** | Respuesta 400/403/404/422 ⇒ `toast.error` con `detail` legible; modal cerrado; sin `console.error` como única señal |
| **AC-R191-03** | El cuerpo nunca contiene `phase_code`; siempre `lot_id` y `phase_id` (unit) |
| **AC-R191-04** | Regresión: `test_lots_bu_enforcement.py::test_l09_control_*` (201 con `lot_id`+`phase_id`) verde; `test_l08_phases_*` según GA-GOV-03 |
| **AC-R191-05** | API: contrato de entrada intacto (`lot_id`+`phase_id`+poblaciones explícitas ⇒ 201 con esas poblaciones) |
| **AC-R191-06** | Tras `add_phase`, la fase anterior queda `is_active = false` con `end_date = start_date` de la nueva; exactamente una fase activa por lote |
| **AC-R191-07** | Poblaciones omitidas ⇒ derivadas del saldo neto por sexo (control: recepción 40♂/60♀ aprobada, mortalidad 5♂ aprobada ⇒ `35/60`) |
| **AC-R191-08** | `LotPhaseRead.phase = {id, code, name}` en `POST` y `GET` |
| **AC-R191-09** | Lote no activo ⇒ 400; fase ya activa ⇒ 400; `start_date < lot.start_date` ⇒ 400 |
| **AC-R191-10** | ES/EN: `lots.transitionSuccess` y `lots.phaseAlreadyActive` presentes |
| **AC-R191-11** | Móvil 390×844 usable |
| **AC-R191-12** | Sin migración/endpoint/permiso nuevo (diff) |
| **AC-R191-13** | Concurrencia: dos `POST` simultáneos ⇒ uno 201 y otro 400 (fase ya activa), nunca dos activas |
| **AC-R191-14** | Runtime: transición por UI en nube ⇒ 201 y estado visible; `GET /lots/{id}/phases` coherente |

## 27 · Pruebas (RED → GREEN)

- **Frontend** `frontend/src/pages/lots/__tests__/r191.phaseTransition.test.tsx` (jsdom; arnés de `gaFe06.lotFormContract.test.tsx` con mocks de api/toast/auth store): AC-01/02/03/10.
- **Backend** `backend/tests/test_r191_lot_phase_transition.py` (PG aislado; patrón `esc`): AC-05/06/07/08/09/13.
- **Regresión**: `test_lots_bu_enforcement.py` (l09 control), `test_lot_closure.py`, `test_lot_close_approval.py`, `test_population_invariant.py`; vitest completa, tsc, build.
- Diseño: `R-191_RED_E2E_UAT_DESIGN.md`.

## 28 · E2E

`E2E-R191-01…05` (nube, actores UAT-09; lote de abuelas en cría con recepción aprobada) — `R-191_RED_E2E_UAT_DESIGN.md §2`; artefactos `specs/R-191/evidence/runtime-c3/`.

## 29 · UAT

`UAT-R191-01…04` — `R-191_RED_E2E_UAT_DESIGN.md §3`.

## 30 · Criterios de cierre

AC-R191-01…14 verdes · RED leída en HEAD · GREEN local (backend PG + vitest + tsc + build) · sensibilidad tras commit · C3 con artefactos · UAT 4/4 · sin migración/endpoint/permiso · C-05 ratificada en UAT · R-191 `CLOSED` en backlog con GA-REM asignado · nota cruzada en P1-12 REAPERTURA (auditoría de `PHASE_STARTED` pendiente allí).
