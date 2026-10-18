# 10 · Estado final de la certificación — Revisión QA 2026-10-17

**Documento**: cierre consolidado de la ronda SPEC 008 (commits, regresiones, sensibilidad y bloque de estado)
**Fecha**: 2026-10-18 · **Baseline de referencia**: `83c9cd8` · **Spec**: `specs/008-qa-yolinel-findings-remediation/spec.md`
**Carácter**: estado local. **No** sustituye la verificación en runtime (`08_RUNTIME_VERIFICATION.md`) ni el contraste con el PDF original de QA.

---

## 1. Commits

| Hito | SHA | Contenido |
|---|---|---|
| Baseline | `83c9cd8` | Árbol de partida de la ronda (main) |
| GOV | `13cabff9474b53399310e007507b11dbe13e941a` | Gobierno: spec, plan, tasks y documentos de auditoría |
| IMPL | `dbd6122a3b32512cf8bf2ae6b4f7b91cf43a9124` | Implementación: BR-23, etiquetas, estado/Desactivar, bucle de revisión, fechas, listados y filtro Granja |
| IMPL-2 | `9390afcad3ca57dcea17d8065054978abe1a0720` | Refuerzo guardián QA-013 (20 maestros) + identidad estable de `useCan` |
| CERT | `68d78fcb8ac65c206d46f1ef0e87198301cdbc94` | Commit de certificación (documentación de cierre) |
| REMOTE | `68d78fcb8ac65c206d46f1ef0e87198301cdbc94` | SHA en remoto; coincidencia con local: `PASS` · árbol: `limpio (solo archivo local de credenciales del arnés sin versionar)` |

Todos los commits se hicieron **en `main`, sin rama nueva y sin push** hasta la autorización del Owner.

## 2. Regresiones

| Momento | Backend (`backend/scripts/run_tests.sh`) | Frontend (`npx vitest run` · `tsc -b` · `vite build`) |
|---|---|---|
| Pre-mutación | **1739 passed · 0 failed · 49 skipped** (22 min 26 s) · acotada a los hallazgos: **118 passed** | **96 archivos · 557 pruebas PASS** · `tsc_rc=0` · `build_rc=0` (Node v24.13.0) |
| Post-mutación (IMPL e IMPL-2) | **1739 passed · 0 failed · 49 skipped (23 min 17 s; idéntica a la pre-mutación)** | **96 archivos · 576 pruebas PASS · `tsc_rc=0` · `build_rc=0`** |

Sin reducción de pruebas: 1731 → 1739 (+8 backend) y 542 → 557 (+15) pre-mutación; con IMPL-2 el frontend pasa a
**576** (`qaYolinel.red.test.tsx` **4 → 23 casos, +19**; total 557 → 576). Ningún test eliminado ni marcado `skip`.
Logs: `evidence/07_backend_full.log`, `evidence/07_backend_targeted.log`, `evidence/07_frontend_regression.log`,
`evidence/07_backend_full_post_mutation.log`, `evidence/07_frontend_regression_post_mutation.log`.

## 3. Sensibilidad

**Resultado final: 5/5 DETECTED.** Cada mutación se revirtió con `git restore --source=<SHA> -- <archivo>` y se
verificó `FINAL_DIFF=0` antes de la siguiente.

| ID | Mutación | Ámbito | Resultado |
|---|---|---|---|
| **S1** | BR-23 desactivada (`validators.py` → `if True`) | `test_br23_sap_reference_business_unit.py` | **DETECTED** — 1 failed / 4 passed |
| **S5** | BR-14 desactivada (`review/service.py` → `return False`) | `test_segregation_r143.py` | **DETECTED** — 3 failed / 3 passed |
| **S6** | Filtro de granja de Lotes eliminado | `qaYolinel.listColumns.test.tsx` | **DETECTED** — 1 failed / 2 passed |
| **S7** | `useCan` sin `useCallback` | `qaYolinel.red.test.tsx` | **NOT_DETECTED** en la 1.ª corrida ⇒ **DETECTED** tras IMPL-2: 1 failed / 22 passed |
| **S8** | `companies.tax_id` rotulado con `common.edit` | guardián de `qaYolinel.red.test.tsx` | **NOT_DETECTED** en la 1.ª corrida ⇒ **DETECTED** tras IMPL-2: 1 failed / 22 passed |

