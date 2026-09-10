# Evidencia · WAVE B · tranche 14 — `R-180` (referencias estructurales de los submovimientos, `GA-REM-002-E`) + `MUTATION CHECKPOINT` ejecutable

**Fecha** 2026-09-10 · **Baseline de entrada** `main` · `6ffd73c` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211 ·
**Commits** `d9ff4bd` (spec) · implementación (`IMPLEMENTATION_COMMIT`, §5) · evidencia (este) · **sin migración** · **sin decisión del propietario**.

## 1. Rectificación documental del recuento (`§6` del encargo)

Dos rótulos del bloque `§29` no coincidían con los elementos que ellos mismos enumeraban. Se rectifica en el documento canónico vigente
(`WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX §30`), **sin reescribir** el bloque histórico ni ningún commit.

| Rótulo | Valor anterior | Enumeraba | Valor canónico | Fuente |
|---|---|---|---|---|
| `P2 ABIERTOS` | `5` | `R-142 · R-144 · R-147 · R-148 · R-164 · R-180` = 6 | **6** | severidades leídas del backlog, una a una |
| `BLOQUEADOS` | `4` | `R-142 · R-144 · R-153 · R-156 · R-177` = 5 | **5** (por decisión; `R-164` es `BLOCKED_RUNTIME`, otra naturaleza) | `AOD-17` · `AOD-08` · `AOD-25` · `AOD-20` · `AOD-24` |

Sin impacto en código ni en el cierre técnico del tranche 13. Recuento canónico de entrada: **36 · 23 · 4 · 9** · P1 0 · P2 6 · P3 3 · decisiones 10.

## 2. Hallazgo, con su significado exacto

`R-180`: un evento correctamente acotado a la empresa A puede contener **submovimientos** que referencian recursos estructurales de la empresa B. El
evento pasa la cadena de inquilino porque **sus propias** columnas se verifican; sus hijos, no.

> `UNA CLAVE FORÁNEA VÁLIDA NO PRUEBA QUE EL GALPÓN SEA DE LA EMPRESA DEL EVENTO.`

**Cuatro** referencias, no las dos que nombraba el alta. La cadena autoritativa se leyó del modelo, no se supuso: `House` **no** declara `company_id`;
pertenece a la empresa a través de `Farm`. `Lot` sí la declara.

| # | Campo | Tabla | Cadena | ¿Estaba en el alta de `R-180`? |
|---|---|---|---|---|
| 1 | `source_house_id` | `bird_movements` | `House → Farm → Company` | sí |
| 2 | `target_house_id` | `bird_movements` | `House → Farm → Company` | sí |
| 3 | `house_id` | `inspection_details` | `House → Farm → Company` | **no — hallado en el pre-flight** |
| 4 | `lot_id` | `egg_storage` | `Lot.company_id` | **no — hallado en el pre-flight** |

**Clasificación:** ACTIVE · GOBERNADO · sin decisión · severidad **`P2` → `P1`** (clase `R-42`/`R-59`/`R-179`: referencia entre empresas persistida en
dato productivo; y la estructural es, por definición del propio addendum, «aquella cuya pertenencia define de quién es el dato»).

**Autoridad:** ADDENDUM Wave 3 de `GA-REM-002` (define la clase estructural y nombra `house_id`) · `AC10` (el recurso estructural ajeno se rechaza sin
fila ni auditoría) · `AC12`/enmienda A (el sub-recurso hereda la pertenencia de su padre). **No faltaba la regla: faltaba su alcance sobre los hijos.**

## 3. Reproducción por API (sonda temporal sobre `6ffd73c`, ejecutada y retirada)

Empresa A (granjas `A1`,`A2`; galpones `A1H`=3, `A2H`=4) · empresa B (galpón `B1H`=5) · actor de A con permisos y unidad correctos. El único elemento
ajeno es la referencia del hijo.

