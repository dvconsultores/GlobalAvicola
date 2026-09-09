# EVIDENCIA · `R-136` (COMPONENTE INTERNO) + `R-165` · REVERSO INTERNO DE REGISTROS APROBADOS

**WAVE B · tranche 5** · 2026-09-09 · decisión `OD-19` (alias `AOD-21`) · spec `GA-REM-041` (commit `651bca3`) ·
pre-flight `R136_INTERNAL_REVERSAL_PREFLIGHT.md` (commit `d20e008`, STOP) · matriz `R136_INTERNAL_REVERSAL_EFFECT_MATRIX.md` ·
base `d20e008` · rama `main`

## 1. Entrada y descomposición

| Ítem | Valor |
|---|---|
| HEAD de partida `d20e008` · local == remoto · árbol limpio · Alembic `s9t0u1v2w3x4` | sí |
| Recuento de la ola B verificado | 22 · 7 cerrados · 2 parciales · 13 abiertos (consistente) |
| `R-136` título oficial | «tabla `reversals` sin servicio ni ruta; `BR-16` sin mecanismo» · P1 (SAP) |
| Componente **interno** | reverso de un registro **aprobado** aún no enviado a SAP, con contrapartida aprobada y exactamente única — **ejecutado** |
| Componente **SAP** | reverso de documento contabilizado (`BR-16`, `R16`, `OD-17.c`) — **`SAP_DEFERRED`** (`GA-REM-017` `BLOCKED_EXTERNAL`, `AOD-04`, `OD-12`) |
| Consolidados · huevos/incubación | **`DEFERRED`** (`OD-19 §11`) · **`BLOCKED_BY_R-161`** (`OD-19 §18`) |
| `BR-16` localizado | `spec.md §5` / `docs/02 R16`: ajuste **post-SAP** por reverso/corrección/nuevo movimiento — no cambia; el reverso **pre-SAP** lo define `OD-19` |
| Decisión requerida | **sí y resuelta**: `AOD-21 → OD-19` (24 cláusulas del propietario) |
| `R-165` | **incluido** (forma B): el reverso se aprueba por el plano de revisión, donde `OD-19 §13` prohíbe el salto de la autoridad global sobre unidad apagada; misma guarda compartida; sin decisión pendiente |

## 2. Vocabulario y modelo (`GA-REM-041 §2-§3`)

`CORRECTION` ≠ `REVERSAL` ≠ `CANCELLATION` ≠ `REJECTION`; `RETURNED` ≠ `REVERSED`; reverso interno ≠ reverso de documento SAP.
Estados: `EventStatus.REVERSED` (nuevo, terminal) para original **y** contrapartida; `AuditAction.REVERSED`. La solicitud crea la
contrapartida (mismo tipo, cantidades del original) en `PENDING_REVIEW` y la fila `reversals` (original, contrapartida,
motivo, solicitante, instantánea). La aprobación por el motor existente aplica la compensación atómicamente. Saldos:
`Σ natural (sin contrapartidas) − Σ contrapartidas efectivas`: el original revertido sigue sumando (+X), la contrapartida
efectiva resta (−X), neto 0, **ambas filas existen**.

| Estado origen | ¿Reversible? | Contrato |
|---|---|---|
| `APPROVED` (tipo elegible) | **sí** | `201` → contrapartida `PENDING_REVIEW` |
| `REGISTERED` · `PENDING_REVIEW` · `IN_REVIEW` · `RETURNED` · `REJECTED` · `CORRECTED` · `CANCELLED` · `SAP_*` | no | `400 BR-16` |
| `CONSOLIDATED` | no (diferido) | `400 BR-16` |
| `REVERSED` | no (ya revertido) | `400 BR-16` |
| con solicitud activa | no | `409` |
| tipo huevos/incubación | no (`R-161`) | `400 BR-16` «bloqueado por R-161» |

## 3. Rojo previo · validez

`tests/test_internal_reversal.py` (22) + `tests/test_review_bu_enforcement.py` (5) · 27 pruebas · sobre `651bca3` (spec
sin código): **22 rojas · 5 verdes**. 0 errores de import/fixture. Cada roja cae en el defecto real:

| Grupo | Pruebas | Observado ≠ exigido | Válida |
|---|---|---|---|
| `R-136`: acción inexistente | `rv01`, `rv02`, `rv03` ×2, `rv04`, `rv05`, `rv06` ×2, `rv07`, `ef01`, `ef02`, `ef06`, `ef07`, `s03_s04`, `s05_s07`, `s08`, `s09`, `au01_au02`, `au03_au05`, `au06`, `rv01` lecturas | `404 «Not Found»` (no existe `POST /reversals`) ≠ `201`/`400`/`403`/`409`/`422` según AC | sí |
| `R-165`: fuga | `165_01` | `200` (la autoridad global inicia revisión sobre unidad apagada) ≠ `403` | sí |

