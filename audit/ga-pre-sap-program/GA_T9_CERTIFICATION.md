# GA · T9 CERTIFICATION — Maestros y usuarios (R-215 · R-196 · R-195)

Fecha: 2026-09-14 · Programa: GA PRE-SAP · Política: **AOD-29 Clarification 01**
(certificación **local** con gates reproducibles; **GitHub Actions retirado**;
**push requerido** a `origin/main` con verificación de SHA remoto).

## 1 · Paquetes y commits

| Paquete | RED | IMPL (`LOCAL_CERTIFIED_SHA`) | Evidencia | Push |
|---|---|---|---|---|
| R-215 · render seguro de errores + `ErrorBoundary` | `4fc63b4` | **`cd2e7bc`** | `73a4fb9` | sincronizado (≤ `aa459ac`) |
| R-196 · maestros por entidad + empresa en servidor | `4c0f819` | **`571b4d5`** | `aa459ac` (C2b) | sincronizado |
| R-195 · edición de usuario (subconjunto + errores) | `7bde916` | **`bcfdebd`** | `e515858` (C2b) | **`e515858`** |

`HEAD` remoto tras el cierre: **`e515858`** · `REMOTE_SHA_MATCH = YES` (cada push verificado con `git ls-remote`).

## 2 · Gates locales (PASS)

| Gate | Resultado |
|---|---|
| R-215 targeted | 28/28 (7 archivos, incluye legacy afectadas) |
| Suite FE completa (R-215) | 405/405 |
| R-196 targeted FE/BE | 9/9 · 3/3 + 5/5 (setups adaptados) |
| Suite FE completa (tras R-196) | 414/414 |
| Suite BE completa (tras R-196) | **1367 passed / 0 failed / 49 skipped** |
| R-195 targeted | 5/5 (+ regresión usuarios r215/gaFe02/gaFe04) |
| Suite FE completa final (T9) | **62 archivos / 419/419** |
| `npm run build` (`tsc -b && vite build`) | EXIT 0 en cada checkpoint |
| BE en R-195 | sin cambio de producto (SPEC §10: contrato `UserUpdate` ya correcto) |

## 3 · Sensibilidad (mutación + restore desde SHA explícito)

- **R-215** S1-S6: cada mutación tiñe su test (1F/5P); cluster único esperado en
  S1 (selector). Restore `--source=cd2e7bc`.
- **R-196** S1-S6: S1 clúster de selector (4 tests, una ruta); S2-S6 1:1
  (AC-04/05/07 · be_01/be_02). Restore `--source=571b4d5`.
- **R-195** S1-S4: AC-01 · AC-03 · AC-05 · clúster {AC-03,AC-06} de la guarda.
  Restore `--source=bcfdebd`.
- Post-mutation: FE 419/419 · build OK · BE 1367/0/49.

## 4 · Hallazgos del paquete (subsanados o registrados)

1. **Cross-tenant en setups de tests (R-196)**: 5 tests de áreas creaban datos de
   otra empresa con `company_id` del cliente — agujero cerrado; setups adaptados a
   `switch-company` con actor legítimo (aserciones negativas intactas).
2. **Modal duplicado en `UsersPage` (R-195)**: el bloque de datos personales se
   renderizaba dos veces (inputs duplicados, raíz de ambigüedades de test);
   deduplicado en C2.
3. **AC-04 (R-196) reforzado**: el guard original no distinguía “campo sin tocar”
   de “campo limpiado”; ahora ejerce `''` (el caso real del 422 del `int`).
4. **AC-02 (R-195) ya verde por R-215**: el catch del guardado ya usaba
   `getErrorMessage` + toast; se conserva como regresión.

## 5 · Explícitos de política

- `GITHUB_ACTIONS = NOT_APPLICABLE_BY_OWNER_DECISION` (nunca PASS).
- `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION`; `REMOTE_SHA_VERIFICATION = PASS`.
- **`AOD29-DEPLOY-IMPACT`**: auto-deploy compartido no disponible (dependía de
  Actions retirados); `PUSH != DEPLOY`.

## 6 · UAT

Pendiente **acumulable** (no bloquea cierre técnico): R-215 (2 casos), R-196
(4), R-195 (3) — agrupables (decisión del programa: UAT del propietario se
ejecuta cuando el flujo/paquete lo requiera; el gate final PRE-SAP los lista).

## 7 · Estado

- **T9 = `CLOSED_TECHNICALLY`** · KPI de procesos sin cambio (**0/17**) ·
  `NO_GO_SAP_FUNCTIONAL_GAPS` · SAP **NOT_STARTED**.
- **Siguiente**: **T10** (R-197 · R-207; +R-142 si AOD-17) — arranque automático.
