# Evidencia · WAVE B · tranche 13 — `R-179` (referencias a catálogos entre empresas, `GA-REM-002-D`) · `R-166` (decisión de revisión concurrente, `GA-REM-007-B`)

**Fecha** 2026-09-10 · **Baseline de entrada** `main` · `a93d4d1` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211 ·
**Modo** `R179_PLUS_R166` · **Commits** `1cf6c37` (spec) · implementación (`IMPLEMENTATION_COMMIT`, §3) · evidencia (este) ·
**Sin migración** · **Sin decisión del propietario nueva**.

## 1. Pre-flight (commit `1cf6c37`)

| Hallazgo | Significado exacto | Clasificación | Autoridad | Artefacto |
|---|---|---|---|---|
| `R-179` | un evento de la empresa A acepta, persiste y edita referencias a **catálogos** de la empresa B (proveedor, transporte, causa de mortalidad, causa de descarte, vacuna, medicamento, planta) | **ACTIVE · GOBERNADO · sin decisión · P3 → P1** | `GA-REM-002` ADDENDUM Wave 3: «existir no basta»; «los catálogos maestros declaran `company_id` como anulable: **global si es nulo, propio de la empresa si está fijado**»; su ampliación cubrió solo lo **estructural** · `MASTER_DATA_BUSINESS_UNIT_SCOPE_MATRIX` · `RQ-03` · precedentes `R-42`, `R-59`, `R-111` | `R179_MASTER_REFERENCE_AUTHORITY_MATRIX.md` · `GA-REM-002-D` |
| `R-166` | `approve` y `reject` (y los demás escritores de decisión) leen el estado **sin bloqueo**: dos peticiones concurrentes lo superan y ambas escriben decisión, historia, auditoría y notificación | **ACTIVE · GOBERNADO · sin decisión · P3 → P2** | `GA-REM-007` (aprobación) · `GA-REM-006-A §A.2` (mapa de transiciones: desde `APPROVED`/`REJECTED` no se decide) · contrato de error ya existente (`400` «no está en estado aprobable») · primitiva `FOR UPDATE` del reverso (`GA-REM-041`) | `R166_REVIEW_DECISION_CONCURRENCY_MATRIX.md` · `GA-REM-007-B` |
| registrado | `R-180` (P2): `bird_movements.source_house_id` / `target_house_id` admiten galpones de otra empresa (clase **estructural**, regla de `R-59`, sin el caso «nulo = compartido») | fuera | ADDENDUM Wave 3 (cubrió `house_id` del evento, no los del submovimiento) | backlog |

Recuento canónico al entrar: 35 · 21 · 4 · 10; tras el alta de `R-180`: **36 · 21 · 4 · 11** · decisiones 10 (ninguna nueva).

## 2. Reproducción del pre-flight por API (`§10`, `§16`-`§18`, `§36`-`§39`) — sondeo temporal sobre `a93d4d1`, retirado

```
R-179   POST /operations {supplier_id | transport_id | cause_id | cull_cause_id | vaccine_id | medication_id | destination_plant_id: <de la empresa B>}
        → 201 en las SIETE familias
        PUT /operations/{id} {cause_id: <de B>}          → 200
        POST /corrections    {cause_id → <de B>}         → 201
        verdad persistida:   evento.company_id = A   ·   suppliers.company_id = B      (fila leída por SQL)

R-166   approve || reject (evento CORRECTED, dos revisores autorizados, BR-14 satisfecha)
        → approve = 200 · reject = 200
          estado final APPROVED · approval_actions = APPROVED(1) + REJECTED(1) · auditoría de éxito ×2
          notificaciones = 1  «registro rechazado» sobre un evento que quedó APROBADO
        approve || approve → 200 · 200 · approval_actions = APPROVED(2) · auditoría ×2
```

El rojo formal (§3) repite ambas como pruebas versionadas.

## 3. Rojo válido (leído en `1cf6c37`) — `§66`

`tests/test_master_reference_tenancy.py` + `tests/test_review_decision_concurrency.py`.

