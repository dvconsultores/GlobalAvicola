# GA-REQ-061 · CUTOVER OPERACIONAL (T14) — CERTIFICACIÓN TÉCNICA

Fecha: 2026-09-15 · Tranche: **T14** (`GA-REQ-061` · Cutover operacional / Cargas
Iniciales) · Cabeza de cierre: `__CLOSURE__` · Política `AOD-29 Clar.
01`: certificación local + `PUSH = REQUIRED_AFTER_LOCAL_CERTIFICATION` +
`REMOTE_SHA_MATCH` en cada checkpoint.

## Alcance ejecutado (C1–C9)

| Checkpoint | Contenido | RED | IMPL/cierre |
|---|---|---|---|
| C1 | Fundación: tablas `cutover_batches/items/staging_rows/opening_balance_corrections`, extensiones `OpeningBalance`/`Lot`, migración `b7c8d9e0f1a2` + `c8d9e0f1a2b3` (enums), RBAC `cutover`, `AuditModule.CUTOVER` | `cad5e3c` | `cf03253` |
| C2 | Parser openpyxl v1 + staging + validación estructurada + idempotencia por checksum | `efb098d` | `3e138a1` |
| C3 | Ciclo `submit/approve/reject` con segregación creador≠aprobador + 409 deterministas | `b7f596f` | `3e3f2cb` |
| C4 | Apply atómico: lotes MIGRATED/reuso, snapshots «saldo vivo al corte», BU habilitada + alcance actor, rollback total `FAILED_APPLY` | `b30a58a` | `782547b` / `fe5fe98` |
| C5 | `GET /reconciliation`: Opening/Post/Lifetime; golden **9.965** (nunca 9.465); UNKNOWN=null visible; post `event_date > corte` con contrapartidas `GA-REM-041` | `81ea05f` | `3452117` / `4b8bc74` |
| C6 | Correcciones formales AC59-65: lista blanca, razón ≥5, before/after/delta, auditoría `CORRECT`, tenancy 404, sin borrar post (9.900⇒9.865) | `bfadb41` | `f7819f1` / `02e0632` |
| C7 | Matriz `CUT-RED-01..22` + controles `CUT-CTL-01..06`; **2 deficits reales destapados y cerrados**: `MASTER_INACTIVE` (OD-21/AC52, histórica AC53 preservada) y **alcance BU del actor no-super-admin resuelto en BD** (patrón `/me`) | `b3217ac` | `5f40842` / `69f5aa8` |
| C8 | FE «Cargas Iniciales» `/cutover` (menú admin): flujo completo, apply bloqueado con errores, UNKNOWN≠0 visual, i18n ES/EN; jsdom 4/4; FE 524/524; build 0 | — (FE tranche) | `a7ada1f` |
| C9 | `GET /cutover-templates/{bu}` (v1 versionada, Instrucciones/Meta/Datos, semántica UNKNOWN impresa) + botón UI + **E2E 4 BUs** con journals y negativas | `C9-RED` | IMPL+E2E / `1976011` |

## Semántica de oro (mandato §53)

| Salida | Valor certificado |
|---|---|
| `current_live` (10.000 − 35) | **9.965** — jamás 9.465 |
| `post.mortality` | **35** |
| `lifetime.mortality` | **535** (500 histórica + 35 post) |
| Histórico alimentación ausente | **UNKNOWN** (`null` en API, nunca `0`) |
| Feed lifetime / FCR | UNKNOWN si falta el componente histórico |

## Sensibilidad S1–S10 (todas con RED quirúrgica + restore desde IMPL SHA)

