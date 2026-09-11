# MASTER FRONTEND + DEPLOYED RUNTIME AUDIT — EVIDENCE

**2026-09-10** · base auditada `3808ed5` · runtime `https://avicola.globaldv.net` (ENV-01, shared test/certification) · **AUDIT ONLY — cero código de producto modificado**.

---

## 1. Baseline

| Dato | Reportado en el encargo | Verificado |
|---|---|---|
| Rama / HEAD local | `main` / `6ffd73c` | `main` / **`3808ed5`** (+3 commits: tranche 14) |
| Remote | local == remote | `3808ed5` == `3808ed5` (ls-remote) |
| Worktree | limpio | limpio |
| Origin | HTTPS | `https://github.com/dvconsultores/GlobalAvicola.git` |
| WAVE B | — | 36 canónicos · 24 cerrados · 4 parciales · 8 abiertos |
| Alembic / rutas | — | `x4y5z6a7b8c9` / 211 |

## 2. Alcance de la auditoría

Cinco capas: SPEC · backend · frontend repo · frontend desplegado · flujo de usuario autenticado. Sin remediación. Procedimiento completo en `MASTER_FRONTEND_RUNTIME_GAP_AUDIT_SPEC.md` + `AUDIT_PLAN.md`.

## 3. Metodología

Spec Development aplicado: SPEC → CLARIFY → PLAN → CHECKLIST → TASKS → ANALYZE → IMPLEMENT (arnés de auditoría) → EXECUTE → EVIDENCE → CLASSIFY → CONVERGE → ROADMAP. Controles: Vitest 108/108 · `tsc -b` 6 errores · build local OK · worktree temporal por commit · sondas HTTP read-only · bundle diff · sesión de navegador.

## 4. Inventario de fuentes

`specs/remediation/OD-09…OD-19` · `GA-REM-001…042` · `REMEDIATION_BACKLOG.md` (R-1…R-180) · `WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md` · `POST_PUSH_PRODUCTION_STATE_REPORT.md` (+addenda R-99) · `PHASE_9_DEPENDENCY_PREFLIGHT.md` · `MASTER_PROGRAM_STATUS_RECONCILIATION.md` · `FRONTEND_SCREEN_IMPLEMENTATION_MATRIX.md` · `FRONTEND_ROUTE_MODULE_MATRIX.md` · `E2E_TEST_INVENTORY.md` · `ENV-01` · `docs/02` · código `frontend/src` y `backend/app` · runtime. Clases: ACTIVE/HISTORICAL/SUPERSEDED — nadie usa un histórico como contrato sin verificación.

## 5. Catálogo de capacidades

`MASTER_PRODUCT_CAPABILITY_CATALOG.md` — **38 capacidades user-visible** (23 clasificadas + 15 bloqueadas por auth) + 7 capacidades internas fuera de conteo.

## 6. Inventario backend

`BACKEND_CAPABILITY_MAP.md` — 211 rutas; familias de negocio vivas en el runtime (401/405), incluidas las de fase 7–8, clasificación pendiente y reverso.

## 7. Inventario frontend

`FRONTEND_ROUTE_COMPONENT_MAP.md` — 33 rutas declaradas (29 efectivas + redirects); guards: `ProtectedRoute` (sesión + rama `roles` **muerta**), `WebOnlyRoute` (view_type); 0 `hasPermission`; stores `auth`/`company`; nav estático.

## 8. Fingerprint desplegado

`DEPLOYMENT_FRONTEND_FINGERPRINT.md` — artefacto servido **2026-09-05 14:09:27 GMT** (`index-D5dwMXuP.js`, sha256 `4eb822a5…`); local `index-Cl0MIg8E.js` (`5afa1a37…`); causas: ver §22.

## 9. Autenticación / usuarios

`AUTHENTICATED_RUNTIME_BLOCKER`: sin cuentas autorizadas del shared (GA-REM-004 rotó las históricas; prohibido usar seeds contra el shared). Deep links sin sesión → `/login` (correcto). Captura: `AUDIT_001_DEPLOYED_LOGIN.png`.

