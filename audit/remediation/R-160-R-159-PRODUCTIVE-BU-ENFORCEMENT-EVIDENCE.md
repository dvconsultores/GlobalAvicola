# EVIDENCIA · `R-160` + `R-159` · LA UNIDAD DE NEGOCIO SE EXIGE AL OPERAR SOBRE `operations`

**WAVE B · tranche 2** · 2026-09-09 · spec `GA-REM-040` enmienda G (commit `9d21d40`) · matriz previa
`R160_R159_OPERATION_BU_AUTHORITY_MATRIX.md` · base `57e22b6` · rama `main`

## 1. Alcance certificado (frontera técnica)

| Hallazgo | Sev. | Superficies | AC | Resultado |
|---|:--:|---|---|---|
| `R-160` | P1 | `POST /operations` · `PUT /operations/{id}` (lote y ubicación destino) · `submit` · `cancel` · `POST/DELETE …/evidences` · `PATCH alerts/{id}/resolve` (global) | `AC-W01…W15` (W08 `N/A`) | **CERRADO** (técnico) |
| `R-159` | P2 | `GET /operations/alerts` · `PATCH alerts/{id}/resolve` (actor) | `AC-A01…A13` (A10 `N/A`) | **CERRADO** (técnico) |

Certificación de proceso de negocio: **no** (`BLOCKED_RUNTIME`, sin E2E). Ninguna fase se certifica por
transitividad; ningún endpoint queda «certificado» por sí solo.

## 2. Rojo previo (`T-040-G1`) · validez

`tests/test_operations_bu_enforcement.py` · 39 pruebas · **23 rojas · 16 verdes (controles)** sobre `9d21d40`
(spec sin código). Cada roja cae en la aserción de contrato, no en fixture, import ni `NameError` (0 errores
no de aserción; el único `AttributeError` del log es el aviso conocido de `bcrypt.__about__`, atrapado).

| Prueba | AC | Aserción roja (observado ≠ exigido) | Válida |
|---|---|---|---|
| `w02_la_unidad_apagada_bloquea_aunque_haya_concesion_historica` | W02 | `201` con cuerpo del evento ≠ `400 BR-07` | sí |
| `w03_la_unidad_habilitada_sin_concesion_bloquea` | W03 | `201` ≠ `400 BR-07` | sí |
| `w03b_cero_unidades_efectivas_no_opera_dato_productivo` | W03b | `201` ≠ `400 BR-07` | sí |
| `w03b_cero_unidades_efectivas_tampoco_crea_dato_pendiente` | W03b | `assert 201 == 403` | sí |
| `w05_progenitoras_el_actor_de_abuelas_no_escribe_en_reproductoras` | W05/W15 | `201` ≠ `400 BR-07` | sí |
| `w06b_la_evidencia_de_un_evento_de_unidad_no_alcanzable_no_se_borra` | W06 | `assert 204 == 404` | sí |
| `w09_…_a_un_lote_de_otra_unidad` | W09 | `200` (evento repuntado) ≠ `400 BR-07` | sí |
| `w09_…_a_un_lote_de_otra_empresa` | W09 | `200` ≠ `400 BR-07` | sí |
| `w09_…_la_ubicacion_a_otra_empresa` | W09 | `200` ≠ `400 BR-07` | sí |
| `w13_la_autoridad_global_situada_no_crea_sobre_unidad_apagada` | W13 | `assert 201 == 403` | sí |
| `w13_submit_…` | W13 | `assert 200 == 403` | sí |
| `w13_cancel_…` | W13 | `assert 200 == 403` | sí |
| `w13_upload_…` | W13 | `assert 201 == 403` | sí |
| `w13_delete_…` | W13 | `assert 204 == 403` | sí |
| `a01_a04_el_actor_ve_exactamente_las_alertas_de_sus_unidades_efectivas` | A01/A04 | `{al_r, al_p, al_h, al_g} == {al_r, al_p}` | sí |
| `a02_la_unidad_apagada_con_concesion_historica_no_aporta_alertas` | A02 | `al_h in …` | sí |
| `a03_la_unidad_habilitada_sin_concesion_no_aporta_alertas` | A03 | `al_g in …` | sí |
| `a03_progenitoras_el_actor_de_abuelas_ve_solo_las_suyas` | A03/W15 | `{4 alertas} == {al_g}` | sí |
| `a05_cero_unidades_efectivas_es_lista_vacia` | A05 | `[4 alertas] == []` | sí |
| `a07_el_predicado_precede_a_la_paginacion` | A07 | `al_g in {al_r, al_p}` (la ajena consumió la página) | sí |
| `a07_el_filtro_por_lote_no_salta_el_predicado` | A07 | `[al_g] == []` | sí |
| `a13_resolver_una_alerta_de_unidad_no_alcanzable_es_404` | A13 | `assert 200 == 404` | sí |
| `a13_la_autoridad_global_no_resuelve_sobre_unidad_apagada` | A13 | `assert 200 == 403` | sí |

