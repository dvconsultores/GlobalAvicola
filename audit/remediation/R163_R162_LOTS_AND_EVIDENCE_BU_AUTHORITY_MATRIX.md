# MATRIZ DE AUTORIDAD DE UNIDAD DE NEGOCIO · `lots` y descarga de evidencia — `R-163` + `R-162`

**WAVE B · tranche 3** · 2026-09-09 · base `3d0c5d0` · construida **antes** de los AC y del código

Fuentes leídas: `R-163`, `R-162` (backlog, alta en el pre-flight del tranche 2), `GA-REM-040 §4, §5, §8, §12,
§17-A/B/C`, enmienda G, `OD-09.a/b/c`, `OD-14.c/d`, `OD-16.b/d/e/f` + §7, `OD-15 §6`, fases 3 (`:88`), 7 y 8
(evidencia), `R-139` (S04, S05), `R-160/R-159` (evidencia §6, §9), `route_scope.py:111-124`,
`masters/service.py` (`_apply_company_filter`, `_apply_business_unit_filter:113`, `get_by_id`, `update`),
`lots/service.py` (todas las superficies), `lots/router.py`, `lots/schemas.py` (`LotBase.bird_type`,
`LotUpdate` sin `bird_type`), `operations/service.py` (`get_evidence_for_download`, `get_evidences`,
`delete_evidence`), `operations/router.py:388`, `business_units/service.py` (`unidades_habilitadas`,
`unidades_efectivas_por_id`, `exigir_acceso_a_unidad` — 0 llamadores), `seeds/test_seeds.py` (todas las
unidades ON y concedidas a todos), `tests/test_lot_row_scope.py`, `tests/test_od14_productive_surfaces.py`.

## 1. Verificación exacta de los hallazgos

### `R-163` — lo que el repositorio muestra

| Hecho | Evidencia |
|---|---|
| `_apply_business_unit_filter` **omite el predicado de unidad para `is_super_admin`** «exactamente donde queda fuera del de empresa» | `masters/service.py:113`; fase 3 `:88` («se declara como excepción, no como descuido») |
| Toda superficie de `lots` que resuelve el lote por `MasterService` hereda la exención: `get_lots`, `get_lot`, `update_lot` (`update → get_by_id`), `close_lot` (`get_by_id`), `activate_manual` (`get_lot`), `add_phase`, `get_lot_phases`, `get_opening_balance` (`get_lot`) | `lots/service.py:77-100, 214-223, 336-360, 441-475` |
| Para el **actor de empresa** la unidad ya se exige en esas superficies (`404`, fase 3 certificada: `test_no_se_modifica_un_lote_de_otra_cadena`, `test_no_se_activa_manualmente…`, `test_no_se_cuelga_una_fase…`) | `tests/test_lot_row_scope.py:283, 377, 399` |
| **`POST /lots` (`create_lot`) no consulta la unidad para nadie**: `bird_type` viene del cuerpo y se guarda tal cual; solo se verifica la granja | `lots/service.py:136-213`; ninguna prueba de creación por unidad en `test_lot_row_scope.py` |
| La unidad de un lote **no cambia por `PUT`**: `LotUpdate` no declara `bird_type` (`extra="forbid"`) | `lots/schemas.py:50-70` |
| `egg-batches` / `chick-batches` leen el lote destino **sin** unidad a propósito (contrato `P-10`, `CONTRATO`) | `lots/router.py:264-276`, `route_scope.py:177-179` |
| La escritura certificada de la autoridad global situada es sobre unidad **habilitada** (`lote_a_manual` = `breeder`, ON en `A`) | `R-139` `test_s05_situada_en_a_activa_el_lote_de_a…` |

Severidad real: **P2 confirmada** para el actor global (requiere autoridad comodín y situarse en la empresa;
la unidad apagada no es dato oculto para él) y **P1 de clase `AC-C05`** para `POST /lots` con actor de
empresa (crea dato productivo en una cadena no concedida o apagada, sin autoridad comodín). El hallazgo se
**amplía a cinco superficies de escritura** por inventario (§11 del encargo), no por suposición.

