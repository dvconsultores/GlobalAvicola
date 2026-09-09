# EVIDENCIA · `R-135` + `R-143` (+ `R-140` PARTE A · `R-154` subconjunto) · CONTINUIDAD DE ESTADOS DE `P-07` Y SEGREGACIÓN CORRECTOR/RECHAZADOR ≠ APROBADOR

**WAVE B · tranche 4** · 2026-09-09 · specs `GA-REM-006` enmienda A y `GA-REM-007` enmienda A (commit `83a984b`) ·
matriz previa `R135_R143_STATE_CORRECTION_MATRIX.md` · pre-flight `WAVE_B_TRANCHE_4_PREFLIGHT.md` · base `5b64104` · rama `main`

## 1. Pre-flight

| Ítem | Resultado |
|---|---|
| HEAD de partida `5b64104` · local == remoto · árbol limpio · Alembic `s9t0u1v2w3x4` | sí |
| `R-163` severidad normalizada | **P1** (criterio del propio backlog: clase `R-160` para `POST /lots` sin unidad para todo actor; clase `R-139` para lotes sin empresa); `R-163` **no** se reabre |
| `lots.company_id IS NULL` | consulta contra la base configurada (`DATABASE_URL`, host remoto; credenciales no expuestas): `TimeoutError` → **`BLOCKED_RUNTIME`** · recuento **`UNKNOWN`** · **no se infiere cero** · **nada limpiado** |
| Filas históricas inválidas encontradas | `UNKNOWN` (sin acceso) |
| Hallazgos nuevos | **`R-164`** (P2: `Lot.company_id` nulable sin restricción; deuda `UNKNOWN`) · **`R-165`** (P2: plano de revisión sin habilitación para la autoridad global) · **`R-166`** (P3: carrera `approve`/`reject`) |

## 2. Composición del tranche (puerta §21 del encargo)

| Pregunta | Respuesta | Por qué |
|---|---|---|
| `R-135` + `R-143` misma raíz | **NO** (raíz y spec distintas) · **misma máquina de estados, mismo servicio, misma decisión `OD-17.b`** | dos enmiendas (`GA-REM-006-A`, `GA-REM-007-A`), un tranche, AC/pruebas/estado separados |
| `R-140` subconjunto | **SÍ · PARTE A** (guarda de estados de `cancel`) | motivo obligatorio: el cliente llama `cancel` **sin cuerpo** (`operations.service.ts:47`) → vertical de UI, fuera; permiso «solo administrador» → `AOD-18` |
| `R-154` subconjunto | **SÍ** (`DRAFT` en el mapa de transiciones + controles; `version` documentada: avanza en `PUT` y en corrección) | dos «cierres» (`AOD-08`) y `LotStatus.CANCELLED` quedan abiertos |
| Decisión pendiente dentro del subconjunto | **NO** | `OD-17.a/b` vigente; `RR-01`, `RR-03` |
| SAP · `BU-D10` | **NO** | `OD-17.c` diferido; fixtures siembran ON/OFF |

## 3. `OD-17` y el grafo (matriz §2)

`RETURNED`/`REJECTED` = devolución interna, viva; `CANCELLED` y el ciclo SAP = terminal/diferido. Reenvío = acto explícito
(`POST /operations/{id}/submit`) → `PENDING_REVIEW`. Corrección (`RR-01`) → `CORRECTED` → aprobador. `CORRECTED` por
`complete_review` (`R-142`, `AOD-17`) **no se toca**. Sin estados nuevos, sin renombrar, sin migración.

## 4. Rojo previo · validez

`tests/test_state_continuity.py` (24) + `tests/test_segregation_r143.py` (6) · 30 pruebas · sobre `83a984b` (spec sin
código): **16 rojas · 14 verdes**. 0 errores de import/fixture/`NameError`. Cada roja cae en la aserción de contrato:

| Prueba | AC | Observado ≠ exigido | Válida |
|---|---|---|---|
| `s01_el_devuelto_se_reenvia…` | S01 U03 | `400 «Solo eventos registrados…»` ≠ `200` | sí |
| `s01_el_rechazado_se_reenvia…` | S01 S02 | `400` ≠ `200` | sí |
| `s02_el_rechazado_es_editable…` | S02 | `400 «…borrador, registrados o devueltos»` ≠ `200` | sí |
| `s02_el_rechazado_es_corregible…` | S02 S03 | `400 «no se puede corregir en estado 'rejected'»` ≠ `201` | sí |
| `s06_la_unidad_no_concedida_no_se_corrige` | S06 | `201` (corrección escrita) ≠ `404` | sí |
| `s07_la_unidad_apagada_no_se_corrige…` | S07 | `201` ≠ `404` | sí |
| `s07_la_autoridad_global_no_corrige…` | S07 | `201` ≠ `403` | sí |
| `s11_los_terminales_no_se_cancelan…` | S11 (`R-140` A) | `200` (cancelado un `SAP_CONFIRMED`) ≠ `400` | sí |
| `r01_r05_…sobreviven…` | R01 R04 R05 | `400` en el reenvío ≠ `200` | sí (cadena de `R-135`) |
| `r02_r03_…no_vacio` | R03 | `201` con motivo de espacios ≠ `4xx` | sí |
| `u03_u04_…vuelve_a_la_cola…` | U03 U04 | `400` ≠ `200` | sí |
| `u05_el_reenvio_no_duplica_el_efecto` | U05 | `400` ≠ `200` | sí (cadena) |
| `progenitoras_…` | Progenitoras | `400` ≠ `200` | sí |
| `g02_quien_corrige_no_aprueba…` | G02 | `200` (aprobado por su corrector) ≠ `403 BR-14` | sí |
| `g04_quien_rechazo_no_aprueba_el_reenvio` | G04 | `200` (aprobado por quien lo rechazó) ≠ `403 BR-14` | sí |
| `g06_completar_la_revision…` | G06 | `200` (aprobado vía `complete`) ≠ `403 BR-14` | sí |

