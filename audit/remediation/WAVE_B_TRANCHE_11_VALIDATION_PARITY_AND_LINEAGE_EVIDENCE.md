# Evidencia · WAVE B · tranche 11 — `R-176` (paridad de validación en edición y corrección, + `R-45`) · `R-178` (linaje efectivo al anular o mover) · `R-177` (pre-flight, `AOD-24`) · `R-175` (control → bloqueante → remediado)

**Fecha** 2026-09-10 · **Baseline de entrada** `main` · `80cce71` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211 (guardián `test_ac14`) ·
**Modo** `R176_PLUS_R178` (CASE A) · **Commits** `172ec12` (spec) · `4c72c40` (spec `GA-REM-015-B`, `R-175`) · implementación (`IMPLEMENTATION_COMMIT`, §3) ·
evidencia (este) · **Sin migración** · **Decisión nueva** `AOD-24` (solo `R-177`, sin código).

## 1. Pre-flight (commits `172ec12`, `4c72c40`)

| Hallazgo | Clasificación | Autoridad | Artefacto |
|---|---|---|---|
| `R-176` | **ACTIVE · GOBERNADO · P2** (normalizado desde P3: misma raíz que `R-45` P2; `BR-18` deja superar la OC moviendo el acumulado) · absorbe `R-45` (Wave 2, «corregir `event_date` no revalida `BR-19`», abierto) | `AC-W09`/`RR-18` (destino de una edición = alta) · `GA-REM-023` (`BR-06`, `BR-08`, `BR-10`, `BR-17`, `BR-19` se aplican en el alta) · `GA-REM-035 §3` (`BR-18`, `OD-04`) · `R-30` · `docs/02 §7 R6` · `spec.md §5` → paridad de validación **sin repetir el alta** | `R176_CREATE_EDIT_CORRECTION_VALIDATION_PARITY_MATRIX.md` · `GA-REM-023-B` |
| `R-178` | **CONFIRMADO · GOBERNADO · P3** · linaje = trazabilidad generacional (`egg_batches`/`chick_batches`), **no** genética | `OD-10 §2.4` («la fila es el traspaso»), `§2.5` («anulado … lo ve desaparecer»), `§4bis` («sin cascada; la historia se conserva»), `§4bis.5` («ante la duda, se deniega») · `BR-10` · `GA-REM-008 AC04/AC06` · `GA-REM-031 AC03` → histórico conservado + efectivo derivado en lectura + reasignación de eventos casados denegada | `R178_LINEAGE_CANCEL_MOVE_INTEGRITY_MATRIX.md` · `GA-REM-031-A` |
| `R-177` | **PARTIAL**: registro corregido (el bloque con categorías de ovoscopía es del evento `ovoscopy`, no de la recepción) · DATA QUALITY DEFECT confirmado (cadena libre, UI cruda, `commercial` sin etiqueta) · modelo (tipo de huevo ≠ resultado de ovoscopía en el mismo campo) → **`OWNER_DECISION_REQUIRED` (`AOD-24`)** · **sin código** | `docs/02 §3.6.2/§3.6.3/§3.7.3` · `docs/03 :277` · `spec.md :164/:188/:192` · `RR-17` | `R177_EGG_TYPE_OVOSCOPY_DOMAIN_MATRIX.md` · `AOD-24` |
| `R-175` | NON-BLOCKING al entrar; **BLOQUEANTE** durante el verde dirigido (rojo falso: «las fases se duplicaron: 5» con `test_lot_start_date` antes que `test_clean_baseline`, prompt §49) → remediación mínima del arnés bajo `GA-REM-015-B` (teardown por prefijo en las tres suites; guardián y dominio intactos) | `GA-REM-015` (`R-28`: el defecto está en los tests) · patrón `test_opening_balance.py:73` | `R175_TEST_ORDER_DEPENDENCY_CONTROL.md §4-§5` · `GA-REM-015-B` |

Recuento canónico al entrar: 34 · 17 · 4 · 13 (P2 7 · P3 6) · decisiones 9 (`AOD-24` nueva).

## 2. Rojo válido (leído en `172ec12`, antes de tocar código) — `§59`

Backend: `tests/test_edit_validation_parity.py` + `tests/test_lineage_cancel_move.py` → **10 failed · 4 passed** (15 s).