```
destino ajeno      bird_transfer target_house_id=5   → 201   bird_movements = (3, 5)      evento de A con galpón de B
origen ajeno       bird_transfer source_house_id=5   → 201   bird_movements = (5, 4)
ambos ajenos       source = target = 5               → 201   bird_movements = (5, 5)
POSITIVO A1H→A2H   entre granjas de la misma empresa → 201   (3, 4)      ← debe seguir aceptándose
hijos mixtos       hijo1 válido + hijo2 ajeno        → 201   [(3, 4), (3, 5)]   ambos persistidos: sin validación no hay atomicidad
inspección         inspection_details.house_id = 5   → 201   inspection_details = (5,)
almacenamiento     egg_storage.lot_id = lote de B    → 201   egg_storage = (4,)
```

## 4. Superficies — inventario completo

| Superficie | ¿Puede fijar estos campos? | Prueba |
|---|---|---|
| `POST /api/v1/operations` | **sí** | `operations/service.py` construye los seis hijos desde el cuerpo |
| `PUT /api/v1/operations/{id}` | **no** | `OperationalEventUpdate` no declara ninguna lista de submovimientos |
| `POST /api/v1/corrections` | **no** | los campos corregibles derivan de `OperationalEventUpdate.model_fields` |
| reverso | derivada | copia las columnas de las filas originales; no acepta entrada del cliente |

Una sola superficie escritora. La imposibilidad de las otras dos deja de ser una lectura y se versiona como guardián (`AC-R180-14`): si algún día
`PUT` o la corrección admitieran submovimientos, la prueba enrojece y obliga a extender la enmienda.

## 5. Unidad de negocio — por qué no se inventa ninguna restricción

`House` y `Farm` **no declaran** `business_unit_id` (comprobado sobre el modelo); la unidad se deriva del **lote**. No existe «unidad del galpón» que
comparar, de modo que `OD-10` queda intacto: no se exige misma unidad entre origen y destino, no se exige que el actor tenga concedida la unidad del
galpón destino, y **no** se restringe el movimiento entre granjas distintas de la misma empresa. Ese control positivo es obligatorio y se prueba.

## 6. Rojo válido (leído en `d9ff4bd`) — `§65`

`tests/test_submovement_structural_tenancy.py` · prefijo `SUBM-` · empresa A (breeder ON, hatchery OFF) con granjas `A1`/`A2`, empresa B con `B1`.

| Prueba | AC | Actor · empresa · unidad · lote · referencia del hijo | Esperado → **real** | Por qué es `R-180` |
|---|---|---|---|---|
| `test_r180_02_04[origen]` | `AC-R180-02` | op · A · ON · lote de A · `source_house_id` = galpón de B | `400 BR-07` → **`201`** + fila | ninguna capa recorre la cadena para el hijo |
| `test_r180_02_04[destino]` | `AC-R180-03` | ídem · `target_house_id` de B | `400` → **`201`** + fila | independiente del anterior: son dos contratos |
| `test_r180_02_04[ambos]` | `AC-R180-04` | ídem · ambos de B | `400` → **`201`** + fila | — |
| `test_r180_13` | `AC-R180-13` | ídem | `BR-07 «no encontrado»` → **`201`** | no había denegación que examinar |
| `test_r180_05` | `AC-R180-05` | `farm_inspection` · `inspection_details[0].house_id` de B | `400` → **`201`** + fila | referencia no declarada en el alta |
| `test_r180_06` | `AC-R180-06` | `egg_collection` · `egg_storage[0].lot_id` = lote de B | `400` → **`201`** + fila | ídem |
| `test_r180_07` | `AC-R180-07` | tres hijos: válido · **ajeno** · válido | nada persiste → **`201` con los tres** | sin validación no hay atomicidad |
| `test_r180_09_10` | `AC-R180-09` | contexto declarado de B, galpón de B | denegado → **`201`** | — |