| Prueba | AC | Ruta · actor · permiso · empresa · unidad · recurso · maestro/estado | Esperado → **real** | Por qué es el defecto |
|---|---|---|---|---|
| `test_r179_02_05_…[supplier_id, transport_id, cause_id, cull_cause_id, vaccine_id, medication_id, destination_plant_id]` (7) | `AC-R179-02/05` | `POST /operations` · op (A) · `operations:create` · A · `breeder` ON · lote de A · **catálogo de B** | `400 BR-07` → **`201`** en las siete | ninguna capa comprueba la pertenencia del catálogo |
| `test_r179_03_04_…` | `AC-R179-03/04` | `PUT /operations/{id}` y `POST /corrections` · `cause_id` → causa de B | `400 BR-07` → **`200`** (`PUT`) y **`201`** (corrección) | ni la guarda de edición ni la de corrección conocían las FK de catálogo |
| `test_r179_07_12_…` | `AC-R179-07/12` | contexto declarado de B / autoridad global situada en A · vacuna de B | `400 BR-07` → **`201`** | ídem |
| `test_r179_08_…` | `AC-R179-08` | `feed_movements[].feed_type_id` de B | `400 BR-07` → **`201`** | submovimientos sin comprobación |
| `test_r179_08_09_…` | `AC-R179-08/09` | `hatchery_params[].hatchery_id` de B | `400 BR-07` → **`201`** | ídem |
| `test_r166_01_…` | `AC-R166-01` | `approve \|\| reject` · dos revisores · evento `CORRECTED` | una decisión efectiva → **`acciones = {approved: 1, rejected: 1}`**, dos auditorías, notificación de rechazo sobre evento aprobado | estado leído sin bloqueo |
| `test_r166_02_…` | `AC-R166-02` | `approve \|\| approve` | una → **`{approved: 2}`**, auditoría ×2 | ídem |
| `test_r166_03_…` | `AC-R166-03` | `reject \|\| reject` | una → **`{rejected: 2}`**, auditoría ×2, notificaciones ×2 | ídem |
| `test_r166_09_…` | `AC-R166-09` | `complete_review \|\| approve` desde `IN_REVIEW` | transiciones encadenadas y serializadas → **dos transiciones con el mismo estado origen** (`['in_review', 'in_review']`) | ídem |
| `test_r166_10_…` | `AC-R166-10` | `start_review \|\| start_review` | una → **ambas `200`** | ídem |

**Rojo válido: 16** (11 de `R-179`, 5 de `R-166`). Controles verdes antes y después: `AC-R179-01` (catálogo propio), `AC-R179-06` (compartido),
`AC-R179-10` (raza global), `AC-R166-07/08` (`BR-14` y contrato secuencial), `AC-R166-12/13` (seguridad; revisar no serializa el saldo).

**Rojas inválidas y su corrección (crédito 0)**: ocho de la primera pasada de `R-166` fallaban en el harness, no en el producto — el helper creaba el
evento con `mortality_recording` sobre un lote sin saldo (`BR-01`), la carrera de `complete_review` usaba una ruta inexistente (`/review/complete/{id}`
en vez de `/review/complete` con el id en el cuerpo) y el evento de la unidad apagada no podía crearse por API. Corregidos el helper (evento sin efecto
de saldo), la ruta y el sembrado por SQL. Además `AC-R166-09` se **reformuló**: medía denegación, pero `complete_review` y `approve` son transiciones
encadenadas legales (`IN_REVIEW → CORRECTED → APPROVED`); el invariante verificable es que **ninguna parta del mismo estado origen**. Reformulada,
discrimina: verde con bloqueo, roja sin él.

## 4. Implementación (`IMPLEMENTATION_COMMIT = 919803a`)

