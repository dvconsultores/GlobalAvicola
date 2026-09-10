# Evidencia · WAVE B · tranche 12 — `R-152` (plan de importación de abuelas, `GA-REM-042`) · `R-153` (`AOD-25`) · Progenitoras ≠ Reproductoras

**Fecha** 2026-09-10 · **Baseline de entrada** `main` · `5e9bbee` · limpio · local == remoto · cabeza `x4y5z6a7b8c9` · rutas 211 ·
**Modo** `R152_ONLY` · **Commits** `d3e0e70` (spec) · implementación (`IMPLEMENTATION_COMMIT`, §3) · evidencia (este) · **Sin migración** ·
**Decisión nueva** `AOD-25` (solo `R-153`, sin código).

## 1. Pre-flight (commit `d3e0e70`)

| Hallazgo | Significado exacto | Clasificación | Autoridad | Artefacto |
|---|---|---|---|---|
| `R-152` (P2, `H360A-02`) | la importación de abuelas es un evento genérico sin esquema: el plan de `docs/02 §3.4.1` no se captura con tipo, no tiene identidades, proveedor/transporte sin pertenencia, adjuntos sin clase, ninguna regla de tipo de lote | **ACTIVE · GOBERNADO · sin decisión · ejecutable** · `PROGENITORAS_SPECIFIC` (Reproductoras no importan; `BR-20`/`B02`/agua siguen siendo suyas; `BR-17`/`BR-18` quedan en la recepción) | `docs/02 §3.4.1` · `spec.md §4.4` · `RR-12` (patrón de identidad) · `GA-REM-040-G/H` (`AC-W05/W15/L14`: cadena de acceso certificada para `grandparent`) · `GA-REM-005 E.3` (documental) · `GA-REM-030`/`R-42` | `R152_R153_DEPENDENCY_TRACE.md` · `R152_R153_PROGENITORAS_FUNCTIONAL_PARITY_MATRIX.md` · `R152_PROGENITORAS_GAP_MATRIX.md` · `GA-REM-042` (`BR-22`) · `RC-16`/`RR-19` |
| `R-153` (P3, `H360A-03`) | nada crea el lote de abuelas al «completar» la importación; hoy el lote se crea a mano antes (la importación exige `lot_id`) | **ACTIVE · no gobernado en lo implementación-crítico → `OWNER_DECISION_REQUIRED` (`AOD-25`)** · depende de `R-152` (`HARD_DATA_MODEL` + `HARD_FUNCTIONAL`) | `docs/02 §3.4.2` · `spec.md §4.4` · `docs/15 :237` · `PROCESS-01` | `R153_PROGENITORAS_GAP_MATRIX.md` · `AOD-25` |
| registrado | `R-179` (P3): FK de maestros de otra empresa en eventos (`supplier_id`, `transport_id`, causas, vacunas, medicamentos, planta) sin `verificar_pertenencia`; `GA-REM-042` cubre proveedor/transporte solo en la importación | fuera | clase `R-42` | backlog |

Recuento canónico al entrar: 34 · 20 · 4 · 10; tras el alta de `R-179`: **35 · 20 · 4 · 11** · decisiones 10 (`AOD-25`).

## 2. Rojo válido (leído en `d3e0e70`, antes de tocar código) — `§67`

Backend: `tests/test_grandparent_import.py` → **13 failed · 5 passed** (42 s). Frontend: `grandparentImportContract.test.ts` → **6 failed**.