Controles verdes en rojo (16): `w01`, `w03c`, `w04`, `w05` positivo, `w06`, `w07`, `w10`, `w12`, `w14` ×2,
`a06`, `a08`, `a09`, `a11`, `a12`, `a13` positivo. **Corrección de fixture tras el rojo** (no del contrato):
dos post-condiciones de `w13_submit`/`w13_cancel` comparaban `status = 'registered'` y el tipo de la columna
guarda el nombre del enumerado (`REGISTERED`); la aserción de `403` ya había fallado antes por su motivo. Se
cambió a `upper(status::text)`. Ninguna prueba se debilitó.

## 3. Implementación (`T-040-G2…G4`) · `app/operations/service.py` (+145/−9) · `router.py` (+4)

| Pieza | Qué hace |
|---|---|
| `_unidad_del_lote(lot_id)` | `lot.bird_type → código` del lote **de la empresa efectiva** (`_acotar_a_empresa`); ajeno o sin empresa → `BR-07 «Lote no encontrado»`; sin tipo → `None` (pendiente) |
| `_unidad_clasificada(cbu_id)` | código de la habilitación fijada por el plano de control (fase 6) |
| `exigir_unidad_operativa(lot_id= \| event=)` | la guarda: deriva la unidad y aplica `§G.3` — actor de empresa: `unidad ∈ unidades_efectivas` o `BR-07`; pendiente: ≥ 1 efectiva o `403`; autoridad global: situada con habilitaciones y `unidad ∈ unidades_habilitadas` o `403` |
| `create_event` | la guarda **antes** de `_apply_business_rules` y de `db.add` |
| `update_event` | `lot_id` nuevo → `validate_lot_active(empresa)` + `validate_event_date`; `farm/house/destination` → `verificar_ubicacion`; guarda sobre el lote destino (o el actual) |
| `submit_to_review` · `cancel_event` · `create_evidence` | guarda tras `get_event` |
| `delete_evidence` | `get_event` (404 por unidad) + guarda antes de buscar la evidencia |
| `_acotar_alertas_a_unidades` · `get_alerts` | `lot_id IN lotes_alcanzables(empresa, efectivas)` en la consulta, antes de `order/offset/limit`; global: sin predicado (visibilidad certificada) |
| `resolve_alert` | mismo predicado (`404`) + guarda (global sobre apagada `403`) |
| `router.upload_evidence` | guarda antes de escribir el fichero (sin huérfanos) |

Sin rutas nuevas (17 → 17 en `operations`), sin migración (`s9t0u1v2w3x4`), sin campo de unidad en el
cuerpo, sin `is_global_actor`, sin lógica por nombre de rol (3 usos nuevos de `is_super_admin`, la capacidad
comodín resuelta en sesión, en la misma convención que `get_events`/`get_event`). `exigir_acceso_a_unidad`
sigue sin llamadores: la guarda de `operations` necesita el diccionario de sesión y la derivación por lote,
no el ORM del usuario; la regla (`AC-C08`, `AC-C16`) vive ahora en el servicio y es invocable desde el
enrutador.

## 4. Verde dirigido (`T-040-G2…G4`)

| Suite | Resultado |
|---|---|
| `test_operations_bu_enforcement.py` · **`R-160`** (`w*`, 24 pruebas incl. la de lote cerrado añadida tras `S4b`) | **24/24** |
| `test_operations_bu_enforcement.py` · **`R-159`** (`a*`, 16 pruebas) | **16/16** |
| `test_od14_productive_surfaces.py` (`R-139`) | **35/35** (tras reordenar `delete_evidence`; ver §6) |
| `test_population_invariant.py` (`R-130`) | **21/21** |
| relacionadas: `business_unit_admin` (`== 7`) · `business_unit_guard` · `business_units` · `grant_candidates` · `kpi_scope` · `lot_row_scope` · `master_tenant_isolation` · `operations` · `pending_classification` · `session_payload` (`OD-15`) · `user_tenant_isolation` · `weight_alert` · `rbac` (`SOLO_SUPER_ADMIN ≤ 15`) · `runtime_startup` · `transaction_boundary` · `access_administration` · `audit_coverage` | **397 passed · 14 skipped · 3 failed** en la primera pasada (las 3 = `R-139 S03`, contrato `403` entre inquilinos; corregido el orden, 74/74 en la repetición de `R-139` + suite nueva); las demás sin cambio |

