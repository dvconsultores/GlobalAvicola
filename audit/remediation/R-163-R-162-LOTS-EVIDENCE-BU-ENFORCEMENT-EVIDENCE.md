# EVIDENCIA · `R-163` + `R-162` · LA HABILITACIÓN DE LA EMPRESA ES ABSOLUTA PARA TODA ESCRITURA PRODUCTIVA — `lots` Y DESCARGA DE EVIDENCIA

**WAVE B · tranche 3** · 2026-09-09 · spec `GA-REM-040` enmienda H (commit `b41b360`) · matriz previa
`R163_R162_LOTS_AND_EVIDENCE_BU_AUTHORITY_MATRIX.md` · base `3d0c5d0` · rama `main`

## 1. Alcance certificado (frontera técnica) — dos hallazgos, dos estados

| Hallazgo | Sev. | Clase | Superficies | AC | Resultado |
|---|:--:|---|---|---|---|
| `R-163` | P2 (P1 en `POST /lots` con actor de empresa, clase `AC-C05`) | `PRODUCTIVE_WRITE` | `POST /lots` · `PUT /lots/{id}` · `POST /lots/{id}/close` · `POST /lots/activate-manual` · `POST /lots/{id}/phases` | `AC-L01…L15` | **CERRADO** (técnico) |
| `R-162` | P2 | `PRODUCTIVE_READ` | `GET /operations/{id}/evidences/{eid}/download` | `AC-E01…E08` | **CERRADO** (técnico) |

Certificación de proceso de negocio: **no** (`BLOCKED_RUNTIME`, sin E2E). Ninguna fase ni proceso se certifica por
transitividad. Las lecturas de `lots` para la autoridad global **no cambian**: frontera declarada y probada como
control (`AC-L11`). El plano de control de la unidad apagada sigue operable (`AC-L15`).

## 2. Verificación exacta desde el repositorio (antes del código)

- `R-163`: la exención de `is_super_admin` en `masters/service._apply_business_unit_filter:113` alcanza `update_lot`,
  `close_lot`, `activate_manual` y `add_phase` (todas resuelven el lote por `MasterService`); **además** `create_lot`
  no consultaba la unidad para **ningún** actor (`bird_type` se guardaba tal cual) y la autoridad global sin
  contexto creaba lotes con `company_id` nulo (`Lot.company_id` es nulable). El hallazgo se amplió por inventario
  (encargo §11) de dos a cinco superficies; el registro del backlog lo dice.
- `R-162`: una sola superficie (`download`); la hermana de listado ya acota por unidad vía `get_event`; ninguna
  otra superficie de evidencia existe fuera de `operations`.
- Aclaración del propietario: `OD-16.e/f` y `AC-A05` ya eran explícitas → **sin decisión nueva**; registrada en
  `GA-REM-040-H §H.2` como CLARIFIES/PROPAGATES `OD-16`, con fila de traza en `OD-16 §9`.

## 3. Rojo previo (`T-040-H1`) · validez

`tests/test_lots_bu_enforcement.py` · 28 pruebas · sobre `b41b360` (spec sin código): **14 rojas · 14 verdes**.
Trece rojas son tratamiento y caen en la aserción de contrato; una (`l09` control) cayó por fixture (el lote usado
para `activate-manual` ya tenía un evento sembrado: «El lote ya tiene operaciones registradas») y se corrigió
sembrando un lote sin operaciones (`LG2`); no es defecto ni contrato. 0 errores de import/`NameError`/fixture.

