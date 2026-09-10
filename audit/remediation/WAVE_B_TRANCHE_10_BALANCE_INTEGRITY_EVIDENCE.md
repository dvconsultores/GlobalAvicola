# Evidencia · WAVE B · tranche 10 — `R-173` (edición/anulación frente a los saldos) · `R-172` (huevo fértil = disponible) · `R-174` (despacho de pollitos > 0) · `R-171` (catálogo de incubadora) · `R-175` (control de orden)

**Fecha** 2026-09-10 · **Baseline de entrada** `main` · `4f70273` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211 ·
**Modo** A (`R-173` → `R-172` → `R-174` → `R-171`) · **Commits** `c56b2de` (spec) · `64dff76` (implementación + pruebas) · evidencia (este) ·
**Sin migración** · **Sin decisión del propietario**.

## 1. Pre-flight (commit `c56b2de`, solo spec)

| Hallazgo | Clasificación | Autoridad | Artefacto |
|---|---|---|---|
| `R-173` | **ACTIVE · GOBERNADO · P1** (normalizado desde P2: saldo negativo al anular entradas; efecto movido sin validación por `PUT`; **corrección de `lot_id` sin empresa/unidad/activo/fecha/ubicación** → reasignación entre empresas; sin bloqueo) | `docs/12 §3` (editar antes de enviar) · `GA-REM-040-G AC-W09` (destino de una edición = alta) · `GA-REM-005-B §B.2` / `D §D.1.4` (saldo ≥ 0 bajo bloqueo) · `docs/13 §2` (auditoría con valor anterior/nuevo) → **modelo B**; la premisa de `B.2` («`cancel` solo aumenta») era incompleta | `R173_EDIT_CANCEL_BALANCE_EFFECT_MATRIX.md` · `GA-REM-005-E` · `RC-15`/`RR-18` |
| `R-172` | **ACTIVE · GOBERNADO · P2** (100 fértiles + 70 de otros tipos → despachaba 170) | `Bases` p.7-8 («Traslado de huevos fértiles»), p.9 («Número de Huevos Recibidos: cantidad de huevos fértiles recibidos») · `docs/02 §3.6.4/§3.7.1` · `spec.md :166/:176/:187` → un predicado (`fertile`), dos saldos | `R172_EGG_TYPE_AVAILABILITY_MATRIX.md` · `GA-REM-005-F` · `RC-14`/`RR-17` |
| `R-174` | **ACTIVE · GOBERNADO · P3** | `GA-REM-005-B §B.2` nombra «despacho de pollitos» en `D` con `cantidad(D) > 0`; `validate_chick_dispatch` ya rechazaba 0 y el servicio lo esquivaba | `R174_ZERO_QUANTITY_DISPATCH_AUTHORITY_TRACE.md` · `GA-REM-005-E §E.3` |
| `R-171` | **UI_ONLY confirmado · P2** (backend acepta, persiste y resta de viables una vez: `AC-R161-16`; el catálogo era lo único que faltaba; i18n existente) | `RR-16` (`RC-13`) · `Bases` p.10 · `Rec. §12` | `R171_HATCHERY_MORTALITY_DISCARD_TRUTH_MATRIX.md §4` · `GA-REM-021-D` |
| `R-175` | **NON-BLOCKING** (control: aisladas 4/4 · B→A 3/3 · A→B 3/3 rojas por «las fases se duplicaron: 5», residuo reproducido bajo control; alfabético limpio; las suites nuevas no tocan `productive_phases`) | regla permanente C/D | `R175_TEST_ORDER_DEPENDENCY_CONTROL.md` |
| registrados | `R-176` (edición sin reglas no keyed por lote: `BR-17`, `BR-18`, fecha) · `R-177` (`egg_type` sin enum; formulario de recepción en incubadora con categorías de ovoscopía) · `R-178` (linaje `egg_batches`/`chick_batches` no neutralizado) — P3, fuera | — | backlog |

Recuento canónico tras las altas: **34** · 13 cerrados · 4 parciales · 17 abiertos (P1 1 · P2 8 · P3 8) · decisiones 8.

## 2. Rojo válido (leído en `4f70273`, antes de tocar código) — `§59`

Backend: `tests/test_edit_cancel_balance.py` + `tests/test_egg_type_availability.py` → **19 failed · 5 passed** (53 s). Frontend: **4 failed · 5 passed**.

