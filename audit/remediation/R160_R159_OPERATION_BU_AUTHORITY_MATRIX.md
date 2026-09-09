# MATRIZ DE AUTORIDAD DE UNIDAD DE NEGOCIO SOBRE `operations` — `R-160` + `R-159`

**WAVE B · tranche 2** · 2026-09-09 · base `57e22b6` · construida **antes** de los AC y del código

Fuentes leídas: `R-160`/`R-159` (backlog), `GA-REM-040 §4.2, §4.3, §7, §8, §11, §14.2, §17-C`,
fases 1-3, 6-8 (evidencia), `OD-09.a/b/c`, `OD-14.c/d`, `OD-16.b/d/e/f`, `R-139` evidencia
(§6: exención de visibilidad preservada; nota para fases 10-11 sobre escrituras del actor global),
`business_units/classification.py` (`predicado_de_evento`, `estado_de_clasificacion`),
`business_units/scope.py` (`predicado`, `lotes_alcanzables`), `business_units/service.py`
(`unidades_efectivas`, `unidades_habilitadas`, `exigir_acceso_a_unidad`), `operations/router.py`,
`operations/service.py`, `operations/schemas.py`, `masters/service._apply_business_unit_filter`,
`seeds/test_seeds.py` (concesiones), `tests/test_business_unit_guard.py`, `tests/test_lot_row_scope.py`.

## 1. Derivación canónica de la unidad de un evento

| Fuente candidata | ¿Canónica? | Evidencia |
|---|---|---|
| **`Lot.bird_type` → `BusinessUnit.code`** (`grandparent`/`breeder`/`hatchery`/`broiler`) | **sí, primera** | `scope.predicado` casa `Lot.bird_type` con los códigos de unidad; `classification.estado_de_clasificacion` → `derived` si el lote tiene tipo |
| **`OperationalEvent.business_unit_id`** (FK `company_business_units`) | **sí, segunda**: solo la fija la clasificación del plano de control (`classify`/`reclassify`, `masters:update`/`corrections:correct`, fase 6) | `predicado_de_evento` = lote alcanzable **OR** `business_unit_id` en habilitaciones alcanzables |
| lote sin `bird_type` · evento sin lote (`farm_inspection`, `hatchery_inspection`) sin clasificar | **no derivable → `pending`** (`OD-10.c`, `GA-REM-040 §11`); no es una quinta unidad | `estado_de_clasificacion` → `pending`; `predicado` excluye nulos; `BU-D06` (segunda fuente: la raza) sigue pendiente |
| `event_type`, `farm.farm_type`, `house`, `hatchery_params.hatchery_id`, texto | **no** | ninguna fuente los declara atribución; `§11.4` prohíbe auto-asignar «por nombre de granja, por URL ni por conjetura» |
| **campo de unidad en el payload** | **no existe**: `OperationalEventBase`/`Create`/`Update` no declaran `business_unit_id` ni `company_id` | `operations/schemas.py` (los `company_business_unit_id` de las líneas 309/322 son de `classify`/`reclassify`, plano de control) |

Por tanto: **el servidor deriva la unidad del lote referenciado (`lot_id`) en la misma transacción,
antes de escribir**; el cliente no puede afirmarla. El único vector de suplantación es **cambiar
`lot_id`** (alta o edición) hacia un lote de otra unidad o de otra empresa: se cierra verificando
el lote destino (empresa + unidad) siempre que se resuelve.

## 2. Semántica por actor (fijada por fuentes, no inferida)