| Prueba | AC | Aserción roja (observado ≠ exigido) | Válida |
|---|---|---|---|
| `l02_la_unidad_habilitada_sin_concesion_no_admite_alta` | L02 | `201` con el lote creado ≠ `403` | sí |
| `l03_la_unidad_apagada_no_admite_alta_aunque_haya_concesion_historica` | L03 | `201` ≠ `403` | sí |
| `l04_cero_unidades_efectivas_no_crea_lotes` | L04 | `201` ≠ `403` | sí |
| `l05_la_autoridad_global_sin_contexto_no_crea_lotes` | L05 | **`201` con `company_id: null`** ≠ `403` | sí |
| `l07_la_autoridad_global_situada_no_crea_en_unidad_apagada` | L07 | `201` ≠ `403` | sí |
| `l08_put_sobre_unidad_apagada…` | L08 | `200` ≠ `403` | sí |
| `l08_close_sobre_unidad_apagada…` | L08 | `400 BR-05` (la regla de negocio se alcanzó antes que la autoridad) ≠ `403` | sí |
| `l08_activate_manual_sobre_unidad_apagada…` | L08 | `201` ≠ `403` | sí |
| `l08_phases_sobre_unidad_apagada…` | L08 | `201` ≠ `403` | sí |
| `l14_progenitoras_el_actor_de_abuelas_crea_abuelas_y_no_reproductoras` | L14 | `201` (lote `breeder`) ≠ `403` | sí |
| `e02_la_evidencia_de_una_unidad_habilitada_no_concedida_es_inalcanzable` | E02 | `CONTENIDO-G` descargado ≠ `404` | sí |
| `e03_la_evidencia_de_una_unidad_apagada_es_inalcanzable…` | E03 | `CONTENIDO-H` descargado ≠ `404` | sí |
| `e04_cero_unidades_efectivas_no_descarga_nada` | E04 | `CONTENIDO-R` descargado ≠ `404` | sí |
| `l09_control_…_escribe_sobre_unidad_habilitada` | L09 (control) | fixture: lote con operaciones | corregida (setup) |

Controles verdes en rojo (14): `l01`, `l04` control, `l06`, `l09` close, `l10`, `l11` ×2, `l12`, `l15`, `e01`,
`e05`, `e06`, `e07`, `e08`.

## 4. Implementación (`T-040-H2…H4`) · commit `ab71b20` · `business_units/service.py` (+63/−) · `lots/service.py` (+42) · `operations/service.py` (+37)

| Pieza | Qué hace |
|---|---|
| `business_units.service.exigir_unidad_operativa(db, *, current_user, company_id, unidad, efectivas)` | la decisión de `G.3`/`H.5` en **un solo sitio**: actor de empresa → `unidad ∈ efectivas` o `no_concedida`; pendiente → ≥ 1 efectiva o `sin_unidades`; autoridad global → situada con habilitadas o `sin_empresa`, `unidad ∈ habilitadas` o `no_habilitada`; sin concesión exigida a la global |
| `AccesoDeUnidadDenegado(motivo, unidad)` | motivo estructurado; `exigir_acceso_a_unidad` (ORM, 0 llamadores) conserva su mensaje |
| `OperationsService.exigir_unidad_operativa` | deriva la unidad como antes y **delega**; traduce `no_concedida` → `400 BR-07 «Lote no encontrado»`, resto `403` (contrato de la enmienda G intacto: 40/40) |
| `LotService._exigir_unidad_operativa` + `_codigo` | traduce todo a `403`; llamada en `create_lot` (antes de `db.add`, con `data.bird_type`), `update_lot`, `close_lot` (antes de toda regla), `activate_manual`, `add_phase` |
| `get_evidence_for_download` | evidencia (`404`) → empresa (`403`, `R-139`) → **`get_event`** (`404` por unidad para el actor; global situada sin predicado) → fichero |

Sin rutas nuevas (`lots` 12 → 12, `operations` 17 → 17), sin migración (`s9t0u1v2w3x4`), sin campo de autorización en
el cuerpo (`bird_type` es dato de dominio, contrastado por el servidor), sin `is_global_actor`, sin lógica por
nombre de rol (2 usos nuevos de `is_super_admin`: la capacidad comodín, en la guarda compartida y en `lots`).

## 5. Verde dirigido

