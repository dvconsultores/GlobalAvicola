# EVIDENCIA · `R-161` · LOS SALDOS DE HUEVOS E INCUBACIÓN BAJO EL BLOQUEO DEL LOTE (+ pre-flight `R-171`)

**WAVE B · tranche 9** · 2026-09-10 · spec `GA-REM-005-D` + `RC-13` (commit `22476bb`) · código (commit `abd3179`) · base `8720e31` · rama `main` ·
cabeza `x4y5z6a7b8c9` (sin migración) · rutas 211

## 1. Entrada y descomposición

| Ítem | Valor |
|---|---|
| HEAD de partida `8720e31` · local == remoto · árbol limpio · Alembic `x4y5z6a7b8c9` · rutas 211 · origin https | sí |
| Recuento revalidado desde el backlog | 27 · 12 cerrados · 4 parciales · 11 abiertos (consistente con `WAVE_B §19`); altas de este pre-flight `R-172`…`R-174` → **30** |
| `R-161` | P2 `DATA_INTEGRITY`: `validate_egg_dispatch` (`BR-02`) y `validate_incubation_load` (`BR-03`) leían el saldo sin `bloquear_saldo_del_lote`; el servicio saltaba la validación con cantidad 0 |
| `R-171` | UI_ONLY, gobernado, raíz distinta (`R171_HATCHERY_MORTALITY_DISCARD_TRUTH_MATRIX.md`) → **OPEN, siguiente**; control `AC-R161-16` demuestra que el dominio ya lo admite |
| Modo | **R161_ONLY** (CASO B) |
| Decisión del propietario | ninguna |

## 2. Superficies y bloqueo (`R161_EGG_INCUBATION_BALANCE_WRITER_MATRIX.md`)

| Saldo | Escritores (−) | Fila autoritativa | Antes | Ahora |
|---|---|---|---|---|
| `BR-02` huevos del lote (Σ recolección − Σ despacho) | `egg_dispatch` | `lots.id` | lectura sin bloqueo; `if total > 0` saltaba la regla | `bloquear_saldo_del_lote` → relectura → `> 0` y `≤ saldo` → alta en la misma transacción |
| `BR-03` huevos en incubadora (Σ recepción − Σ cargas) | `incubation_load` | `lots.id` | ídem | ídem |

Corrección: N/A (submovimientos no corregibles). Aprobación: N/A (el efecto nace en el alta). Reverso: `OD-19 §18` intacto (los saldos de
huevos no usan `_suma_neta`; habilitar su reverso es una enmienda futura de `GA-REM-041`). `R-166`: otro invariante, sigue OPEN. Bloqueo por
recurso (lote): dos lotes no se serializan entre sí (`AC-R161-07`). Un solo bloqueo: sin orden ni interbloqueo. Registrados fuera: `R-172`
(todas las `egg_type` cuentan en `BR-02`), `R-173` (`PUT` de lote / `cancel` de entradas sin revalidar), `R-174` (`chick_dispatch` 0), y en el
cierre `R-175` (aislamiento de pruebas: `test_lot_start_date`, `test_lots_bu_enforcement` y `test_od14_productive_surfaces` dejan una
`ProductivePhase`; `test_t_025_07` cae en invocaciones no alfabéticas — la roja 724/725 del verde dirigido — y no en la regresión completa;
identificado por pares ordenados, `test_opening_balance` sí limpia).

## 3. Rojo previo · validez (sobre `22476bb`: spec sin código)

Reproducción **observada**, no inferida (`asyncio.gather`, cinco decrementos de 70 sobre 100 en tres lotes frescos por familia):

| Prueba | Observado | Exigido | Válida |
|---|---|---|:--:|
| `r161_05` despachos de huevos | en `lr`, `lr2`, `lr3`: códigos `[201 ×5]`, **5 filas, saldo −250** | `[201, 400 ×4]`, 1 fila, saldo 30 | sí |
| `r161_06` cargas de incubadora | en `lh`, `lh2`, `lh3`: `[201 ×5]`, **saldo −250** (con tres peticiones y un solo lote reproducía sola 3/3 y en la suite pasó una vez por tiempo: por eso se reforzó a cinco peticiones y tres lotes) | ídem | sí |
| `r161_04` cantidad 0 | despacho y carga de 0 → `201` (la guarda `if total > 0` saltaba la regla) | `400 BR-02/03` | sí |
| controles verdes en rojo | `r161_01_02_03_15` (secuencial, resto exacto, uno de más), `r161_07` (dos lotes), `r161_10_14` (cadena certificada), `r161_16` (`R-171`: mortalidad y descarte en incubadora restan de viables) | — | — |

