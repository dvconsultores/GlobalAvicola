# EVIDENCIA · WAVE B tranche 8 · PRE-FLIGHT DE CONSISTENCIA (`R-167` · `R-169` · `R-168`) + `R-170` + `GA-REM-021` `B13` (+ `B03` a decisión)

**WAVE B · tranche 8** · 2026-09-10 · spec `GA-REM-021-C` + `GA-REM-005-C` + `GA-REM-035-A` + `RC-12` + `AOD-22`/`AOD-23` (commit `ec974f0`) ·
código (commit `c653ff8`) · base `a02936c` · rama `main` · cabeza final `x4y5z6a7b8c9`

## 1. Entrada y descomposición

| Ítem | Valor |
|---|---|
| HEAD de partida `a02936c` · local == remoto · árbol limpio · Alembic `w3x4y5z6a7b8` · rutas 211 · origin https | sí |
| Recuento canónico | **27** tras el alta formal de `R-167…R-171` (`WAVE_B §18`; precedente `R-159…R-166`); antes 22 |
| Orden ejecutado | `R-167` / `R-169` / `R-168` → clasificación → `R-170` (activo, P1) corregido **antes** de `B13` → `B13` · `B03` gate → modo **C: `B13 ONLY`** |

## 2. Pre-flight (gates)

| Hallazgo | Determinación | Evidencia | Severidad | Acción |
|---|---|---|---|---|
| `R-167` | **NOT_REPRODUCED**: ninguna ruta descuenta `dead_on_arrival`; el alta no fabrica mortalidad; editar la tupla no toca el saldo; un `mortality_recording` es otro hecho y descuenta una vez (100/5/5 → saldo 90 → 90 → 85) | `R167_ARRIVAL_MORTALITY_ACCOUNTING_MATRIX.md` · `test_r167_…` (verde = no reproducido) | P3 → NO_DEFECTO | cerrado; residuo = doble captura por el operador (instrucción de proceso); KPI de mortalidad → ola C; `docs/16:177` superada |
| `R-169` | **ACTIVE_UI_CLASSIFICATION** (2 ocurrencias): recuadro «diferencia superior al 10 %» y texto «⚠️ ALERTA …» **inyectado en `observations`** al enviar; cantidad recibida vs OC (**no peso**); contrario a `OD-04` (parciales legítimas, sin tolerancia); sin backend, sin bloqueo, sin `OperationalAlert`. Otros ±10 %: `thermalCurves.ts` (`R-147`/`AOD-19`), KPI de uniformidad (ola C), fixture e2e, nombre de medicamento — no `R-169` | `R169_UNSOURCED_TOLERANCE_INVENTORY.md` (8 ocurrencias inventariadas) | P3 → P2 | retiradas ambas y sus textos; tarjeta de la OC conservada sin umbral (`GA-REM-035-A`, `AC15…17`) |
| `R-168` | **ACTIVE DEFECT** (pérdida silenciosa): «Muestra tomada» (Rec. §6) capturada por galpón y descartada por `BirdMovementSchema`; no altera `B02`; sin cálculo que la lea | `R168_SAMPLE_SIZE_CLASSIFICATION.md` | P3 → P2 | la recepción registra `sample_size` de evento (existente); campos por galpón retirados (recepción y distribución); control backend `test_r168_…` |
| **`R-170`** | **CONFIRMED ACTIVE DEFECT**: la UI emitía «Total nacidos» + ♂ + ♀ + «Débiles» como 4 filas; sin regla de nacimiento; observado por API: `201`, 4 filas, **viables 200, saldo 200** para 100 pollitos; `BR-04` admitía despachar el doble | `GA_REM_021_B13_BIRTH_CLASSIFICATION_MATRIX.md §3` · `test_r170_…` | **P1** (nuevo) | `GA-REM-005-C` · `BR-21` (una fila por sexo; `mixed` excluyente; Σ ≥ 1) + formulario sin fila total |
| `R-171` | la etapa de incubadora no ofrece descarte ni mortalidad (viables ≡ nacidos desde la UI) | matriz `B13 §8` | P2 (nuevo) | registrado; fuera |
| `B13` | gobernado: sanos/débiles = atributos disjuntos de los nacidos (`Bases` p.9), `≤ nacidos`, sin efecto en saldo; débil ≠ descarte; solo incubadora; igualdad de la partición → `AOD-23` (no bloquea) | matriz `B13` · `RC-12` (`RR-14`, `RR-15`) | P2 | implementado |
| `B03` | **`OWNER_DECISION_REQUIRED`** (`AOD-22`: parciales vs diferencia acumulada, dato/derivado, unidad (`AOD-19`), cero) — `OD-04` no se extiende a OT por inferencia (`GA-REM-035 §4`); maestros silo/lote `SAP_DEFERRED` | `GA_REM_021_B03_FEED_TRANSFER_MATRIX.md` | P2 | **sin código** |