| Prueba | Hallazgo · AC | Ruta · actor · permiso · empresa · unidad · recurso · estado | Saldo inicial → acción → esperado → **real** → saldo final | Por qué es el defecto |
|---|---|---|---|---|
| `test_r173_02_mover_una_salida_a_un_lote_sin_saldo_se_deniega` | `R-173` · `AC-R173-02` | `PUT /operations/{id}` · operador · `operations:update` · A · breeder/hatchery · descarte de 80 sobre `lr` (100) → `lr2` (50) · `REGISTERED` | `lr` 20, `lr2` 50 → mover → `400 BR-01` → **`200`** → efecto movido (`lr2` −30) | destino sin regla de saldo |
| `test_r173_03_10_…verdad_final_y_auditada` | `AC-R173-10` | ídem, movimiento válido | → `200` con `previous_values.lot_id`/`new_values.lot_id` → **`(None, None)`** | auditoría sin valores (`docs/13`) |
| `test_r173_04_mover_una_entrada_conserva_el_origen_no_negativo` | `AC-R173-04` | recepción de 100 con descarte de 30 → `lr2` | `lr` 70 → mover → `400 BR-01` → **`200`** → `lr` −30 | origen sin invariante |
| `test_r173_05_cancelar_una_entrada_que_dejaria_negativo_se_deniega` | `AC-R173-05` | `POST /operations/{id}/cancel` · operador · `operations:create` · recepción de 100 con descarte de 30 | 70 → anular → `400 BR-01` → **`200`** → −30 | anulación sin invariante |
| `test_r173_08_carrera_cancelar_una_entrada_frente_a_salidas_concurrentes` | `AC-R173-08` | `gather(cancel, 5 × descarte de 20)` en tres lotes | 100 → `≥ 0` → **`cancel 200` + `[201 ×5]`, saldo −100 en los tres lotes** | sin bloqueo en `cancel` |
| `test_r173_09_carrera_mover_una_entrada_frente_a_una_salida_en_el_origen` | `AC-R173-09` | `gather(PUT lot_id→B, salida de 100 en A)` | → exactamente una → **`200` + `201`, A = −100** | sin bloqueo en la reasignación |
| `test_r173_11_correccion_de_lote_a_otra_empresa_se_deniega` | `AC-R173-11` | `POST /corrections` · operador · `corrections:correct` · `lot_id` → lote de **B** | → `400 BR-07` → **`201`** (evento de A apuntando a un lote de B) | corrección sin control de inquilino |
| `test_r173_12_…unidad_apagada_o_sin_concesion` | `AC-R173-12` | corrección `lot_id` → lote broiler (unidad **apagada** en A) | → `400 BR-07` → **`201`** | sin control de unidad |
| `test_r173_13_…destino_sin_saldo_inactivo_o_con_fecha_invalida` | `AC-R173-13` | corrección `lot_id` → `lr2` sin saldo | → `400 BR-01` → **`201`** | sin regla de saldo |
| `test_r173_14_correccion_de_ubicacion_a_otra_empresa_se_deniega` | `AC-R173-14` | corrección `farm_id` → granja de B | → `400 BR-07` → **`201`** | sin `verificar_ubicacion` |
| `test_r174_01_despacho_de_cero_pollitos_se_rechaza_sin_fila` | `R-174` · `AC-R174-01` | `POST /operations` · `chick_dispatch` de 0 · lote `lh` (100 nacidos) | → `400 BR-04`, sin fila → **`201`** (fila, auditoría, notificación) | guarda `if total_qty > 0` |
| `test_r172_02_05_recoleccion_mixta…` | `R-172` · `AC-R172-02` | recolección `fertile 100 + dirty 50 + broken 10 + infertile 5 + discarded 5` | disponibles 100 → **170** | todos los tipos cuentan |
| `test_r172_03_…[dirty, broken, infertile, discarded, commercial]` (5) | `AC-R172-03` | recolección de 50 de un tipo no disponible | 0 → **50** | ídem |
| `test_r172_04_un_despacho_con_fila_no_fertil_se_rechaza_sin_fila` | `AC-R172-04` | despacho `[fertile 10, dirty 5]` | `400 BR-02` → **`201`** | el despacho acepta cualquier tipo |
| `test_r172_06_en_la_incubadora_solo_cuenta_el_fertil_recibido` | `AC-R172-06` | recepción `fertile 100 + broken 5 + contaminated 3` | cargables 100 → **108** | `BR-03` suma todo |
| `vitest` `AC-R171-01/02/03` | `R-171` | `STAGE_OPERATIONS.hatchery` / `STAGE_FLOWS.hatchery` | contiene mortalidad/descarte → **no** (`indexOf = −1`) | catálogo sin los dos tipos |
| `vitest` `AC-R172-08` | `R-172` | `case 'egg_dispatch'` | solo `fertile` → **contiene `dirty`, `broken`, `infertile`, `discarded`** | formulario ofrece filas que la fuente no despacha |