Controles verdes en rojo (5): `165_02`, `165_03`, `165_04`, `165_05`, `s01_s02` (este último pasaba por la ruta
inexistente; tras la implementación pasa por la razón correcta: `404` de alcance de empresa). **Corrección de prueba tras
el rojo** (no de contrato): `s08` enviaba el campo extra `company_id` a través de la ayuda cuyo parámetro homónimo situaba
el token; se envía el cuerpo crudo.

## 4. Implementación (commit `83437a2`; 20 ficheros, +1074/−48)

| Pieza | Qué hace |
|---|---|
| `alembic/versions/t0u1v2w3x4y5_reversed_status.py` | `eventstatus` y `auditaction` ganan `REVERSED` (`ADD VALUE IF NOT EXISTS`, `autocommit_block`); la bajada se detiene si hay filas `REVERSED` |
| `EventStatus.REVERSED` · `AuditAction.REVERSED` · `audit_state_transition` | estado y acción de auditoría propios (sin etiquetas engañosas) |
| `app/reversals/` (`schemas`, `service`, `router`) | `POST /reversals` (`reversals:create`): `get_event` + `exigir_unidad_operativa` + `FOR UPDATE` del original + elegibilidad + contrapartida + `reversals` + auditoría; `GET /reversals`, `GET /reversals/event/{id}` (`reversals:read`) |
| `reversals.service.efectuar_reverso_si_procede` | al aprobar una contrapartida: bloquea el original, exige `APPROVED`, valida saldos resultantes ≥ 0 (`BR-01`/`BR-04`, bloqueo de lote de `R-130`), marca ambos `REVERSED`, audita `approved → reversed` |
| `review/service.py` | `approve` y `complete_review` (un nivel) invocan la aplicación; `_exigir_habilitacion` en `_get_event` y `_get_event_for_approval` (**`R-165`**) |
| `operations/validators.py` `_suma_neta` | saldos de aves y viables con contrapartidas efectivas (huevos: sin cambio, subtipo bloqueado) |
| `operations/service.py` · `corrections/service.py` | contrapartida no editable ni corregible; `REVERSED` no cancelable |
| `auth/service.MODULOS` · `route_scope` · `main.py` | módulo `reversals` en el catálogo (sin migración de permisos); tres rutas `MULTI_UNIDAD` |
| guardianes | cabeza `t0u1v2w3x4y5`; rutas **211** (208 + 3); `SOLO_SUPER_ADMIN` **15** (≤ 15): `reversals:create/read` hasta que el propietario los asigne |

Sin lógica por nombre de rol, sin `is_global_actor`, 0 usos nuevos de `is_super_admin`, sin frontend, SAP y despliegue intactos.

## 5. Verde dirigido

| Suite | Resultado |
|---|---|
| `test_internal_reversal.py` · **`R-136` interno** | **22/22** |
| `test_review_bu_enforcement.py` · **`R-165`** | **5/5** |
| guardianes: `test_mortality::test_los_enums_de_python_existen_en_postgresql` · `test_population_invariant` (`R-130` 21 + head/rutas) · `test_company_catalog` (head) · `test_rbac` (`SOLO_SUPER_ADMIN`) | **98/98** (con las 27 anteriores) |
| relacionadas: estados (`R-135`/`R-143` 30) · correcciones · flujo completo (23) · revisión · cierre de lote · notificaciones · `R-160/R-159` (40) · `R-163/R-162` (28) · `R-139` (35) · unidades (admin `== 7`, guardia, catálogo) · sesión (`OD-15`) · accesos · SAP transversal · auditoría · humo · pendientes · aislamiento (empresa, usuarios, maestros) · lotes fase 3 · KPI | **498/498** |

## 6. Sensibilidad (`GA-REM-041 §7`)

Cada mutación se aplica marcada `MUTACION` (aplicación atómica), se ejecuta la suite del tranche (27), se revierte con
`git checkout --` y se comprueba `git diff --quiet -- app/`. Todas revertidas limpias.