| Capa | Archivo | Cambio |
|---|---|---|
| inquilino | `backend/app/tenancy.py` | `verificar_catalogo_de_empresa(db, modelo, id, company_id, etiqueta)`: `company_id IS NULL` → compartido (aceptado); fijado → igualdad, si no `BR-07` «no encontrado» (anti-enumeración) · `verificar_catalogos_del_evento(db, company_id, **campos)`: mapa campo → modelo para los nueve directos y los dos derivados (por su `hatchery_id`) |
| alta | `backend/app/operations/service.py` | llamada en `_apply_business_rules`, junto a `verificar_ubicacion`: siete FK del evento + `feed_movements[].feed_type_id` + `hatchery_params[].{hatchery_id, incubator_id, hatcher_id}` |
| edición y corrección | `backend/app/operations/service.py` (`_reglas_puras_del_candidato`) | solo la FK de catálogo **que cambia** se valida sobre el candidato (`R-176`: sin arrastre de las no mencionadas) |
| corrección | `backend/app/corrections/service.py` | `cause_id`, `cull_cause_id`, `vaccine_id`, `medication_id`, `destination_plant_id` pasan por la guarda central (ya lo hacían `supplier_id`/`transport_id` desde `GA-REM-042`) |
| revisión | `backend/app/review/service.py` | `_bloquear_evento(db, event)`: `SELECT … FOR UPDATE` sobre `operational_events` + relectura de `status`; invocado en `ApprovalService._get_event_for_approval` (`approve`, `reject`, y por herencia `batch_*`) y en `ReviewService._get_event` (`start_review`, `return_to_operator`, `complete_review`), **después** de la cadena de inquilino/unidad y **antes** de validar la transición |

Sin migración · sin ruta, permiso, estado ni enum nuevos · sin reclasificar ningún maestro · `breeds` y `productive_phases` siguen siendo globales.

**Incidente registrado (y su corrección).** Al validar la reformulación de `AC-R166-09` ejecuté el driver de mutaciones **antes** del commit de
implementación: su reversión (`git checkout -- backend/app/review/service.py`) devolvió el archivo al commit de spec y borró la implementación de
`R-166`. Se detectó de inmediato (`grep _bloquear_evento` = 0), se reimplementó con el mismo parche, se verificó 34/34 y **solo entonces** se creó el
commit de implementación. Es exactamente el riesgo que la regla MUTATION CHECKPOINT (tranche 10) describe: el driver no debe ejecutarse con la
implementación sin confirmar, ni siquiera para validar una prueba. La sensibilidad definitiva (§5) corrió íntegramente sobre `919803a`.

## 5. Sensibilidad (`§81`-`§96`) — MUTATION CHECKPOINT cumplido

```
IMPLEMENTATION_COMMIT ......... 919803a  (tenancy · operations/service · corrections/service · review/service + las dos suites)
antes ......................... git status --short: solo la evidencia sin versionar · git show --stat HEAD verificado por el runner
driver ........................ mutar13.py (ancla única por archivo) · sensibilidad13.sh (aborta si hay código sucio o si HEAD no contiene la implementación)
tras cada mutación ............ git diff HEAD -- backend/app = 0 líneas
al final ...................... HEAD == 919803a · residuo 0 · humo: 34/34
```