| Prueba | AC | Fuente | Ruta · actor · permiso · empresa · unidad empresa · unidad usuario · tipo de ave · recurso · estado · fecha | Esperado → **real** | Por qué es el defecto |
|---|---|---|---|---|---|
| `test_r152_02_sin_plan_se_deniega` | `AC-R152-02` | `docs/02 §3.4.1` | `POST /operations` · `op_gp` · `operations:create` · A · `grandparent` ON · concesión `grandparent` · `grandparent` · lote `lg` · `REGISTERED` · `recent_event_date()` | `400 BR-22` → **`201`** (el cuerpo de hoy, sin plan) | sin esquema ni regla |
| `test_r152_03_identidades_del_plan[…]` (6) | `AC-R152-03` | `RR-12`/`RR-19` | ídem | `400 BR-22` → **`201`** en las seis (embarcada ≠ recibida + mortalidad; recibida ≠ Σ ♂/♀; llegada < salida; fin de cuarentena < llegada; sin país; sin filas) | sin identidades |
| `test_r152_03b_cantidad_comprada_cero_se_rechaza` | `AC-R152-03` | ídem | ídem | `400/422` → **`201`** | sin tipo |
| `test_r152_05_09_oc_proveedor_transporte…` | `AC-R152-05` | `§3.4.1` · `R-42` | ídem | `400 BR-22` sin OC → **`201`** (primera aserción) | OC y proveedor no obligatorios; pertenencia no verificada |
| `test_r152_04_…solo_sobre_un_lote_de_abuelas` | `AC-R152-04` | `spec.md §4.4` | `op_ambos` · lote `lr` (`breeder`) | `400 BR-22` → **`201`** | tipo de lote no cruzado |
| `test_r152_06_07_los_adjuntos_del_plan_se_clasifican` | `AC-R152-06` | `§3.4.1` (5 clases) | `POST /operations/{id}/evidences` · `evidence_type=sanitary_document` | `201` con la clase → **`201` con `document`** | clase derivada del MIME, parámetro ignorado |
| `test_r152_17_la_edicion_revalida_el_plan` | `AC-R152-17` | `GA-REM-023-B` | `PUT extra_data` con `shipped_total = 999` | `400 BR-22` → **`200`** | la guarda no conoce el plan |
| `test_r152_18_la_correccion_revalida_el_plan` | `AC-R152-18` | ídem | `POST /corrections extra_data` con `transit_mortality = 50` | `400 BR-22` → **`201`** | ídem |
| vitest (6) | `AC-R152-20/21` | `§3.4.1` · i18n | formulario, detalle, locales | plan bajo `extra_data.import_plan.*`, detalle, clases, claves ES/EN → **ausentes** | captura libre, detalle sin plan |

Controles verdes antes y después: `AC-R152-01/08/19` (importación completa por actor con solo `grandparent`; saldo 0; recepción con la misma OC pasa
—la importación no acumula—; anulación sin efecto), `AC-R152-10/11` (`breeder` no autoriza `grandparent` y viceversa), `AC-R152-11b` (empresa con
`grandparent` ON y `breeder` OFF importa), `AC-R152-12/13/14` (unidad apagada, global sin contexto / situada, inquilino), `AC-R152-15/16` (RBAC,
Administrador de Accesos, Contraloría). Crédito por rojo inválido: **0** (ninguna roja por empresa, unidad, concesión, permiso, fase, fecha, fixture no
`grandparent`, fila `breeder` reutilizada, `R-166`, `R-164`, sintaxis, maestro ausente ni requisito equivocado).

## 3. Implementación (`IMPLEMENTATION_COMMIT`, §4) — sin migración; primitivas compartidas con justificación (`GA-REM-042 §3`)