Detalle, interpretación de S6 y refuerzo IMPL-2 en `07_TEST_EVIDENCE.md` §3.

## 4. Bloque de estado final

```
QA_FINDINGS_TOTAL=18
ALREADY_COMPLIANT=4 (QA-001, QA-002 backend, QA-011, QA-016 event_date)
DEFECT=2 (QA-013, QA-017)
FUNCTIONAL_GAP=3 (QA-007 implementado BR-23; QA-009 matriz propuesta; QA-015 incubadora declarada)
UX_IMPROVEMENT=6 (QA-002 UI, QA-003 columnas, QA-012, QA-014, QA-016 max=hoy, QA-018)
DOCUMENTATION_CLARIFICATION=4 (QA-005, QA-006, QA-010, QA-011)
QA_MISUNDERSTANDING=0
OWNER_DECISION_REQUIRED=5 (QA-003 unicidad, QA-004, QA-008, QA-009, QA-016 otras fechas)
# nota: algunos hallazgos tienen doble clasificación; la suma supera 18
QA-001=DOCUMENTADO — no hay FK granja→unidad; la cadena se deriva del lote
QA-002=IMPLEMENTADO — Desactivar/Reactivar, columna Estado, fila atenuada y toast de error
QA-003=OWNER_DECISION (OD-QA2-01) — unicidad de vacunas/medicamentos/causas
QA-004=OWNER_DECISION (OD-QA2-02) — zona/área en plantas de incubación
QA-005=DOCUMENTADO — maestros SAP: RAW → validación → mapeo → staging → referencias
QA-006=DOCUMENTADO — `lots.origin`: NATIVE / MIGRATED; SAP nunca crea lotes
QA-007=IMPLEMENTADO — BR-23: cadena de la OC vs cadena del lote (400 si discrepan)
QA-008=OWNER_DECISION (OD-QA2-03) — autocompletado adicional desde la OC
QA-009=OWNER_DECISION (OD-QA2-04) — predecesores: matriz propuesta, sin backend
QA-010=DOCUMENTADO — máquina de estados: rechazo, cancelación y reversa con guardas
QA-011=DOCUMENTADO — BR-14 / RR-03: segregación configurable por paso
QA-012=IMPLEMENTADO — columna del padre (Granja/Planta) en galpones, equipos y nacedoras

QA-013=IMPLEMENTADO — claves de columna propias + guardián de los 20 maestros
QA-014=IMPLEMENTADO — `farm_name`/`lot_code`/`registered_by_name`; columnas Lote/Granja/Fecha del evento/Registrado por/Fecha de registro en Lotes, Historial, Mis pendientes, Centro de Revisión y Aprobaciones; incubadora = brecha de QA-015
QA-015=IMPLEMENTADO (filtro Granja en Lotes, Historial, Aprobaciones y Centro de Revisión) + FUNCTIONAL_GAP (incubadora: no existe `hatchery_id`)
QA-016=IMPLEMENTADO parcial (`event_date` con `max=hoy`); otras fechas = OWNER_DECISION
QA-017=IMPLEMENTADO — `useCan` memoizado; sin REQUEST_LOOP (1 `GET /review/pending`)
QA-018=IMPLEMENTADO — «Registrado por» y «Fecha de registro» (distinguidas de la fecha del evento) en Centro de Revisión y Aprobaciones
P0_FIXED=0
P1_FIXED=3 (QA-007, QA-013, QA-017)
UX_FIXED=6
DOCUMENTATION_UPDATED=YES
REPRODUCTORAS_READY_FOR_DETAILED_QA=YES (plan entregado; condicionado a dataset en runtime)
HATCHERY_READY_FOR_DETAILED_QA=YES (filtro por planta = brecha declarada)
BREEDER_TO_HATCHERY_FLOW_READY=YES (RP-13 → IN-01)
SAP_REAL_TEST=PENDING_2026_10_20
REAL_SAP_CALLS=0
REAL_SAP_WRITES=0
QA_DATASET=PRESENT_IN_REPO_NOT_LOADED_IN_RUNTIME (BLOCKED_EXTERNAL)

BACKEND_TARGETED=118 passed
BACKEND_FULL=1739 passed · 0 failed · 49 skipped
BACKEND_FULL_POST_MUTATION=1739 passed · 0 failed · 49 skipped (23 min 17 s; idéntica a la pre-mutación)
FRONTEND=557/557 (pre) · 576/576 (post, IMPL-2)
TSC=PASS
BUILD=PASS
E2E=64/64 afectados (10 specs) + spec SPEC 008 8/8 passed (A–H, 35 s)
MUTATION=5/5 DETECTED (S7/S8 tras IMPL-2)
RUNTIME=NOT_VERIFIED_FROM_WORKSTATION
QA_RESPONSE_DOC=docs/RESPUESTA_REVISION_GENERAL_QA_YOLINEL_2026_10_17.docx
QA_PLAN_DOC=docs/PLAN_QA_REPRODUCTORAS_INCUBADORA.docx
STATE_FLOW_DOC=docs/FLUJO_DE_ESTADOS_GLOBAL_AVICOLA.docx
IMPLEMENTATION_SHA=dbd6122a3b32512cf8bf2ae6b4f7b91cf43a9124 (+ IMPL-2 9390afcad3ca57dcea17d8065054978abe1a0720)
CERTIFICATION_SHA=68d78fcb8ac65c206d46f1ef0e87198301cdbc94
REMOTE_SHA=68d78fcb8ac65c206d46f1ef0e87198301cdbc94
REMOTE_SHA_MATCH=PASS
TREE=limpio (solo archivo local de credenciales del arnés sin versionar)
FINAL_STATUS=LOCALLY_CERTIFIED_RUNTIME_BLOCKED_EXTERNAL
```

