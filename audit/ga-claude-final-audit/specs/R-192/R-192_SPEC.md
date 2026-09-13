# R-192 · SPEC — CIERRE DE LOTE CON REVERSOS EFECTIVOS, RESUMEN DE CIERRE NETO Y FEEDBACK DE ERROR EN LA UI DE CIERRE

Fecha: 2026-09-13 · Hallazgo canónico: **R-192** (P1 · bloquea) · HEAD `c0b4afc` · Origen: E-02, E-03 (`E_domain_ledger.md §1.3`), C-8 · Registro `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §1 G-03`. Secciones según el encargo §47 (orden obligatorio).

## 1 · Contexto

`OD-19`/`GA-REM-041` (certificada 2026-09-09) añadió el reverso interno de registros aprobados: la contrapartida aprobada deja **original y contrapartida en `REVERSED`**, estado terminal, no cancelable, con efecto neto 0 sobre los saldos (`validators.py:21-46 _suma_neta`). El cierre de lote (`POST /lots/{id}/close`, `lots/service.py:438-549`) aplica BR-05 (`validators.py:362-390`) y R7 (`R-76`, `validators.py:409-455`) y devuelve el resumen `LotClosureSummary` (`lots/schemas.py:264-282`). R7 fue escrita antes de `OD-19` y su conjunto de estados «aprobados» (`ESTADOS_APROBADOS`, `validators.py:400-406`) no contiene `REVERSED`. Los sumatorios del resumen no filtran estado. La UI de cierre (`LotDetailPage.tsx:107-118`) no muestra errores.

## 2 · Evidencia

Detallada en `R-192_FINDING.md §2-§3`. Resumen: `validators.py:436-438` (R7 excluye sólo `ESTADOS_APROBADOS ∪ {CANCELLED}`), `operations/service.py:76-78` (`REVERSED ∈ NO_CANCELABLES`), `reversals/service.py:215-216` (ambos `REVERSED`), `lots/service.py:469-498` (sumas sin filtro), `:511-514` (`approved_events`), `LotDetailPage.tsx:115` (`console.error`), `tests/test_lot_close_approval.py:34-42` (sin `REVERSED`). Runtime: `evidence/ui-e2e-local-pass1.json H8-*` (reverso efectuado, `cancel` 400; cierre bloqueado por BR-05 antes de R7 — no discriminante), «H8b (pasa 2)» (lotes gemelos, diseño `ui_e2e_local_pass2.mjs:527-559`).

## 3 · Causa raíz

1. Deriva de reglas: `REVERSED` nació (`OD-19`) sin reconciliar R7 (`R-76`) ni el resumen de cierre (`G-09`/`R-73`); ninguna prueba parametriza `REVERSED` en el cierre.
2. El resumen de cierre se calcula con sumatorios «históricos» (sin `status`) mientras que los saldos del dominio usan `≠ CANCELLED` y, desde `OD-19`, la aritmética neta.
3. `handleCloseLot` no adoptó el patrón `toast.error(getErrorMessage(...))` (ya presente en `LotDetailPage.tsx:79-81`).

## 4 · Impacto de negocio

- Lotes con reverso aprobado **no cierran** ⇒ ciclo de vida P-06 roto; el reverso (`OD-19`) deja de ser una operación segura.
- Resumen de cierre (dato de cierre, insumo de la futura fase SAP/informes de lote) con mortalidad, alimento y huevos **anulados o duplicados**.
- El operador/supervisor no sabe por qué no cierra (R7, BR-05, 403, 404): pérdida de confianza y tickets.

## 5 · Comportamiento actual