| Capa | Archivo | Cambio |
|---|---|---|
| dominio | `backend/app/operations/schemas.py` | `PlanDeImportacion` (pydantic, `extra="forbid"`): `origin_country`, `purchased_total ≥ 1`, `shipped_total ≥ 1`, `received_total ≥ 0`, `transit_mortality ≥ 0`, `departure_date`, `arrival_date`; opcionales `reception_condition`, `quarantine_days ≥ 0`, `quarantine_end_date`, `initial_health_inspection` |
| dominio | `backend/app/operations/validators.py` | `validate_import_plan(event_type, bird_type, plan, filas, sap_document_ref, supplier_id)` (`BR-22`): solo lote `grandparent`; plan obligatorio y tipado; OC y proveedor declarados; ≥ 1 fila ♂/♀; `recibida = Σ ♂/♀`; `embarcada = recibida + mortalidad en traslado`; `llegada ≥ salida`; `fin de cuarentena ≥ llegada` · `CLASES_DE_ADJUNTO` (photo, document, signature, audio + las cinco del plan) |
| API | `backend/app/operations/service.py` | rama `GRANDPARENT_IMPORT` en `_apply_business_rules` (plan + `_verificar_maestros_de_importacion`: `verificar_pertenencia` de proveedor y transporte, `GA-REM-030`/`R-42`) · `_reglas_puras_del_candidato`: si cambian `extra_data`, `supplier_id`, `transport_id` o `lot_id` en una importación, `BR-22` sobre el candidato con las filas persistidas y pertenencia de los maestros cambiados (`R-176`, sin repetir el alta) |
| API | `backend/app/corrections/service.py` | `extra_data`, `supplier_id`, `transport_id` pasan por la guarda central (`R-173`/`R-176`) |
| API | `backend/app/operations/router.py` | `upload_evidence`: campo `evidence_type` opcional; fuera del conjunto cerrado → `400`; ausente → derivado del MIME (como hoy) |
| seguridad | — | **sin cambio**: cadena `GA-REM-040` (empresa, unidad habilitada, concesión, RBAC, propiedad) certificada para `grandparent`; sin permiso, ruta, estado ni enum nuevos; `bird_type` no autoriza |
| frontend | `frontend/src/pages/operations/OperationFormPage.tsx` | caso `grandparent_import`: proveedor y transporte (selectores existentes), país, comprada, embarcada, recibida, mortalidad en traslado, fechas de salida/llegada, condición, cuarentena (días y fin), inspección inicial bajo `extra_data.import_plan.*`; ♂/♀ recibidas (`renderMFRows`); la OC la ofrece el bloque común (ya incluía `grandparent_import`) |
| frontend | `frontend/src/pages/operations/OperationDetailPage.tsx` | bloque «Plan de importación» (etiquetas i18n); selector de clase de adjunto en importaciones; la clase se muestra en la lista |
| frontend | `frontend/public/locales/{es,en}/translation.json` | `operations.import*` (14 claves) · `evidence.typeLabel`, `evidence.typeAuto`, `evidence.types.*` (7) — sin texto fijo en componentes |
| E2E (documental, runtime `BLOCKED_RUNTIME`) | `e2e/proceso-p01-progenitoras-cria.spec.ts` · `test-support/e2e-api.ts` | el paso 1 envía el plan; `crearMaestros` crea proveedor y transporte |
| pruebas | `backend/tests/test_grandparent_import.py` (18) · `frontend/src/pages/operations/__tests__/grandparentImportContract.test.ts` (6) | `AC-R152-01…21` |

Lo que **no** cambia (paridad no asumida): `validate_reception_reconciliation` (`BR-20`, Reproductoras; sigue prohibiendo la tupla en la importación),
`validate_house_capacity`/`validate_oc_limit` (paso 4), evaluación de curva (`B02`), agua (`RR-11`), `get_current_bird_balance` (la importación no es entrada),
`create_lot` (la creación del lote sigue siendo manual hasta `AOD-25`).

## 4. Verde dirigido (`§76-§85`) — `R-152`; `R-153` sin código (`AOD-25`)

| Bloque | Resultado |
|---|---|
| dominio (plan tipado, identidades, tipo de lote, OC/proveedor, comprada = 0) | `_02`, `_03[×6]`, `_03b`, `_04`, `_05_09`: **10/10** |
| API (alta documental, anulación, adjuntos clasificados) | `_01_08_19`, `_06_07`: **2/2** |
| seguridad (RBAC, Administrador de Accesos, Contraloría, global sin contexto / situada, inquilino) | `_12_13_14`, `_15_16`: **2/2** |
| aislamiento de unidades (solo `breeder` → denegado; solo `grandparent` → pasa y no autoriza `breeder`; empresa con `grandparent` ON y `breeder` OFF; empresa con `grandparent` OFF) | `_10_11`, `_11b`, `_12_13_14`: **3/3** |
| reglas de negocio (`BR-22`, `BR-20` prohibida, `BR-07` maestros) | dentro de las anteriores |
| edición / corrección (`BR-22` sobre el candidato; proveedor ajeno; sin repetir el alta) | `_17`, `_18`: **2/2** |
| saldo (documental; recepción puebla una vez; la importación no acumula contra la OC) | `_01_08_19`: **1/1** |
| linaje | **N/A** (la importación no crea vínculos) |
| frontend (formulario, detalle, clases de adjunto, i18n ES/EN) | `vitest` **6/6** (108/108 totales) · `tsc` 6 preexistentes (`R-158`) |
| **suite nueva** | **18/18** (primera pasada 17/18: la fixture de la empresa C usaba el proveedor de B — `Proveedor no encontrado`, `BR-07` —; corregida la fixture (proveedor y transporte propios de C), 18/18; sin cambio de código) |
| regresiones dirigidas | `test_edit_validation_parity` (R-176) 7/7 · `test_edit_cancel_balance` (R-173) 16/16 · `test_lineage_cancel_move` (R-178) 7/7 · `test_corrections` 18/18 · `test_operations_bu_enforcement` (R-159/R-160, `AC-W05/W15`) 32/32 · `test_lots_bu_enforcement` (R-163, `AC-L02/L14`) 28/28 · `test_population_invariant` (R-130) 21/21 · `test_reception_reconciliation` (B01) 10/10 · `test_purchase_order_receipt` (BR-18) 7/7 · `test_egg_incubation_concurrency` (R-161) 7/7 · `test_state_continuity` (R-135/R-143) 24/24 · `test_traceability` 4/4 · `test_clean_baseline` 18/18 (N/A por cambio, ejecutada) · `test_time_determinism` 10/10 |
| total dirigido | **234 passed · 1 failed (fixture) → 18/18 en la repetición de la suite** (340 s + 43 s) |

