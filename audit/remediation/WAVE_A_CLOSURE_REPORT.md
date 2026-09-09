# INFORME DE CIERRE — WAVE A (A0-P · A0-G · A1)

**2026-09-09** · base de entrada `7ee72a1` (Master 360) · commits de la ola: `2b3c36b` `5d2e355`
`90577d8` `e9ab11e` `e339c1e` + cierre · metodología Spec Development

```
WAVE A0-P   COMPLETE   OD-16 · spec.md v1.1.0 §4.0 · addendum Master 360 · matriz Progenitoras · matriz activación por empresa · BU-D10 PENDING_RATIFICATION
WAVE A0-G   COMPLETE   OD-17 (AOD-09) · OD-18 (AOD-12) · 75 hallazgos reconciliados, 0 sin disposición · R-130…R-157 · INDEX reconciliado · A01 verificado → R-139
WAVE A1     COMPLETE   R-127 CERRADO (GA-REM-033-A CERTIFIED) · R-127.b DEFERRED · fase 9 READY AFTER REMEDIATION (R-139) · FROZEN
WAVE A      COMPLETE   R-139 CERRADO (GA-REM-002-C · ec536c0 · 35/35 · sensibilidad 8 válidas) — ver §7
```

## 1. Baseline de entrada verificado

`main` · local `7ee72a1` = remoto `7ee72a1` · árbol limpio · Alembic `s9t0u1v2w3x4` · backend
784/49/0 · vitest 87/87 · E2E `NOT EXECUTED` (runtime no disponible). Los documentos
`GLOBAL_AVICOLA_MASTER_360_AUDIT_REPORT` y `GLOBAL_AVICOLA_REMEDIATION_ROADMAP_POST_AUDIT`
que el encargo pedía leer **no existen** en el repositorio: la Master 360 vive en
`MASTER_PROGRAM_STATUS_RECONCILIATION.md` y sus nueve matrices; la hoja de ruta, en su `§11`.
Historia preservada: `eb10739` (rojo) y `21e7423` (rectificación) intactos; sin `amend`, `rebase`
ni `force push`.

## 2. Regresión (§72–§87)