## 10. Contexto de empresa

Store + dropdown super_admin presentes en repo y bundle (desde jun-2026); condición de render `activeCompanyName || company_name`; `catch{}` silencioso; `/switch-company` 405 (existe). Clasificación: `IMPLEMENTED_BUT_NOT_EXPOSED`. Detalle en `EVIDENCE §10` → matriz.

## 11. Unidades por empresa (BU admin)

0 referencias en frontend (ni local ni desplegado); backend desplegado (401). Fase 9 `T-040-21` congelada por autorización del propietario. **FRONTEND_MISSING**.

## 12. Unidades por usuario (grant/revoke)

0 referencias; backend listo (`grant-candidates` sin `users:read`, `R-129` cerrado). **FRONTEND_MISSING**.

## 13. Roles y permisos

`RolesPage` local (09-06) **ausente del bundle servido**: `/roles` 1→7 refs, router servido sin la ruta. **DEPLOYMENT_STALE**. Asignación de rol en formulario: presente.

## 14. Navegación

`NAVIGATION_ROLE_BU_MATRIX.md` — menú estático para todos; 0 gating; `/poultry/:birdType` lleva la unidad en la URL; fase 9 `T-040-23` sin construir. **FRONTEND_MISSING**.

## 15. Dashboard

Presente en ambos bundles; funcionalidad pendiente de auth. Sin superficie de unidades/empresa más allá del badge.

## 16. Progenitoras

Hub/etapas presentes; **importación con plan tipado: local sí, runtime no** — y la UI servida **produce 400 BR-22** contra el backend nuevo. **DEPLOYMENT_STALE** + ruptura vigente.

## 17. Reproductoras

Recepción con cuadre B01/rendimiento B02: local sí; runtime no → **400 BR-20** con la UI servida. **DEPLOYMENT_STALE** + ruptura.

## 18. Incubadora

Nacimiento → **400 BR-21** (UI vieja × backend nuevo); catálogo sin mortalidad/descarte (local R-171); despacho con riesgo 400 (BR-02). **DEPLOYMENT_STALE** + rupturas.

## 19. Engorde

Captura presente; agua (B05) sin captura en runtime (local sí). Evidencias con R-52 (volumen no montado → efímeras).

## 20. Maestros

20 entidades locales (19 + áreas); runtime sirve 13/20 (`/masters` 30→39). **DEPLOYMENT_STALE**.

## 21. Operaciones (formularios)

`FORM_API_CONTRACT_GAP_MATRIX.md` — tabla de divergencias; las tres rupturas P1 y el detalle de campos.

## 22. Causa raíz de la congelación (R-99) — demostrada

```
frontend/Dockerfile: RUN npm run build  =  tsc -b && vite build
f46cb13 (09-05 16:08, artefacto servido): tsc GREEN (worktree, exit 0)
4386f87 (09-06 03:36): elimina pestañas de AuditPage y deja User/Database sin uso → 2×TS6133 → tsc RED
950bb21 (09-07): +4 errores (LotFormPage áreas/tupla) → 6 errores
15/15 commits de frontend posteriores: tsc RED  →  Docker build falla SIEMPRE → sin imagen → Watchtower sin novedad
```
No es caché (§92 descartado), no es Watchtower (el backend sí se despliega), no es "tsc preexistente" como excusa: **los 6 errores SON el bloqueo**.

## 23. Correcciones

`POST /operations/{id}/submit` (R-135) y corrección de devueltos: backend desplegado; corrección tiene UI; **el reenvío explícito no tiene control UI** (servicio sin llamadores) → **R-181** (nuevo).

## 24. Reversos

Backend desplegado (401); UI diferida a fase 9 por el propio programa (`GA-REM-041 §10`, evidencia R-136). **FRONTEND_MISSING** (gobernada).

## 25. Evidencias

Subida/descarga presentes; R-52 (volumen) sigue pendiente y hace las evidencias efímeras en el shared.

## 26. Formularios vs contratos

Ver §21 y `FORM_API_CONTRACT_GAP_MATRIX.md`.