| Mutación | Qué quita | ¿Instalada? | ¿Rama ejecutada? | ¿Propiedad retirada? | Prueba objetivo | Resultado | ¿Motivo exacto? | ¿Restaurada? |
|---|---|---|---|---|---|---|---|---|
| `R179-S1` | la comparación de pertenencia del catálogo | sí | sí | sí | `r179_02` | **7 failed** | sí: las siete familias vuelven a aceptarse (`201`) | sí (diff 0) |
| `R179-S2` | la comprobación **solo en el alta** | sí | sí | sí | `r179_02` | **7 failed** | sí: `201` en el alta; `PUT`/corrección siguen verdes → cobertura por superficie | sí |
| `R179-S3` | la comprobación en `PUT`/corrección (candidato) | sí | sí | sí | `r179_03_04` | **1 failed** | sí: «PUT hacia la causa de B, `200`» | sí |
| `R179-S4` | `cause_id` de la lista de campos que la corrección enruta a la guarda | sí | sí | sí | `r179_03_04` | **1 failed** | sí: «corrección hacia la causa de B, `201`» | sí |
| `R179-S5` | **sobre-bloqueo**: exigir misma empresa también al catálogo compartido | sí | sí | sí | `r179_06` | **7 failed** | sí: «compartido (`company_id NULL`) debe aceptarse, `400`» — prueba la precisión de la clasificación | sí |
| `R179-S6` | confiar en una empresa declarada por el cliente | sí | **no** | **no** | `r179_02` | **7 passed** | — el código **no tiene** superficie donde el cliente aporte la empresa (`self.company_id` sale de la sesión resuelta, `OD-11`); la mutación no altera ninguna rama → **inválida, reclasificada N/A con evidencia** (`§87`: «N/A otherwise»). `AC-R179-07` sigue como control verde | sí |
| `R166-S1` | el bloqueo y la relectura | sí | sí | sí | `r166_01`, `r166_02` | **2 failed** | sí: `{approved: 1, rejected: 1}` y `{approved: 2}` | sí |
| `R166-S3` | la **relectura** (conservando el bloqueo) | sí | sí | sí | `r166_01`, `r166_02` | **2 failed** | sí: mismas dos incoherencias → prueba el *momento*, no la mera presencia del bloqueo | sí |
| `R166-S4` | el bloqueo **solo** del camino de aprobación/rechazo | sí | sí | sí | `r166_02` | **1 failed** | sí: `{approved: 2}`; el camino de revisión sigue serializado → todos los escritores convergen | sí |
| `R166-S5` | el bloqueo **solo** del camino de revisión | sí | sí | sí | `r166_10` | **1 failed** | sí: `start \|\| start` ambas `200` | sí |
| `R166-S7` | la habilitación de unidad (dos capas: habilitadas y efectivas) | sí | sí | sí | `r166_12` | **1 failed** | sí: se aprobó un evento de la unidad **apagada** (`200`), violando `R-165`/`OD-16` | sí |
| `R166-S8` | el filtro de empresa y de unidad en la carga del evento | sí | sí | sí | `r166_12` | **1 failed** | sí: «otra empresa» — el revisor de B alcanzó el evento de A | sí |

Contabilidad: intentadas 12 · inicialmente inválidas 1 (`R179-S6`) · reconstruidas 0 · **válidas finales 11** · N/A 1 (`R179-S6`, con evidencia de por
qué no existe la superficie) · crédito por inválidas 0 · residuo 0.

## 6. Control de orden `R-175` (cerrado en el tranche 11) — con las suites nuevas (`T13`)

| Suite | Aislada | A→B | B→A | `T13 → A` | `A → T13` |
|---|---|---|---|---|---|
| `test_lot_start_date` | 6/6 | 24/24 | 24/24 | 40/40 | 40/40 |
| `test_lots_bu_enforcement` | 28/28 | 46/46 | 46/46 | 62/62 | 62/62 |
| `test_od14_productive_surfaces` | 35/35 | 53/53 | 53/53 | 69/69 | 69/69 |
| `test_clean_baseline` | 18/18 | — | — | `T13 → B`: 52/52 | `B → T13`: 52/52 |

18/18 pares verdes; el residuo «5 fases» no reaparece y las suites nuevas retiran todo lo que crean (catálogos por familia, incubadoras, lotes, empresas).

## 7. Regresiones exigidas (`§98` y siguientes) — dentro de la regresión completa

