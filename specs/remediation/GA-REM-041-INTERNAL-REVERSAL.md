# `GA-REM-041` · REVERSO INTERNO DE REGISTROS APROBADOS — `R-136` (componente interno) + `R-165`

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-041` · `BUSINESS WORKFLOW / DATA INTEGRITY SPEC` · **Estado** **`CERTIFIED`** (frontera técnica, 2026-09-09; E2E `BLOCKED_RUNTIME`) · evidencia `R-136-INTERNAL-REVERSAL-EVIDENCE.md` |
| **Hallazgos** | **`R-136`** («tabla `reversals` sin servicio ni ruta; `BR-16` sin mecanismo», P1, `H360-P05`, `G-R09`, `GA-TD-028`) — **solo el componente interno** (aprobado, pre-SAP) · **`R-165`** (P2: el plano de revisión no exige la habilitación de la unidad a la autoridad global) — **incluido** (§1.2) |
| **Decisión** | **`OD-19`** (alias `AOD-21`) · `OD-17.a` · `OD-14` · `OD-16` (aclaración `GA-REM-040-H §H.2`) |
| **Requisito raíz** | Rec. central 7.17 («corrección sobre aprobado sin versión/reverso») · `G-R09` («reverso con registro compensatorio») · `docs/16 §8` (`ANULADO/REVERSADO`) · `BR-16`/`R16` (post-SAP, no cambia) · `docs/13` (auditoría de anulación: usuario, fecha/hora, motivo, registro completo) |
| **Matriz previa** | `R136_INTERNAL_REVERSAL_EFFECT_MATRIX.md` (efectos por evento; resuelta en su §«Decidido por OD-19») · `R136_INTERNAL_REVERSAL_PREFLIGHT.md` |
| **Fuera de alcance** | reverso de documentos SAP · reenvío/reproceso SAP · `P-08` · **consolidados** (`OD-19 §11`, `DEFERRED`) · **huevos/incubación** (`OD-19 §18`, `BLOCKED_BY_R-161`) · `R-161` · `R-164` · `R-166` · `R-140`/`R-154` residuales · `GA-REM-021` · ola C · fase 9 · `R-158` · `BU-D10` · frontend · marco genérico de compensación/event sourcing |

## 1. Composición

### 1.1 `R-136`

| Componente | Requisito | Estado actual | ¿Ejecutable? | Bloqueo | Seleccionado |
|---|---|---|---|---|---|
| reverso de un **aprobado pre-SAP** con contrapartida | `OD-19` §1-§21 | sin servicio, ruta, estado ni permiso | **sí** | — | **sí** |
| reverso de un **consolidado** | `OD-19 §11` | — | no | contrato de des-consolidación (`R8`) | no (`DEFERRED`) |
| reverso de **documentos SAP** | `BR-16`, `OD-17.c` | — | no | `GA-REM-017` `BLOCKED_EXTERNAL` · `AOD-04` · `OD-12` | no (`SAP_DEFERRED`) |
| subtipo **huevos / incubación** | `OD-19 §18` | — | no | `R-161` | no (`BLOCKED_BY_R-161`) |

Cierre esperado: `R-136 INTERNAL = CLOSED` · `R-136 OVERALL = PARTIAL` · `SAP = DEFERRED` (`OD-19 §22`).

### 1.2 `R-165` — incluido (forma B del encargo)

El reverso **se aprueba por el mecanismo existente** (`OD-19 §6`): la contrapartida entra en la cola de revisión y la
decide `approvals/approve|reject` (o `review/complete` con un nivel). Ese plano resuelve el evento con
`_ambito_de_unidad()`, que devuelve `[]` para la autoridad global: hoy podría **aprobar un reverso sobre una unidad
apagada**, lo que `OD-19 §13` prohíbe expresamente. Cerrar el reverso sin cerrar `R-165` dejaría la prohibición sin
efecto en su propio camino de aprobación. Mismo primitivo (`business_units.service.exigir_unidad_operativa`), sin
decisión pendiente, sin cambiar la raíz de `R-136`: **se incluye**, con AC y estado propios (`AC-165-*`). Superficies
exactas: `POST /review/start/{id}`, `POST /review/return`, `POST /review/complete`, `POST /approvals/approve`,
`POST /approvals/reject`, `batch-approve`, `batch-reject` — clase **`PRODUCTIVE_REVIEW`** (`OD-14.c`: dato productivo =
inquilino). El actor de empresa ya queda fuera por `unidades_efectivas`; el control-plane (`business-units`) no cambia.

## 2. Vocabulario (mapeado; nada se renombra)

`CORRECTION` (`POST /corrections` → `CORRECTED`) ≠ `REVERSAL` · `CANCELLATION` (`cancel` → `CANCELLED`, antes de efecto
aceptado) ≠ `REVERSAL` · `REJECTION` (`REJECTED`, viva) ≠ `REVERSAL` · `RETURNED` (viva) ≠ `REVERSED` · reverso
**interno** (esta spec) ≠ reverso de **documento SAP** (`BR-16`, diferido).

## 3. Modelo

### 3.1 Estados

`EventStatus` gana **`REVERSED`** (`OD-19 §1`): terminal. `AuditAction` gana **`REVERSED`** para que la transición se
audite con su nombre y no como `UPDATED` (`OD-19 §9`, `docs/13`). Ambos son enumerados **nativos** de PostgreSQL
(`eventstatus`, `auditaction`) → **migración** (§9).

### 3.2 La solicitud es la contrapartida

Una solicitud de reverso crea, en la misma transacción:

1. la **contrapartida**: un `OperationalEvent` de la **misma empresa, lote, granja, galpón y tipo** que el original, con
   **copia de sus submovimientos** (cantidades derivadas del original, `OD-19 §4`), `registered_by_id` = solicitante,
   `status = PENDING_REVIEW` (entra en la cola de revisión, `OD-19 §6`), `event_date` = hoy (`t2`), `observations` =
   «Reverso de #\<id\>: \<motivo\>»;
2. la fila **`reversals`** (`OD-19 §21`, modelo existente, sin esquema nuevo): `original_event_id`, `reversal_event_id`
   = contrapartida, `company_id`, `reason`, `reversed_by_id` = solicitante, `original_data_snapshot` (campos del original
   y sus submovimientos, congelados), `reversal_data` (cantidades compensadas por tipo);
3. auditoría `CREATED` sobre `entity_type="reversal"` con el motivo.

La contrapartida **no se edita ni se corrige** (`PUT`/`POST /corrections` → `400`): sus cantidades son del original.
Puede **cancelarse** mientras no sea efectiva (retirar la solicitud: `CANCELLED`, sin efecto), rechazarse (`REJECTED`,
sin efecto; original sigue `APPROVED`, `OD-19 §2`) o reenviarse tras el rechazo (`GA-REM-006-A`).

### 3.3 La aprobación aplica la compensación (atómica, `OD-19 §20`)

Cuando `approve` (o `complete_review` con un nivel) aprueba una contrapartida:

```
bloquear original (FOR UPDATE) → original.status == APPROVED (aún reversible; si no: 400 BR-16, nada cambia)
→ validar saldos resultantes ≥ 0 (BR-01/BR-04 para aves y viables; bloqueo de lote como R-130)
→ contrapartida.status = REVERSED · original.status = REVERSED · approved_by = aprobador
→ approval_actions.APPROVED · audit_logs (original: approved→reversed; contrapartida: in_review→reversed) → commit
```

Ambos terminan `REVERSED`: el original (historia: «X ocurrió») y la contrapartida (historia: «X fue neutralizado»).
Ninguno vuelve a `APPROVED`, ninguno se consolida ni viaja a SAP (`sap/service` solo consolida `APPROVED`), ninguno
cuenta en KPI (`reports` cuentan `APPROVED`+).

### 3.4 Aritmética de los saldos (`OD-19 §3, §5, §17`)

Los saldos (`get_current_bird_balance`, `get_viable_chick_balance`, y por simetría los de huevos) pasan a:

```
SALDO = apertura + Σ natural(eventos que NO son contrapartida, status ∉ {CANCELLED})
                 − Σ natural(contrapartidas EFECTIVAS, status = REVERSED)