Cruce de unidades (`§78`): solo `breeder` → `grandparent` denegado ✔ · solo `grandparent` → `breeder` denegado ✔ · empresa `grandparent` OFF → denegado
(actor de empresa `400 BR-07`; global situada `403`) ✔ · sin concesión → denegado ✔ · sin RBAC → `403` ✔ · global sin contexto → `400 BR-07` ✔ ·
Administrador de Accesos → `403` ✔ · Contraloría (lectura) → `403` ✔. Configuración de empresa (`§79`): `grandparent` ON + `breeder` OFF funciona ✔;
`breeder` ON + `grandparent` OFF no expone la importación ✔. Configuración de usuario (`§80`): concesión `grandparent` sin `breeder` funciona ✔.
Primitiva compartida (`§81`): las suites de Reproductoras (B01, OC, R-130) siguen verdes ✔. Diferencia Progenitoras-específica (`§82`): `dead_on_arrival` en la
importación → `BR-20` (Reproductoras) y `BR-22` en el lote `breeder` (Progenitoras) — pares de fixtures independientes ✔. Migración: ninguna
(`test_clean_baseline` ejecutada como control). Tiempo: `test_time_determinism` verde (fechas de `tests.time_reference`).

## 5. Sensibilidad (`§86-§98`) — MUTATION CHECKPOINT cumplido

```
IMPLEMENTATION_COMMIT ......... 2323d0c (validators, schemas, service, corrections, router, frontend, pruebas)
antes ......................... git status --short: solo la evidencia sin versionar · git show --stat HEAD leído
driver ........................ mutar12.py (ancla única verificada por archivo) · sensibilidad12.sh (aborta con código sucio o sin implementación en HEAD)
después de cada mutación ...... git diff HEAD -- backend/app frontend/src = 0 líneas (la reversión vuelve al commit de implementación)
después de todo ............... HEAD == 2323d0c · residuo de código 0 · humo tras la sensibilidad: test_grandparent_import 18/18
```