Controles verdes antes y después: `AC-R173-01` (cantidad no editable ni corregible), `AC-R173-06/07` (anular con saldo suficiente; anular una salida
restaura, `AC-R130-07`; segunda anulación `400`), `AC-R173-17` (evento sin efecto cambia de lote), `AC-R174-02…05`, `AC-R172-01` (el fértil cuenta),
`AC-R171-04/05` (i18n existente; otras etapas intactas), contrato del formulario de recolección. Crédito por rojo inválido: **0** (ninguna roja por
autenticación, unidad, fixture, estado, padre ausente, residuo `R-175`, sintaxis, orden, `R-166` ni cantidad errónea).

## 3. Implementación (commit `64dff76`)

| Archivo | Cambio |
|---|---|
| `backend/app/operations/validators.py` | `TIPO_DISPONIBLE = "fertile"` · `cuenta_como_disponible` · `validate_egg_dispatch_types` (`BR-02`) · predicado en `get_egg_balance` (entrada y salida) y `get_hatchery_egg_balance` (entrada) · `ENTRADAS_DE_SALDO`/`SALIDAS_DE_SALDO` · `tiene_efecto_en_saldo` · `efecto_persistido` (n del servidor) · `bloquear_saldos_de_lotes` (PK ascendente) · `validate_retiro_de_entrada` (origen ≥ 0: `BR-01`/`BR-04`/`BR-02`/`BR-03`) · `validate_salida_en_destino` (mismos validadores del alta) |
| `backend/app/operations/service.py` | `verificar_destino_de_edicion(event, cambios)` — guarda central (empresa, activo, fecha, ubicación, unidad, y con cambio de lote y efecto: bloqueo de ambos lotes, relectura, invariante) usada por `update_event` · auditoría `UPDATED` con `previous_values`/`new_values` · `cancel_event`: bloqueo del lote + relectura del estado + invariante de entradas · `EGG_DISPATCH`: tipos antes de la cantidad · `CHICK_DISPATCH`: sin `if total_qty > 0` |
| `backend/app/corrections/service.py` | `lot_id`/`farm_id`/`house_id`/`destination_farm_id` pasan por `verificar_destino_de_edicion` antes de `setattr` |
| `backend/app/audit/helpers.py` | `audit_state_transition(..., previous_values, new_values)` |
| `frontend/src/data/processCatalog.ts` | `STAGE_OPERATIONS.hatchery` + `mortality_recording`, `cull_recording`; `STAGE_FLOWS.hatchery` + dos pasos tras el nacimiento |
| `frontend/src/pages/operations/OperationFormPage.tsx` | `case 'egg_dispatch'`: una sola fila (`fertile`) |
| `backend/tests/test_kpi_hatchery.py` | **fixture adaptada (solo setup)**: cargaba 1.000 con 800 fértiles recibidos (imposible bajo `BR-03` + `RR-17`); ahora carga 750 → nacimiento 80 %, eclosión 75 %, rendimiento 72 %, fertilidad 80 % (los denominadores siguen siendo distintos, que es lo que la suite mide) |

Sin migración (cabeza `x4y5z6a7b8c9`) · sin ruta, permiso, estado ni enum nuevos · sin lógica por nombre de rol.

## 4. Verde dirigido (`§79-§83`)