```

El original `REVERSED` sigue sumando en su signo natural (+X o −X); la contrapartida efectiva resta exactamente lo mismo
(−X o +X) → neto 0. Una contrapartida **pendiente, rechazada o cancelada** no cuenta (0). No hay exclusión retroactiva:
las dos filas están y las dos suman. `R-130` intacto: el signo natural y el bloqueo de lote no cambian; la validación
≥ 0 en §3.3 impide la sobre-restauración inversa (revertir una recepción ya consumida).

### 3.5 Elegibilidad (`OD-19 §10, §11, §18`)

| Elegible ahora | Tipos |
|---|---|
| efecto en población de aves (`R-130`) | `bird_reception` · `mortality_recording` · `cull_recording` · `bird_exit` · `chick_dispatch` · `birth_registration` (viables + aves; validación ≥ 0) |
| sin efecto de saldo (solo KPI/registro) | `feed_registration` · `weight_recording` · `vaccination` · `medication` · `farm_inspection` · `transport_inspection` · `hatchery_inspection` · `bird_transfer` · `bird_distribution` |
| **`BLOCKED_BY_R-161`** | `egg_collection` · `egg_classification` · `egg_reception_classification` · `egg_dispatch` · `egg_reception_hatchery` · `incubation_load` · `ovoscopy` · `transfer_to_hatcher` |
| **no elegibles** (otros) | `lot_closure` · `grandparent_import` (`R-152`) |

Estado: solo `APPROVED`. `CONSOLIDATED` → `400 BR-16` (`DEFERRED`). Ya con reverso activo (contrapartida en
`PENDING_REVIEW`/`IN_REVIEW`/`CORRECTED`/`REVERSED`) → `409`. Contrapartida rechazada o cancelada no bloquea una nueva.

### 3.6 Autoridad (`OD-19 §7, §8, §13-§16`)

| Acto | Permiso | Quién |
|---|---|---|
| solicitar (`POST /reversals`) | **`reversals:create`** (módulo nuevo en el catálogo `MODULOS`; acción existente; sin migración) | cualquier actor con la capacidad, incluido el registrador original |
| leer (`GET /reversals`, `GET /reversals/event/{id}`) | `reversals:read` | ídem |
| aprobar / rechazar | `approvals:approve` / `approvals:reject` (motor existente) | aprobador ≠ solicitante (`BR-14` sobre `registered_by_id` de la contrapartida = solicitante: la regla existente lo cubre) |

Cadena productiva en todos los actos: empresa efectiva (`get_event`), unidad efectiva del actor (`predicado_de_evento`),
`exigir_unidad_operativa` (global: situada y unidad **habilitada**; apagada → `403`). Administrador de Accesos y
Contraloría (solo lectura/control): `403` por RBAC. Hasta que el propietario asigne la capacidad a un rol, `reversals:*`
queda en `SOLO_SUPER_ADMIN` (13 → **15**, techo `≤ 15` respetado; ningún rol sembrado la recibe: no se decide por él).

## 4. Criterios de aceptación

### Elegibilidad (`AC-RV`)

| AC | Criterio | Contrato |
|---|---|---|
| `AC-RV01` | `APPROVED` elegible + actor con `reversals:create` → solicitud creada: contrapartida `PENDING_REVIEW`, fila `reversals` vinculada, original sigue `APPROVED` | `201` |
| `AC-RV02` | estados no elegibles (`REGISTERED`, `PENDING_REVIEW`, `RETURNED`, `REJECTED`, `CORRECTED`, `CANCELLED`, `SAP_CONFIRMED`) → `400 BR-16`; `CONSOLIDATED` → `400 BR-16` (`DEFERRED`) | `400` |
| `AC-RV03` | original ya `REVERSED` → `400 BR-16`; con solicitud activa → `409`; una contrapartida efectiva por original | `400`/`409` |
| `AC-RV04` | `CANCELLED` no entra en el camino de reverso (`400 BR-16`); la contrapartida cancelada no es efectiva y permite nueva solicitud | `400`/`201` |
| `AC-RV05` | `RETURNED`/`REJECTED` (corregibles) no entran en el reverso; su vía sigue siendo `GA-REM-006-A` | `400` |
| `AC-RV06` | el original permanece inmutable: `PUT`/`POST /corrections`/`submit` sobre `APPROVED` → `400`; sobre `REVERSED` → `400`; la contrapartida no se edita ni corrige → `400` | `400` |
| `AC-RV07` | tipo `BLOCKED_BY_R-161` (`egg_collection`…) → `400 BR-16` con detalle explícito | `400` |

### Efecto (`AC-EF`)

| AC | Criterio |
|---|---|
| `AC-EF01` | mortalidad de 10 sobre saldo 100 (→ 90) · solicitud · aprobación → saldo **100**; original y contrapartida `REVERSED`; ambas filas existen |
| `AC-EF02` | recepción de 100 con consumo posterior de 30 (→ 70) · reverso aprobado → `400 BR-01` (saldo resultante −30) · original sigue `APPROVED`, contrapartida no efectiva |
| `AC-EF03` | sin sobre-compensación: tras el reverso de `EF01` el saldo es exactamente el previo al original |
| `AC-EF04` | segunda solicitud sobre el original `REVERSED` → `400`; efecto extra 0 |
| `AC-EF05` | aprobación fallida (saldo negativo) → cero cambios: estados, `reversals`, `approval_actions`, auditoría de éxito |
| `AC-EF06` | dos solicitudes concurrentes sobre el mismo original → exactamente **una** `201`, la otra `409`; una sola contrapartida |
| `AC-EF07` | evento sin efecto de saldo (`farm_inspection`) → reverso aprobado → ambos `REVERSED`; saldo invariante; `N/A` de compensación numérica documentado |

### Seguridad (`AC-S`)

| AC | Criterio | Contrato |
|---|---|---|
| `AC-S01` | actor de `B` sobre original de `A` → `404` | `404` |
| `AC-S02` | autoridad global sin empresa efectiva → `403`/`404` (fallo cerrado); situada en `B` sobre `A` → `404` | — |
| `AC-S03` | unidad **apagada**: actor con concesión histórica → `404`; autoridad global situada → `403` | — |
| `AC-S04` | actor sin la unidad (habilitada, no concedida) → `404` | `404` |
| `AC-S05` | sin `reversals:create` → `403` | `403` |
| `AC-S06` | Administrador de Accesos → `403` | `403` |
| `AC-S07` | control de solo lectura (Contraloría representada) → `403` | `403` |
| `AC-S08` | el cuerpo solo lleva `event_id` y `reason`; cantidades, unidad y empresa se derivan del original (`extra="forbid"`) | `422` |
| `AC-S09` | Progenitoras: reverso sobre lote `grandparent` por el actor de abuelas → `201`; por el actor de reproductoras → `404` | — |

### Motivo y auditoría (`AC-AU`)

| AC | Criterio |
|---|---|
| `AC-AU01` | sin `reason` → `422` |
| `AC-AU02` | `reason` en blanco / espacios / < 5 → `422` |
| `AC-AU03` | `reversals` guarda motivo, solicitante, fecha; la aprobación guarda aprobador (`approved_by_id`, `approval_actions`) |
| `AC-AU04` | `audit_logs`: original `approved → reversed` y contrapartida `in_review → reversed`, acción `REVERSED` |
| `AC-AU05` | `reversals.original_event_id` + `reversal_event_id` + `original_data_snapshot` permiten reconstruir el original |
| `AC-AU06` | solicitud denegada o aprobación fallida → sin auditoría de éxito ni fila `reversals` |

### `R-165` (`AC-165`)

| AC | Criterio |
|---|---|
| `AC-165-01` | autoridad global situada en `A`, evento (o contrapartida) en unidad **apagada**: `start` · `return` · `complete` · `approve` · `reject` → `403`; cero cambios |
| `AC-165-02` | ídem en unidad habilitada → contrato vigente (`200`) |
| `AC-165-03` | actor de empresa con concesión histórica sobre unidad apagada → `404` (control, `unidades_efectivas`) |
| `AC-165-04` | autoridad global sin contexto → `404` (control) |
| `AC-165-05` | `GET /business-units` y `PATCH …/disable` por el Administrador de Accesos siguen `200` (plano de control intacto) |

## 5. Rutas y guardianes (justificación explícita)

| Ruta | Permiso | `route_scope` | Por qué existe |
|---|---|---|---|
| `POST /api/v1/reversals` | `reversals:create` | `MULTI_UNIDAD` | `OD-19 §6/§8`: acto semántico propio; no es corrección ni cancelación |
| `GET /api/v1/reversals` | `reversals:read` | `MULTI_UNIDAD` | trazabilidad (`OD-19 §21`) |
| `GET /api/v1/reversals/event/{event_id}` | `reversals:read` | `MULTI_UNIDAD` | ídem, por original |

Guardianes que cambian **exactamente**: rutas `208 → 211` (`test_ac14_sin_migracion_ni_rutas_nuevas`); cabeza de Alembic
`s9t0u1v2w3x4 → t0u1v2w3x4y5` (`test_ac14…`, `test_t10_ac20_ac21…`); `SOLO_SUPER_ADMIN` `13 → 15`
(`≤ 15`). `test_business_unit_admin == 7` no cambia. Ningún `>=`.

## 6. Tareas

| Tarea | Contenido |
|---|---|
| `T-041-01` | pruebas rojas `backend/tests/test_internal_reversal.py` (fixture: `A` breeder/grandparent ON, hatchery OFF; `B`; lotes con saldo; originales `APPROVED` por tipo; actores: solicitante, aprobador, sin permiso, lectura-control, Administrador de Accesos, `B`, global) y `tests/test_review_bu_enforcement.py` (`R-165`) |
| `T-041-02` | migración `t0u1v2w3x4y5`: `ALTER TYPE eventstatus ADD VALUE IF NOT EXISTS 'REVERSED'` · `ALTER TYPE auditaction ADD VALUE IF NOT EXISTS 'REVERSED'` (fuera de transacción, patrón `r8s9t0u1v2w3`); `downgrade` documentado como no reversible del tipo (PostgreSQL no quita valores) |
| `T-041-03` | `EventStatus.REVERSED`, `AuditAction.REVERSED`, `audit_state_transition` mapa; `MODULOS` + `reversals` |
| `T-041-04` | `app/reversals/` (`schemas`, `service`, `router`): solicitud (bloqueo del original, elegibilidad, contrapartida, `reversals`, auditoría), lecturas; `route_scope` |
| `T-041-05` | `review/service`: `_efectuar_reverso_si_procede(event)` invocado desde `approve` y `complete_review` (un nivel); `_get_event`/`_get_event_for_approval` + `exigir_unidad_operativa` (`R-165`) |
| `T-041-06` | `operations/service`: contrapartida no editable/corregible; `validators`: saldos con contrapartidas efectivas |
| `T-041-07` | guardianes exactos (§5); sensibilidad; regresión; evidencia `R-136-INTERNAL-REVERSAL-EVIDENCE.md`; cierre parcial |

## 7. Sensibilidad

| Mut. | Retira | Debe caer |
|---|---|---|
| `S1` | la guarda de estado origen en la solicitud (cualquier estado reversa) | `AC-RV02` |
| `S2` | la guarda «ya revertido / solicitud activa» | `AC-RV03`/`AC-EF04` (segunda contrapartida) |
| `S3` | la compensación en los saldos (contrapartidas efectivas no restan) | `AC-EF01` (saldo 90 en vez de 100) |
| `S4` | doble compensación (la contrapartida efectiva resta dos veces) | `AC-EF03` |
| `S5` | la empresa (tres capas, como en el tranche 4: `get_event`, `lotes_alcanzables`, `_unidad_del_lote`) | `AC-S01` con escritura observada |
| `S6` | la habilitación en la solicitud (guarda compartida) y en el plano de revisión (`R-165`) | `AC-S03`, `AC-165-01` |
| `S7` | `reversals:create` → `reversals:read` en la ruta | `AC-S05`/`S07` |
| `S8` | la auditoría `REVERSED` de la aprobación | `AC-AU04` |
| `S9` | el bloqueo `FOR UPDATE` del original en la solicitud | `AC-EF06` (dos `201`) — si no reproduce determinísticamente, se registra la limitación |

## 8. Definición de terminado

`AC-RV01…07`, `AC-EF01…07`, `AC-S01…09`, `AC-AU01…06`, `AC-165-01…05` verdes · rojo válido · `S1–S9` según §7 ·
`R-130` 21/21 · tranche 2/3/4 suites · `R-139` 35/35 · guardianes exactos · regresión completa · migración aplicada por
`upgrade` en la base de pruebas (`test_los_enums_de_python_existen_en_postgresql`) · sin frontend · `R-136` interno
cerrado, `R-136` **PARTIAL**, SAP diferido · `R-165` cerrado · certificación de proceso `BLOCKED_RUNTIME`.

## 9. Plan de migración

`t0u1v2w3x4y5_reversed_status.py` · revises `s9t0u1v2w3x4` · `upgrade`: dos `ALTER TYPE … ADD VALUE IF NOT EXISTS` (idempotentes,
fuera de bloque transaccional como `a1b2c3d4e5f6`) · `downgrade`: sin efecto sobre el tipo (documentado; PostgreSQL no
elimina valores de enumerados) — ninguna fila tendrá `REVERSED` si se baja antes de usarlo; si las hay, la bajada se
detiene con error explícito. Sin datos migrados. `test_upgrade_path` (script dedicado) queda como estaba.

---

# Enmienda A · la capacidad de reverso tiene titulares sembrados (2026-09-09 · WAVE B tranche 6 · pre-flight)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-041-A` · `ROLE GOVERNANCE` · **Estado** `SPEC_READY` |
| **Decisión** | `OD-19` **Aclaración A** (propietario) |
| **Cambio** | solo semillas y pruebas de gobierno: `dev_seeds` y `test_seeds` «Supervisor Avícola» + `reversals:create`, `reversals:read`; `integration_seeds` «Contralor Avícola» + `reversals:read`; `SOLO_SUPER_ADMIN` **15 → 13** (los dos permisos dejan de ser exclusivos de la autoridad global: el guardián se reduce, no se amplía) |
| **Sin cambio** | motor de reverso, estados, compensación, rutas, `OD-19 §1-§24`; `R-136` interno sigue cerrado. *«Sin migración» decía la versión inicial: la enmienda B lo corrige — las semillas solo sirven a instalaciones nuevas (`R-44`)* |