| Actor | Empresa | Unidad habilitada | Concesión | RBAC | Fuente |
|---|---|---|---|---|---|
| actor de empresa | la suya (`OD-11.a`) | **obligatoria** | **obligatoria** (`unidades_efectivas` = habilitada ∧ concedida viva ∧ activa en producto) | permiso de la ruta | `GA-REM-040 §4.2`, `AC-A05`, `AC-B02`, `AC-C05`; `OD-09.c` (cero unidades → no opera dato productivo) |
| actor de empresa sobre dato **pendiente** (lote sin tipo · evento sin lote) | la suya | n/a (no derivable) | **≥ 1 unidad efectiva** para operar dato productivo; el dato entra en la bandeja de pendientes | permiso de la ruta | `OD-09.c`, `OD-10.c`, fase 6 (creación en pendiente sin adivinar la cadena) |
| autoridad global (`("*", …, "all")`, `is_super_admin`) | **situada** obligatoria (`OD-14.d`; sin contexto → cero filas / `BR-07` / `404`) | **obligatoria para escribir**: `AC-A05` («operativamente inaccesible»), `OD-16.b/e` (la empresa no opera esa unidad); **no** para leer (visibilidad de control certificada: fase 3 `:88`, `R-139` §6, `test_s02_situada_en_a_solo_ve_a_incluidas_todas_sus_unidades`) | **no exigida**: la autoridad se deriva de la capacidad comodín, no de concesiones (fase 3 `_apply_business_unit_filter`, `R-139` S05 «exención de unidad se preserva»; `AC-C14` habla del conjunto efectivo, no de la autoridad) | permiso de la ruta (el comodín lo tiene) | `GA-REM-040 §4.3`, fase 3, `R-139`; lectura de `OD-16.e` como absoluta para **escrituras** |
| Contraloría (`OD-09.a`) | — | — | — | — | **no implementada como resolutor** («otro resolutor, de una fase posterior», `business_units/service.py:21`); ninguna ruta de `operations` la reconoce → `N/A` |
| Administrador de Accesos (`OD-15`) | la suya | — | cero unidades por defecto | **sin** permisos `operations:*` → `403` antes de cualquier unidad | `OD-15 §6`, `test_h14_*` |
| Analista SAP (`OD-12`) | la suya | superficies SAP solamente (`AC-SAP07`) | — | — | fuera de `operations` → sin cambio |

## 3. Las superficies