### `R-162` — lo que el repositorio muestra

| Hecho | Evidencia |
|---|---|
| `GET /operations/{id}/evidences/{eid}/download` busca la evidencia por `id` + `event_id`, compara **solo la empresa** (`R-139`, `403`) y sirve el fichero | `operations/service.py get_evidence_for_download`; `router.py:388` |
| Su hermana `GET …/evidences` (listado) pasa por `get_event` → predicado de unidad para el actor de empresa (`404`) | `operations/service.py get_evidences` |
| `DELETE …/evidences/{eid}` ya sigue el orden empresa (`403`) → evento por unidad (`404`) → guarda (`403` global apagada) desde la enmienda G | `delete_evidence` (`R-160`) |
| Contrato certificado que **no cambia**: actor de empresa → evidencia de otra empresa `403`; global sin contexto `403`; global situada en `A` descarga la de `A` y no la de `B` | `R-139` S04 (3 pruebas) |
| No existe otra superficie de evidencia fuera de `operations` | `grep Evidence app/` → solo `operations` |

Severidad real: **P2 confirmada** (lectura de fichero de otra cadena de la **misma** empresa por un actor
de empresa con `operations:read`; no cruza inquilinos).

## 2. Clasificación de superficies (§16 del encargo) — una clase de seguridad autoritativa por ruta

| Ruta · método | Clase autoritativa | Dimensiones | `route_scope` | Actor de empresa (certificado) | Autoridad global situada (certificado) | Cambia en este tranche |
|---|---|---|---|---|---|---|
| `POST /lots` | **PRODUCTIVE_WRITE** | TENANT_SCOPED | `MULTI_UNIDAD` | sin gate de unidad (**defecto**) | sin gate de habilitación (**defecto**) | **sí** (`R-163`) |
| `PUT /lots/{id}` | **PRODUCTIVE_WRITE** | TENANT_SCOPED | `MULTI_UNIDAD` | `404` fuera de su alcance (fase 3) | exenta también de la habilitación (**defecto**) | **sí** (`R-163`, solo global) |
| `POST /lots/{id}/close` | **PRODUCTIVE_WRITE** | TENANT_SCOPED | `MULTI_UNIDAD` | ídem | ídem | **sí** |
| `POST /lots/activate-manual` | **PRODUCTIVE_WRITE** | TENANT_SCOPED | `MULTI_UNIDAD` | `400 BR-07` ajeno · `404` otra cadena | ídem (`R-139` S05 solo probó unidad ON) | **sí** |
| `POST /lots/{id}/phases` | **PRODUCTIVE_WRITE** | TENANT_SCOPED | `MULTI_UNIDAD` | `404` (fase 3) | ídem | **sí** |
| `GET /lots` · `GET /lots/{id}` · `/phases` · `/opening-balance` · `/traceability` | **PRODUCTIVE_READ** | TENANT_SCOPED · visibilidad de control certificada para la autoridad global (fase 3 `:88`, `R-139` S02) | `MULTI_UNIDAD` | por unidad efectiva (fase 3) | toda la empresa situada, unidades apagadas incluidas | **no** (frontera declarada y probada como control) |
| `POST /lots/egg-batches` · `/chick-batches` | **PRODUCTIVE_WRITE** (contrato entre unidades) | CONTRATO | `CONTRATO` | origen por unidad, destino por contrato (`P-10`, fase 5) | ídem | **no** (fase 5; fuera del hallazgo) |
| `PATCH /business-units/{code}/enable\|disable` · `GET /business-units/…` | **CONTROL_PLANE** | TENANT_SCOPED | `CORE` | por `business_units:*` (`OD-15 §6`, fase 7) | ídem | **no** (se prueba como control: administrar la unidad apagada sigue posible) |
| `GET /operations/{id}/evidences/{eid}/download` | **PRODUCTIVE_READ** | TENANT_SCOPED · **no** es control global (§14.H del encargo) | `MULTI_UNIDAD` | solo empresa (**defecto**) | empresa situada (`R-139`) | **sí** (`R-162`, solo actor de empresa) |
| `GET /operations/{id}/evidences` | **PRODUCTIVE_READ** | TENANT_SCOPED | `MULTI_UNIDAD` | por unidad vía `get_event` | empresa situada | **no** (control) |