Los veredictos de `QA-001`…`QA-018` provienen de `05_FIX_PLAN.md` §1. `P1_FIXED` cuenta los defectos de prioridad 1;
`UX_FIXED` agrupa las correcciones de usabilidad que no cambian contrato.

## 5. Pendientes para el Owner

| ID | Pendiente | Efecto |
|---|---|---|
| **OD-QA2-01** | ¿Nombre único por empresa y/o código en vacunas, medicamentos y causas? (QA-003) | Se mantiene la identidad por nombre; riesgo de homónimos duplicados |
| **OD-QA2-02** | Zona/área en plantas de incubación (QA-004) | Las plantas siguen clasificándose solo por `location` (texto) |
| **OD-QA2-03** | Autocompletado adicional desde la OC SAP (QA-008) | Granja/galpón/lote/transporte siguen siendo manuales |
| **OD-QA2-04** | Predecesores de proceso: ¿bloqueante o aviso? ¿severidad? (QA-009) | La UI avisa, el backend no impide registrar fuera de orden |
| **OD-QA2-05** | Fechas distintas de la del evento (QA-016): ¿cuáles se limitan a hoy? | Solo `event_date` recibe `max=hoy` |

Además:

- **PDF original de QA** — «REVISION GENERAL DE SISTEMA GLOBAL AVICOLA - 17-10-2026.pdf» no disponible en la
  estación: los 18 hallazgos se trabajaron desde el mandato del Owner y quedan **pendientes de contraste**.
- **Ejecutar el runbook QA-DEMO-V1** — `audit/qa-integral-dataset/09_RUNTIME_VERIFICATION.md`
  (dataset presente en el repo, **no cargado** en runtime: `BLOCKED_EXTERNAL`).
- **Verificación UAT** — checklist de `08_RUNTIME_VERIFICATION.md`, con datos reales en el entorno desplegado.
- **Reiniciar el MCP** para cargar `server.py` y exponer las herramientas actualizadas.

## 6. Nota E2E