## 5. Sensibilidad (`§G.8`) · 9 mutaciones · 8 ejecutadas válidas · 3 `N/A` con motivo

Cada mutación se aplica marcada `MUTACION`, se ejecuta la suite completa del tranche (39 pruebas; 40 en la
repetición de `S4b`), se revierte con `git checkout --` y se comprueba `git diff --quiet -- app/` y
`grep -c MUTACION == 0`. Todas revertidas limpias.

| Mut. | Qué retira | Debía caer | Cayó | Válida |
|---|---|---|---|:--:|
| `S1` | la guarda de unidad en el alta (`exigir_unidad_operativa(lot_id=…)` → `pass`) | `W02`, `W03`, `W05` | **6**: `w02`, `w03`, `w03b` ×2, `w05`, `w13` (alta global sobre apagada) | sí |
| `S2` | la habilitación de la empresa (`is_enabled.is_(True)` → `in_((True, False))` en `unidades_efectivas_por_id`) | `W02` | **4**: `w02`, `a01_a04`, `a02`, `a07` (paginación: `al_h` entra) | sí |
| `S3` | confiar en la unidad del payload | — | **`N/A`**: `OperationalEventBase`/`Update` no declaran `business_unit_id` ni `company_id` (0 coincidencias; `Update` es `extra="forbid"`): no hay campo que mutar | — |
| `S4` | la guarda sobre el lote destino en la edición | `W09` | **1**: `w09` otra unidad | sí |
| `S4b` (extra) | `validate_lot_active` en la edición | — | 1.ª pasada **0** (sobrevivió: la guarda ya cubre la empresa); se añadió `w09_…_lote_cerrado`; 2.ª pasada **1**: esa prueba | sí (tras corregir la suite) |
| `S5` | el predicado de unidad en `get_alerts` | `A01`/`A02`/`A05` | **7**: `a01_a04`, `a02`, `a03` ×2, `a05`, `a07` ×2 | sí |
| `S6` | el orden predicado → paginación (predicado fuera de la consulta; filtro en Python tras `limit`) | `A07` | **1**: `a07_el_predicado_precede_a_la_paginacion` (solo ella: el resto pasa con `limit=50`) | sí |
| `S7` | la empresa efectiva para la autoridad global sin contexto (unión de inquilinos) | `A09` (control `R-139`) | **1**: `a09` | sí |
| `S8` | tratar una capacidad de control como autoridad productiva | — | **`N/A`**: la guarda no mapea capacidades; el Administrador de Accesos cae en `require_permission` antes del servicio (`w10`, `a11` verdes en todas las pasadas); no existe rama de código que mutar sin inventarla | — |
| `S9` | `get_event` + guarda en el borrado de evidencia | `W06` | **2**: `w06b`, `w13_delete` | sí |

`git diff --quiet -- app/` tras cada reversión: limpio (8/8 + `S4b` ×2). `grep -c MUTACION`: 0.

## 6. Correcciones durante el tranche (todas documentadas, ninguna decide por el propietario)

| # | Qué | Clase | Dónde |
|---|---|---|---|
| 1 | el orden del borrado de evidencia: la primera redacción de `§G.4` ponía `get_event` delante de la comparación de empresa y convertía el `403` certificado por `R-139` (`AC-S03`, 3 pruebas) en `404` | corrección de redacción de la enmienda (la spec certificada y cerrada prevalece: `R-139` sigue cerrado) | `GA-REM-040-G §G.4`, matriz fila `W6`, `delete_evidence` |
| 2 | dos post-condiciones comparaban `status = 'registered'` con una columna que guarda el nombre del enumerado | corrección de fixture tras el rojo; la aserción de contrato ya había caído por su motivo | `w13_submit`, `w13_cancel` |
| 3 | `S4b` sobrevivía: `validate_lot_active` en la edición solo aporta el estado del lote, sin prueba | prueba añadida (`w09_…_lote_cerrado`); `S4b` repetida: 1 roja | suite |
| 4 | `test_lot_closure.py::test_t_073_06` (`GA-REM-029 AC07`): el montaje del CONTROL registraba eventos (`weight_recording`…) con el sujeto **antes** de habilitar y concederle unidades; con cero unidades efectivas esa escritura era posible solo por el defecto que `R-160` cierra (`OD-09.c`) → ahora `400 BR-07` | **TEST FIXTURE DEPENDENCY ON DEFECT**: se movió `habilitar_y_conceder_todo` antes de `_lote_cerrable`; la aserción del cierre (200 propio · 404 ajeno) no cambia; regresión completa repetida | `tests/test_lot_closure.py` |