| Prueba | Hallazgo · AC | Ruta · actor · permiso · empresa · unidad · recurso · estado | Valores originales → candidato → regla esperada → **real** → efecto | Por qué es el defecto |
|---|---|---|---|---|
| `test_r176_01_02_…galpon_por_debajo_de_la_capacidad` | `R-176` · `AC-R176-01/02` | `PUT` · operador · `operations:update` · A · breeder · recepción de 100 aves en galpón de 100 000 · `REGISTERED` | `house_id` → galpón de capacidad 50 → `400 BR-17` → **`200`** → 100 aves en un galpón de 50 | `BR-17` no se reevalúa en la edición |
| `test_r176_03_04_06_07_…oc_sin_cupo` | `AC-R176-03/04` | `PUT` · recepción de 50 con `PARI-OC-B`; `PARI-OC-A` (100) ya con 80 | `sap_document_ref` → `PARI-OC-A` → `400 BR-18` (130 > 100) → **`200`** → acumulado de la OC superado | `BR-18` no se reevalúa; `exclude_event_id` sin uso |
| `test_r176_05_…fecha_fuera_de_las_reglas` | `AC-R176-05` (+ `R-45`) | `PUT` · recepción | `event_date` → +91 días → `400 BR-19` → **`200`** → evento en período cerrado | `BR-19` no se reevalúa (edición y corrección) |
| `test_r176_05b_…ubicacion` | `AC-R176-05b` | `PUT` · recepción (evento de ubicación) | `house_id` → `null` → `400 BR-08` → **`200`** (`"house_id": null` persistido) | `BR-08` no se reevalúa |
| `test_r176_05c_…documento_sap` | `AC-R176-05c` | `PUT` · vacunación con `PARI-DOC-2`; `PARI-DOC-1` ya existe en el lote | `sap_document_ref` → `PARI-DOC-1` → `400 BR-10` → **`200`** → documento duplicado | `BR-11` no se reevalúa |
| `test_r176_11_12_…cadena_de_seguridad` | `AC-R176-12` | `PUT` · `operador_r` (sin unidad `hatchery`) sobre evento de `lh` | → `404`/`400 BR-07` → **`404`** — aserción inicial esperaba solo `BR-07`: **rojo inválido por aserción de la prueba** (el evento de otra unidad no se ve, `R-159`/`R-160`); corregida a `404 | BR-07`; crédito 0 | — |
| `test_r178_02_11_anular_el_despacho…` | `R-178` · `AC-R178-02` | `POST /cancel` · despacho casado (`EggBatch` lr → lh) | anular → el árbol de `lr` deja de listarlo → **lo lista** (`egg_batches_sent = [{…}]`) → traspaso anulado presentado como vigente (`OD-10 §2.5`) | el árbol no mira el estado de los eventos |
| `test_r178_03_anular_la_recepcion…` | `AC-R178-03` | anular la recepción casada | el emisor lo ve incompleto (`quantity_received = null`) → **`100`** | ídem |
| `test_r178_04_05_06_…no_se_reasigna` | `AC-R178-04` | `PUT lot_id` del despacho casado → `lr2` (con saldo) | → `400` → **`200`** → vínculo con `source_lot_id` falso (`GA-REM-031 AC03`) | sin guarda de vínculo efectivo |
| `test_r178_08_…cadena_de_pollitos` | `AC-R178-08` | `PUT lot_id` del despacho de pollitos casado | → `400` → **`200`** | ídem |

Controles verdes antes y después: `AC-R176-09` (la edición válida no repite el alta: ya era cierto), `AC-R178-01` (par → vínculo orientado, `GA-REM-031`),
`AC-R178-07` (denegación de inquilino/unidad no toca el linaje), `AC-R178-09/10` (sin vínculo se mueve; el enlace manual se lista). Crédito por rojo
inválido: **0** (una aserción corregida, documentada arriba; ninguna roja por fixture, estado, autenticación, residuo `R-175`, sintaxis, orden ni linaje
inexistente).

## 3. Implementación (`IMPLEMENTATION_COMMIT` = `00b3bd6`; árbol limpio en código antes de la sensibilidad)