**Rojo válido: 8.** Controles verdes antes y después: `AC-R180-01`/`08` (dentro de la empresa y **entre granjas distintas**), `AC-R180-14`
(`PUT` y corrección no declaran submovimientos).

**Rojas inválidas y su corrección (crédito 0):** dos aserciones de `test_r180_11_12` esperaban `403` para la unidad apagada y para la falta de unidad
concedida, y el sistema responde `400 BR-07`. No es un defecto: en el **alta**, ambas situaciones dejan el lote fuera de ámbito y la denegación llega
antes de discutir permisos. Se corrigió la expectativa al contrato existente, conservando lo que la prueba debe demostrar: que el control de acceso
deniega **antes** de llegar a la validación estructural.

## 7. Implementación (`IMPLEMENTATION_COMMIT = 8a9f3cc`)

| Capa | Archivo | Cambio |
|---|---|---|
| inquilino | `backend/app/tenancy.py` | `verificar_estructurales_del_submovimiento(db, company_id, **campos)`: mapa campo → modelo (`source_house_id`, `target_house_id`, `house_id` → `House`; `lot_id` → `Lot`), apoyado en `verificar_pertenencia`, que ya recorre `House → Farm → Company` y trata lo ajeno como inexistente |
| alta | `backend/app/operations/service.py` | recorrido de **todos** los hijos de `bird_movements`, `inspection_details` y `egg_storage_records` en `_apply_business_rules`, antes de cualquier `db.add` |

No se reutiliza `verificar_catalogo_de_empresa`: la clase estructural no tiene el caso «nulo = compartido», y convertir el galpón en catálogo sería
modelar mal el dominio. Sin migración, sin ruta, permiso, estado ni enum nuevos. `OD-10` intacto.

## 8. `MUTATION CHECKPOINT` — de instrucción escrita a precondición ejecutable

El incidente ocurrió en los tranches 10 y 13: el driver restaura con `git checkout`, que toma `HEAD`; con la implementación sin confirmar, eso **borra
la implementación**. Ahora hay una guarda (`backend/scripts/mutation_guard.py`) con siete señales fail-closed, probada en repositorios desechables
(`backend/tests/test_mutation_guard.py`, casos A…E, 6/6 verdes) y gobernada en `MUTATION_CHECKPOINT_GOVERNANCE.md`.

**Prueba negativa en ejecución real (`§93`)**, antes de la sensibilidad de este tranche: se ensució deliberadamente un archivo productivo y se pidió
permiso a la guarda.

```
IMPLEMENTATION_COMMIT ..... 8a9f3cc40b3efd7e7a6ca4012e1a3bd010c857f3
HEAD ...................... 8a9f3cc40b3efd7e7a6ca4012e1a3bd010c857f3
COINCIDEN ................. SÍ
CÓDIGO PRODUCTIVO LIMPIO .. NO
OBJETIVO DE RESTAURACIÓN .. VÁLIDO
MUTACIÓN PERMITIDA ........ NO
MOTIVOS:  - 4. hay código de producción sin confirmar: backend/app/tenancy.py
RESULTADO: la guarda ABORTÓ antes de instalar ninguna mutación ✔
```

Retirada la simulación (residuo 0), la guarda volvió a evaluar y permitió. Cada restauración de la sensibilidad se hizo **desde el commit declarado**,
no desde `HEAD`, y se comprobó byte a byte.

## 9. Sensibilidad (`§82`-`§94`)