| Mut. | Qué retira | Debía caer | Cayó | Válida |
|---|---|---|---|:--:|
| `S1` | la guarda de estado origen (`APPROVED`) en la solicitud | `AC-RV02` | **3**: `rv02`, `rv05`, `au06` (se crean contrapartidas de no aprobados) | sí |
| `S2` | la guarda «solicitud activa» (`409`) | `AC-RV03`/`AC-EF06` | **2**: `rv03_activa` (segunda `201`), `ef06` (dos `201`) | sí |
| `S2b` | además, la elegibilidad de `REVERSED` (lo revertido vuelve a solicitarse) | `AC-RV03`/`AC-EF04` | **3**: `rv03_ef04` (segunda solicitud `201` ≠ `400`), `rv03_activa`, `ef06` — el efecto sigue bloqueado en la aprobación (`efectuar…` exige `APPROVED`): tercera capa | sí |
| `S3` | la compensación en los saldos (contrapartida efectiva no resta) | `AC-EF01` | **2**: `ef01` (saldo **90** ≠ 100: `REVERSED` solo no basta), `rv03_ef04` | sí |
| `S4` | doble compensación (la efectiva resta dos veces) | `AC-EF03` | **2**: `ef01` (saldo **110**), `rv03_ef04` | sí |
| `S5` | la empresa en tres capas (`get_event`, `lotes_alcanzables`, `_unidad_del_lote`) | `AC-S01` | **1**: `s01_s02` — el actor de `B` **crea** la solicitud sobre el original de `A` (`201` observado) | sí |
| `S6` | la habilitación de la unidad en la guarda compartida | `AC-S03`/`AC-165-01` | **2**: `s03_s04` (global reversa sobre unidad apagada), `165_01` (global revisa sobre unidad apagada) | sí |
| `S7` | `reversals:create` → `read` en la ruta | `AC-S05`/`S07` | **2**: `s05_s07` (el actor de control-lectura solicita), `s01_s02` (contrato `404` → `403`) | sí |
| `S8` | la auditoría `approved → reversed` del original | `AC-AU04` | **1**: `au03_au05` | sí |
| `S9` | el `FOR UPDATE` del original en la solicitud | `AC-EF06` | **1**: `ef06` (las dos solicitudes concurrentes devolvieron `201`: dos contrapartidas) — reproducido en una pasada | sí |

Contabilidad: intentadas 10 (9 + `S2b`) · inicialmente inválidas 0 · reconstruidas 0 · válidas finales 10 · `N/A` 0 ·
acreditadas inválidas 0 · residuo `MUTACION` 0. Lección de `S2b`: la doble compensación está protegida por tres capas
(solicitud activa, elegibilidad de `REVERSED`, `APPROVED` exigido al aplicar); se documenta como defensa en profundidad.

## 7. Regresión

| Comprobación | Resultado |
|---|---|
| backend completo (`scripts/run_tests.sh`: `alembic upgrade head` → semillas → pytest) | **976 passed · 49 skipped · 0 failed** (807 s, primera pasada; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) |
| `R-130` 21/21 (invariante con contrapartidas: `ef01`, `ef02`) · `R-135`/`R-143` 30/30 · `R-159/R-160` 40/40 · `R-162/R-163` 28/28 · `R-139` 35/35 · fases 7/8 · `OD-14` (`s01_s02`, `165_04`) · `OD-16` (`s03_s04`, `165_01`) · Administrador de Accesos (`s05_s07`, `165_05`) · control-lectura (Contraloría representada, `s05_s07`) · Progenitoras (`s09`) | verdes |
| `RQ-03` (`route_scope`: tres rutas clasificadas) · `authorization_coverage` (211 con permiso) · `SOLO_SUPER_ADMIN` 15 · BU admin `== 7` | exactos |
| migración | `t0u1v2w3x4y5` aplicada por `upgrade` en la base de pruebas; guardián de enumerados verde |
| `vitest` | 87/87 |
| `tsc -b --noEmit` | 6 errores, los mismos (`AuditPage.tsx` ×2, `LotFormPage.tsx` ×4) = `R-158` |
| E2E | `BLOCKED_RUNTIME` |

## 8. Cierre

```
R-136 INTERNO ...... CERRADO (técnico): elegibilidad · contrapartida aprobada · exactamente una · saldos netos · inmutabilidad ·
                     inquilino/unidad/RBAC · motivo/auditoría · concurrencia                                                  ✔
R-136 OVERALL ...... PARTIAL (componente SAP: SAP_DEFERRED · consolidados: DEFERRED · huevos/incubación: BLOCKED_BY_R-161)   ◐
R-165 .............. CERRADO (técnico): superficie exacta (5 acciones del plano de revisión) · global bloqueada en BU OFF ·
                     actor de empresa y control-plane intactos                                                              ✔
E2E ................ BLOCKED_RUNTIME → certificación de proceso NO                                                            —
```

## 9. Riesgos restantes y fuera de alcance

`R-161` OPEN (huevos/incubación no reversibles hasta cerrarlo) · `R-164` BLOCKED_RUNTIME · `R-166` OPEN (la carrera
`approve`/`reject` afecta también a las contrapartidas: la aprobación bloquea el original, no la decisión) · `R-140`/`R-154`
parciales · consolidados diferidos · SAP diferido · frontend sin pantalla de reverso (fase 9) · `BU-D10` no tocado.

## 10. Siguiente tranche (identificado, NO iniciado)

`GA-REM-021` — captura exigida por el cliente: **agua** (`B05`), P1, `SPEC_READY`; `B01` desbloqueado por `R-130`; `B04`
fuera hasta `AOD-14`. Releída `WAVE_B §3`: es el siguiente ejecutable de mayor prioridad y verdad de negocio.