| Escenario | Hoy |
|---|---|
| Lote con todos los registros aprobados + 1 par revertido (`REVERSED`×2) | `close` ⇒ `400 R7` «2 registro(s) sin aprobar (2 en «reversed»). Apruébelos o anúlelos…» — imposible de resolver. |
| Lote con contrapartida **pendiente** (`PENDING_REVIEW`/`IN_REVIEW`) | `400 R7` (correcto: hay un registro vivo sin decidir). |
| Resumen con mortalidad cancelada (10) y aprobada (5) | `total_mortality = 15`. |
| Resumen con alimento revertido (7 kg, par `REVERSED`) | `total_feed_kg = 14.0`; `approved_events` no cuenta el par; `total_events` cuenta ambos. |
| UI: cierre rechazado | Modal se cierra, `console.error`, sin mensaje, botón sigue visible, lote `active`. |

## 6 · Comportamiento esperado

| Escenario | Esperado |
|---|---|
| Par revertido + resto aprobado | `close` ⇒ **200** con resumen; `status='closed'`, `end_date` fijada. `REVERSED` se trata como **estado terminal decidido** (no es «sin aprobar»). |
| Contrapartida pendiente (`PENDING_REVIEW`, `IN_REVIEW`, `CORRECTED`, `RETURNED`, `REJECTED`, `REGISTERED`) | `400 R7` (sin cambio): el detalle nombra el estado y la acción posible. |
| Resumen | `total_mortality`, `total_feed_kg`, `total_eggs` **excluyen** `CANCELLED` y `REVERSED` (original y contrapartida) ⇒ semántica **neta** equivalente a `_suma_neta` (ambos miembros del par están en `REVERSED`). `total_events` y `approved_events` sin cambio de definición (compatibilidad), salvo lo decidido en C-04. |
| BR-05 | Pesaje/alimento **vigentes** (`∉ {CANCELLED, REVERSED}`) — C-05. |
| UI | Rechazo ⇒ `toast.error(getErrorMessage(err, t('lots.closeError')))` con el `detail` del backend (R7/BR-05/403/404/409) legible; modal cerrado; lote sigue `active`; botón operativo; sin React #31. Éxito ⇒ tarjeta de resumen (sin cambio) + `toast.success` (opcional, C-06). |
| Mensaje R7 | Cuando lo pendiente son contrapartidas de reverso, el mensaje indica «reverso pendiente de decisión» (C-07). |

## 7 · Alcance

1. **Backend · R7** (`validators.py`): `validate_lot_records_approved` excluye también `REVERSED` (conjunto de «no gobernados» = `ESTADOS_APROBADOS ∪ {CANCELLED, REVERSED}`); docstring actualizado con la justificación `OD-19`.
2. **Backend · resumen** (`lots/service.py:469-498`): los tres sumatorios con `status.not_in([CANCELLED, REVERSED])`.
3. **Backend · BR-05** (`validators.py:362-390`): `not_in([CANCELLED, REVERSED])` (C-05, por defecto sí).
4. **Backend · tests**: `test_lot_close_approval.py` parametriza `REVERSED` (par real vía `reversals`, no sólo `_fijar_estado`); `test_lot_closure.py` cubre el resumen neto; helper `_reverso_efectivo` reutilizado de `test_internal_reversal.py:243`.
5. **Frontend · `LotDetailPage.handleCloseLot`**: error visible con `getErrorMessage`; estado local de error opcional para lectores de pantalla (`role="alert"`).
6. **Frontend · test** (vitest): render de `LotDetailPage` con `POST /lots/{id}/close` ⇒ 400 R7 ⇒ toast con el `detail`.
7. **Runtime**: certificación H8b (control 200 / con reverso 200 tras el fix) + UI (toast visible).

## 8 · Fuera de alcance

- Auditoría del cierre/activación/fases de lote (E-10 → `P1-12-REOPEN`).
- Resumen con FCR/peso final (`R-144`/AOD-08). No se añaden campos obligatorios al contrato.
- Reverso con superficie de usuario (`R-207`), reverso de consolidados/SAP (`OD-19 §11`, diferido), huevos (`R-161`, `OD-19 §18`).
- BR-18 tras reverso (`R-193`), KPI con filtro de estado (`R-214`/E-24), cancelación con motivo/rol (`R-140`).
- Transición de fase por UI (`R-191`), badges `reversed` en listados (`R-220`/C-27).
- Reapertura de lotes (`LotStatus.CLOSED → ACTIVE` no existe; `R-51`).