## 3. Semántica por actor (fijada por `OD-16.e/f`, `AC-A05`, `OD-09.a/b/c`, `OD-14.d`; la misma que `GA-REM-040-G §G.3`)

| Actor | Escritura productiva sobre unidad `u` | Dato pendiente (lote sin `bird_type`) | Lectura productiva |
|---|---|---|---|
| actor de empresa | `u ∈ unidades_efectivas` (habilitada ∧ concedida viva) o **denegado**; en `POST /lots` → `403` (la unidad es catálogo público, no hay nada que no enumerar); en superficies por `id` → `404` (fase 3, sin cambio) | ≥ 1 unidad efectiva (`OD-09.c`) o `403` | por unidad efectiva (fase 3) |
| autoridad global | situada (`OD-14.d`) **y** `u ∈ unidades_habilitadas(empresa)`; apagada → `403`; **sin concesión requerida** (fase 3, `R-139`, `G.3`) | situada, con ≥ 1 unidad habilitada | visibilidad de control certificada (toda la empresa situada) — **no cambia** |
| Administrador de Accesos (`OD-15`) | `403` por RBAC (sin `lots:*`/`operations:*`) | `403` | `403` |
| Contraloría | `N/A` (sin resolutor) | — | — |

**Frontera de excepción del actor global (§8 del encargo):** exento de la **concesión de usuario** (certificado
en fase 3 y preservado por `R-139` y `G.3`) ≠ exento de la **habilitación de la empresa** (nunca; `OD-16.f`:
«sin retroceso… por `is_super_admin`»). **Administrar ≠ operar (§9):** el plano de control de la unidad
apagada (fase 7) no se toca.

## 4. Las superficies, columna a columna

| ID | Ruta · método | Acción | Recurso | Empresa | Unidad canónica | ¿campo BU en payload? | Comp. habilitación | Comp. concesión | RBAC | Global | Hoy | Exigido | Hallazgo | AC | Test |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1 | `POST /lots` | crear lote | `lots` | `self.company_id` (granja verificada) | **`data.bird_type`** (dato de dominio del lote; None → pendiente) | sí, y **es el dato**, no la autorización: el servidor lo contrasta con el alcance | **ninguna** | **ninguna** | `lots:create` | situada; escribe en unidad apagada | cualquier actor crea en cualquier cadena | actor: `bird_type ∈ efectivas` o `403`; None → ≥ 1 efectiva; global: habilitada o `403`; sin contexto `403` | **R-163** (ampliado) | `L01–L07, L12–L14` | `test_lots_bu_enforcement.py::l*` |
| L2 | `PUT /lots/{id}` | editar | `lots` | `get_by_id` (todos) | `lot.bird_type` (inmutable por `PUT`) | no | ninguna para global | `get_by_id` (actor: `404`) | `lots:update` | exenta | global edita lote de unidad apagada | global: habilitada o `403` | **R-163** | `L08, L09, L10` | `::l08_put*` |
| L3 | `POST /lots/{id}/close` | cerrar | `lots` | ídem | ídem | no | ídem | ídem | `lots:create` | exenta | ídem | ídem | **R-163** | `L08, L09` | `::l08_close*` |
| L4 | `POST /lots/activate-manual` | saldo de apertura | `opening_balances` | `verificar_pertenencia` (`400 BR-07`) + `get_lot` | ídem | no (`lot_id`) | ídem | `get_lot` (actor `404`) | `lots:create` | exenta | ídem | ídem | **R-163** | `L08, L09` | `::l08_activate*` |
| L5 | `POST /lots/{id}/phases` | añadir fase | `lot_phases` | `get_lot` | ídem | no (`lot_id`) | ídem | ídem | `lots:create` | exenta | ídem | ídem | **R-163** | `L08, L09` | `::l08_phase*` |
| L6 | `GET /lots`, `/{id}`, `/phases`, `/opening-balance` | leer | — | por empresa | — | — | actor: sí (fase 3) | actor: sí | `lots:read` | control | global ve unidad apagada | **sin cambio** (frontera de lectura declarada) | — | `L11` (control) | `::l11*` |
| E1 | `GET …/evidences/{eid}/download` | leer fichero | `evidences` | `evidence.company_id` (`403`, `R-139`) | del evento (lote · clasificación) | — | actor: **ninguna** | actor: **ninguna** | `operations:read` | control situada | actor descarga evidencia de otra cadena de su empresa | empresa (`403`) → `get_event` (`404` por unidad para el actor) → fichero; global situada: sin predicado de unidad (lectura) | **R-162** | `E01–E08` | `::e*` |
| E2 | `GET …/evidences` | listar | `evidences` | `get_event` | ídem | — | vía `get_event` | ídem | `operations:read` | control | correcto | sin cambio (control) | — | `E08` | `::e08*` |
| C1 | `PATCH /business-units/{code}/disable` · `GET /business-units/company` | plano de control | `company_business_units` | por empresa | — | — | n/a | n/a | `business_units:*` | — | certificado (fase 7) | sin cambio; se prueba como control que sigue operable con la unidad OFF | — | `L15` | `::l15*` |