## 4. Implementación (commit `abd3179`; 2 ficheros de producto)

| Pieza | Qué hace |
|---|---|
| `validators.validate_egg_dispatch` · `validate_incubation_load` | `bloquear_saldo_del_lote(lot_id)` **antes** de `get_egg_balance` / `get_hatchery_egg_balance`; la validación usa el saldo releído bajo el bloqueo (misma primitiva que `validate_bird_decrement`, `R-130`) |
| `service._apply_business_rules` | sin la guarda `if total > 0` en `EGG_DISPATCH` e `INCUBATION_LOAD`: la regla rechaza el cero (`BR-02`/`BR-03`), como `R-130 AC04` |
| sin cambio | fórmulas de saldo, esquemas, rutas (211), migraciones (cabeza `x4y5z6a7b8c9`), frontend |

## 5. Verde dirigido

| Grupo | Resultado |
|---|---|
| secuencial / bordes / cero (`AC-R161-01…04`) | **2/2** |
| carreras (`AC-R161-05/06`, 3 lotes × 5 peticiones cada una) | **2/2** — `[201, 400 ×4]`, 1 fila, saldo 30 en los seis lotes |
| bloqueo por recurso (`AC-R161-07`) | **1/1** |
| multi-escritor (`08`) · corrección (`09`) | **N/A** (un decremento por saldo; submovimientos no corregibles) |
| seguridad (`10…14`) · auditoría (`15`) · control `R-171` (`16`) | **2/2** |
| obligatorias: `test_clean_baseline` (N/A por cambio; ejecutada) · `test_time_determinism` · guardianes de cabeza/rutas/catálogo | verdes |
| relacionadas: `R-130` (21) · `R-170`/`B13` · `B01` · `B02` · `B05` · KPI incubadora · linaje · trazabilidad · OC · reversos · `R-135`/`R-143` · `R-159`/`R-160` · `R-162`/`R-163` · `OD-14` · RBAC · unidades · acceso · sesión · roles · flujo completo · humo · transacción · error · persistencia · maestros · aislamiento · genética · cierre · fecha · notificaciones · saldo inicial · seguridad · multiempresa | **724/725 en una invocación no alfabética (la roja, `test_t_025_07` «5 fases», es residuo de otra suite: no se reproduce en la regresión completa; suite identificada por pares ordenados, ver `R-175`)** |
| `vitest` · `tsc` | 95/95 · 6 (`R-158`), sin cambio de frontend |

## 6. Sensibilidad (`GA-REM-005-D §D.3`)

Cada mutación se aplica marcada `MUTACION`, se ejecuta `test_egg_incubation_concurrency.py` (7), se revierte con `git checkout --` y se
comprueba `git diff --quiet -- app/`. Todas revertidas limpias.

| Mut. | Qué retira | Debía caer | Cayó | Válida |
|---|---|---|---|:--:|
| `R161-S1` | el bloqueo en los dos validadores | `AC-R161-05/06` | **2**: `r161_05`, `r161_06` — vuelven las cinco confirmaciones y el saldo −250 en los seis lotes (la carrera se **observa**) | sí |
| `R161-S2` | el bloqueo pasa a después de leer el saldo | `AC-R161-05/06` | **2**: `r161_05`, `r161_06` — con el bloqueo después de la lectura, todas leen el saldo previo y confirman: el bloqueo tardío no protege | sí |
| `R161-S3` | se bloquea y se relee, pero se valida contra el saldo leído antes del bloqueo | `AC-R161-05/06` | **2**: `r161_05`, `r161_06` — bloquear y releer no basta si se valida contra el saldo viejo: la relectura tiene que ser la que decide | sí |
| `R161-S4` | el bloqueo solo en `egg_dispatch` (se omite en `incubation_load`) | `AC-R161-06` | **1**: `r161_06` — solo la incubadora vuelve a correr (el despacho sigue bloqueado): la cobertura de los dos escritores es lo que cierra `R-161` | sí |
| `R161-S5` | la cota `cantidad ≤ saldo` (ambos validadores) | `AC-R161-03` (uno de más) | **3**: `r161_01_02_03_15` (uno de más → `201`), `r161_05`, `r161_06` (sin cota, todas confirman aun serializadas) | sí |
| `R161-S6` | la empresa en las cuatro capas del alta | `AC-R161-10` con fila observada | **1**: `r161_10_14` — el actor de `B` **despacha** los huevos del lote de `A` (`201` observado; fila creada) | sí |
| `R161-S7` | la habilitación de la unidad en la guarda compartida | `AC-R161-11` (global) | **1**: `r161_10_14` — la autoridad global situada en `B` carga la incubadora apagada (`201` ≠ `403`) | sí |
| `R161-S8` | la concesión del actor | `AC-R161-11/12` | **1**: `r161_10_14` — el actor sin la unidad de incubadora y el de concesión histórica sobre unidad apagada operan | sí |
| `R161-S9` | `operations:create` → `read` en la ruta | `AC-R161-14` | **1**: `r161_10_14` — `sin_perm`, el Administrador de Accesos y el actor de control-lectura despachan con `operations:read` | sí |
| `R161-S10` | vuelve la guarda `if total > 0` en el despacho | `AC-R161-04` | **1**: `r161_04` — un despacho de 0 huevos vuelve a registrarse con `201` | sí |

