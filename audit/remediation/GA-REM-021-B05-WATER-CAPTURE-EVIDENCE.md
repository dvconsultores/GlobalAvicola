# EVIDENCIA · `GA-REM-021` enmienda A · `B05` CAPTURA OPERATIVA DEL CONSUMO DE AGUA (+ pre-flight de roles del reverso, `OD-19` Acl. A)

**WAVE B · tranche 6** · 2026-09-09/10 · spec `GA-REM-021-A` + `GA-REM-041-A` + `OD-19` Aclaración A (commit `c8447de`) · roles (commit `cdb0670`) ·
código `B05` (commit `72600f1`) · spec `GA-REM-041-B` (commit `8df04f7`) · migración de roles (commit `daa0c0e`) · matriz
`GA_REM_021_B05_WATER_CAPTURE_MATRIX.md` · `RC-10` (`RR-10`, `RR-11`) · base `55d9072` · rama `main` · cabeza final `v2w3x4y5z6a7`

## 1. Entrada y descomposición

| Ítem | Valor |
|---|---|
| HEAD de partida `55d9072` · local == remoto · árbol limpio · Alembic `t0u1v2w3x4y5` · rutas 211 | sí |
| Recuento de la ola B verificado (pre-flight) | 22 · 8 cerrados · 3 parciales · 11 abiertos (consistente con `WAVE_B §13`) |
| Pre-flight A: asignación de roles del reverso | decisión del propietario (`OD-19` Aclaración A): Supervisor Avícola → `reversals:create` + `reversals:read`; Contraloría → `reversals:read`; Administrador de Accesos → ninguno; operativos → ninguno; Super Admin conserva la autoridad gobernada |
| `B05` | `R-13` = `H360-B05` (P1): «Cantidad de agua consumida … durante el día», exigido por el cliente en tres etapas y ausente del backend |
| Decisión requerida para `B05` | **no**: cada semántica quedó resuelta en un nivel superior a la implementación o por regla de evidencia sin cambio de comportamiento (`§2`) |
| Fuera | `B04` (`AOD-14`) · `B01`/`B02`/`B03`/`B13` · KPI de agua (ola C) · umbrales · sensores · SAP · fase 9 · `BU-D10` · `R-158` · reverso del dato |

## 2. Gobierno del requisito (`GA_REM_021_B05_WATER_CAPTURE_MATRIX.md §2`, `REQUIREMENT_CONFLICT_RESOLUTION §1`, `§10 RC-10`)

| Semántica | Resuelta por | Resultado |
|---|---|---|
| qué / cuándo / quién | nivel 2 (`Bases` p.2, 4, 12) | cantidad consumida por la parvada **durante el día**; registro operativo de granja |
| etapas | nivel 2 | Reproductoras cría y producción, Engorde; Incubadora no lo pide (p.7-11); Progenitoras no es etapa del documento |
| unidad | `RR-10` (nivel 5 `ReportsPage` lee `water_liters`, precisado por nivel 6) | **litros**, campo `water_liters` |
| valor | `RR-11` (nivel 5: misma regla que `quantity_kg`) | `> 0`, decimales sin redondeo, «sin dato» = ausencia (`NULL`), nunca `0` |
| granularidad | nivel 2 + nivel 5 (modelo de eventos) | por lote y día; varios registros del mismo día son **aditivos** (no se inventa unicidad) |
| recurso padre | nivel 5 | `operational_events` (`event_type = water_consumption`), como el alimento; lote obligatorio; granja/galpón opcionales |
| fecha de negocio | nivel 5 | `event_date` (`BR-06` activación; `BR-19`/`R-30` genérica: cerrado > 90 días, futura > 1 día); **sin regla propia** |
| empresa / unidad | `OD-14.c/d`, `OD-16`, `GA-REM-040 G/H` | derivadas del lote por el servidor; cuerpo ignorado |
| corrección | `RR-01` (`campos_corregibles` = `OperationalEventUpdate`) | `water_liters` corregible; `RR-11` también en corrección |
| reverso | `GA-REM-041 §3.5` (no lista el agua) | **no elegible** (`400 BR-16`) |
| SoR | `SYSTEM_OF_RECORD_AND_AUTHORITY_MATRIX` | la app (`APP_MANDANTE`); SAP no participa |
| `AOD-19` | UoM/umbrales de `R-147` | **no gobierna `B05`** (la unidad la fija la evidencia de nivel 5/6; no hay umbral) |