| Suite | Resultado |
|---|---|
| `test_lots_bu_enforcement.py` · **`R-163`** (`l*`, 19) | **19/19** |
| `test_lots_bu_enforcement.py` · **`R-162`** (`e*`, 9) | **9/9** |
| `test_operations_bu_enforcement.py` (`R-160`/`R-159`, delegación) | **40/40** |
| `test_od14_productive_surfaces.py` (`R-139`) | **35/35** |
| `test_lot_row_scope.py` (fase 3) · `test_population_invariant.py` (`R-130`, 21) · `test_lot_closure.py` · `test_lot_close_approval.py` · `test_business_unit_admin.py` (`== 7`) · `test_business_units.py` · `test_grant_candidates.py` · `test_session_payload.py` (`OD-15`) · `test_access_administration.py` · `test_rbac.py` · `test_multicompany_isolation.py` · `test_smoke.py` · `test_master_tenant_isolation.py` · `test_pending_classification.py` | **400 passed · 5 failed** en la primera pasada: las 5 de `test_business_unit_guard.py`, porque `exigir_acceso_a_unidad` seguía construyendo la excepción con un mensaje posicional (`KeyError`); corregido a motivo estructurado (mismo mensaje) → **25/25** + suite nueva 28/28 |

## 6. Sensibilidad (`§H.8`) · 6 ejecutadas · 3 `N/A` con motivo

Cada mutación se aplica marcada `MUTACION` (aplicación atómica: si un ancla falla, se revierte), se ejecuta la suite
del tranche (28; `S9` además la de la enmienda G, 40), se revierte con `git checkout --` y se comprueba
`git diff --quiet -- app/`.

| Mut. | Qué retira | Debía caer | Cayó | Válida |
|---|---|---|---|:--:|
| `S1` | la guarda en `create_lot` | `L02`/`L03`/`L07` | **6**: `l02`, `l03`, `l04`, `l05`, `l07`, `l14` | sí |
| `S2` | la habilitación en `unidades_habilitadas` (`is_enabled` ignorado) | `L07`/`L08` | **5**: `l07`, `l08` ×4 | sí |
| `S3` | confiar en la unidad del cliente | — | **`N/A`**: `bird_type` es el dato de dominio del lote y la guarda lo contrasta; «confiar» = no contrastar = `S1` | — |
| `S4` | la guarda en `update`/`close`/`activate-manual`/`phases` (4 sitios) | `L08` | **4**: `l08` ×4, exactamente | sí |
| `S5` | `get_event` en la descarga | `E02`/`E03`/`E04` | **3**: `e02`, `e03`, `e04`, exactamente | sí |
| `S6` | filtrar tras agregar/paginar | — | **`N/A`**: sin agregado ni paginación en estas superficies | — |
| `S7` | la negativa a la autoridad global **sin contexto** en la guarda compartida (`OD-14.d`) | `L05` | 1.ª pasada **0** (sobrevivió: sin contexto `habilitadas = []` y la rama «no habilitada» ya denegaba el lote **con** cadena); se añadió a `l05` el lote **sin** cadena; 2.ª pasada **1**: `l05` | sí (tras corregir la suite) |
| `S8` | tratar una capacidad de control como autoridad productiva | — | **`N/A`**: RBAC deniega antes (`l12`, `e07`, `l15` verdes en todas las pasadas); no hay rama que mutar | — |
| `S9` | la rama de habilitación del global **en la guarda compartida** | `L07`/`L08` + `AC-W13`/`A13` de la enmienda G | **11** sobre 68 (28 + 40): `l07`, `l08` ×4, `w13` ×5, `a13` global — la guarda es una y sujeta a las dos enmiendas | sí |

`git diff --quiet -- app/` tras cada reversión: limpio (6/6 + `S7` ×2). `grep -c MUTACION`: 0.

## 7. Correcciones durante el tranche

| # | Qué | Clase |
|---|---|---|
| 1 | `l09` control: el lote de `activate-manual` tenía un evento sembrado | fixture (setup), antes del código |
| 2 | `test_business_unit_guard.py` ×5: `exigir_acceso_a_unidad` construía `AccesoDeUnidadDenegado` con mensaje posicional tras añadir `motivo` | implementación (compatibilidad del constructor), mismo mensaje |
| 3 | `mutar3.py` `S4`: ancla sin la línea en blanco → el driver se detuvo y se relanzó con aplicación atómica; ningún resultado parcial se contabiliza | herramienta de sensibilidad |
| 4 | `S7` sobrevivía: `l05` solo enviaba un lote con cadena | prueba reforzada (lote sin cadena); `S7` repetida: 1 roja |
| 5 | `test_lot_planned_close.py::test_t_038_49`: el montaje creaba un usuario nuevo con `lots:create` y **sin concesión** y registraba un lote con él; con cero unidades efectivas esa escritura solo era posible por el defecto que `R-163` cierra (`OD-09.c`) → `403` | **TEST FIXTURE DEPENDENCY ON DEFECT**: se le concede la unidad antes de registrar (`habilitar_y_conceder_todo`) y el teardown retira la concesión antes que el usuario (clave foránea); las aserciones sobre el aviso no cambian; regresión completa repetida |