| Mutación | Qué quita | ¿Instalada? | ¿Rama ejecutada? | ¿Propiedad retirada? | Objetivo | Resultado | ¿Motivo exacto? | ¿Restaurada desde el commit? |
|---|---|---|---|---|---|---|---|---|
| `R180-S1` | comprobación del galpón **origen** | sí | sí | sí | `r180_02_04[origen]` | **1 failed** | sí: `201` con origen de B | sí, verificada |
| `R180-S2` | comprobación del galpón **destino** | sí | sí | sí | `r180_02_04[destino]` | **1 failed** | sí: `201` con destino de B | sí |
| `R180-S3` | la **cadena**: se comprueba contra el modelo equivocado | sí | sí | sí | `r180_02_04` | **1 failed** (2 pasan) | sí: prueba que importa recorrer `House → Farm → Company` | sí |
| `R180-S4` | comprobación del galpón de la **inspección** | sí | sí | sí | `r180_05` | **1 failed** | sí | sí |
| `R180-S5` | comprobación del lote del **almacenamiento** | sí | sí | sí | `r180_06` | **1 failed** | sí | sí |
| `R180-S6` | solo se valida el **primer hijo** | sí | sí | sí | `r180_07` | **1 failed** | sí: prueba que se recorren todos los hijos | sí |
| `R180-S7` (1º) | sobre-bloqueo mal dirigido | sí | **no** | **no** | `r180_01_08` | 1 passed | comparaba el galpón consigo mismo: rama inerte → **inválida, crédito 0** | sí |
| `R180-S7c` | **sobre-bloqueo**: exigir misma granja entre origen y destino | sí | sí | sí | `r180_01_08` | **1 failed** | sí: «entre granjas de la misma empresa debe aceptarse» — prueba que el arreglo **no** sobre-restringe | sí |
| `R180-S8` (1º) | inquilino, mal dirigida | sí | **no** | **no** | `r180_02_04` | 4 passed | anuló la rama `company_id` pero dejó viva la rama `farm_id`, que es justamente la que valida galpones → **inválida, crédito 0** | sí |
| `R180-S8c` | inquilino **multicapa**: las dos ramas del filtro de empresa + la unidad apagada | sí | sí | sí | `r180_02_04` · `r180_11_12` | **3 failed** | sí: `201` con galpón ajeno en origen y destino | sí |

Contabilidad: intentadas 10 · inicialmente inválidas 2 · reconstruidas 2 · **válidas finales 8** · N/A 0 · crédito por inválidas 0 · **residuo 0** ·
`HEAD` tras la sensibilidad `8a9f3cc` == `IMPLEMENTATION_COMMIT`.

## 10. Integridad posterior a la sensibilidad

```
git rev-parse HEAD ........... 8a9f3cc40b3efd7e7a6ca4012e1a3bd010c857f3  == IMPLEMENTATION_COMMIT
git status --short ........... solo esta evidencia sin versionar
git diff HEAD -- backend/app . 0 líneas
restos de «MUTACION» ......... ninguno
humo ......................... 17/17
```

## 11. Control de orden `R-175` — con las suites nuevas (`T14`)

| Suite | Aislada | A→B | B→A | `T14 → A` | `A → T14` |
|---|---|---|---|---|---|
| `test_lot_start_date` | 6/6 | 24/24 | 24/24 | 23/23 | 23/23 |
| `test_lots_bu_enforcement` | 28/28 | 46/46 | 46/46 | 45/45 | 45/45 |
| `test_od14_productive_surfaces` | 35/35 | 53/53 | 53/53 | 52/52 | 52/52 |
| `test_clean_baseline` | 18/18 | — | — | `T14 → B`: 35/35 | `B → T14`: 35/35 |

18/18 pares verdes. Las suites nuevas retiran todo lo que crean (empresas, granjas, galpones, lotes, eventos y sus hijos) y el guardián de mutación
trabaja sobre repositorios desechables en `tmp_path`, sin tocar el repositorio real.

## 12. Regresiones exigidas — dentro de la regresión completa