| Bloque | Resultado |
|---|---|
| `R-173` edición de cantidad (control) | 1/1 · lote/recurso: 4/4 (`_02`, `_03_10`, `_04`, `_17`) · anulación: 3/3 (`_05`, `_06_07`, `_07b`) · concurrencia: 2/2 (`_08`, `_09`) · seguridad (correcciones): 4/4 (`_11…_14`) · auditoría: 1/1 |
| `R-174` | cero: DENEGADO (`400 BR-04`, sin fila, sin auditoría, sin notificación) · negativo: DENEGADO (`422`, esquema) · uno: PASS · resto exacto: PASS · uno de más: DENEGADO |
| `R-172` | clasificación: 6/6 (positivo + 5 negativos) · `BR-02`: PASS · `BR-03`: PASS · mixto: PASS · `R-161` concurrencia: 7/7 |
| `R-171` | backend (`AC-R161-16`): PASS · catálogo: 5/5 · ES/EN: PASS · aplicabilidad (otras etapas intactas): PASS · `R-170`/`B13`: 6/6 |
| regresiones dirigidas | `test_population_invariant` (R-130) 21/21 · `test_state_continuity` (R-135/R-143) 24/24 · `test_operations_bu_enforcement` (R-159/R-160) 32/32 · `test_birth_classification` 6/6 · `test_reception_reconciliation` (B01) 10/10 · `test_kpi_hatchery` 7/7 (fixture adaptada) · `test_clean_baseline` 18/18 · `test_time_determinism` 10/10 |
| total dirigido | **161 passed** (278 s) + **8 passed** (KPI + `_07b`, 16 s) · `vitest` **102/102** · `tsc` 6 preexistentes (`R-158`) |

## 5. Sensibilidad (`§84-§95`) — driver atómico `mutar10.py` (ancla única verificada; una mutación cada vez; reversión con `git checkout --` sobre la implementación confirmada `64dff76`; residuo 0)

| Mutación | Qué quita | ¿Instalada? | ¿Rama ejecutada? | ¿Propiedad retirada? | Prueba objetivo | Resultado | ¿Motivo exacto? |
|---|---|---|---|---|---|---|---|
| `R173-S1` | la regla de saldo del destino (`validate_salida_en_destino` → `pass`) | sí | sí | sí | `r173_02`, `r173_13` | **2 failed** | sí: «AC-R173-02 aves: el destino no tiene saldo para la salida, 200» · «AC-R173-13: el destino no tiene saldo, 201» |
| `R173-S2` | el bloqueo del lote y la relectura en `cancel` | sí | sí | sí | `r173_08` | **1 failed** | sí: «la cancelación y las salidas no se serializaron: cancel 200 + [201 ×5], saldo −100» (carrera **observada**, no por tiempo) |
| `R173-S3` | el invariante del origen al anular una entrada | sí | sí | sí | `r173_05` | **1 failed** | sí: «AC-R173-05 aves: la anulación dejaría el saldo en −30, 200» |
| `R173-S4` | la relectura del estado bajo el bloqueo en `cancel` (bloqueo conservado) | sí | sí | sí | `r173_07b` | **primera ejecución: 1 passed** sobre la doble anulación de una **entrada** — la propia regla de saldo (`validate_retiro_de_entrada` lee el saldo fresco bajo el bloqueo: la recepción ya anulada no cuenta → «dejaría el saldo en −100») frena la segunda transición aunque el estado esté viejo: mutación **inicialmente inválida** (otra guarda seguía bloqueando) · **reconstruida**: la prueba se amplía con la doble anulación concurrente de una **salida** (sin invariante que la frene) → ver fila siguiente | — |
| `R173-S4` (rebuilt) | ídem | sí | sí | sí | `r173_07b` (entrada + salida) | **1 failed** | sí: «AC-R173-07: una sola transición — lr-salida: códigos [200, 200, 200], auditorías 3» (doble transición y doble auditoría `CANCELLED` sin la relectura); la parte de entrada sigue frenada por el invariante |
| `R173-S5` | la guarda de destino en la corrección de `lot_id`/ubicación (`verificar_destino_de_edicion` → `pass`): la única capa de ese camino; el movimiento **ocurre** | sí | sí | sí | `r173_11…14` | **4 failed** | sí: «el lote de B no existe para A, 201» · «unidad broiler apagada, 201» · «destino sin saldo, 201» · «granja de otra empresa, 201» |
| `R172-S1` | el predicado de tipo en `get_egg_balance` (entrada y salida): «todos los tipos cuentan» | sí | sí | sí | `r172_02`, `r172_03[5]` | **6 failed** | sí: «100 fértiles + 70 de otros tipos → disponibles 100» (170) · «dirty/broken/infertile/discarded/commercial no es disponibilidad» (50) |
| `R172-S2` | `fertile` del predicado (`TIPO_DISPONIBLE = "fertile-mutado"`) | sí | sí | sí | `r172_01` | **1 failed** | sí: «AC-R172-01» (el fértil deja de contar) |
| `R172-S3` | la validación de tipos del despacho | sí | sí | sí | `r172_04` | **1 failed** | sí: «una fila 'dirty' no se despacha a incubadora, 201» |
| `R172-S4` | el predicado en `get_hatchery_egg_balance` | sí | sí | sí | `r172_06` | **1 failed** | sí: «100 fértiles + 8 no fértiles → cargables 100» (108) |
| `R172-S5` | la fila única del formulario de despacho (vuelve `dirty`) | sí | sí | sí | `vitest` `AC-R172-08` | **1 failed** | sí: «not to contain key: 'dirty'» |
| `R174-S1` | restaurar `if total_qty > 0` | sí | sí | sí | `r174_01` | **1 failed** | sí: «un despacho de 0 pollitos no es un despacho, 201» (fila persistida observada) |
| `R171-S1` | `mortality_recording` y `cull_recording` de `STAGE_OPERATIONS.hatchery` | sí | sí | sí | `vitest` `AC-R171-01/02` | **2 failed** | sí: «expected [...] to include 'mortality_recording'» / «'cull_recording'» |
| `R171-S1b` | el paso `cull_recording` de `STAGE_FLOWS.hatchery` | sí | sí | sí | `vitest` `AC-R171-03` | **1 failed** | sí: «cull_recording en el flujo: expected -1 to be greater than 6» |
| `R171-S2` | mapear «débil» a descarte | — | — | — | — | **N/A** | no existe mapeo en el frontend entre `chicks_weak` y ningún evento (el catálogo lista tipos de evento); nada que mutar |