## 9 · Impacto frontend

`frontend/src/pages/lots/LotDetailPage.tsx` (`handleCloseLot :107-118`): `catch` ⇒ `toast.error(getErrorMessage(err, t('lots.closeError')))`; `useToast`/`getErrorMessage` ya importados (`:11,42`). Sin cambios de layout; la tarjeta `closeResult` (`:198-209`) se mantiene. Nuevo test `frontend/src/pages/lots/__tests__/r192.closeLotError.test.tsx`.

## 10 · Impacto backend

- `backend/app/operations/validators.py`: `validate_lot_records_approved` (`:436-438`) y `validate_lot_closure` (`:368-372, :380-384`).
- `backend/app/lots/service.py:469-498`: filtro de estado en los tres sumatorios (`OperationalEvent.status.not_in([EventStatus.CANCELLED, EventStatus.REVERSED])`).
- Sin cambio en `reversals/service.py`, `review/service.py`, rutas, esquemas ni permisos.

## 11 · Contrato frontend↔backend

`POST /api/v1/lots/{lot_id}/close` · permiso `lots:create` · cuerpo vacío · respuesta `200 LotClosureSummary` (`lot_id, lot_code, age_days, total_mortality, total_feed_kg, total_eggs, total_events, approved_events, status, end_date`) **sin cambio de forma**; semántica de los tres totales: **netos** (vigentes). Errores: `400 {detail, rule}` (`R7`, `BR-05`), `400` «Solo se pueden cerrar lotes activos», `403`, `404`. La UI consume `detail` mediante `getErrorMessage`.

## 12 · Impacto en datos

Sin migración. Ninguna fila cambia. Lotes hoy «atascados» (con par revertido) pasan a ser cerrables sin intervención en datos. Resúmenes ya devueltos antes del fix no se recalculan (no se persisten: `close_lot` devuelve un `dict`, `lots/service.py:519-531`); `Lot.end_date`/`status` no cambian de semántica.

## 13 · Seguridad

Sin superficie nueva. Se mantienen `require_permission("lots","create")` (`lots/router.py:83`), alcance de empresa/unidad (`MasterService.get_by_id` + `_exigir_unidad_operativa`, `lots/service.py:441-444`) y `company_id` en las consultas del resumen (`:473,483,493`). El filtro de estado no abre ninguna lectura cruzada.

## 14 · Inquilino

Todas las consultas del cierre siguen acotadas por `OperationalEvent.company_id == self.company_id`; R7 recibe `company_id` (`lots/service.py:465`). Sin cambio.

## 15 · Unidad de negocio

`_exigir_unidad_operativa(self._codigo(lot))` antes de toda regla (`lots/service.py:444`, `AC-L08`). Sin cambio; la regresión `tests/test_lots_bu_enforcement.py` (cierre) debe seguir verde (nota: 6 casos de esa suite fallan en HEAD por deriva OD-16 — `GA-GOV-03`; no son de este paquete).

## 16 · RBAC

`lots:create` para cerrar (sin cambio; la revisión del permiso «cerrar ≠ crear» no es de este paquete). UI: botón condicionado por `can({permission:'lots:create'})` (`LotDetailPage.tsx:185`). Sin permiso nuevo.

## 17 · Transacciones

`close_lot` corre bajo `RutaTransaccional`; R7/BR-05 se evalúan **antes** de mutar (`lots/service.py:456-465`) ⇒ un 400 no deja el cierre a medias (`AC05/AC06` de `R-76`). Sin cambio. No hay bloqueo `FOR UPDATE` del lote en el cierre (fuera de alcance; el segundo cierre ya responde 400 por `status != active`).

## 18 · Auditoría