Los flujos E2E certificados en la ronda anterior **no cambian de contrato**: los campos nuevos del contrato de
lectura (`farm_name`, `house_name`, `lot_code`, `registered_by_name`, `business_unit_code`, `chain_known`) y las
nuevas props de `DataTable` (`rowClassName`, `RowAction.visible`) son **aditivos y opcionales**; ningún campo
existente se renombró ni se eliminó. La UI se verificó con **jsdom** (`npx vitest run`: 576/576) y con `tsc -b` y
`vite build` en verde, por lo que el recorrido E2E no se re-ejecutó (`E2E=NOT_RUN`): el cierre funcional extremo a
extremo queda cubierto por la verificación UAT con el checklist de `08_RUNTIME_VERIFICATION.md`.

## 8. Verificación runtime UAT (2026-10-18)

Sonda Playwright headless y comprobaciones por API contra `https://avicola.globaldv.net` con las credenciales
efímeras de **GA-UAT-09** (operador y aprobador de Progenitoras). Evidencia: `evidence/14_uat_runtime_probe.log`,
`evidence/15_uat_br14_state_machine.log`, `evidence/uat_screens/*.png`, `evidence/13_e2e_affected_raw.log`,
`evidence/13_e2e_spec008_raw.log`.

```
UAT_RUNTIME_FOUND=YES
UAT_SHA=68d78fc (código) / c436811 (docs)
UAT_SHA_MATCH=PASS
QA_DATA_PRESENT_BEFORE=NO
QA_DATA_DRY_RUN=BLOCKED_EXTERNAL
QA_DATA_APPLY=BLOCKED_EXTERNAL
QA_DATA_VERIFY=BLOCKED_EXTERNAL
QA_DATA_IDEMPOTENCY=BLOCKED_EXTERNAL
QA_CLEANUP=READY_NOT_EXECUTED
QA_USERS_RUNTIME=PARTIAL (solo UAT-09 progenitoras; sin qa.*)
RUNTIME_3_1..3_5=PASS
RUNTIME_3_6=PASS (UI) / BR-23 API NOT_TESTABLE_IN_UAT
RUNTIME_3_7=PASS_READONLY
RUNTIME_3_8=PASS
BR14_RUNTIME=PASS (por permiso)
STATE_MACHINE_RUNTIME=PASS
REVIEW_REQUEST_LOOP=NOT_PRESENT
E2E_SPEC008=8/8 passed (A–H, 35 s)
E2E_AFFECTED=64/64
BREEDER_RUNTIME_SMOKE=BLOCKED_EXTERNAL
HATCHERY_RUNTIME_SMOKE=BLOCKED_EXTERNAL
BREEDER_TO_HATCHERY_RUNTIME=BLOCKED_EXTERNAL
UNKNOWN_CHAIN_OC=ALLOWED_CURRENTLY_OWNER_DECISION_PENDING
REAL_SAP_CALLS=0
REAL_SAP_WRITES=0
FINAL_STATUS=LOCALLY_CERTIFIED_RUNTIME_BLOCKED_EXTERNAL
```

Lectura: el **código** de la ronda SPEC 008 está desplegado y verificado en UAT (8 PASS, 0 FAIL); lo que queda fuera
es **externo al repositorio**: la carga del dataset QA-DEMO-V1 (misma `ConnectionResetError` en el handshake SSL que
en SPEC 007 ⇒ ejecutar el runbook en el host del backend), los usuarios `qa.*` y la prueba real de SAP del
2026-10-20. `BR14_RUNTIME=PASS` se sostiene en el **bloqueo por permiso del rol** (el operador recibe 403
`approvals:approve`); la variante estricta registrador≠aprobador sigue cubierta por `test_segregation_r143`.

## 9. Cierre

```
CERT_SHA=68d78fcb8ac65c206d46f1ef0e87198301cdbc94
PUSH_SSH=git push git@github.com:dvconsultores/GlobalAvicola.git main:main (83c9cd8..68d78fc)
LOCAL_SHA=68d78fcb8ac65c206d46f1ef0e87198301cdbc94
REMOTE_SHA=68d78fcb8ac65c206d46f1ef0e87198301cdbc94
REMOTE_SHA_MATCH=PASS
TREE=limpio (solo archivo local de credenciales del arnés sin versionar)
```

Nota: el commit CLOSE registra estos SHAs; su propio SHA se publica en el push de cierre.