| Mutación (prompt) | Qué quita | ¿Instalada? | ¿Rama ejecutada? | ¿Propiedad retirada? | Prueba objetivo | Resultado | ¿Motivo exacto? | ¿Restaurada? |
|---|---|---|---|---|---|---|---|---|
| `R152-S1` (S1 quitar el soporte añadido) | la validación del plan (`validate_import_plan` devuelve sin validar) | sí (+1/−1) | sí | sí | `r152_02`, `r152_03_*` | **1 failed, 6 passed** | sí: «sin plan de importación, `201`»; las identidades (`_03`) siguen verdes porque la mutación solo salta la presencia del plan (el resto del validador sigue) — acreditada por `_02` | sí (diff 0) |
| `R152-S2` (S2 fallback `breeder`) | `breeder ∈ efectivas` autoriza `grandparent` en `exigir_unidad_operativa` | sí | sí | sí | `r152_10` | **1 failed** | sí: «solo breeder no importa abuelas, `201`» | sí |
| `R152-S3` (S3 `grandparent` exige `breeder`) | acoplamiento inverso en `exigir_unidad_operativa` | sí | sí | sí | `r152_10`, `r152_11b` | **2 failed** | sí: «solo grandparent importa sin necesitar breeder» y «grandparent es unidad de primera clase» → `400 BR-07` (`Lote no encontrado`, anti-enumeración) | sí |
| `R152-S4` (S4 empresa apagada) | dos capas: `unidades_habilitadas` y `unidades_efectivas_por_id` ignoran `is_enabled` | sí (+2/−4) | sí | sí | `r152_12` | **1 failed** | sí: «grandparent apagada en B (concesión histórica)» → el actor de B importó con la unidad apagada | sí |
| `R152-S5` (S5 concesión de usuario) | `no_concedida` no se lanza | sí (+1/−3) | sí | sí | `r152_10` | **1 failed** | sí: «solo breeder no importa abuelas, `201`» (sin concesión de `grandparent` escribió) | sí |
| `R152-S6` (S6 RBAC) | `require_permission` no comprueba (`if False and …`) | sí | sí | sí | `r152_15` | **1 failed** | sí: «sin_perm, `201`» (el actor sin `operations:create` importó) | sí |
| `R152-S7` (S7 inquilino) | tres capas: `validate_lot_active` sin empresa · `verificar_pertenencia` sin empresa · `_acotar_a_empresa` sin acotar | sí (3 archivos, +3/−5) | sí | sí | `r152_12` | **1 failed** | sí: «global sin empresa» → **`201`** (fail-closed de `OD-14.d` retirado: un actor sin empresa efectiva escribió una importación); la aserción de inquilino cruzado (actor de B sobre lote de A) es posterior en la misma prueba y no se alcanzó: la fuga observada es la de contexto de empresa, que es la primera capa del inquilino | sí |
| `R152-S8` (S8 paridad errónea) | la regla de tipo de lote (la importación acepta `breeder`) | sí (+1/−2) | sí | sí | `r152_04` | **1 failed** | sí: «lote breeder, `201`» | sí |
| `R152-S9` (S9 frontend) | el campo país del caso `grandparent_import` | sí | sí | sí | `vitest` `AC-R152-20` | **1 failed, 5 passed** | sí: «expected … to contain `extra_data.import_plan.origin_country`» | sí |
| `R152-S10` (S10 saldo) | `GRANDPARENT_IMPORT` como entrada de `get_current_bird_balance` | sí | sí | sí | `r152_01` | **1 failed** | sí: «la importación no puebla el lote» (saldo 100 tras importar) | sí |
| `R152-S11` (clase de adjunto) | se ignora el `evidence_type` declarado | sí | sí | sí | `r152_06` | **1 failed** | sí: «sanitary_document, `201` con `document`» | sí |

Contabilidad: intentadas 11 · inicialmente inválidas 0 · reconstruidas 0 · válidas finales **11** · N/A 0 · crédito por inválidas 0 · residuo 0.

## 6. Control de orden `R-175` (`§102`, cerrado en la tranche 11) — con la suite nueva (`T12` = `test_grandparent_import`)

| Suite | Aislada | A→B | B→A | `T12 → A` | `A → T12` |
|---|---|---|---|---|---|
| `test_lot_start_date` | 6/6 | 24/24 | 24/24 | 24/24 | 24/24 |
| `test_lots_bu_enforcement` | 28/28 | 46/46 | 46/46 | 46/46 | 46/46 |
| `test_od14_productive_surfaces` | 35/35 | 53/53 | 53/53 | 53/53 | 53/53 |
| `test_clean_baseline` | 18/18 | — | — | `T12 → B`: 36/36 | `B → T12`: 36/36 |

18/18 pares verdes; sin reintroducir el residuo «5 fases». La suite nueva retira todo lo que crea (proveedores, transportes, OC, lotes, empresas, adjuntos del servidor).

## 7. Regresiones exigidas (`§100-§104` + cola establecida) — dentro de la regresión completa