## 27. Errores de runtime

`RUNTIME_CONSOLE_ERROR_SUMMARY.md` — sin errores en la superficie pública; consola autenticada pendiente.

## 28. Comportamiento de ruta directa

Sin sesión: `/roles` `/masters/weight-curves` `/notifications` `/poultry/hatchery` `/review` → todas `/login` (esperado). Con sesión: pendiente de auth. En el runtime servido, `/roles` no existe como ruta (router viejo).

## 29. Responsive

No re-verificado visualmente (bloqueado auth). El código local incluye paridad responsive de fase 9 pendiente (`AC-H09` sin construir).

## 30. R-98 / R-99

- **R-98**: vigente — 0 `hasPermission`; menú estático; `ProtectedRoute.roles` muerto. Es el trabajo de `T-040-23`.
- **R-99**: vigente y **re-medido hoy**: artefacto congelado; causa raíz demostrada; 15 entregas afectadas; 3 flujos rotos. Addendum en backlog.

## 31. Reconciliación de certificaciones previas

`CERTIFICATION_SCOPE_RECONCILIATION.md` — frontera técnica vs producto; 11 filas reconciliadas; sin reescribir historia.

## 32. Hallazgos

- **Reusados**: R-98, R-99, R-119, R-120, R-122, R-124, R-127, R-140, R-150, R-153, R-158, R-44, R-52, R-112, R-176, R-181(no)…
- **Nuevo**: **`R-181`** — el reenvío/envío explícito a revisión no tiene control UI (detalle abajo, §34).
- **Sin duplicados**: dedup realizada contra R-98/R-119/R-135/R-140 y gobernanza de fase 9.

## 33. Conteo de seis estados (§139) — ver informe final. Invariante verificado por `generate_gap_matrix.py`.

## 34. R-181 (nuevo) — dossier del hallazgo

```
ID            R-181 (siguiente libre tras R-180; sujeto a ratificación del programa)
TÍTULO        El envío/reenvío explícito a revisión (POST /operations/{id}/submit) no tiene
              control en la interfaz: operationsService.submit sin llamadores en todo el historial
SEVERIDAD     P2 (flujo de producto relevante sin gesto UI; la cola de revisión incluye REGISTERED,
              de modo que el ciclo no queda muerto, pero «Operador reenvía» de docs/12 §2 no es ejecutable)
RAÍZ          vertical de UI nunca cableada (distinta de R-98/R-119: no es permisos; de R-135: backend cerrado)
REQUISITO     docs/12 §2 («Devuelto → Operador reenvía»; «Rechazado → Operador reenvía (corregido)»)
              · OD-17.b · spec §4.10
EVIDENCIA     grep /submit en frontend/src → solo la definición · 0 refs en bundle desplegado
              · E2E proceso-03/p06/p14 invocan la API directamente · sin claves i18n
BACKEND       IMPLEMENTED y desplegado (401) — nada que hacer
FRONTEND      control «Enviar a revisión / Reenviar» en detalle + móvil (y feedback de estado)
DEPENDENCIAS  ninguna (no fase 9, no decisión)
OLA           E (frontend) — puede viajar con T-040-23
```

## 35. Grupos de causa raíz

G7 paridad de despliegue · G2/G3/G6 fase 9 · G5 navegación/RBAC+submit · G4 exposición del selector · G1 decisión de empresas · G0 verificación autenticada · G8 guardia de paridad. (`FRONTEND_REMEDIATION_DEPENDENCY_MAP.md`).

## 36. Decisiones del propietario

| Decisión | Estado | Impacto en este alcance |
|---|---|---|
| Autorización de fase 9 | **pendiente** (`FROZEN`) | G2/G3/G4/G6 |
| `AOD-06`/`R-124` empresas | pendiente | G1 |
| `AOD-25`/`R-153` lote automático | pendiente | Tranche 4 |
| `BU-D07` comercial vs operativo | pendiente | diseño fino del selector (no bloquea) |
| `BU-D10` reactivación | `PENDING_RATIFICATION` | posible 2.º control en la pantalla BU |