Contabilidad: intentadas 10 (`R161-S1…S10`) · inicialmente inválidas 0 · reconstruidas 0 · válidas finales 10 · `N/A` 0 · acreditadas inválidas 0 ·
residuo `MUTACION` 0 · 10 reversiones limpias (`git diff --quiet -- app/`). `S1`/`S2`/`S3` demuestran que lo que protege no es la presencia del
bloqueo sino su **momento** y que la validación use la **relectura**; `S4` demuestra que ambos escritores convergen en la misma primitiva; `S6`
retira cuatro capas de empresa a la vez (lección del tranche 4): la fuga se observa, no se infiere.


## 7. Regresión

| Comprobación | Resultado |
|---|---|
| backend completo (`scripts/run_tests.sh`: `alembic upgrade head` → semillas → pytest) | **1031 passed · 49 skipped · 0 failed** (1210 s; 1024 previas + 7 de `test_egg_incubation_concurrency.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) |
| `R-130` 21/21 · `R-170`/`B13` 6/6 · `B01` 10/10 · `B02` 8/8 · `B05` 16/16 · `R-136`/`R-165` · `R-135`/`R-143` · `R-159/R-160` · `R-162/R-163` · `R-139` 35/35 · `OD-14`/`OD-16` · fases 7/8 (BU admin `== 7`, sesión, acceso) · `R-121`/`R-113`/`R-129` (seguridad) | verdes |
| `authorization_coverage` (211) · `route_scope` (`RQ-03` estable, sin tabla nueva) · `SOLO_SUPER_ADMIN` 13 · `t_025_02` 48 · cabeza `x4y5z6a7b8c9` | exactos |
| `vitest` · `tsc` | 95/95 · 6 |
| E2E | `BLOCKED_RUNTIME` |

## 8. Cierre

```
R-161 ................ CERRADO (técnico): bloqueo antes de leer · relectura · > 0 y ≤ saldo · una fila autoritativa (lote) · por recurso ·
                       carreras observadas y cerradas en BR-02 y BR-03 · cero rechazado · seguridad intacta                                 ✔
GA-REM-005-D ......... CERTIFIED (frontera técnica)                                                                                       ✔
R-171 ................ OPEN · UI_ONLY · gobernado (RR-16) · siguiente tranche                                                                —
R-166 ................ OPEN (carrera approve/reject: otro invariante; no absorbido)                                                          —
R-172 · R-173 · R-174  OPEN (registrados en este pre-flight)                                                                                  —
OD-19 §18 ............ huevos/incubación siguen no reversibles hasta enmienda de GA-REM-041 (_suma_neta en saldos de huevos)                  —
E2E .................. BLOCKED_RUNTIME → certificación de proceso NO                                                                        —
```

## 9. Riesgos restantes y fuera de alcance

`R-173` es la brecha más cercana a `R-161` (mutaciones posteriores al alta sin revalidar en las cuatro familias de saldo). `R-172` cambia
qué cuenta como disponible en `BR-02` (semántica). `R-175` (higiene de pruebas) explica los residuos de orden de los tranches 7-9 y se corrige
en las tres suites cuando se toquen. `R-164` BLOCKED_RUNTIME · `R-166` OPEN · `AOD-22`/`AOD-23` pendientes · `BU-D10` · `R-158`.

## 10. Siguiente tranche (identificado, NO iniciado)

**`R-171`** (UI_ONLY, gobernado, sin decisión: catálogo de la etapa de incubadora con `mortality_recording` y `cull_recording`, pasos de flujo,
i18n, contrato estático) con **`R-173`** como acompañante si la traza lo muestra independiente (`PUT` de lote y `cancel` de entradas contra los
saldos, misma primitiva de bloqueo; `DATA_INTEGRITY` P2). Alternativa: `R-152` → `R-153` (Progenitoras).