## 3. Pre-flight de roles del reverso (`OD-19` Aclaración A · `GA-REM-041-A` · commit `cdb0670`)

| AC | Contrato | Prueba (`tests/test_reversal_role_matrix.py`, estática sobre las semillas + runtime) | Resultado |
|---|---|---|---|
| `REV-R01`/`R02` | «Supervisor Avícola» tiene `reversals:create` y `reversals:read` en `dev_seeds`/`test_seeds` | `r01_r02` | verde |
| `REV-R03`/`R04` | «Contralor Avícola» (`integration_seeds`) tiene `read` y **no** `create` | `r03_r04` | verde |
| `REV-R05`/`R06` | «Administrador de Accesos» no tiene ningún `reversals:*`; ningún rol operativo lo tiene | `r05_r06` | verde |
| `REV-R07` | nadie salvo Super Admin (`*`) tiene `reversals:approve`; el reverso se aprueba por `approvals:*` del motor existente | `r07` | verde |
| `REV-R08` | runtime: usuario con el rol sembrado «Supervisor Avícola» + concesión → `POST /reversals` `201`; `POST /approvals/approve` `403` | `r08` | verde |
| guardián | `SOLO_SUPER_ADMIN` 15 → **13** (salen `reversals:create`, `reversals:read`); techo ≤ 15 intacto | `test_rbac` | verde |

`dev_seeds` no tiene rol de Contraloría: **no se inventa** (`NO INVENTAR NOMBRES DE ROLES`); la figura de contraloría existe como
«Contralor Avícola» en `integration_seeds` y es la que recibe `reversals:read`. Sin permiso nuevo en el catálogo; sin ruta nueva.

### 3.1 Enmienda B: la decisión llega a las instalaciones existentes (`GA-REM-041-B` · commits `8df04f7` spec · `daa0c0e` código)

La **primera regresión completa** (tras `72600f1`) dejó roja `test_clean_baseline::test_t_025_02` (`GA-REM-025 AC03`: 48 ≠ 46).
Causa: la fuente única de la matriz RBAC para instalaciones existentes y para el baseline es `PERMISOS_POR_ROL` de la migración
de reconciliación `l2m3n4o5p6q7` (`R-44`: «las semillas sirven a instalaciones nuevas»), que `baseline_seeds` importa. La
enmienda A decía «sin migración» y cambió solo semillas: la instalación desplegada **nunca habría recibido** la capacidad decidida
por el propietario. No es una decisión nueva (los titulares no cambian): es la vía por la que la decisión llega a una base ya
migrada. Se corrigió **por spec antes que por código** (`8df04f7` → `daa0c0e`).

| AC | Contrato | Prueba | Resultado |
|---|---|---|---|
| `REV-R09` | sobre una instalación con «Supervisor Avícola» sin los permisos, `v2w3x4y5z6a7.aplicar` los añade; segunda pasada no duplica | `test_reversal_role_migration::r09` | verde |
| `REV-R10` | matriz compuesta del baseline: Supervisor con `reversals:create`/`read`; 48 asociaciones en 5 roles; sin «Contralor Avícola» | `::r10` · `test_clean_baseline::t_025_02` (48, «faltan»/«sobran» vacíos) | verde |
| `REV-R11` | `retirar` quita exactamente el delta; volver a aplicar repone | `::r11` | verde |
| `REV-R12` | guardianes: cabeza `v2w3x4y5z6a7` · rutas 211 · `t_025_02 == 48` · `SOLO_SUPER_ADMIN == 13` | guardianes | verde |

Rojo previo válido (sobre `8df04f7`): `r09`/`r11` «falta la migración v2w3x4y5z6a7», `r10` «el baseline concede el reverso al
Supervisor» (matriz sin el delta), `t_025_02` «48 ≠ 46». Verde dirigido: **170/170** (migración de roles, baseline, matriz de
roles, RBAC, invariante, catálogo, enumerados, agua, determinismo temporal, reverso interno, notificaciones).

## 4. Rojo previo · validez (sobre `cdb0670`: spec y roles, sin código de `B05`)