| Archivo | Cambio |
|---|---|
| `backend/app/operations/service.py` | `_reglas_puras_del_candidato(event, cambios, lote_destino)`: compone el candidato (`farm_id`, `house_id`, `event_date`, `sap_document_ref` = cambio o persistido) y corre solo la regla cuyo campo cambia: `BR-08` (`validate_farm_house`), `BR-06` + `BR-19` (`validate_event_date`, `validate_period_open`), `BR-11` (`validate_sap_document_unique`, `exclude_event_id`, tipo ≠ recepción), `BR-17` (`validate_house_capacity`, `n` de `bird_movements`), `BR-18` (`validate_oc_limit`, `exclude_event_id`) · `_exigir_sin_vinculo_efectivo(event, cambios, lote_destino)`: si cambia el lote o el destino declarado y el evento es despacho de un vínculo o recepción de un vínculo cuyo despacho no está anulado → `400` · ambas dentro de `verificar_destino_de_edicion`, tras la cadena de inquilino/unidad y **antes** del bloqueo de lotes y de las reglas de saldo (`R-173` intacto) |
| `backend/app/corrections/service.py` | la guarda también para `event_date` y `sap_document_ref` (antes: `lot_id`, `farm_id`, `house_id`, `destination_farm_id`) |
| `backend/app/lots/router.py` | `GET /lots/{id}/traceability`: `_estado_de_eventos` (una consulta por los eventos de los vínculos) + `_vinculos_efectivos` (despacho anulado → fuera de ambos lados; recepción anulada → incompleto en el emisor, fuera en el receptor; manuales siempre). Lectura pura: la fila no cambia |
| `backend/tests/test_corrections.py` | `test_la_fecha_corregida_sigue_sujeta_a_las_reglas`: la aserción tolerante de `R-45` pasa a exigir `400 BR-19` y fecha intacta |
| `backend/tests/test_edit_cancel_balance.py` | **solo setup**: los despachos de huevos declaran un destino sin recepción posible (`granja_a`), porque con `planta_a` se casaban con las recepciones de `lh*` y la guarda de linaje denegaba mover un evento casado antes de llegar a la regla de saldo que la suite mide |
| `backend/tests/test_lot_start_date.py` · `test_lots_bu_enforcement.py` · `test_od14_productive_surfaces.py` | `GA-REM-015-B` (`R-175`): teardown borra la `ProductivePhase` creada por la suite, por prefijo, después de los lotes |
| nuevas | `tests/test_edit_validation_parity.py` (7) · `tests/test_lineage_cancel_move.py` (7) |

Sin migración (cabeza `x4y5z6a7b8c9`) · sin ruta, permiso, estado, enum ni columna nuevos · frontend sin cambio · `create_event` sigue siendo el único
camino que persiste, audita `created`, crea alertas, notificaciones y vínculos (`AC-R176-09`).

## 4. Verde dirigido (`§69`, `§70`) — 288/288 (363 s), con las tres suites de residuo **antes** de `test_clean_baseline`

| Bloque | Resultado |
|---|---|
| `R-176` `BR-17` PUT: 1/1 · `BR-17` corrección: 1/1 · `BR-18` PUT: 1/1 · `BR-18` corrección: 1/1 · fecha (`BR-19` cerrado/futuro, `BR-06`) PUT + corrección: 1/1 · `BR-08`: 1/1 · `BR-11`: 1/1 · ediciones válidas (`_06/_07`): 1/1 · sin repetir el alta (`_09`): 1/1 · seguridad y aprobado (`_11_12`): 1/1 | `test_edit_validation_parity` 7/7 |
| `R-178` anulación (despacho: 1/1 · recepción: 1/1) · movimiento denegado (huevo: 1/1 · pollitos: 1/1) · historia conservada: dentro de `_02/_03/_08` · denegación de inquilino/unidad sin tocar el linaje: 1/1 · controles (sin vínculo se mueve; manual): 1/1 · atomicidad: N/A (dinámico) | `test_lineage_cancel_move` 7/7 |
| `R-175` (`§48`, primer control con la remediación): `test_lot_start_date` → `test_lots_bu_enforcement` → `test_od14_productive_surfaces` → `test_clean_baseline` | 6 + 28 + 35 + 18 = 87/87 (antes: «5 fases») |
| `R-173` (guarda de destino, bloqueo, anulación, auditoría) | `test_edit_cancel_balance` 16/16 |
| `R-135`/`R-143` + correcciones (`R-45`) | `test_corrections` 18/18 · `test_state_continuity` 24/24 |
| `GA-REM-008`/`GA-REM-031` (trazabilidad) · `OD-10` | `test_traceability` 4/4 · `test_reception_lineage` 5/5 · `test_pending_classification` 35/35 |
| `R-159`/`R-160` · `GA-REM-035` (`BR-18` en el alta) · `R-161` · `R-130` | 32/32 · 7/7 · 7/7 · 21/21 |
| guardianes | `test_ac14` (rutas 211, cabeza) · `test_time_determinism` 10/10 |
| frontend | `vitest` 102/102 · `tsc` 6 preexistentes (`R-158`) — sin cambios en esta tranche |