| ID | Ruta · método | Acción | Recurso | Padre | Empresa | Unidad canónica | ¿campo BU en payload? | Comprobación unidad-empresa | Comprobación concesión | RBAC | Actor global | Comportamiento actual | Comportamiento exigido | Hallazgo | AC | Test |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **W1** | `POST /operations` | crear evento | `operational_events` (+ movimientos) | `lots` (opcional) | `self.company_id` (servidor) · `validate_lot_active(company)` | `lot.bird_type` → código · sin lote / sin tipo → pendiente | **no** | **ninguna** | **ninguna** | `operations:create` | situada; sin unidad: `BR-07`; con lote de unidad apagada: **hoy escribe** | se crea sobre cualquier lote de la empresa; con cero unidades también | actor: unidad efectiva o `400 BR-07 «Lote no encontrado»`; pendiente: ≥ 1 unidad efectiva o `403`; global: unidad habilitada o `403` | **R-160** | `W01–W05, W09–W13, W15` | `test_operations_bu_enforcement.py::w*` |
| **W2** | `PUT /operations/{id}` | editar evento | ídem | lote (puede **cambiar** por payload) | `get_event` (empresa para todos) · **el lote destino no se verifica** | del lote **destino** | no | `get_event` acota por unidad al actor de empresa (fase 3) · **el `lot_id` nuevo se asigna con `setattr` sin comprobar empresa ni unidad** | ídem | `operations:update` | situada; unidad apagada: hoy edita | repuntar el evento a un lote de otra unidad **o de otra empresa** | destino verificado: `validate_lot_active(company)` + unidad efectiva/habilitada; ubicaciones vía `verificar_ubicacion` | **R-160** | `W06–W09` | `::w06*`, `::w09*` |
| **W3** | `POST /operations/{id}/submit` | transición | evento | — | `get_event` | del evento (lote / clasificación) | no | `get_event` (actor: `404` si no alcanzable) | ídem | `operations:create` | situada; unidad apagada: hoy transita | correcto para el actor de empresa; global sobre unidad apagada: escribe | global: unidad habilitada o `403` | R-160 (global) | `W13` | `::w13_submit*` |
| **W4** | `POST /operations/{id}/cancel` | transición | evento | — | ídem | ídem | no | ídem | ídem | `operations:create` | ídem | ídem | ídem | R-160 (global) | `W13` | `::w13_cancel*` |
| **W5** | `POST /operations/{id}/evidences` | adjuntar | `evidences` | evento | `get_event` | del evento | no | `get_event` | ídem | `operations:create` | ídem | correcto para el actor; global apagada: escribe | global: habilitada o `403` | R-160 (global) | `W13` | `::w13_upload*` |
| **W6** | `DELETE /operations/{id}/evidences/{eid}` | borrar | `evidences` (+ fichero) | evento | `evidence.company_id == self.company_id` (`R-139`) · **sin `get_event`** | del evento | no | **ninguna**: un actor de la empresa borra evidencia de un evento de una unidad **no concedida** | ninguna | `operations:delete` | situada (`R-139`); apagada: borra | borra evidencia ajena por unidad | empresa de la evidencia primero (`403`, `R-139`), después `get_event` (`404` por unidad) y la guarda (global: habilitada o `403`) | **R-160** | `W06b` | `::w06b*`, `::w13_delete*` |
| **W7** | `PATCH /operations/alerts/{id}/resolve` | resolver alerta | `operational_alerts` | lote (`lot_id NOT NULL`) | `company_id == self.company_id` | `alert.lot` → `bird_type` | no | **ninguna** | ninguna | `operations:update` | situada; apagada: resuelve | resuelve alertas de lotes de unidades no concedidas | actor: `lot_id ∈ lotes_alcanzables` o `404`; global: habilitada o `403` | **R-159** (mismo predicado) | `A13` | `::a13*` |
| **R1** | `GET /operations/alerts` | listar | `operational_alerts` | lote | `_acotar_a_empresa` (`R-139`) | `alert.lot` → `bird_type` | — | **ninguna** para el actor de empresa (`route_scope`: «alertas de sus lotes»; fase 3 `:38` «parcial») | ninguna | `operations:read` | situada: toda la empresa, **incluidas** unidades apagadas (visibilidad de control certificada, como `get_events`) | el actor ve alertas de lotes de unidades no concedidas o apagadas; cero unidades → toda la empresa | `lot_id IN lotes_alcanzables(company, unidades_efectivas)` **en la consulta**, antes de `offset/limit`; cero unidades → `[]`; global: sin predicado de unidad | **R-159** | `A01–A12` | `::a*` |
| C1 | `POST /operations/{id}/classify` · `/reclassify` | plano de control | evento pendiente / clasificado | — | `predicado_de_pendientes` | la unidad **se asigna** aquí | `company_business_unit_id` (plano de control, `masters:update` / `corrections:correct`) | n/a por diseño: `OD-09.b` (administrar ≠ operar), fase 6 | n/a | control | — | certificado (fase 6) | sin cambio | — | — | fase 6 |
| — | `GET /operations/{id}/evidences/{eid}/download` | leer fichero | evidencia | evento | `evidence.company_id` (`R-139`) · **sin `get_event`** | del evento | — | **ninguna** para el actor de empresa (lectura por unidad) | — | `operations:read` | control | descarga evidencia de unidad no concedida | fuera de este tranche → **`R-162`** (P2, mismo primitivo) | — | — | — |

## 4. Orden de comprobación (por superficie de escritura)

```
1 autenticación → 2 empresa efectiva (OD-11/OD-14) → 3 recurso destino (lote / evento) → 4 misma empresa
→ 5 unidad canónica del destino (lot.bird_type · business_unit_id · pendiente) → 6 unidad habilitada para la empresa
→ 7 autoridad del actor sobre la unidad (efectiva · global situada) → 8 RBAC (ya en la ruta) → 9 reglas de negocio (BR-01…, R-130) → 10 escribir
```

Todo dentro de la transacción de la petición (`RutaTransaccional`); el lote se lee en la misma
sesión en la que luego `R-130` lo bloquea. Un fallo en 4-7 precede a `db.add`: cero efectos.

## 5. Lo que esta matriz registra y no arregla

- **`R-162`** (P2): `GET …/evidences/{eid}/download` no aplica predicado de unidad para el actor de empresa (misma raíz; una línea con `get_event`; fuera del alcance «escritura» y «alertas» de este tranche).
- **`R-163`** (P2): en el módulo `lots` (`PUT /lots/{id}`, `POST /lots/activate-manual`) el actor global sigue exento de la habilitación (`_apply_business_unit_filter` omite todo para `is_super_admin`): incoherente con la lectura absoluta de `OD-16.e` que este tranche aplica a `operations`. Requiere enmienda de `GA-REM-033`/`GA-REM-040` propia.
- `BU-D10`: las fixtures siembran `is_enabled` explícitamente; ninguna prueba reactiva.