| Suite | Resultado | Fuente |
|---|---|---|
| Backend completo | **795 passed · 49 skipped · 0 failed** (539 s; 784 previas + 11 de `test_company_catalog.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) | `scripts/run_tests.sh -q -rA` |
| Vitest | **87 passed / 8 archivos** | `npx vitest run` |
| `tsc -b --noEmit` | **6 errores TS6133/TS2493 preexistentes** (`AuditPage.tsx`, `LotFormPage.tsx`): reproducidos en `7ee72a1`, frontend sin cambios en esta ola → `R-158` | `npx tsc -b --noEmit` |
| E2E | **`BLOCKED_RUNTIME`** — no ejecutada; la certificación funcional 15/15 sigue siendo histórica | — |

### 2.1 Requisito de alcance productivo (§72) — lo que las pruebas existentes soportan hoy

| Unidad | Archivos de test que la nombran | E2E que la recorren | Certificación funcional (histórica) | Estado real |
|---|:--:|:--:|---|---|
| `GRANDPARENT` | 7 | 3 (`p01`, `p02`, `p03`) | `P-01` 12/12 · `P-02` 9/9 (2026-09-05/06) | definida, implementada, disponible; huecos propios `R-152`, `R-153`; evidencia de fase y cierre pendiente (`H360A-04`) |
| `BREEDER` | 20 | 7 | `P-03`, `P-04` | ídem, sin huecos propios nuevos |
| `HATCHERY` | 21 | 3 | `P-05` | ídem; `R-133` (KPI vacunación) es genérico |
| `BROILER` | 21 | 5 | `P-06` | ídem; `R-130` (salida sin saldo), `R-131/134` (FCR/AFCR) son genéricos |
| Activación por empresa | `test_business_units` 31 · `test_business_unit_admin` 39 · `test_business_unit_guard` 25 · `test_session_payload` 16 | 0 | — | implementada y probada por integración; **no certificada como proceso** (`0/15`) |
| Concesiones de usuario | `test_access_administration` 16 · `test_grant_candidates` 14 · `test_session_payload` 16 | 0 | — | ídem |

Ninguna de estas cifras es certificación: son pruebas de integración verdes en la regresión de hoy.

### 2.2 Regresiones específicas exigidas

| § | Exigencia | Pruebas | Resultado |
|---|---|---|---|
| 73 | `RQ-03` sigue `COMPLETE`; `CompanyBusinessUnit` y `UserBusinessUnit` acotadas a inquilino; catálogo conforme | `test_master_tenant_isolation` 16 · `test_user_tenant_isolation` 17 · `test_business_units` (`AC-A07`, `AC-B10`) · `test_company_catalog` `T5` | **PASS** — 16 · 18 · 31 · 11 verdes |
| 74 | resolutor: ON+concesión → efectiva · OFF+concesión → no · ON sin concesión → no · cero → `[]` · sin retroceso | `test_business_units` (`ac_b04`, `ac_a05`, `ac_a06`, `nombre_del_rol_no_concede`) · `test_business_unit_admin` (`deshabilitar_*`, `habilitar_no_concede`) | **PASS** — 31 + 39 verdes |
| 75 | sesión: `effective_business_units` del resolutor central; Administrador de Accesos → `[]`; Super Admin según semántica certificada | `test_session_payload` 16 (`h11`, `h14`) | **PASS** — 16 verdes |
| 76 | `R-121`: catálogo compartido ≠ autoridad global | `test_role_tenancy` 12 | **PASS** — 12 verdes |
| 77 | `OD-14`/`R-126`: catálogo `CONTROL_GLOBAL`; `CompanyBusinessUnit` y concesiones `TENANT_SCOPED` | `test_master_tenant_isolation` (`od14_*`) · `test_company_catalog` `T6`/`T7` · `test_business_unit_admin` | **PASS** — 16 · 11 · 39 verdes |
| 78 | `OD-15`/`R-128`: auto-concesión denegada; habilitar no es vía de auto-concesión | `test_access_administration` 16 | **PASS** — 16 verdes |
| 79 | `R-113`: Administrador de Accesos sin comodín, sin `users:read`, sin concesiones automáticas | `test_access_administration` · `test_rbac` (`SOLO_SUPER_ADMIN`) | **PASS** — 16 · 21 verdes (`SOLO_SUPER_ADMIN` ≤ 15, sin tocar) |
| 80 | `R-129`: candidatos acotados, sin `users:read`, semántica de empresa seleccionada, auto-concesión denegada | `test_grant_candidates` 14 | **PASS** — 14 verdes |
| 81 | fase 7: listar/habilitar/deshabilitar · listar/conceder/revocar · transacción · auditoría · inquilino; las cuatro unidades independientes | `test_business_unit_admin` 39 (recuento de rutas `== 7`) | **PASS** — 39 verdes; las cuatro unidades se habilitan/deshabilitan por par sin regla cruzada |
| 82 | autoridad de la API de `CompanyBusinessUnit` por permiso, con empresa efectiva, sin nombres de rol | `test_business_unit_admin` (`_empresa_efectiva` → 403) · `test_el_nombre_del_rol_no_concede_nada` | **PASS** |
| 83 | guardianes: rutas, transacción, clasificación de recursos, RBAC, `SOLO_SUPER_ADMIN` (15) | arranque (`authorization_coverage`, `route_scope`, `transaction`) · `test_rbac` · `test_pending_classification` | **PASS** — arranque sin excepción; `test_rbac` 21 · `test_pending_classification` 35 verdes |
| 84 | recuentos exactos preservados (`== N`) | `test_business_unit_admin` (`== 7`) · `test_rbac` (`<= 15`) sin cambio | sin cambio de guardianes en la ola |

## 3. Puertas de cierre (§100)

| Puerta | Estado |
|---|:--:|
| Alcance productivo vigente formalizado · 4 unidades explícitas · Progenitoras trazada | ✓ `OD-16`, `spec.md §4.0`, `PROGENITORAS_COVERAGE_MATRIX` |
| Requisito de activación por empresa · distinción `CompanyBusinessUnit` vs `UserBusinessUnit` | ✓ `OD-16.b/d`, matriz de activación |
| Addendum Master 360 · `H360A` dispuestos · `BU-D10` explícito | ✓ |
| `AOD-09`, `AOD-12` formalizadas | ✓ `OD-17`, `OD-18` |
| `H360` dispuestos · `INDEX` reconciliado · `A01` verificado | ✓ (`R-130…R-157`; 12 filas de `INDEX`; `A01` → `R-139`) |
| `R-127`: spec/AC · rojo válido · arreglo · no nulo → 200 · `sap_config` ausente · sin migración · sin SAP | ✓ |
| `RQ-03` · `OD-14` · `OD-15` · `R-113` · `R-129` · fase 7 · fase 8 · guardianes | ✓ (§2.2, todos `PASS`) |
| backend completo · frontend | ✓ backend **795 passed · 49 skipped · 0 failed** (539 s; 784 previas + 11 de `test_company_catalog.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 87 passed / 8 archivos · `tsc` **6 errores TS6133/TS2493 preexistentes** (`AuditPage.tsx`, `LotFormPage.tsx`): reproducidos en `7ee72a1`, frontend sin cambios en esta ola → `R-158` |
| remoto verificado · árbol limpio | ver §6 |
| **`R-139`** | ✓ **CERRADO** (2026-09-09, tanda propia): `GA-REM-002-C`, 8/8 superficies, `AC26`; evidencia `R-139-OD14-PRODUCTIVE-DATA-EVIDENCE.md` |

## 4. `BU-D10`

```
BU-D10   PENDING_RATIFICATION
PREGUNTA ¿Qué ocurre con las concesiones de usuario cuando una empresa deshabilita una unidad de
         negocio y más tarde la vuelve a habilitar?
   A     la concesión histórica vuelve a ser efectiva automáticamente
         (comportamiento provisional vigente: GA-REM-040 §6.3 · AC-A06 · probado)
   B     la concesión queda histórica/inactiva y hace falta una concesión explícita nueva
NO se resolvió · NO hay código que dependa de la elección
```

## 5. Lo que queda diferido, con nombre

| Tema | Estado | Autoridad |
|---|---|---|
| `R-127.b` escritura de `sap_config` | `DEFERRED` | `OD-18.b` |
| Persistencia y superficie administrativa de la configuración SAP | `SAP_DEFERRED` | `OD-18.b`, `AOD-12` (parte de persistencia) |
| `R-139` conformidad `OD-14` en dato productivo | `WAVE A` · tanda propia | spec + AC pendientes |
| Fase 9 | `READY AFTER REMEDIATION (R-139)` · **`FROZEN`** | propietario |
| `WAVE B` — IDs preparados (no iniciada) | `R-130` población · `R-135` reenvío (`OD-17`) · `R-136` reverso · `R-140` · `R-142` · `R-143` · `R-144` · `R-147` · `R-148` · `R-152`/`R-153` Progenitoras · `R-154` · `R-156` · `GA-REM-021` (agua `R-13` + `H360-B01…B04`, `B13`) | `INDEX.md` «Asignación por olas» |
| `WAVE C` / `D` | sin implementación (KPI · SAP estructural) | `INDEX.md` |

## 6. Verificación remota

Tras el push del commit de cierre: `git ls-remote git@github.com:dvconsultores/GlobalAvicola.git refs/heads/main` debe coincidir con `git rev-parse HEAD` y `git status --short` debe estar vacío. El resultado real se reporta en el bloque final de la tanda (no puede constar aquí antes de existir el commit).

## 7. Cierre definitivo de `WAVE A` (2026-09-09 · `R-139`)

```
R-127   CERRADO   catálogo seguro de empresas (OD-18)
R-139   CERRADO   OD-14.c/d en las 8 superficies de dato productivo + primitivo fail-closed (GA-REM-002-C)
R-149   documental · sigue en WAVE A (no bloquea)         R-158   tsc preexistente · sigue en su ola (no bloquea)
R-159   NUEVO P2 · alcance de unidad en alertas · WAVE B
regresión tras R-139: **830 passed · 49 skipped · 0 failed** (542 s; 795 previas + 35 de `test_od14_productive_surfaces.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Por archivo: aislamiento de maestros 16 · usuarios 18 · roles 12 · unidades 31 · guarda 25 · administración 39 · sesión 16 · accesos 16 · candidatos 14 · `test_rbac` 21 (`SOLO_SUPER_ADMIN` ≤ 15 sin tocar) · clasificación pendiente 35 · curvas 16 · multiempresa 5 + 12 · saldo de apertura 12 · filas por unidad 21 · KPI por unidad 15 · catálogo de empresas 11 · vitest 87 passed / 8 archivos · tsc 6 errores preexistentes (`AuditPage.tsx`, `LotFormPage.tsx`), mismo número y mismos ficheros que en `7ee72a1` (`R-158`, sin cambio) (mismo número que en 7ee72a1)
WAVE A  COMPLETE en su alcance de autoridad/seguridad/datos
FASE 9  TECHNICALLY READY · FROZEN · NO INICIADA
BU-D10  PENDING_RATIFICATION
```