Controles verdes en rojo (14): `s03`, `s04/s08`, `s05`, `s06` (reenvío), `s07` (sin contexto), `s09`, `s10`, `s12`,
`r06/r07`, `d01-d05`, `u01/u02`, `g01`, `g03`, `g05`.

## 5. Implementación (commit `5c824d9`) · `operations/service.py` (+30/−) · `corrections/service.py` (+27) · `corrections/schemas.py` (+10) · `review/service.py` (+20)

| Pieza | Qué hace |
|---|---|
| `EDITABLES` · `REENVIABLES` · `NO_CANCELABLES` | mapa explícito de `P-07` desde el que cada acto es válido; sin `setattr` de estado desde el cliente (`R-32`) |
| `submit_to_review` | reenvía desde `RETURNED` y `REJECTED` → `PENDING_REVIEW`; `audit_state_transition` con `previous_state`/`new_state`; `approval_actions` del revisor intactos; misma fila (sin doble efecto) |
| `update_event` | `REJECTED` editable (`OD-17.a`); `version += 1` |
| `cancel_event` | denegado desde `SAP_CONFIRMED`, `SAP_ERROR`, `CANCELLED` (`R-140` PARTE A) |
| `create_correction` | `REJECTED` corregible; el evento se resuelve con `OperationsService.get_event` (empresa + unidad efectiva → `404`) y `exigir_unidad_operativa` (global: habilitada o `403`) |
| `CorrectionCreate.reason` | validador: motivo en blanco → `422` |
| `_exigir_segregacion` | aprobador ∉ {registrador} ∪ {`correction_logs.corrected_by_id`} ∪ {`approval_actions.REJECTED.user_id`} bajo `require_segregation`; `BR-14`; devolver no cuenta |

Sin rutas nuevas (`review` 6, `corrections` 3, `operations` 17, `lots` 12; total 208), sin migración, sin estados ni
enumerados nuevos, sin frontend, sin `is_global_actor`, sin lógica por nombre de rol, 0 usos nuevos de `is_super_admin`.

## 6. Verde dirigido

| Suite | Resultado |
|---|---|
| `test_state_continuity.py` · **`R-135`** (+ `R-140` A · `R-154` subconjunto) | **24/24** |
| `test_segregation_r143.py` · **`R-143`** | **6/6** |
| `R-140` subconjunto (`s11`) · `R-154` subconjunto (`d01-d05`, `s09`, `s12`) | verdes (incluidos arriba) |
| relacionadas: `test_corrections` (9) · `test_full_workflow_audit` (23, incl. `f4b` segregación) · `test_review` (7) · `test_lot_close_approval` (6) · notificaciones · `R-160/R-159` (40) · `R-163/R-162` (28) · `R-139` (35) · `R-130` (21) · `rbac` · pendientes · `OD-15` · SAP transversal · auditoría | **353/353** |

## 7. Sensibilidad (`§A.7`, `§A.3` de las enmiendas) · 10 ejecutadas · 1 `N/A`

Cada mutación se aplica marcada `MUTACION` (aplicación atómica), se ejecuta la suite del tranche (30), se revierte con
`git checkout --` y se comprueba `git diff --quiet -- app/`. Todas revertidas limpias.