## 5. Sensibilidad (`§73-§84`) — MUTATION CHECKPOINT cumplido

```
IMPLEMENTATION_COMMIT ......... 00b3bd6 (contiene backend/app/operations/service.py, corrections/service.py, lots/router.py y las pruebas)
antes ......................... git status --short: solo la evidencia sin versionar · git show --stat HEAD leído
driver ........................ mutar11.py (ancla única verificada en cada archivo) · sensibilidad11.sh (aborta si hay código sucio o si HEAD no contiene la implementación)
después de cada mutación ...... git diff HEAD -- backend/app = 0 líneas (la reversión vuelve al commit de implementación, no al de spec)
después de todo ............... HEAD == 00b3bd6 · residuo de código 0 · humo tras la sensibilidad: test_edit_validation_parity + test_lineage_cancel_move 14/14
```

| Mutación | Qué quita | ¿Instalada? (`git diff HEAD --stat`) | ¿Rama ejecutada? | ¿Propiedad retirada? | Prueba objetivo | Resultado | ¿Motivo exacto? | ¿Restaurada? |
|---|---|---|---|---|---|---|---|---|
| `R176-S1` | `BR-17` de la guarda (`validate_house_capacity` → `pass`) | sí (1 archivo, +1/−1) | sí | sí | `r176_01` | **1 failed** | sí: «100 aves no caben en un galpón de 50, `200`» | sí (diff 0) |
| `R176-S2` | la corrección de `event_date`/`sap_document_ref` deja de pasar por la guarda (superficie de corrección) | sí | sí | sí | `r176_03`, `r176_05_` | **2 failed** | sí: «AC-R176-04, `201`» (OC sin cupo por corrección) · «AC-R176-05 corrección · período cerrado (R-45), `201`» — el `PUT` sigue verde: prueba las dos superficies por separado | sí |
| `R176-S3` | `BR-18` de la guarda (`validate_oc_limit` → `pass`) | sí | sí | sí | `r176_03` | **1 failed** | sí: «80 + 50 = 130 > 100 de la OC-A, `200`» | sí |
| `R176-S4` | `BR-06`/`BR-19` sobre la fecha candidata | sí (+1/−3) | sí | sí | `r176_05_` | **1 failed** | sí: «PUT · período cerrado (+90 d), `200`» | sí |
| `R176-S5` | reproducir un efecto del alta en la edición válida (`audit_event_created` tras el `PUT`) | sí (+1) | sí | sí | `r176_09` | **1 failed** | sí: «una sola auditoría (updated)» (se observó una auditoría `created` de más) | sí |
| `R178-S1` | el filtro por estado del despacho en el árbol | sí (+1/−2) | sí | sí | `r178_02` | **1 failed** | sí: «un traspaso anulado desaparece del lado emisor (OD-10 §2.5)» — el árbol lo volvió a listar | sí |
| `R178-S2` | la guarda de vínculo efectivo en la reasignación | sí | sí | sí | `r178_04`, `r178_08` | **2 failed** | sí: «PUT lot_id del despacho, `200`» · «el despacho de pollitos casado no se mueve, `200`» | sí |
| `R178-S3` | borrar la fila del vínculo al anular el despacho (historia) | sí (+4) | sí | sí | `r178_02` (`r178_03` no la alcanza: anula la recepción, no el despacho) | **1 failed, 1 passed** | sí: «la historia se conserva (BR-10): la fila no se borra» — la fila desapareció; `_03` verde por diseño de la mutación (no se acredita) | sí |
| `R178-S4` | atomicidad parcial | — | — | — | — | **N/A** | linaje dinámico: no hay escritura de linaje en anular/mover | — |
| `SEC-S1` | el filtro de empresa de `get_event` (una capa) | sí (+1/−2) | sí | **no**: la capa de unidad (`predicado_de_evento`) siguió ocultando el evento de A al actor de B (`404`) | `r176_11` | **1 passed** | — | sí |
| `SEC-S1b` (reconstruida) | dos capas: el filtro de empresa **y** el predicado de unidad de `get_event` | sí (+5/−7, con la sonda de prueba sin versionar) | sí | **parcial**: el actor de B alcanzó la guarda de destino, pero `_unidad_del_lote` (acotada a la empresa) siguió respondiendo «Lote no encontrado» `BR-07` | `r176_11` (sonda de campo inocuo, primero) | **1 failed** | roja, pero **no por la fuga**: `400 BR-07` en vez de `200` → todavía inválida | sí (diff 0) |
| `SEC-S1c` (reconstruida, protocolo del tranche 4) | tres capas: las dos de `get_event` + el acotamiento a la empresa de `_unidad_del_lote` | sí (+6/−9) | sí | **sí**: el actor de B editó `observations` de un evento de A → **`200`** (fuga observada, fila cambiada) | `r176_11` | **1 failed** | sí: «otra empresa no edita ni un campo inocuo, `200`» — con el código íntegro la sonda es verde (`404`) | sí (diff 0 · HEAD `00b3bd6`) |