## A.1 Criterios de aceptación (`REV-R`)

| AC | Criterio | Fuente de verdad |
|---|---|---|
| `REV-R01` | «Supervisor Avícola» concede `reversals:create` | `dev_seeds.py`, `test_seeds.py` |
| `REV-R02` | «Supervisor Avícola» concede `reversals:read` | ídem |
| `REV-R03` | «Contralor Avícola» concede `reversals:read` | `integration_seeds.py` |
| `REV-R04` | «Contralor Avícola» **no** concede `reversals:create` | ídem |
| `REV-R05` | «Administrador de Accesos» no concede ninguno (sigue con sus cuatro `business_units:*`) | `dev_seeds.py`, `OD-15 §6` |
| `REV-R06` | «Operador de Granja» no concede ninguno | `dev_seeds.py` |
| `REV-R07` | ningún rol sembrado gana `("*", …)` ni `scope_type = all`; «Supervisor Avícola» no gana `approvals:*`, `users:*` ni `business_units:*` | los tres ficheros de semillas |
| `REV-R08` | en tiempo de ejecución, un usuario con el rol sembrado «Supervisor Avícola» solicita un reverso (`201`) y **no** puede aprobarlo (`BR-14`, sin `approvals:approve` → `403`) | `test_reversal_role_matrix.py` |