| Mut. | Qué retira | Debía caer | Cayó | Válida |
|---|---|---|---|:--:|
| `S1` | `RETURNED`/`REJECTED` del mapa de reenvío | `S01` | **6**: `s01` ×2, `r01_r05`, `u03_u04`, `u05`, `progenitoras` | sí |
| `S2` | la guarda de estado origen en `submit` (cualquier estado reenvía) | `S09`/`S10`/`S11` | **6**: `s09`, `s10`, `s11`, `d01_d05`, `r01_r05`, `r06_r07` | sí |
| `S3` | el permiso de la ruta de corrección (`correct` → `read`) | `S04` | **2**: `s04_s08` (el actor de control-lectura corrige), `s05` (contrato `404` → `403`) | sí |
| `S4` | la empresa en `get_event` (una capa) | `S05` | **1**: solo `s07` (global sin contexto → `400`); `s05` **no** cayó: el predicado de unidad (ligado a la empresa) y la guarda compartida siguen bloqueando la escritura entre inquilinos — **insuficiente**, no acreditada | **inicialmente inválida** |
| `S4b` (reconstruida) | la empresa en `get_event` **+** en `lotes_alcanzables` **+** en `_unidad_del_lote` (tres capas) | `S05` | **1**: `s05` — el actor de `B` **escribe** una corrección sobre el evento de `A` (`201` observado ≠ `404`) | sí |
| `S5` | la guarda de habilitación en la corrección | `S07` | **1**: `s07` global (corrección escrita sobre unidad apagada) | sí |
| `S6` | el validador de motivo en blanco | `R03` | **1**: `r02_r03` | sí |
| `S7` | la auditoría del reenvío | `R04`/`R05` | **1**: `r01_r05` | sí |
| `S8` | la inmutabilidad de `APPROVED` en `update_event` | `S10` | **1**: `s10` | sí |
| `S9` | doble aplicación | — | **`N/A`**: no existe rama que duplique filas/movimientos al reenviar (`u05` es control) | — |
| `S10` | los correctores del conjunto de segregación | `G02`/`G06` | **3**: `g02`, `g04` (su mitad de corrector), `g06` | sí |
| `S11` | quien rechazó del conjunto | `G04` | **1**: `g04`, exactamente | sí |

Contabilidad: intentadas 12 · inicialmente inválidas 1 (`S4`) · reconstruidas 1 (`S4b`) · válidas finales 10 · `N/A` 1 ·
acreditadas inválidas 0 · residuo `MUTACION` 0. Lección de `S4`: la escritura entre inquilinos en la corrección está
protegida por **tres** capas independientes; una sola mutación no la abre. Se registra como defensa en profundidad, no como
mérito de la prueba.

## 8. Regresión

| Comprobación | Resultado |
|---|---|
| backend completo | **949 passed · 49 skipped · 0 failed** (735 s, primera pasada; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) |
| `R-130` 21/21 · `R-159/R-160` 40/40 · `R-162/R-163` 28/28 · `R-139` 35/35 · `GA-REM-006` 9/9 · `GA-REM-007` (`f4b`) · `RQ-03` (`test_route_scope`/clasificación en `test_business_units`) · `OD-14` (`test_od14`) · `OD-16` (`l07/l08`, `w13`, `s07`) · Administrador de Accesos (`s04/s08`) · control transversal de solo lectura (`lectura` → `403`) · Contraloría (`N/A`: sin resolutor; el rol de solo lectura la representa) · Progenitoras (`ev_ret_g2`) | verdes |
| rutas 208 · `SOLO_SUPER_ADMIN ≤ 15` · `test_business_unit_admin == 7` | sin cambio |
| migración | ninguna; `s9t0u1v2w3x4` |
| `vitest` | 87/87 |
| `tsc -b --noEmit` | 6 errores, los mismos (`AuditPage.tsx` ×2, `LotFormPage.tsx` ×4) = `R-158` |
| E2E | `BLOCKED_RUNTIME` |

## 9. Puertas de cierre

```
R-135 .......... CERRADO (técnico): devuelto/rechazado no terminales · reenvío explícito y gobernado · estados inválidos
                 denegados · inquilino/unidad/RBAC · motivo del revisor y auditoría preservados · sin doble efecto ·
                 aprobado inmutable                                                                                ✔
R-143 .......... CERRADO (técnico): aprobador ≠ registrador ≠ corrector ≠ quien rechazó, bajo require_segregation    ✔
R-140 .......... PARTIAL: PARTE A (guarda de estados) cerrada · motivo (UI) y permiso (AOD-18) OPEN                  ◐
R-154 .......... PARTIAL: DRAFT en el mapa + version documentada · cierres (AOD-08) y LotStatus.CANCELLED OPEN       ◐
SPEC/AC/ROJO/VERDE/SENSIBILIDAD/REGRESIÓN/EVIDENCIA ............................................................. ✔
E2E ............ BLOCKED_RUNTIME → certificación de proceso NO                                                       —
```

## 10. Fuera de alcance — no tocado

SAP (`OD-17.c`) · `R-136` · `R-142` (`AOD-17`) · `R-140` motivo/permiso · `R-154` cierres · `R-161` · `R-144` · `R-147` ·
`R-148` · `R-152` · `R-153` · `R-156` · `GA-REM-021` · ola C · fase 9 · `R-158` · `BU-D10` · `R-164` · `R-165` · `R-166` ·
frontend · migración · sistema de versiones · reverso.

## 11. Siguiente tranche (identificado, NO iniciado)

Releída la matriz de dependencias (`§3`: tranche siguiente = `R-136` reverso interno, «requiere los estados de 3 estables»,
ya estables): **`R-136` parte interna** (P1; `BR-16`, `docs/16 G-R09`, tabla `reversals` sin servicio; spec propia; la parte
SAP sigue `SAP_DEFERRED`), con **`R-165`** como acompañante de coste mínimo (misma guarda compartida). `GA-REM-021` agua
(P1, `SPEC_READY`) es la alternativa si el propietario prioriza captura sobre integridad de estados; `R-164` espera acceso
a la base (`BLOCKED_RUNTIME`).