Independencia: `B03` ⟂ `B13`; `B13` ⟂ `R-161` (agregados de aves con bloqueo; sin regla nueva sobre huevos).

## 3. Rojo previo · validez (sobre `ec974f0`: spec sin código)

| Grupo | Pruebas | Observado ≠ exigido | Válida |
|---|---|---|:--:|
| `R-170` | `test_r170_…` | 4 filas → `201` (viables 200) ≠ `400 BR-21` | sí (reproducción del defecto) |
| `B13`: datos descartados / sin regla | `b13_01…` (`KeyError 'chicks_healthy'`), `b13_02_03_04` (negativo → `201`; > nacidos → `201`), `b13_15` (campos aceptados en `chick_dispatch` y en reproductoras), `b13_11_14` (`PUT` → `422 extra_forbidden`) | el contrato ignora `chicks_healthy`/`chicks_weak` (patrón `R-47`) y no existe rama de nacimiento | sí |
| `R-169` / `R-168` (frontend) | `receptionFormContract.test.ts`: `AC15` (`pctDiff` presente), `AC16` (`sapQtyAlert` presente), `R-168` (`bird_movements.${i}.sample_size` presente) | contrato estático | sí |
| controles verdes en rojo | `b13_05_09` (cadena certificada), `test_r167_…` (no reproducido), `test_r168_…` (el campo de evento ya se persistía), `AC17` (tarjeta de la OC) | — | — |
| arnés | `b13_01` afirmaba el KPI sobre un evento `REGISTERED` (el KPI cuenta aprobados): se aprueba por SQL antes de leerlo | inválido como rojo; corregido | — |

## 4. Implementación (commit `c653ff8`)

| Pieza | Qué hace |
|---|---|
| `alembic/versions/x4y5z6a7b8c9_birth_classification.py` | `operational_events.chicks_healthy`, `chicks_weak` (`INTEGER NULL`); sin relleno; bajada guardada |
| `validators.validate_birth_registration` (`BR-21`) | una regla, tres puntos (alta, edición, corrección): Σ ≥ 1 · una fila por sexo · `mixed` excluyente · sanos/débiles obligatorios y explícitos en incubadora · `sanos + débiles ≤ nacidos` · prohibidos fuera del nacimiento y fuera de la incubadora |
| `OperationalEventBase`/`Update` | `chicks_healthy`, `chicks_weak` (`ge=0`); corregibles uno a uno con revalidación (`≤`, no tupla de igualdad) |
| `OperationFormPage` nacimiento | filas «Nacidos machos / hembras / sin sexar» + «Sanos» + «Débiles» + total derivado; sin fila «Total nacidos» ni «Débiles» como nacidos |
| `OperationFormPage` recepción | sin `pctDiff`/`outOfRange`/recuadro ámbar; sin inyección `sapQtyAlert` en `observations`; «Muestra tomada» como `sample_size` de evento; sin `bird_movements[i].sample_size` (recepción y distribución); textos es/en retirados/añadidos |
| guardianes | cabeza → `x4y5z6a7b8c9`; rutas 211; `test_clean_baseline` (55 tablas) y `test_time_determinism` en el verde dirigido |
| fixtures (solo setup) | nacimientos de incubadora de `test_kpi_hatchery` (2), `test_reception_lineage` (1), `test_population_invariant` (1) declaran sanos/débiles; aserciones intactas |

Saldo: `get_viable_chick_balance`, `get_current_bird_balance`, `_suma_neta` y el KPI **no cambian**: `BR-21` garantiza que las filas
sumadas son los nacidos y nada más.

## 5. Verde dirigido

| Suite | Resultado |
|---|---|
| `test_birth_classification.py` · **`R-170` + `B13`** | **6/6** |
| `test_reception_reconciliation.py` · `B01` + `R-167` + `R-168` | **10/10** |
| `receptionFormContract.test.ts` (`R-169` `AC15…17` · `R-168` · `R-170`/`B13` formulario) | **6/6** (vitest 95/95 en total) |
| obligatorias (§6): `test_clean_baseline` · `test_time_determinism` · guardianes de cabeza/rutas/catálogo · enumerados | verdes |
| relacionadas: `R-130` (21) · `B02` · `B05` · OC (`GA-TD-014`) · linaje · trazabilidad · KPI de incubadora · genética (4) · reversos · `R-135`/`R-143` · `R-159`/`R-160` · `R-162`/`R-163` · `OD-14` · RBAC · unidades · acceso · sesión · roles del reverso · flujo completo · humo · transacción · contrato de error · persistencia · maestros · aislamiento · cierre de lote · fecha de inicio · notificaciones · saldo inicial | **705/705** |
| `tsc -b --noEmit` | 6 errores, los mismos (`R-158`) |