Sensibilidad `S9` (encargo §84): (a) dar `reversals:create` a «Contralor Avícola» → `REV-R04` roja; (b) darle `reversals:read`
al «Administrador de Accesos» → `REV-R05` roja; (c) quitar `reversals:create` al «Supervisor Avícola» → `REV-R01`/`R08` rojas.

---

# Enmienda B · la asignación llega a las instalaciones existentes y al baseline (2026-09-10 · WAVE B tranche 6 · hallazgo de la regresión completa)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-041-B` · `ROLE GOVERNANCE` / `DATA MIGRATION` · **Estado** `SPEC_READY` |
| **Decisión** | `OD-19` Aclaración A — **sin cambio** de titulares ni de semántica |
| **Hallazgo** | La regresión completa tras `cdb0670` dejó roja `test_clean_baseline::test_t_025_02` (`GA-REM-025 AC03`: 46 asociaciones para los 5 roles operativos). La **fuente única** de la matriz RBAC para las instalaciones existentes y para el baseline es `PERMISOS_POR_ROL` de la migración de reconciliación `l2m3n4o5p6q7` (`R-44`: «actualizar las semillas no basta: las semillas sirven a instalaciones nuevas»), que `seeds/baseline_seeds.py` importa. La enmienda A cambió solo semillas, así que una instalación ya desplegada **nunca recibiría** la capacidad decidida por el propietario, y el baseline tampoco la sembraría. Las pruebas dirigidas no lo vieron porque `test_clean_baseline` no estaba entre ellas: solo la regresión completa lo mostró (por eso se lee antes de certificar). |
| **Corrección** | (1) migración de datos **`v2w3x4y5z6a7`** (revisa `u1v2w3x4y5z6`) con `PERMISOS_ADICIONALES`: «Supervisor Avícola» + `reversals:create`, `reversals:read`; «Contralor Avícola» + `reversals:read`. Mismo contrato que `l2m3n4o5p6q7`: **solo añade**, idempotente, tolera el rol ausente (no crea roles). A diferencia de aquella, **sí se revierte**: el módulo `reversals` nace con `OD-19`, no existe personalización previa que confundir, y la bajada retira exactamente esas asociaciones. (2) `baseline_seeds._matriz_de_la_migracion()` **compone** la base (`l2m3n4o5p6q7`) con los deltas de las migraciones de reconciliación posteriores, solo para roles que ya están en la base: el baseline no inventa roles («Contralor Avícola» sigue viviendo en `integration_seeds`, `OD-19` Acl. A). Sigue habiendo una copia de cada hecho. (3) `GA-REM-025 AC03`: **46 → 48** por `OD-19` Aclaración A. |
| **Sin cambio** | las semillas de la enmienda A · `SOLO_SUPER_ADMIN` 13 · motor, rutas, estados · `OD-19 §1-§24` |