Ninguna prueba se debilitó; ningún contrato certificado cambió; ninguna decisión pendiente (`AOD-*`, `BU-D10`) se resolvió.

## 8. Regresión

| Comprobación | Resultado |
|---|---|
| backend completo (`scripts/run_tests.sh`, pgserver aislado) | 1.ª pasada **918 passed · 49 skipped · 1 failed** (760 s): `test_t_038_49`, dependencia de fixture del defecto (§7.5) · 2.ª pasada, tras ajustar solo el montaje: **919 passed · 49 skipped · 0 failed** (719 s; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) |
| `R-130` 21/21 · `R-139` 35/35 · `R-160`/`R-159` 40/40 · fase 3 `lots` · fase 7 (`== 7`) · fase 8 · `OD-15` · `OD-16` · Progenitoras (`l14`) · cero concesiones (`l04`, `e04`) · Administrador de Accesos (`l12`, `e07`, `l15`) | verdes |
| Contraloría | `N/A` (sin resolutor) |
| SAP transversal · `EX-01` · Watchtower · `pull_policy` | 0 ficheros tocados |
| migración | ninguna; `alembic heads` = `s9t0u1v2w3x4` |
| rutas | `lots` 12 → 12 · `operations` 17 → 17 |
| `vitest` | 87/87 (8 ficheros) |
| `tsc -b --noEmit` | 6 errores, los mismos preexistentes (`AuditPage.tsx` ×2, `LotFormPage.tsx` ×4) = `R-158` |
| E2E | `BLOCKED_RUNTIME` (sin cambio) |

## 9. Puertas de cierre

```
SPEC ............ GA-REM-040 enmienda H (b41b360) antes del código · aclaración del propietario trazada a OD-16   ✔
AC .............. AC-L01…L15 · AC-E01…E08                                                                      ✔
ROJO VÁLIDO ..... 13 tratamientos rojos por la aserción de contrato · 1 control corregido en fixture · 0 errores  ✔
VERDE ........... 28/28 (R-163 19/19 · R-162 9/9)                                                                 ✔
SENSIBILIDAD .... S1, S2, S4, S5, S9 válidas · S7 válida tras reforzar l05 · S3, S6, S8 N/A                                                 ✔
REGRESIÓN ....... completa leída antes de este commit                                                              ✔  (**919 passed · 49 skipped · 0 failed** (719 s; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado))
EVIDENCIA ....... este documento                                                                                  ✔
E2E ............. BLOCKED_RUNTIME → certificación de proceso NO                                                    —
```

`R-163` **CERRADO** (técnico) · `R-162` **CERRADO** (técnico) · `GA-REM-040-H` `CERTIFIED` en su frontera técnica.

## 10. Fuera de alcance — no tocado

`R-135` `R-143` `R-140` `R-154` `R-161` · resto de la ola B · ola C · fase 9 (FROZEN) · `R-158` · SAP · `BU-D10`
(PENDING_RATIFICATION; las fixtures siembran OFF y nada se reactiva) · frontend · migraciones · `P-08` · `R-99` ·
`EX-01` · lecturas de `lots` para la autoridad global (frontera declarada) · `egg-batches`/`chick-batches` (contrato).

## 11. Siguiente tranche (identificado, NO iniciado)

`R-135` + `R-143` (+ `R-140` motivo/guarda · `R-154` `DRAFT`/`version`): máquina de estados de `P-07`, `OD-17`
vigente; P1; sin SAP, sin fase 9, sin `BU-D10`. Tranche 3 del orden de `WAVE_B §3`; su pre-flight decide la spec.