## 6. Sensibilidad (`GA-REM-021-C §C.7`)

Cada mutación se aplica marcada `MUTACION`, se ejecuta `test_birth_classification.py` (backend) o el contrato estático (frontend), se
revierte con `git checkout --` y se comprueba el árbol. Todas revertidas limpias.

| Mut. | Qué retira | Debía caer | Cayó | Válida |
|---|---|---|---|:--:|
| `S-R170-1` | la regla de filas (`mixed` exclusivo, una por sexo, Σ ≥ 1) | `AC-R170-01…04` | **1**: `r170` — las formas «total + desglose», «mixed + sexadas» y «dos filas del mismo sexo» vuelven a dar `201` (nacidos duplicados) | sí |
| `S-B13-1` | `sanos + débiles ≤ nacidos` | `AC-B13-03` | **2**: `b13_02_03_04` (91 + 5 > 95 → `201`), `b13_11_14` (edición y corrección que superan los nacidos → `200`/`201`) | sí |
| `S-B13-2` | `ge=0` del esquema (negativos y decimales admitidos por el contrato) | `AC-B13-02` | **1**: `b13_02_03_04` — negativos y decimales dejan de dar `422` | sí |
| `S-B13-3` | los sanos entran también al saldo de viables (segunda contabilidad) | `AC-B13-12` | **2**: `b13_01_10_12` (viables 185 ≠ 95: los sanos se suman al saldo), `b13_11_14` (viables alterados por la corrección) | sí |
| `S-B13-4` | confiar en un total del cliente | — | **`N/A`**: no hay total en el cuerpo (los nacidos son Σ filas) | — |
| `S-B13-5` | la habilitación de la unidad en la guarda compartida | `AC-B13-06` (global) | **1**: `b13_05_09` — la autoridad global situada en `B` registra el nacimiento sobre la incubadora apagada (`201` ≠ `403`) | sí |
| `S-B13-6` | la concesión del actor | `AC-B13-06/07` | **1**: `b13_05_09` — el actor con concesión histórica sobre la incubadora apagada registra | sí |
| `S-B13-7` | `operations:create` → `read` en la ruta | `AC-B13-08` | **2**: `b13_05_09` (`sin_perm`, Administrador de Accesos y control-lectura registran con `operations:read`), `b13_11_14` (la denegada esperada deja de serlo) | sí |
| `S-B13-8` | la revalidación en corrección | `AC-B13-11` | **1**: `b13_11_14` — la corrección deja `sanos + débiles > nacidos` y crea `correction_logs` | sí |
| `S-B13-9` | obligatoriedad y aplicabilidad por cadena/tipo (campos admitidos en cualquier evento/unidad; ausentes admitidos) | `AC-B13-03/15` | **2**: `b13_02_03_04` (sin sanos/débiles → `201`), `b13_15` (`chick_dispatch` y lote de reproductoras aceptan los campos) | sí |
| `SEC-S1` | la empresa en las cuatro capas del alta | `AC-B13-05` con fila observada | **1**: `b13_05_09` — el actor de `B` **escribe** el nacimiento sobre el lote de `A` (`201` observado; fila creada) | sí |
| `S-R169-1` | reintroducir el umbral ±10 % en el formulario | `AC15` (contrato estático) | **1**: `AC15` — `pctDiff`/`outOfRange` reaparecen en el formulario | sí |
| `S-R169-2` | frontend ±10 % de peso contra la curva del backend | — | **`N/A`**: el ±10 % nunca fue de peso; la evaluación de peso consume el backend | — |
| `S-R168-1` | volver a registrar la muestra por galpón en vez del campo de evento | `AC-R168-01` (contrato estático) | **1**: `R-168` — vuelve `bird_movements.${i}.sample_size` y desaparece el campo de evento | sí |