`tests/test_water_capture.py` (16, prefijo `AGUA-`): **15 rojas · 1 verde**. `processCatalog.test.ts` (vitest, 2): **1 roja · 1 verde**.
0 errores de import/fixture. Cada roja cae en el defecto real:

| Grupo | Pruebas | Observado ≠ exigido | Válida |
|---|---|---|:--:|
| tipo inexistente | `w01_w02_w07`, `w03_s09_w04`, `w05_w06`, `v01_v04`, `v05_v06`, `v07_bu03_bu04`, `v08`, `s01_s06`, `s02_s03`, `bu02`, `c01_c03`, `c02`, `au01_au02`, `rv` | `500 Internal Server Error` (`water_consumption` no es `EventType`; el servicio no lo reconoce) ≠ `201`/`400`/`403` según AC | sí |
| un dato, un registro | `v09` | `201` (`feed_registration` acepta `water_liters` y lo descarta en silencio) ≠ `400` | sí |
| catálogo del frontend | `processCatalog.test.ts` (etapas con agua) | `water_consumption` ausente de `STAGE_OPERATIONS[breeder_rearing/breeder_production/broiler]` | sí |

Controles verdes en rojo: `s04_s07_s08` (`403` sin `operations:create`; `403` para el actor de solo lectura; `403` para el
Administrador de Accesos — la ruta ya exigía el permiso) y la mitad negativa del test de catálogo (grandparent/hatchery sin agua).
**Correcciones de prueba tras el rojo** (no de contrato): `w03` enviaba `company_id` extra a través de la ayuda cuyo parámetro
homónimo situaba el token → cuerpo crudo; `v08` pasaba la fecha como texto a `asyncpg` → `date`; `v06` esperaba `201` para una fecha
futura siguiendo la redacción inicial de `AC-V06` (que atribuía el veto a `BR-06`) — la regla genérica `R-30`/`BR-19` ya veta
la fecha futura para **todo** evento, así que el contrato correcto es `400 BR-19` y la enmienda se corrige en su redacción
(sin regla propia del agua, como exigía). `v01_v04` ganó la edición del registro vivo (`PUT` con `0` → `400`; con `80` → `200`).

## 5. Implementación (commit `72600f1`; 17 ficheros, +522/−9)

| Pieza | Qué hace |
|---|---|
| `alembic/versions/u1v2w3x4y5z6_water_consumption.py` | `eventtype` gana `WATER_CONSUMPTION` (`ADD VALUE IF NOT EXISTS`, `autocommit_block`); `operational_events.water_liters FLOAT NULL`; la bajada se detiene si hay eventos de agua (el miembro del enumerado permanece: PostgreSQL no lo elimina) |
| `EventType.WATER_CONSUMPTION` · `OperationalEvent.water_liters` | tipo de evento propio (cola de revisión, corrección y serie propias) y su valor en litros |
| `OperationalEventBase.water_liters` · `OperationalEventUpdate.water_liters` | contrato de alta/lectura y de edición; por `RR-01` entra en `campos_corregibles()` |
| `validators.validate_water_consumption` · `UNIDADES_CON_CONSUMO_DE_AGUA = {breeder, broiler}` | **una regla**, tres puntos de aplicación: obligatorio y `> 0` en `water_consumption`; prohibido en otro tipo; solo lotes `breeder`/`broiler` (lote sin cadena → `400`) |
| `OperationsService._apply_business_rules` · `update_event` · `_tipo_de_lote` | alta y edición aplican la regla; la cadena se lee del lote **acotado a la empresa efectiva** (`_acotar_a_empresa`), nunca del cuerpo |
| `corrections/service.py` | tras `_convertir`, la corrección de `water_liters` aplica la misma regla (`AC-C03`) |
| autorización | **ninguna lógica nueva**: `operations:create` en la ruta, `get_event`/`validate_lot_active(company)` (`OD-14`), `exigir_unidad_operativa` (`OD-16`/`R-160`) por la guarda compartida |
| guardianes | `test_population_invariant` y `test_company_catalog` → cabeza `u1v2w3x4y5z6`; rutas `== 211` (sin endpoint nuevo) |
| frontend (`§A.4`, vertical mínima) | `processCatalog.ts`: `water_consumption` en el grupo diario, en `STAGE_OPERATIONS` de las tres etapas, icono `Droplets`, color `sky`, paso «Registrar el consumo de agua» tras el alimento en `STAGE_FLOWS` de `breeder_rearing`/`breeder_production`/`broiler` (no en progenitoras ni incubadora) · `OperationFormPage.tsx`: `water_liters` en el esquema (`positive`) y un campo «Consumo de agua (L)» · `domain.types.ts` · `translation.json` es/en (`events`, `eventsShort`, `process.flowDesc`, `operations.waterLiters`, `reports.waterConsumption`/`waterL`) · `ReportsPage.tsx`: gráfico de agua sobre la serie `water_l` que ya calculaba |