Sin cambio (el cierre sigue **sin** `audit_accion`: E-10, tratado en `P1-12-REOPEN`). Este paquete no debe introducir auditoría parcial para no duplicar el trabajo de aquel.

## 19 · i18n

Claves existentes: `lots.closeError` («Error al cerrar lote» / «Error closing lot», `translation.json:858`), `lots.closedSummary`, `lots.closeButton`. Los mensajes del backend (R7/BR-05) se muestran tal cual (ES). Si se implementa C-07, el texto nuevo del backend es ES (patrón vigente: mensajes de regla en castellano). Sin texto fijo nuevo en el frontend.

## 20 · Escritorio

`LotDetailPage` ≥ 1024 px: botón «Cerrar Lote» → modal → toast de error (esquina superior, `Toast.tsx`) o tarjeta de resumen. Capturas en C3.

## 21 · Móvil

Ruta `/lots/:id` accesible en móvil (usuario `view_type=mobile` — `LotDetailPage` no es `WebOnly`); toast visible a 390×844 sin overflow. Verificación en C3 (captura móvil).

## 22 · Manejo de errores

| Código | Origen | UI |
|---|---|---|
| 400 `R7` | registros vivos sin decidir (incl. contrapartida pendiente) | toast con `detail` |
| 400 `BR-05` | sin pesaje/alimento vigentes | toast con `detail` |
| 400 «Solo se pueden cerrar lotes activos» | segundo cierre | toast |
| 401 | sesión | interceptor global existente |
| 403 | sin `lots:create` / unidad apagada (global) | toast «sin permiso» (`detail`) |
| 404 | lote fuera de alcance (empresa/unidad) | toast |
| 409 | n/a | — |
| 422 | n/a (sin cuerpo) | `getErrorMessage` lo normaliza igualmente |

## 23 · Impacto de migración

Ninguna (sin cambio de esquema ni de enumerados).

## 24 · Impacto SAP

`REVERSED` no se consolida ni viaja a SAP (`GA-REM-041 §3.3`); el cierre no toca `sap_*`. El resumen neto es el dato correcto para la futura conciliación de cierre de lote. SAP sigue siendo el sistema de registro futuro; sin cambio en `P-08`.

## 25 · Compatibilidad hacia atrás