| Mutación | Rojo esperado | Resultado |
|---|---|---|
| S1 tenancy batch | CUT-RED-01/02/03 | **3:3** (c7 red01/02/03) |
| S2 BU-empresa en apply | CUT-RED-04 | **1:1** |
| S3 grant de BU | CUT-RED-05 | **1:1** |
| S4 estado/duplicado apply | CUT-RED-08/09 | **clúster 4:4** (apply-path c4, documentado) |
| S5 atomicidad (inválidas) | CUT-RED-07 | **1:1** (preview 3/2/1) |
| S6 UNKNOWN→0 | CUT-RED-11 | **1:1** (c5 unknown) |
| S7 resta doble de historical | CUT-RED-12/13 | **2:2** (c5 golden) + **1:1** (C4) |
| S8 edición directa de APPLIED | CUT-RED-15/16 | **1:1** (c6, ruta inyectada y restaurada) |
| S9 razón opcional | CUT-RED-17 | **1:1** |
| S10 sin FOR UPDATE | CUT-RED-10 | **1:1** (concurrencia) |

Todas restauradas desde el SHA de implementación del checkpoint con `git
restore --source=…` (worktree limpio verificado) y post-mutación en verde.

## E2E (regla: sin certificar BU por transitividad)

`e2e/proceso-p16-cutover-cargas-iniciales.spec.ts` — 4/4 BUs con corrida propia,
journal JSON por BU (`evidence/e2e/e2e-*.json`) y log serializado
(`evidence/e2e/c9-e2e-4bus.log`):

- **grandparent/breeder/hatchery/broiler**: batch→plantilla→upload→validated→
  submit→approve (actor distinto)→apply→reconciliación; reproducible (dos
  consultas idénticas).
- **Broiler (numérico obligatorio)**: 10.000/500/35 ⇒ `current_live` **9.965**,
  `lifetime` **535**, histórico desconocido ⇒ `lifetime=null` + `feed_kg=null`
  (UNKNOWN visible; `0` sería fabricación).
- **Sondas negativas**: cross-company lectura ⇒ 404; cross-company apply ⇒
  403/404; re-apply ⇒ 409; submit con fila inválida ⇒ 409 (apply bloqueado).
- **Sin fabricaciones**: la reconciliación expone `source` real
  (EXCEL/SAP según batch); los E2E no crean eventos/documentos SAP.

## Gates finales

- **BE targeted por checkpoint**: C1 2/2 · C2 5/5 · C3 4/4 · C4 4/4 · C5 4/4 ·
  C6 5/5 · C7 15/15 · C9 +1 (plantilla) — guardias de conjunto **67/67**.
- **BE full**: **1428 passed / 0 failed / 49 skipped** (runner `scripts/run_tests.sh`, 21:17; evidencia `evidence/green/be-full-1428.log`).
- **Guardas estructurales**: tablas **60** (`test_population_invariant`), rutas
  `/api/` **226**, cabeza alembic única `c8d9e0f1a2b3`.
- **FE**: full **524/524** (`vitest run`), `npm run build` EXIT 0.
- **E2E**: **4/4** (harness `scripts_e2e.sh`, stack aislado 8099/5199).

## Evidencia

`audit/ga-claude-final-audit/specs/GA-REQ-061/evidence/` —
`red/` (incluye c7 red-final causa-exacta), `green/` (incluye 67/67), `sensibilidad/`
(S1-S10), `post-mutation/`, `fe/`, `e2e/` (journals).

## Hallazgos y correcciones de la tranche

1. **`MASTER_INACTIVE` inexistente** (OD-21/AC52): añadido en upload de
   referencia nueva; la referencia histórica a lote existente se conserva (AC53).
2. **Alcance BU del actor no-super-admin jamás resuelto**: el servicio leía claves
   de sesión que `get_current_user` no puebla ⇒ todo apply no-super-admin era 403
   por construcción. Resuelto contra BD (`unidades_efectivas ∪ concedidas`,
   patrón `/me`).
3. **Plantilla descargable ausente** (arquitectura §6): añadida versionada v1 por
   BU con la semántica UNKNOWN impresa y gate `cutover:create`.

## Estado

**T14 = CLOSED_TECHNICALLY** (pendiente del commit de cierre y `REMOTE_SHA_MATCH`).
Siguiente en el orden canónico: **T12** (ver `GA_PRE_SAP_PROGRAM_STATUS.md`).