Contabilidad: intentadas 14 · inicialmente inválidas 1 (`R173-S4`, otra guarda seguía bloqueando) · reconstruidas 1 · válidas finales 13 · N/A 1 (`R171-S2`, con motivo) ·
crédito por inválidas 0 · residuo 0 (`git status` sin cambios en `backend/app`, `processCatalog.ts`, `OperationFormPage.tsx` tras cada reversión).

## 6. Control de orden `R-175` (`§83`, regla permanente C/D)

| Suite | Aislada | A→B (suite → `test_clean_baseline`) | B→A (`test_clean_baseline` → suite) | ¿Afecta al tranche? |
|---|---|---|---|---|
| `test_lot_start_date` | 6/6 | **1 failed** (`test_t_025_07`: «las fases se duplicaron: 5») | 24/24 | no |
| `test_lots_bu_enforcement` | 28/28 | **1 failed** (ídem) | 46/46 | no |
| `test_od14_productive_surfaces` | 35/35 | **1 failed** (ídem) | 53/53 | no |
| `test_clean_baseline` | 18/18 | — | — | — |

Residuo **reproducido bajo control** (fase productiva creada por la suite y no retirada; la afirmación del baseline es global). No produce rojo ni verde
falso en la regresión certificada (alfabética; el baseline corre antes) ni impide aislar las suites del tranche (no tocan `productive_phases`). `R-175`
queda **OPEN**, NON-BLOCKING, sin limpieza oportunista (`R175_TEST_ORDER_DEPENDENCY_CONTROL.md`).

## 7. Regresiones exigidas (`§96-§106` + cola establecida)