- Contrato de respuesta idéntico; sólo cambia el valor de los tres totales cuando existen anulados/revertidos (antes: incorrecto).
- Comportamiento R7 idéntico para los 13 estados ya cubiertos por `test_lot_close_approval.py`; sólo `REVERSED` cambia de «bloquea» a «no bloquea».
- Clientes antiguos: ninguno depende del 400 para lotes con reverso (no existía flujo de usuario de reverso: `R-207`).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC01 | Lote con pesaje+alimento aprobados y **un par revertido** (`bird_reception`/`mortality`/`feed`, cualquiera elegible) ⇒ `POST /lots/{id}/close` **200**; `Lot.status='closed'`, `end_date` = hoy (fecha de negocio). |
| AC02 | Control gemelo sin reverso ⇒ 200 (sin regresión). |
| AC03 | Contrapartida en `PENDING_REVIEW` o `IN_REVIEW` ⇒ **400 R7**; lote `active`; `end_date` nula. |
| AC04 | Los 13 estados de `test_lot_close_approval.py` conservan su veredicto (7 bloquean, 6 no); `REVERSED` se añade a `NO_BLOQUEAN` **mediante un par real** creado por `POST /reversals` + aprobación (no sólo `_fijar_estado`). |
| AC05 | Resumen: mortalidad aprobada 5 + mortalidad cancelada 10 ⇒ `total_mortality = 5`. |
| AC06 | Resumen: alimento aprobado 7 kg revertido (par) + alimento aprobado 3 kg ⇒ `total_feed_kg = 3.0`. |
| AC07 | Resumen: huevos `EGG_COLLECTION` aprobados 100 + cancelados 40 ⇒ `total_eggs = 100`. |
| AC08 | `total_events` y `approved_events` conservan su definición actual (salvo C-04); el par revertido no cuenta en `approved_events`. |
| AC09 | BR-05: lote cuyo **único** pesaje quedó revertido ⇒ `400 BR-05` (C-05); con otro pesaje vigente ⇒ pasa. |
| AC10 | Ninguna mutación ante 400: `status='active'`, `end_date IS NULL` (regresión `R-76 AC05/AC06`). |
| AC11 | UI: `close` ⇒ 400 R7 ⇒ toast con el `detail` del backend; sin `console.error` como único canal; sin React #31; botón sigue visible; lote sigue `active`. |
| AC12 | UI: `close` ⇒ 200 ⇒ tarjeta de resumen con los totales netos (sin cambio de layout). |
| AC13 | UI: 403/404 ⇒ toast legible (`getErrorMessage`). |
| AC14 | Sin migración, sin endpoint nuevo, sin permiso nuevo; contrato `LotClosureSummary` sin campos nuevos obligatorios. |
| AC15 | Regresión: `test_lot_close_approval.py`, `test_lot_closure.py`, `test_internal_reversal.py`, `test_population_invariant.py` verdes en PG local; vitest completo, `tsc`, `build`. |
| AC16 | Runtime C3: H8b re-ejecutado sobre el fix ⇒ control 200 y gemelo con reverso **200**; capturas escritorio + móvil del toast (RED previo) y del resumen. |
| AC17 | Mensaje R7 con contrapartida pendiente distingue «reverso pendiente de decisión» (C-07; si el propietario lo descarta, AC17 = N/A documentado). |

## 27 · Pruebas RED→GREEN

Diseño exacto en `R-192_RED_E2E_UAT_DESIGN.md §1`. Resumen:
- Backend RED (fallan en HEAD): `test_r192_01_un_par_revertido_no_impide_el_cierre` (AC01), `test_r192_02_la_contrapartida_pendiente_si_impide_el_cierre` (AC03, verde en HEAD = control), `test_r192_03_el_resumen_excluye_cancelados` (AC05/AC07), `test_r192_04_el_resumen_excluye_el_par_revertido` (AC06), `test_r192_05_br05_ignora_el_pesaje_revertido` (AC09), `test_r192_06_ningun_estado_cambia_de_veredicto` (AC04, verde en HEAD).
- Frontend RED: `r192.closeLotError.test.tsx` — «un 400 R7 al cerrar se muestra como toast con el detail» (falla en HEAD: no hay toast; sólo `console.error`).
- GREEN: dirigidos + suites completas (backend PG local; vitest ≥314; tsc; build).

## 28 · E2E

Runtime local (pila aislada 8099/5199, `seeds.test_seeds`, actores `TEST Super Admin`/`TEST Aprobador`): H8b lotes gemelos por API + cierre por **UI** desde `/lots/{id}` (toast RED antes del fix; resumen tras el fix). Diseño en `R-192_RED_E2E_UAT_DESIGN.md §2`. Artefactos: `evidence/r192/runtime-c3.json` + PNG.

## 29 · UAT

Visible al usuario (toast y resumen) ⇒ plan UAT del propietario en `R-192_RED_E2E_UAT_DESIGN.md §3` (3 casos: cierre con reverso, cierre rechazado con mensaje, resumen neto).

## 30 · Criterios de cierre

RED válido documentado (evidencia `evidence/r192/red/`) · GREEN local verificable (logs) · AC01-AC16 verdes (AC17 según C-07) · sensibilidad (retirar `REVERSED` del conjunto ⇒ AC01 roja; retirar el filtro de estado ⇒ AC05/AC06 rojas; retirar el toast ⇒ AC11 roja) · runtime C3 con artefactos · UAT del propietario 3/3 · backlog actualizado (R-192 → GA-REM asignado al autorizar) · sin cambios no relacionados.