## B.1 Criterios de aceptación

| AC | Criterio | Fuente de verdad |
|---|---|---|
| `REV-R09` | sobre una instalación con «Supervisor Avícola» **sin** los dos permisos, aplicar la migración los añade; aplicarla de nuevo no duplica ni añade nada más | `tests/test_reversal_role_migration.py` |
| `REV-R10` | la matriz compuesta del baseline concede `reversals:create`/`read` al «Supervisor Avícola», suma **48** asociaciones para los 5 roles operativos y **no** contiene «Contralor Avícola» | `seeds/baseline_seeds._matriz_de_la_migracion` · `test_clean_baseline::test_t_025_02` |
| `REV-R11` | la bajada retira exactamente las asociaciones del delta y ninguna otra; volver a subir las repone | `tests/test_reversal_role_migration.py` |
| `REV-R12` | guardianes exactos: cabeza `v2w3x4y5z6a7` · rutas 211 · `test_t_025_02 == 48` · `SOLO_SUPER_ADMIN == 13` | guardianes |

## B.2 Sensibilidad

`S9d`: la composición del baseline no aplica el delta → `REV-R10` y `test_t_025_02` rojas. `S9e`: la migración no inserta → `REV-R09` roja.

## B.3 Definición de terminado

`REV-R09…R12` verdes · rojo válido · `S9d`/`S9e` válidas · regresión completa **leída** en verde · sin cambio en `OD-19`.