Migración creada **después** del commit de spec `c8447de` (`§A.5`). Sin `company_id`/`business_unit_id` en el contrato de alta (se
ignoran); `Update` es `extra="forbid"`. Sin umbral, sin redondeo, sin unicidad inventada, sin semántica de cero.

## 6. Verde dirigido

| Suite | Resultado |
|---|---|
| `test_water_capture.py` · **`B05`** | **16/16** |
| `test_reversal_role_matrix.py` · **`OD-19` Acl. A** | **5/5** (+ `test_rbac`) |
| relacionadas: `R-160/R-159` (40) · `R-163/R-162` (28) · `OD-14` superficies (35) · continuidad `R-135`/`R-143` (30) · segregación · correcciones · flujo completo (23) · revisión y revisión-BU (`R-165`) · reverso interno (22) · RBAC · unidades (admin `== 7`, guardia, catálogo) · acceso · sesión · mortalidad (enumerados en PostgreSQL) · invariante `R-130` (21) + cabeza/rutas · catálogo de empresa · saldo inicial | **439/439** |
| `vitest` (`processCatalog.test.ts` + 8 suites previas) | **89/89** |
| `tsc -b --noEmit` | 6 errores, los mismos (`AuditPage.tsx` ×2, `LotFormPage.tsx` ×4) = `R-158` |

## 7. Sensibilidad (`GA-REM-021-A §A.7` · `GA-REM-041-A` S9)

Cada mutación se aplica marcada `MUTACION` (aplicación atómica), se ejecuta `test_water_capture.py` (16) —o
`test_reversal_role_matrix.py` + `test_rbac.py` para `S9`—, se revierte con `git checkout --` y se comprueba
`git diff --quiet -- app/ seeds/`. Todas revertidas limpias.

| Mut. | Qué retira | Debía caer | Cayó | Válida |
|---|---|---|---|:--:|
| `S1` | la persistencia de `water_liters` en el alta (`event_fields.pop`) | `AC-W02`/`W07` | **4**: `w01_w02_w07` (el valor vuelve `null`), `v05_v06` (`12.345` no se conserva), `bu02` (engorde), `c01_c03` (el original de la corrección no tiene valor) | sí |
| `S2` | la regla `> 0` (`RR-11`) | `AC-V03`/`V04` | **1**: `v01_v04` (`0` y `−1` devuelven `201`; también en la edición) | sí |
| `S3` | la empresa en **cuatro** capas del alta (`_unidad_del_lote`, `_tipo_de_lote`, `lotes_alcanzables`, `validate_lot_active(company)`) | `AC-S01` | **1**: `s01_s06` — el actor de `B` **escribe** agua sobre el lote de `A` (`201` observado; fila creada) | sí |
| `S4` | la habilitación de la unidad en la guarda compartida (`no_habilitada`) | `AC-S02` (global) | **1**: `s02_s03` (la autoridad global situada en `A` registra sobre `broiler` apagada: `201` ≠ `403`) | sí |
| `S5` | la concesión del actor (`no_concedida`) | `AC-S03` | **1**: `s02_s03` (el operador sin la unidad del lote —y el de concesión histórica sobre unidad apagada— registran) | sí |
| `S6` | `operations:create` → `read` en la ruta | `AC-S04` | **2**: `s04_s07_s08` (el actor sin `create` registra), `au01_au02` (la alta denegada ya no es denegada: deja auditoría) | sí |
| `S7` | confiar en `company_id` del cuerpo | — | **`N/A`**: el contrato de alta no declara `company_id`/`business_unit_id` (se ignoran; `w03_s09_w04` es control) | — |
| `S8` | unicidad por día | — | **`N/A`**: el modelo es aditivo (`AC-V08` es control) | — |
| `S9a` | `reversals:create` dado a «Contralor Avícola» (`integration_seeds`) | `REV-R04` | **1**: `rev_r03_r04` | sí |
| `S9b` | `reversals:read` dado a «Administrador de Accesos» (`dev_seeds`) | `REV-R05` | **1**: `rev_r05_r06` | sí |
| `S9c` | `reversals:create` quitado a «Supervisor Avícola» (`dev_seeds` + `test_seeds`) | `REV-R01`/`R08` | **3**: `rev_r01_r02` (estático), `rev_r08` (runtime: `403` ≠ `201`), `test_rbac::todo_permiso_exigido…` (el permiso deja de estar concedido por rol alguno sin ser de `SOLO_SUPER_ADMIN`) | sí |
| `S9d` | la composición del baseline no aplica el delta de `v2w3x4y5z6a7` (`GA-REM-041-B`) | `REV-R10` | **2**: `rev_r10` (matriz sin el reverso), `test_clean_baseline::t_025_02` (46 ≠ 48: la base sembrada lleva lo que la matriz no declara) | sí |
| `S9e` | la migración de datos no inserta | `REV-R09` | **2**: `rev_r09` (la instalación existente se queda sin la capacidad), `rev_r11` (volver a subir no repone) | sí |
| `S10` | la aplicabilidad por cadena (`bird_type ∈ {breeder, broiler}`) | `AC-BU03`/`BU04` | **1**: `v07_bu03_bu04` (lote sin cadena y lote de progenitoras aceptan agua: `201` ≠ `400`) | sí |