Ningún OD nuevo hace falta para el Tranche 1.

## 37. Roadmap

`MASTER_FRONTEND_REMEDIATION_ROADMAP.md` — 5 tranches propuestos; **T1 = `GA-FE-01` paridad de despliegue** (cero decisiones, riesgo mínimo, desbloquea todo lo demás).

## 38. Primer tranche recomendado

**`GA-FE-01 · Paridad de despliegue (R-99 recovery)`** — eliminar los 6 errores TS (`R-158`), build verde, despliegue normal, verificación por fingerprint y smoke de BR-20/21/22. **No iniciado.**

## 39. Limitaciones y bloqueos

1. `AUTHENTICATED_RUNTIME_BLOCKER` — 15 capacidades + journeys pendientes de cuentas autorizadas (solicitar al propietario: Super Admin, Adm. de Accesos, Supervisor, Operador, Contraloría, multiempresa, zero-BU).
2. Registros del workflow de CI no accesibles (`gh` ausente): la causa raíz no depende de ellos (reproducida localmente).
3. Sin SSH/BD: nada de contenedores; ya documentado por el programa.
4. La rama `origin/main` local estaba desactualizada (34 commits de retraso en la ref cache); el remoto real == local (verificado por `ls-remote`). No afecta al resultado.

## 40. Veredicto final

```
BACKEND TECHNICAL FOUNDATION .... STRONG (211 rutas vivas; WAVE B 24/36; nada tocado aquí)
FRONTEND REPOSITORY COVERAGE .... PARTIAL (operativo completo; shell multiempresa ausente; 1 vertical sin UI)
DEPLOYED FRONTEND PARITY ........ STALE (15 entregas; causa raíz demostrada)
AUTHENTICATED USER FLOW ......... MAJOR_GAPS (15 capacidades sin verificación; 3 flujos rotos en runtime)
MULTI-COMPANY UX ................ MISSING (selector parcial; administración inexistente)
BUSINESS UNIT ADMIN UX .......... MISSING (fase 9)
USER BU ADMIN UX ................ MISSING (fase 9)
DYNAMIC NAVIGATION .............. MISSING (R-98/R-119/T-040-23)
FOUR-BU PRODUCTIVE UX ........... PARTIAL (superficies presentes; adaptación y entregas nuevas no desplegadas)

PRODUCT OVERALL ..... READY_FOR_FRONTEND_REMEDIATION
  razón: la brecha está localizada, medida y ordenable: T1 (paridad, sin decisiones) devuelve
  el producto entregado a la vista; T2 (fase 9 con autorización) construye el shell multiempresa;
  T3 cierra navegación/controles. El backend requerido ya está desplegado y certificado en su frontera.
```

## 41. Evidencia adjunta

`DEPLOYMENT_FRONTEND_FINGERPRINT.md` · `MASTER_FRONTEND_RUNTIME_GAP_MATRIX.md/.csv` · `evidence/BUNDLE_HASHES.txt` · `evidence/AUDIT_001_DEPLOYED_LOGIN.png` · `RUNTIME_SCREENSHOT_INDEX.md` · `RUNTIME_CONSOLE_ERROR_SUMMARY.md` · addendum fechado en `REMEDIATION_BACKLOG.md`.

## 42. Cierre del inventario (2026-09-11)

La **FINAL FRONTEND AUDIT RECONCILIATION** (paquete `audit/final-frontend-audit/`: inventario original
FVA/FIA, matrices 38/7, recuperación de las 15 auth-bloqueadas, trazas de certificación/aceptación, rutas,
navegación, acciones, ledger, capturas S01-S21, red saneada, residuales RES-01…RES-10 y reporte §64) deja
la instantánea de este hogar **reconciliada al día**: 38/38 visibles · 7/7 internas · 15/15 recuperadas;
veredicto **RECONCILED_WITH_RESIDUALS** (0 missing/stale/broken aplicables; 0 unknowns). La instantánea
histórica original (conteos y clasificaciones) **no se reescribe**.