## 5. Orden de comprobación

```
escrituras de lots   autenticación → RBAC → empresa efectiva (get_by_id / verificar_pertenencia / granja) → recurso
                     → unidad canónica (lot.bird_type · data.bird_type · pendiente) → habilitación → concesión (no global)
                     → regla de negocio → escribir           todo antes de db.add / setattr
descarga             autenticación → RBAC → evidencia existe → empresa (403, R-139) → evento por unidad (404, actor) → fichero
```

## 6. Recuento canónico de la ola B (revalidado desde el backlog, no desde informes)

| ID | Sev. | Estado | Ola | | ID | Sev. | Estado | Ola |
|---|:--:|---|:--:|---|---|:--:|---|:--:|
| `R-130` | P1 | **CERRADO** | B | | `R-148` | P2 | abierto | B |
| `R-160` | P1 | **CERRADO** | B | | `R-152` | P2 | abierto | B |
| `R-159` | P2 | **CERRADO** | B | | `R-153` | P3 | tras `R-152` | B |
| `R-135` | P1 | abierto (`OD-17`) | B | | `R-154` | P3 | abierto (parte `AOD-08`) | B |
| `R-136` | P1 (SAP) | abierto · post-SAP `SAP_DEFERRED` | B · D | | `R-156` | P3 | bloqueado `AOD-20` | B |
| `GA-REM-021` | P1 | `SPEC_READY` (1 ítem) | B | | `R-161` | P2 | abierto | B |
| `R-140` | P2 | abierto (parte `AOD-18`) | B | | `R-162` | P2 | abierto → tranche 3 | B |
| `R-142` | P2 | bloqueado `AOD-17` | B | | `R-163` | P2 | abierto → tranche 3 | B |
| `R-143` | P2 | abierto | B | | | | | |
| `R-144` | P2 | bloqueado `R-131` (C) + `AOD-08` | B/C | | | | | |
| `R-147` | P2 | abierto (parte `AOD-19`) | B/C | | | | | |

```
TOTAL 19 · CERRADOS 3 · ABIERTOS 16 · P1 5 (2 cerrados) · P2 11 (1 cerrado) · P3 3
BLOQUEADOS 3 (R-142 · R-144 · R-156) + R-136 parcial (SAP_DEFERRED)
DECISIÓN REQUERIDA 6 (AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20)
Coincide con WAVE_B §7; se corrige allí solo la línea BLOQUEADOS (decía 2: omitía R-142 y R-156, que sí lista como decisiones).
```

## 7. Fuera del tranche (registrado, no remediado)

- `_lote_destino` en `egg-batches`/`chick-batches` lee el destino sin unidad **por contrato** (`P-10`): no es hallazgo.
- `BU-D10`: las fixtures siembran `is_enabled` OFF explícitamente; no se reactiva ninguna unidad en las pruebas.