Contabilidad: intentadas 12 (`S1–S6`, `S9a/b/c/d/e`, `S10`) · inicialmente inválidas 0 · reconstruidas 0 · válidas finales 12 · `N/A` 2 (`S7`, `S8`,
declaradas así en `§A.7`) · acreditadas inválidas 0 · residuo `MUTACION` 0. `S9d`/`S9e` (`GA-REM-041-B §B.2`) se ejecutaron sobre
`test_reversal_role_migration.py` + `test_clean_baseline.py` y se revirtieron limpias (`git diff --quiet -- app/ seeds/ alembic/`). Lección de `S3`: el alta de agua está protegida por cuatro
capas de empresa (una más que el reverso: `_tipo_de_lote` también se acota); cualquier capa sola no la retira, por eso la mutación las
retira todas y la fuga se **observa** (`201` y fila) en vez de inferirse. `S6` muestra además que la auditoría de alta denegada
(`AC-AU02`) depende de que la ruta deniegue: sin permiso en la ruta, no hay denegación que auditar.


## 8. Regresión

**Dos pasadas, la primera roja.** La regla «el resultado completo se lee antes del commit de certificación» se cumplió: ningún commit
de evidencia se hizo sobre la pasada roja.

| Pasada | Resultado | Rojas | Disposición |
|---|---|---|---|
| 1ª (sobre `72600f1`) | 995 passed · **2 failed** · 49 skipped (815 s) | `test_clean_baseline::test_t_025_02` (48 ≠ 46) — **defecto real** de `cdb0670` (`§3.1`) · `test_time_determinism::test_t028_04` (fechas literales en `test_water_capture.py`) — **higiene de pruebas** | spec `8df04f7` + código `daa0c0e` (migración `v2w3x4y5z6a7`, matriz compuesta, `AC03` 48, `future_event_date()` en `tests.time_reference`) |
| 2ª (sobre `daa0c0e`) | **1000 passed · 49 skipped · 0 failed** (819 s; 976 previas + 16 de `test_water_capture.py` + 5 de `test_reversal_role_matrix.py` + 3 de `test_reversal_role_migration.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) | ninguna | certificación |

Lección registrada: las suites dirigidas de un tranche que toque **semillas** o **añada pruebas** deben incluir siempre
`test_clean_baseline.py` (matriz RBAC exacta) y `test_time_determinism.py` (sin fechas literales); ninguna de las dos estaba en el
verde dirigido de `cdb0670` ni de `72600f1`.

| Comprobación | Resultado |
|---|---|
| backend completo (`scripts/run_tests.sh`: `alembic upgrade head` → semillas → pytest), 2ª pasada | **1000 passed · 49 skipped · 0 failed** (819 s; 976 previas + 16 de `test_water_capture.py` + 5 de `test_reversal_role_matrix.py` + 3 de `test_reversal_role_migration.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) |
| `R-130` 21/21 · `R-135`/`R-143` 30/30 · `R-159/R-160` 40/40 · `R-162/R-163` 28/28 · `R-139` 35/35 · `R-136`/`R-165` 27/27 · fases 7/8 · `OD-14` (`s01_s06`) · `OD-16` (`s02_s03` global) · Administrador de Accesos (`s04_s07_s08`) · control-lectura (`s04_s07_s08`) · Progenitoras (`v07` `lg`) · Incubadora (`v07` `lh`) | verdes |
| `authorization_coverage` (211 con permiso) · `route_scope` · `SOLO_SUPER_ADMIN` **13** · `t_025_02` **48** · BU admin `== 7` · cabeza `v2w3x4y5z6a7` | exactos |
| migraciones | `u1v2w3x4y5z6` (enum + columna) y `v2w3x4y5z6a7` (datos de roles) aplicadas por `upgrade` en la base de pruebas (55 tablas); `test_los_enums_de_python_existen_en_postgresql` verde; la lógica de `v2w3x4y5z6a7` ejercida sobre roles existentes por `REV-R09`/`R11` |
| `vitest` | 89/89 |
| `tsc -b --noEmit` | 6 errores preexistentes (`R-158`) |
| E2E | `BLOCKED_RUNTIME` |