| Regresión | Suites | Resultado |
|---|---|---|
| `R-179` catálogos · `R-166` decisión de revisión (tranche 13) | `test_master_reference_tenancy` · `test_review_decision_concurrency` | 26/26 · 8/8 |
| `R-42`/`R-59`/`R-139` aislamiento de inquilino | `test_master_tenant_isolation` · `test_multicompany_isolation` | 16/16 · 12/12 |
| `R-173`/`R-176`/`R-178` edición, anulación y linaje | `test_edit_validation_parity` · `test_edit_cancel_balance` · `test_lineage_cancel_move` · `test_corrections` | verdes |
| `R-130`/`R-161` saldo y concurrencia · `R-135`/`R-143` estado · reverso | `test_population_invariant` · `test_egg_incubation_concurrency` · `test_state_continuity` · `test_internal_reversal` | verdes |
| `R-159`…`R-163`/`R-165`/`OD-16` unidades | `test_operations_bu_enforcement` · `test_lots_bu_enforcement` · `test_od14_productive_surfaces` | verdes |
| operaciones, mortalidad, recepción y trazabilidad (superficies que usan galpones origen/destino) | `test_operations` · `test_mortality` · `test_reception_reconciliation` · `test_reception_weight_range` · `test_traceability` | verdes |
| `R-152`/`GA-REM-042` importación | `test_grandparent_import` | 18/18 |
| guardianes | `test_ac14` (rutas 211 · cabeza `x4y5z6a7b8c9`) · `test_clean_baseline` · `test_time_determinism` · **`test_mutation_guard`** | verdes |

## 13. Regresión completa (leída antes de certificar) y cierre técnico

```
backend ........ 1139 passed · 49 skipped · 0 failed   (1028 s)
                 1122 previas + 17 nuevas (11 de R-180 + 6 del guardián de mutación)
                 los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado
vitest ......... 108 / 108 (sin cambios de frontend en esta tranche)
tsc ............ 6 errores preexistentes (R-158), sin cambio
alembic ........ x4y5z6a7b8c9 (sin migración) · rutas 211 · guardianes exactos
integridad ..... código de producción == 8a9f3cc tras la sensibilidad · residuo 0
```

| Ítem | Cierre |
|---|---|
| `R-180` | **CERRADO (técnico)** · **P1** (normalizado desde P2) · `GA-REM-002-E` **CERTIFICADA** (frontera técnica) · `AC-R180-01…14` · rojo válido 8 · sensibilidad 8 válidas, 2 reconstruidas, crédito 0 a las inválidas · control positivo entre granjas conservado · sin migración |
| `MUTATION CHECKPOINT` | **ESTABLECIDO Y PROBADO** · 7 señales fail-closed · casos A…E verdes · negativa demostrada en ejecución real · gobernanza en `MUTATION_CHECKPOINT_GOVERNANCE.md` |
| certificación de proceso | `BLOCKED_RUNTIME` (no se reclama; `R-164`) |

**Recuento canónico de salida: 36 · 24 cerrados · 4 parciales · 8 abiertos (P1 0 · P2 5 · P3 3) · decisiones 10.**

Siguiente tranche (identificado, **no iniciado**): `R-147` (constantes de negocio sin fuente declarada, P2, sin decisión pendiente); alternativa `R-148`
(inmutabilidad de `audit_logs` en base de datos). `R-142`, `R-144`, `R-153`, `R-156` y `R-177` siguen bloqueados por decisión del propietario; `R-164`
sigue `BLOCKED_RUNTIME`.

Fuera de alcance, sin tocar: `R-147` · `R-148` · `R-153`/`AOD-25` · `R-177`/`AOD-24` · `R-164` · `R-140`/`R-154` residuales · `R-136` SAP ·
`B03`/`B04`/`R-156` · `AOD-23` · `R-142` · `R-144` · ola C y KPI · fase 9 · SAP real (`P-08`) · `BU-D10` · `R-158` · rediseño de inquilino, de
galpón/granja, del motor de movimientos o de transferencias · limpieza de datos históricos con referencias entre empresas (prevención sin reescritura
retrospectiva; si hiciera falta, remediación aparte).