Contabilidad: intentadas 12 (`S-R170-1`, `S-B13-1/2/3/5/6/7/8/9`, `SEC-S1`, `S-R169-1`, `S-R168-1`) · inicialmente inválidas 0 · reconstruidas 0 ·
válidas finales 12 · `N/A` 2 (`S-B13-4`, `S-R169-2`, declaradas en `§C.7`) · acreditadas inválidas 0 · residuo `MUTACION` 0 · 12 reversiones
limpias (backend `git diff --quiet -- app/`; frontend `git checkout --`). `S-B13-3` demuestra que sanos/débiles **no** son una segunda cuenta:
sumarlos al saldo rompe `viables = nacidos`. `SEC-S1` retira cuatro capas de empresa a la vez (lección del tranche 4): la fuga se observa.


## 7. Regresión

| Comprobación | Resultado |
|---|---|
| backend completo (`scripts/run_tests.sh`: `alembic upgrade head` → semillas → pytest) | **1024 passed · 49 skipped · 0 failed** (857 s; 1016 previas + 6 de `test_birth_classification.py` + 2 de `test_reception_reconciliation.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) |
| `R-130` 21/21 · `B01` 10/10 · `B02` 8/8 · `B05` 16/16 · `GA-TD-014` 7/7 · KPI incubadora · `R-136`/`R-165` · `R-135`/`R-143` · `R-159/R-160` · `R-162/R-163` · `R-139` 35/35 · `OD-14`/`OD-16` | verdes |
| `authorization_coverage` (211) · `route_scope` (`RQ-03` sin recurso nuevo) · `SOLO_SUPER_ADMIN` 13 · `t_025_02` 48 · BU admin `== 7` · cabeza `x4y5z6a7b8c9` | exactos |
| migración | `x4y5z6a7b8c9` aplicada por `upgrade` en la base de pruebas (55 tablas); sin enumerados nuevos |
| `vitest` · `tsc` | 95/95 · 6 (`R-158`) |
| E2E | `BLOCKED_RUNTIME` (`e2e/proceso-p05-incubacion`, `p10`, `p15` registran nacimientos de incubadora sin sanos/débiles: deberán declararlos cuando el runtime esté disponible; no se editan a ciegas) |

## 8. Cierre

```
R-167 ................ CERRADO · NOT_REPRODUCED (nota de proceso; KPI → ola C)                                                          ✔
R-169 ................ CERRADO (técnico) · GA-REM-035-A CERTIFIED (frontera técnica): sin tolerancia ±10 % en el cliente                    ✔
R-168 ................ CERRADO (técnico) · «Muestra tomada» persistida como dato de la recepción                                            ✔
R-170 ................ CERRADO (técnico) · GA-REM-005-C CERTIFIED (frontera técnica) · BR-21 · una sola contabilidad de nacimientos          ✔
B13 / H360-B13 ....... CERRADO (técnico) · sanos/débiles como atributos del nacimiento · ≤ nacidos · sin efecto en el saldo                  ✔
GA-REM-021-C ......... CERTIFIED (frontera técnica)                                                                                       ✔
B03 / H360-B03 ....... OWNER_DECISION_REQUIRED (AOD-22 + AOD-19) · sin código                                                             ⏸
R-171 ................ OPEN (registrado)                                                                                                    —
GA-REM-021 ........... PARTIAL (B03 ◄── AOD-22 · B04 ◄── AOD-14 · R-156 ◄── AOD-20)                                                          ◐
E2E .................. BLOCKED_RUNTIME → certificación de proceso NO                                                                        —
```

## 9. Riesgos restantes y fuera de alcance

`AOD-23` (igualdad sanos + débiles = nacidos: endurecimiento posterior, sin migración) · `AOD-22` (`B03`) · `R-171` (la incubadora sigue sin
poder registrar descarte/mortalidad desde el catálogo) · `R-161` OPEN · `R-164` BLOCKED_RUNTIME · `R-166` OPEN · nacedora/incubadora del
nacimiento no persistida (`docs/02 §3.7.5`; fuera) · KPI «% sanos» (ola C) · `BU-D10` · `R-158`.

## 10. Siguiente tranche (identificado, NO iniciado)

**`R-161`** (P2, `DATA_INTEGRITY`): los saldos de huevos e incubación (`BR-02`, `BR-03`) se leen sin bloqueo de fila — la misma carrera que
`R-130` cerró para las aves; sin decisión pendiente; desbloquea el reverso de huevos/incubación (`OD-19 §18`). Acompañante posible: `R-171`
(catálogo de incubadora: descarte y mortalidad, `Bases` p.10 · Rec. §12; pequeño y gobernado). Alternativa: `R-152` → `R-153` (Progenitoras).
`B03` espera `AOD-22`.