| Regresión | Suite(s) | Resultado (dentro de la regresión completa) |
|---|---|---|
| `R-161` (bloqueo de huevos/incubación; el predicado no reabre la carrera) | `test_egg_incubation_concurrency` | 7/7 |
| `R-130` (población no negativa, decremento acotado, `FOR UPDATE`, viables) | `test_population_invariant` | 21/21 |
| `R-170` / `B13` (sin doble conteo; filas por sexo; sanos/débiles sin efecto) | `test_birth_classification` | 6/6 |
| `B01` (`BR-20`, tupla no corregible, `R-167`) | `test_reception_reconciliation` | 10/10 |
| `B02` (curva, sin ±10 %, alerta no bloqueante) | `test_reception_weight_range`, `test_weight_curve_evaluation`, `test_genetic_curves` | verdes |
| `B05` (agua) | `test_water_consumption` | verde |
| `R-136` / `OD-19` (reverso; huevos no reversibles) | `test_reversals*`, `test_reversal_role_migration` | verdes |
| `R-135` / `R-143` (estado, correcciones, segregación) | `test_state_continuity`, `test_corrections*`, `test_approval*` | verdes |
| `R-159` / `R-160` (unidad en operaciones; la reasignación no elude la guarda) | `test_operations_bu_enforcement` | 32/32 |
| `R-162` / `R-163` (lotes y evidencias; global no opera unidad apagada) | `test_lots_bu_enforcement`, `test_evidence*` | verdes |
| `R-139` · `R-165` · `OD-14` / `OD-16` · `RQ-03` · fases 7/8 · seguridad `R-121`/`R-113`/`R-129` | `test_global_actor*`, `test_review_bu*`, `test_od14_productive_surfaces`, `test_od16*`, `test_clean_baseline`, `test_upgrade_path` (script dedicado, saltada), RBAC/sesión/multiempresa | verdes |
| guardianes | `test_population_invariant::test_ac14` (rutas 211, cabeza `x4y5z6a7b8c9`), `test_rbac` (13), `test_clean_baseline::test_t_025_02` (48), `test_time_determinism` | verdes |
| KPI de incubadora (fixture adaptada a `BR-03`) | `test_kpi_hatchery` | 7/7 |

## 8. Regresión completa (leída antes de certificar) y cierre técnico

```
backend ........ 1056 passed · 49 skipped · 0 failed   (1173 s · 92 suites · 1031 previas + 25 nuevas: 16 de test_edit_cancel_balance + 9 de test_egg_type_availability)
                 los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado
vitest ......... 102 / 102  (95 previas + 5 de R-171 + 2 de R-172)
tsc ............ 6 errores preexistentes (R-158), sin cambio
alembic ........ x4y5z6a7b8c9 (sin migración) · rutas 211 · guardianes exactos
R-175 .......... control documentado; la regresión completa (alfabética) no lo manifiesta
```

| Ítem | Cierre |
|---|---|
| `R-173` | **CERRADO (técnico)** · P1 · `GA-REM-005-E` **CERTIFICADA** (frontera técnica) · `AC-R173-01…18` · rojo válido 10 (+2 carreras observadas) · sensibilidad S1…S5 válidas |
| `R-172` | **CERRADO (técnico)** · `GA-REM-005-F` **CERTIFICADA** · `AC-R172-01…08` · rojo válido 8 + 1 · sensibilidad S1…S5 válidas · `R-161` intacto · `RC-14`/`RR-17` |
| `R-174` | **CERRADO (técnico)** · `GA-REM-005-E §E.3` · `AC-R174-01…05` · sensibilidad S1 válida |
| `R-171` | **CERRADO (técnico)** · `GA-REM-021-D` **CERTIFICADA** · `AC-R171-01…06` · sensibilidad S1/S1b válidas (S2 N/A) · `GA-REM-021` sigue PARTIAL (B03 ◄ AOD-22 · B04 ◄ AOD-14 · R-156 ◄ AOD-20) |
| `R-175` | OPEN (P3) · NON-BLOCKING · control documentado |
| `R-176` · `R-177` · `R-178` | OPEN (P3) · registrados, fuera del tranche |
| certificación de proceso | `BLOCKED_RUNTIME` (no se reclama; `R-164`) |

Recuento canónico tras el cierre: **34 · 17 cerrados · 4 parciales · 13 abiertos (P1 0 · P2 6 · P3 7) · decisiones 8**. Siguiente tranche (identificado,
no iniciado): `R-152 → R-153` (Progenitoras); alternativa `R-176` + `R-178` o `R-175` (higiene bajo gobernanza de validez).

Fuera de alcance, sin tocar: `R-164`, `R-166`, `R-140`/`R-154` residuales, `R-136` SAP, `B03`/`B04`/`R-156` (decisiones), `AOD-23`, `R-142`, `R-144`,
`R-147`, `R-148`, `R-152`, `R-153`, KPI (ola C), fase 9, SAP, `P-08`, `BU-D10`, `R-158`, marcos genéricos de compensación/ledger/event sourcing.