| Regresión | Suite(s) | Resultado |
|---|---|---|
| `R-176` (paridad de validación en `PUT` y `POST /corrections`; la importación entra por la misma guarda) | `test_edit_validation_parity` | 7/7 |
| `R-178` (linaje efectivo; la importación no crea vínculos) | `test_lineage_cancel_move` · `test_traceability` · `test_reception_lineage` | verdes |
| `R-175` (pares) | §6 | 18/18 |
| `R-173` (destino, saldo, bloqueo ascendente, cancel con relectura, auditoría) | `test_edit_cancel_balance` | 16/16 |
| `R-172` · `R-174` · `R-171` · `R-161` · `R-130` · `R-170`/`B13` · `B01` · `B02` · `B05` | `test_egg_type_availability` · `test_edit_cancel_balance` · `vitest` · `test_egg_incubation_concurrency` · `test_population_invariant` · `test_birth_classification` · `test_reception_reconciliation` · `test_reception_weight_range`/`test_weight_curve_evaluation`/`test_genetic_curves` · `test_water_consumption` | verdes |
| `R-136`/`OD-19` · `R-135`/`R-143` · `R-159`/`R-160` (`AC-W05/W15` Progenitoras) · `R-162`/`R-163` (`AC-L02/L14`) · `R-139` · `R-165` · `OD-14`/`OD-16` · `GA-REM-035` (`BR-18`) · `GA-REM-008/031/030` | reversos · correcciones/estado · `test_operations_bu_enforcement` 32/32 · `test_lots_bu_enforcement` 28/28 · global/revisión/`test_od14_productive_surfaces` · `test_purchase_order_receipt` 7/7 · trazabilidad | verdes |
| guardianes · `RQ-03` · seguridad `R-121`/`R-113`/`R-129` | `test_ac14` (211, cabeza `x4y5z6a7b8c9`) · `test_clean_baseline` (N/A por cambio, ejecutada) · `test_time_determinism` · RBAC/sesión/multiempresa | verdes |

## 8. Regresión completa (leída antes de certificar) y cierre técnico

```
backend ........ 1088 passed · 49 skipped · 0 failed   (1113 s · 95 suites · 1070 previas + 18 nuevas de test_grandparent_import)
                 los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado
vitest ......... 108 / 108  (102 previas + 6 del contrato de la importación)
tsc ............ 6 errores preexistentes (R-158), sin cambio
alembic ........ x4y5z6a7b8c9 (sin migración) · rutas 211 · guardianes exactos
integridad ..... código de producción == 2323d0c tras la sensibilidad (residuo 0) · humo 18/18
E2E ............ BLOCKED_RUNTIME (R-164); guion proceso-p01 y helper actualizados (documental)
```

| Ítem | Cierre |
|---|---|
| `R-152` | **CERRADO (técnico)** · P2 · `GA-REM-042` **CERTIFICADA** (frontera técnica) · `AC-R152-01…21` · rojo válido 13 + 6 · sensibilidad 11/11 válidas · Progenitoras ≠ Reproductoras (primitivas compartidas justificadas; `BR-20`/`B02`/agua/`BR-17`/`BR-18`/`create_lot` sin cambio) |
| `R-153` | OPEN · P3 · **`OWNER_DECISION_REQUIRED` (`AOD-25`)** · dependencia de `R-152` satisfecha por esta implementación; sin código hasta la decisión |
| `R-179` | OPEN · P3 · registrado (FK de maestros de otra empresa en eventos; `GA-REM-042` cubre proveedor/transporte en la importación) |
| certificación de proceso | `P-01` sigue certificado como cadena API (`PROCESS-01`); certificación E2E `BLOCKED_RUNTIME` (no se reclama) |

Recuento canónico tras el cierre: **35 · 21 cerrados · 4 parciales · 10 abiertos (P1 0 · P2 5 · P3 5) · decisiones 10**. Siguiente tranche (identificado, no
iniciado): `R-166` (approve/reject concurrentes sobre el mismo `CORRECTED`); alternativa `R-179`.

Fuera de alcance, sin tocar: `R-153` (código), `R-166`, `R-164`, `R-177`/`AOD-24`, `R-140`/`R-154` residuales, `R-136` SAP, `B03`/`B04`/`R-156`, `AOD-23`, `AOD-24`,
`AOD-25`, `R-142`, `R-144`, `R-147`, `R-148`, `R-179`, ola C y todo KPI, fase 9, SAP, `P-08`, `BU-D10`, `R-158`, reescrituras genéricas.