| Regresión | Suite(s) | Resultado |
|---|---|---|
| `R-152` / `GA-REM-042` (la importación exige proveedor y transporte de la empresa: ahora por el helper central) | `test_grandparent_import` | 18/18 |
| `R-176` (paridad de validación en `PUT` y corrección) · `R-173` (destino, saldo, bloqueo, anulación) · `R-178` (linaje) | `test_edit_validation_parity` 7/7 · `test_edit_cancel_balance` 16/16 · `test_lineage_cancel_move` 7/7 | verdes |
| `R-135`/`R-143` (estado, correcciones) · `R-165` (revisión y unidad apagada) · `GA-REM-007-A` (`BR-14`) | `test_state_continuity` 24/24 · `test_corrections` 18/18 · `test_review` 7/7 | verdes |
| `R-136`/`OD-19` (reverso: conserva su propio bloqueo del original; una sola compensación) | `test_internal_reversal` 22/22 · `test_reversal_role_migration` 3/3 | verdes |
| `RQ-03` · `R-42`/`R-59`/`R-115`/`R-116` (aislamiento de inquilino y maestros) | `test_master_tenant_isolation` 16/16 · `test_multicompany_isolation` 12/12 · `test_master_management` 11/11 | verdes |
| `R-159`/`R-160` · `R-162`/`R-163` (unidades en operaciones y lotes) | `test_operations_bu_enforcement` 32/32 · `test_lots_bu_enforcement` 28/28 | verdes |
| `R-130` · `R-161` · notificaciones (`OD-07`/`OD-08`) · operaciones y mortalidad | `test_population_invariant` 21/21 · `test_egg_incubation_concurrency` 7/7 · `test_notification_recipients` 14/14 · `test_operations` 12/12 · `test_mortality` 18/18 | verdes |
| guardianes | `test_ac14` (rutas 211, cabeza `x4y5z6a7b8c9`) · `test_clean_baseline` 18/18 (N/A por cambio, ejecutada) · `test_time_determinism` 10/10 | verdes |

## 8. Regresión completa (leída antes de certificar) y cierre técnico

```
backend ........ 1122 passed · 49 skipped · 0 failed   (1046 s · 97 suites · 1088 previas + 34 nuevas:
                 26 de test_master_reference_tenancy + 8 de test_review_decision_concurrency)
                 los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado
vitest ......... 108 / 108 (sin cambios de frontend en esta tranche)
tsc ............ 6 errores preexistentes (R-158), sin cambio
alembic ........ x4y5z6a7b8c9 (sin migración) · rutas 211 · guardianes exactos
integridad ..... código de producción == 919803a tras la sensibilidad (residuo 0) · humo 34/34
```

| Ítem | Cierre |
|---|---|
| `R-179` | **CERRADO (técnico)** · **P1** · `GA-REM-002-D` **CERTIFICADA** (frontera técnica) · `AC-R179-01…12` · rojo válido 11 · sensibilidad 5 válidas + 1 N/A con evidencia · catálogo compartido preservado (control positivo) · sin migración |
| `R-166` | **CERRADO (técnico)** · **P2** · `GA-REM-007-B` **CERTIFICADA** · `AC-R166-01…13` · rojo válido 5 con carrera **observada** · sensibilidad 6 válidas · una sola decisión efectiva por ciclo; todos los escritores convergen · sin migración |
| `R-180` | OPEN · P2 · registrado (galpones origen/destino de los submovimientos; clase estructural) |
| certificación de proceso | `BLOCKED_RUNTIME` (no se reclama; `R-164`) |

Recuento canónico tras el cierre: **36 · 23 cerrados · 4 parciales · 9 abiertos (P1 0 · P2 5 · P3 4) · decisiones 10**. Siguiente tranche (identificado,
no iniciado): `R-180` (misma familia de aislamiento, clase estructural); alternativa `R-147`/`R-148`.

Fuera de alcance, sin tocar: `R-153`/`AOD-25` · `R-177`/`AOD-24` · `R-164` · `R-140`/`R-154` residuales · `R-136` SAP · `B03`/`B04`/`R-156` · `AOD-23` ·
`R-142` · `R-144` · `R-147` · `R-148` · ola C y KPI · fase 9 · SAP real (`P-08`) · `BU-D10` · `R-158` · rediseño de maestros o del motor de aprobación ·
limpieza de datos históricos con referencias entre empresas (prevención sin reescritura retrospectiva; remediación aparte si se decide).