Contabilidad: intentadas 10 · inicialmente inválidas 2 (`SEC-S1`, `SEC-S1b`: otra capa seguía bloqueando) · reconstruidas 2 (`SEC-S1b` → `SEC-S1c`) · válidas finales **9** (`R176-S1…S5`, `R178-S1…S3`, `SEC-S1c`) · N/A 1
(`R178-S4`) · crédito por inválidas 0 · residuo 0.

Nota de orden: la sonda de campo inocuo se añadió (y luego se antepuso) en `test_r176_11_12` **después** del commit de implementación, como parte del protocolo
de reconstrucción; la regresión completa (§8) corrió con la sonda presente y el humo final (14/14) con el orden definitivo. El cambio de la prueba va en el
commit de evidencia; el código de producción es exactamente `00b3bd6` (`git diff HEAD -- backend/app` = 0 tras cada mutación y al final).

## 6. Control de orden `R-175` (`§48`) — remediación `GA-REM-015-B` verificada (base reseteada en cada invocación; `T11` = `test_edit_validation_parity` + `test_lineage_cancel_move`)

| Suite | Aislada | A→B (`suite → clean_baseline`) | B→A | `T11 → A` | `A → T11` |
|---|---|---|---|---|---|
| `test_lot_start_date` | 6/6 | **24/24** (antes: 1 failed «5 fases») | 24/24 | 20/20 | 20/20 |
| `test_lots_bu_enforcement` | 28/28 | **46/46** (antes: 1 failed) | 46/46 | 42/42 | 42/42 |
| `test_od14_productive_surfaces` | 35/35 | **53/53** (antes: 1 failed) | 53/53 | 49/49 | 49/49 |
| `test_clean_baseline` | 18/18 | — | — | `T11 → B`: 32/32 | `B → T11`: 32/32 |

18/18 pares verdes. El residuo desapareció con el teardown por prefijo (`AC-R175-01…04`); el guardián `test_t_025_07` sigue exigiendo `== 4`. `R-175` pasó a
bloqueante (rojo falso en el primer verde dirigido) y se cierra por remediación explícita bajo spec, no por reclasificación.

## 7. Regresiones exigidas (`§86-§98` + cola establecida) — dentro de la regresión completa