Ninguna prueba se debilitó; ningún contrato certificado cambió; ninguna decisión pendiente (`AOD-*`, `BU-D10`) se resolvió.

## 7. Regresión

| Comprobación | Resultado |
|---|---|
| backend completo (`scripts/run_tests.sh`, pgserver aislado) | 1.ª pasada **890 passed · 49 skipped · 1 failed** (972 s): `test_t_073_06`, dependencia de fixture del defecto (§6.4) · 2.ª pasada, tras ajustar solo el montaje: **891 passed · 49 skipped · 0 failed** (838 s; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) |
| `R-130` (`test_population_invariant.py`) | 21/21 · sin cambios en `validators.py` |
| `R-139` (`test_od14_productive_surfaces.py`) | 35/35 |
| `OD-16` (`test_business_units.py`, `test_grant_candidates.py`) · Progenitoras (`w05` ×2, `a03_progenitoras`) | verdes |
| cero concesiones (`OD-09.c`: `w03b` ×2, `a05`) · Administrador de Accesos (`OD-15`: `w10`, `a11`, `test_session_payload.py`, `test_access_administration.py`) | verdes |
| Contraloría | `N/A` (sin resolutor; ninguna ruta de `operations` la reconoce) |
| SAP transversal | 0 ficheros `sap` tocados desde `57e22b6` |
| `RQ-03` · `R-121`/`OD-15`/`R-113`/`R-129` | suites de `rbac`, `session_payload`, `access_administration`, `user_tenant_isolation` verdes |
| fase 7 (`test_business_unit_admin` `== 7`) · fase 8 · guardianes (`runtime_startup`, `transaction_boundary`, `audit_coverage`, `rbac` `SOLO_SUPER_ADMIN ≤ 15`) | verdes / saltados por diseño en la completa |
| migración | ninguna; `alembic heads` = `s9t0u1v2w3x4` |
| rutas | `operations` 17 → 17; `authorization_coverage` sin cambio |
| `vitest` | 87/87 (8 ficheros) |
| `tsc -b --noEmit` | 6 errores, los mismos preexistentes (`AuditPage.tsx` ×2, `LotFormPage.tsx` ×4) = `R-158` |
| E2E | `BLOCKED_RUNTIME` (sin cambio) |
| `EX-01` · Watchtower · `pull_policy` · auto-deploy | intactos (0 ficheros de despliegue en el diff) |

## 8. Puertas de cierre

```
SPEC ............ GA-REM-040 enmienda G (9d21d40) antes del código          ✔
AC .............. AC-W01…W15 · AC-A01…A13, en la enmienda                  ✔
ROJO VÁLIDO ..... 23/39 por la aserción de contrato · 0 errores            ✔
VERDE ........... 40/40 (R-160 24/24 · R-159 16/16)                         ✔
SENSIBILIDAD .... S1, S2, S4, S4b, S5, S6, S7, S9 válidas · S3, S8 N/A     ✔
REGRESIÓN ....... completa leída antes de este commit                       ✔  (**891 passed · 49 skipped · 0 failed** (838 s; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado))
EVIDENCIA ....... este documento                                           ✔
E2E ............. BLOCKED_RUNTIME → certificación de proceso NO             —
```

`R-160` **CERRADO** (técnico) · `R-159` **CERRADO** (técnico). No se certifica ningún proceso de negocio ni
ninguna fase por transitividad; la enmienda G queda `CERTIFIED` en su frontera técnica.

## 9. Fuera de alcance — no tocado

`R-161` (OPEN) · `R-135` `R-136` `R-140` `R-142` `R-143` `R-144` `R-147` `R-148` `R-152` `R-153` `R-154` `R-156` ·
`GA-REM-021` · ola C · fase 9 (FROZEN) · `R-158` · SAP · `BU-D10` (PENDING_RATIFICATION; las fixtures siembran
`is_enabled` explícitamente) · fórmula de población · concurrencia de huevos · máquina de estados · reverso · agua ·
frontend · `P-08` · `R-99` · `EX-01` · **`R-162`** y **`R-163`** (registrados en este tranche, P2, misma raíz; no
remediados: el primero es lectura de fichero, el segundo vive en `lots`/`masters` y exige su propia enmienda).

## 10. Siguiente tranche (identificado, NO iniciado)

`R-135` + `R-143` (+ `R-140` motivo/guarda · `R-154` `DRAFT`/`version`): máquina de estados de `P-07`, `OD-17`
vigente; P1; sin SAP, sin fase 9, sin `BU-D10`. Es el tranche 3 del orden fijado en
`WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md §3`; su pre-flight decide la spec que lo gobierna.