## 9. Cierre

```
OD-19 Aclaración A ... CERRADA (técnico): Supervisor Avícola create+read · Contralor read · Access Admin y operativos ninguno · SA gobernado   ✔
GA-REM-041-A ......... CERTIFIED (frontera técnica)                                                                                      ✔
GA-REM-041-B ......... CERTIFIED (frontera técnica): la decisión llega a instalaciones existentes (migración v2w3x4y5z6a7) y al baseline (48)  ✔
B05 / R-13 ........... CERRADO (técnico): captura · unidad (L) · > 0 · etapas del cliente · un dato, un registro · aditivo · fecha de negocio ·
                       corregible · no reversible · auditado · inquilino/unidad/concesión · frontend mínimo                                 ✔
GA-REM-021-A ......... CERTIFIED (frontera técnica)                                                                                      ✔
GA-REM-021 ........... PARTIAL (B01 · B02 · B03 · B13 abiertos, enmienda B pendiente · B04 ◄── AOD-14 · R-156 ◄── AOD-20)                 ◐
KPI de agua .......... NO (ola C)                                                                                                        —
E2E .................. BLOCKED_RUNTIME → certificación de proceso NO                                                                       —
```

## 10. Riesgos restantes y fuera de alcance

El dato queda capturado, no interpretado: sin L/ave, sin relación agua/alimento, sin tendencia ni umbral (ola C, `GA-REM-022`).
Sin regla propia de duplicidad: dos registros del mismo día suman (`AC-V08`); si el cliente exigiera un único registro diario, sería
una decisión nueva, no una inferencia. Datos históricos: `water_liters = NULL` en todo lo anterior (ausencia, no cero). El
frontend es la vertical mínima (campo y gráfico), no la pantalla de fase 9. La instalación desplegada recibirá los permisos del
Supervisor cuando `EX-01` aplique `v2w3x4y5z6a7` en el despliegue: **no verificado aquí** (sin acceso a esa base; `E2E BLOCKED_RUNTIME`).
`R-161` OPEN · `R-164` BLOCKED_RUNTIME · `R-166` OPEN · `R-140`/`R-154` parciales · `R-136` SAP diferido · `BU-D10` no tocado · `R-158` no tocado.

## 11. Siguiente tranche (identificado, NO iniciado)

`GA-REM-021` **`B01` + `B02`** — cuadre de recepción (♀ + ♂ + mortalidad + rechazo) y pesos en rango en recepción (`Rec. §6`, P2,
mismo evento de recepción, ambos sobre el saldo de `R-130`, ya cerrado). Es el paso 6 de `WAVE_B §3`. Exige **enmienda B previa**
(`NO SPEC = NO DEVELOPMENT`); «pesos en rango» necesita fuente normativa del rango — si ninguna fuente por encima de la
implementación lo fija, `OWNER_DECISION_REQUIRED` (no se inventa). Alternativa sin decisión aparente: `R-152` → `R-153`
(Progenitoras, `docs/02 §3.4.1`, spec propia; paso 7).