| Regresión | Suite(s) | Resultado |
|---|---|---|
| `R-173` (destino en PUT y corrección, empresa, unidad, activo, fecha vs lote, ubicación, saldos, bloqueo ascendente, cancel con bloqueo y relectura, auditoría con valores) | `test_edit_cancel_balance` | 16/16 |
| `R-172` (solo fértil; despacho no fértil denegado; filas históricas) | `test_egg_type_availability` | 9/9 |
| `R-174` (despacho de 0 → `BR-04`, sin fila) · `R-171` (catálogo) | `test_edit_cancel_balance` (R-174) · `vitest` | verdes |
| `R-161` (bloqueo de huevos/incubación; la paridad no reabre la carrera) | `test_egg_incubation_concurrency` | 7/7 |
| `R-130` | `test_population_invariant` | 21/21 |
| `R-170` / `B13` · `B01` · `B02` · `B05` | `test_birth_classification` · `test_reception_reconciliation` · `test_reception_weight_range`, `test_weight_curve_evaluation`, `test_genetic_curves` · `test_water_consumption` | verdes |
| `R-136` / `OD-19` (reverso; huevos no reversibles) | `test_reversals*`, `test_internal_reversal`, `test_reversal_role_migration` | verdes |
| `R-135` / `R-143` (correcciones, reenvío, aprobado inmutable) | `test_corrections` 18/18 (incluida la de `R-45`, ahora estricta) · `test_state_continuity` 24/24 · `test_review*`, `test_approval*` | verdes |
| `R-159` / `R-160` · `R-162` / `R-163` · `R-139` · `R-165` · `OD-14` / `OD-16` | `test_operations_bu_enforcement` 32/32 · `test_lots_bu_enforcement` 28/28 · `test_evidence*` · `test_global_actor*` · `test_review_bu*` · `test_od14_productive_surfaces` 35/35 | verdes |
| `GA-REM-008` / `GA-REM-031` / `GA-REM-030` (trazabilidad, vínculo manual, empresa) · `OD-10` (traspasos) | `test_traceability` 4/4 · `test_reception_lineage` 5/5 · `test_pending_classification` 35/35 | verdes |
| `GA-REM-035` (`BR-18` en el alta) · `GA-REM-015` (`BR-19` fronteras) | `test_purchase_order_receipt` 7/7 · `test_lot_start_date` 6/6 | verdes |
| guardianes · `RQ-03` · fases 7/8 · seguridad `R-121`/`R-113`/`R-129` | `test_ac14` (211, cabeza) · `test_clean_baseline` · `test_upgrade_path` (script dedicado, saltada) · `test_time_determinism` · RBAC/sesión/multiempresa | verdes |

## 8. Regresión completa (leída antes de certificar) y cierre técnico

```
backend ........ 1070 passed · 49 skipped · 0 failed   (931 s · 94 suites · 1056 previas + 14 nuevas: 7 de test_edit_validation_parity + 7 de test_lineage_cancel_move)
                 los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado · corrió con la sonda de fuga presente
vitest ......... 102 / 102 (sin cambios de frontend en esta tranche)
tsc ............ 6 errores preexistentes (R-158), sin cambio
alembic ........ x4y5z6a7b8c9 (sin migración) · rutas 211 · guardianes exactos
integridad ..... código de producción == 00b3bd6 tras la sensibilidad (residuo 0) · humo final 14/14
```

| Ítem | Cierre |
|---|---|
| `R-176` | **CERRADO (técnico)** · P2 · `GA-REM-023-B` **CERTIFICADA** (frontera técnica) · `AC-R176-01…12` · rojo válido 5 · sensibilidad `R176-S1…S5` válidas · **`R-45` cerrado con él** (prueba estricta en `test_corrections`) |
| `R-178` | **CERRADO (técnico)** · P3 · `GA-REM-031-A` **CERTIFICADA** · `AC-R178-01…11` · rojo válido 4 · sensibilidad `R178-S1…S3` válidas (`S4` N/A: dinámico) · sin migración |
| `R-175` | **CERRADO (técnico)** · `GA-REM-015-B` **CERTIFICADA** · matriz ampliada 18/18 · guardián intacto |
| `R-177` | OPEN · P3 · **`OWNER_DECISION_REQUIRED` (`AOD-24`)** · pre-flight completo, registro corregido, sin código |
| seguridad (`§83`) | `SEC-S1` y `SEC-S1b` inválidas (crédito 0); `SEC-S1c` (tres capas) válida: la cadena de inquilino protege el camino de `R-176`; el resto de la cadena (unidad apagada, sin concesión, RBAC, destino) está certificado por `R-160`/`R-173` y se ejerce en `AC-R176-12` |
| certificación de proceso | `BLOCKED_RUNTIME` (no se reclama; `R-164`) |

Recuento canónico tras el cierre: **34 · 20 cerrados · 4 parciales · 10 abiertos (P1 0 · P2 6 · P3 4) · decisiones 9** (+ `R-45` de Wave 2 cerrado). Siguiente
tranche (identificado, no iniciado): `R-152 → R-153` (Progenitoras); alternativa `R-166` (approve/reject concurrentes).

Fuera de alcance, sin tocar: `R-177` (código), `R-164`, `R-166`, `R-140`/`R-154` residuales, `R-136` SAP, `B03`/`B04`/`R-156` (decisiones), `AOD-23`, `R-142`,
`R-144`, `R-147`, `R-148`, `R-152`, `R-153`, KPI (ola C), fase 9, SAP, `P-08`, `BU-D10`, `R-158`, marcos genéricos de reglas/linaje/auditoría/event sourcing.
