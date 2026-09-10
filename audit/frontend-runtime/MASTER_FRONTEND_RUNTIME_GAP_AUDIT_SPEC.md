# MASTER FRONTEND + DEPLOYED RUNTIME GAP AUDIT — SPEC

`audit/frontend-runtime/` · **2026-09-10** · **MODO AUDIT ONLY — sin remediación de producto**

---

## 1. Propósito

Auditar **el producto que un usuario autorizado realmente ve y puede utilizar hoy**: confrontar
lo que el producto promete (SPEC / Owner Decisions / requisitos) contra el backend implementado,
el frontend del repositorio, el frontend desplegado en el runtime compartido y el flujo de
usuario autenticado — y clasificar cada capacidad visible al usuario con **exactamente uno** de
seis estados de producto.

```
SPEC  vs  BACKEND  vs  FRONTEND REPO  vs  DEPLOYED FRONTEND  vs  AUTHENTICATED USER FLOW
```

Esta auditoría **no es** de backend, ni de tests, ni de endpoints aislados. Es de **producto**.

### Pregunta que debe responder (§0 del encargo)

¿El usuario realmente ve, encuentra y puede usar las capacidades ya certificadas técnicamente?
No asumir que sí.

### Principio de certificación adoptado

```
BACKEND IMPLEMENTED  ≠  PRODUCT IMPLEMENTED
API GREEN            ≠  USER FEATURE AVAILABLE
FRONTEND CODE EXISTS ≠  FEATURE EXPOSED
LOCAL FRONTEND       ≠  DEPLOYED FRONTEND
DIRECT URL           ≠  FEATURE DISCOVERABLE
VISIBLE BUTTON       ≠  FUNCTIONAL FLOW
TECHNICAL CERT      ≠  RUNTIME CERTIFICATION
RUNTIME CERT        ≠  USER ACCEPTANCE
```

---

## 2. Baseline auditado (reconciliado)

| Dato | Valor reportado del encargo | Valor real verificado | Delta |
|---|---|---|---|
| Rama | `main` | `main` | — |
| HEAD | `6ffd73c` | **`3808ed5`** | +3 commits (tranche 14) |
| Remote HEAD | local == remote | `3808ed5` == `3808ed5` | — |
| Worktree | limpio | limpio (0 ficheros) | — |
| Origin | HTTPS | `https://github.com/dvconsultores/GlobalAvicola.git` | — |

Los 3 commits del delta son el tranche 14 de WAVE B (`d9ff4bd` spec · `8a9f3cc` implementación ·
`3808ed5` evidencia) — completado **después** de redactarse este encargo; la base es lineal,
documentada, limpia y publicada. Se audita contra la verdad actual del repositorio (`3808ed5`) y
se registra la reconciliación. Sin ambigüedad de base.

- Entorno desplegado: `ENV-01` → **SHARED DEVELOPMENT/TEST/CERTIFICATION**, URL canónica
  `https://avicola.globaldv.net`. No es producción real.
- Alembic cabeza: `x4y5z6a7b8c9`. Rutas backend: 211.
- WAVE B: 36 ítems canónicos · 24 cerrados · 4 parciales · 8 abiertos (P1 0).
- Fase 9 (`GA-REM-040`, interfaz de unidades): `TECHNICALLY READY · FROZEN`.

---

## 3. Alcance

### Dentro

- Inventario de capacidades prometidas al usuario (§17 del encargo: áreas A–AS).
- Inventario backend (solo como proveedor del frontend, no se re-certifica).
- Inventario frontend: rutas, páginas, navegación, guards, contextos de empresa/unidad, componentes muertos.
- Fingerprint del build local vs el artefacto desplegado (read-only).
- Auditoría de navegador contra el runtime desplegado (hasta donde autoricen las credenciales).
- Clasificación de cada capacidad visible con uno de los seis estados.
- Reconciliación de certificaciones técnicas previas con la realidad de producto.
- Matriz de brechas, grupos de causa raíz, mapa de dependencias y roadmap maestro.

### Fuera (prohibido en esta auditoría)

- NO corregir el producto: sin pantallas, menús, rutas, endpoints, permisos, deployment, UI.
- NO tocar Watchtower, `latest`, CI/CD, Docker, Nginx, auto-deploy, DNS ni proxy.
- NO mutar el runtime; NO reiniciar contenedores; NO limpiar datos.
- NO reescribir evidencia histórica; solo añadir capa de reconciliación.
- NO mutation testing (el checkpoint de mutación del programa queda como gobernanza, no se usa aquí).

### Implementación permitida (únicamente)

Scripts/pruebas de auditoría, captura de evidencia, matrices, documentación, builds locales de
comprobación (sin commit de artefactos), sondas HTTP `GET` sin autenticar, sesiones de navegador
read-only. **Cero código de producto.**

---

## 4. Fuentes autoritativas (jerarquía aplicada)

```
SPEC  >  OWNER DECISIONS  >  AC  >  TASK  >  PROMPT  >  CÓDIGO ACTUAL
```

y para producto:

```
CAPACIDAD PROMETIDA  >  BACKEND IMPLEMENTADO  >  FRONTEND IMPLEMENTADO  >  FRONTEND DESPLEGADO  >  FLUJO REAL
```

Fuentes leídas para esta auditoría (todas del repositorio, HEAD `3808ed5`):

| Fuente | Rol |
|---|---|
| `specs/remediation/OD-09…OD-19` | decisiones del propietario vigentes |
| `specs/remediation/OD-16` | alcance productivo: 4 unidades · activación por empresa · encender ≠ conceder |
| `specs/remediation/GA-REM-040` (+ fases 1–8, enmiendas G/H) | control de acceso por unidad; fase 9 = interfaz |
| `audit/remediation/PHASE_9_DEPENDENCY_PREFLIGHT.md` | qué es la fase 9, dependencias, bloqueo retirado, congelación |
| `audit/remediation/REMEDIATION_BACKLOG.md` | registro canónico R-1…R-180 |
| `audit/remediation/WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md` | estado de ola y tranches |
| `audit/remediation/POST_PUSH_PRODUCTION_STATE_REPORT.md` | R-99, mediciones del runtime compartido |
| `audit/remediation/FRONTEND_SCREEN_IMPLEMENTATION_MATRIX.md` | inventario de pantallas (auditoría 360) |
| `audit/remediation/FRONTEND_ROUTE_MODULE_MATRIX.md` | rutas vs unidad de negocio |
| `audit/remediation/MASTER_PROGRAM_STATUS_RECONCILIATION.md` | estado 360 del programa |
| `audit/remediation/AUDIT_OWNER_DECISIONS_REQUIRED.md` | registro AOD |
| `specs/remediation/ENV-01-ENVIRONMENT-CLASSIFICATION.md` | clasificación del entorno |
| `docs/02-functional-spec.md` §3.1.x/§3.14 | requisitos de UI de producto |
| Código `frontend/src` · `backend/app` (HEAD) | verdad de implementación |
| Runtime `avicola.globaldv.net` (read-only) | verdad desplegada |

Clasificación de fuentes: `ACTIVE` (las anteriores) · `HISTORICAL` (informes de waves ≤ 3,
auditorías 360) · `SUPERSEDED` cuando `H360_AND_ADDENDUM_TO_OFFICIAL_BACKLOG_RECONCILIATION`
lo declara. Ningún documento histórico se usa como contrato actual sin verificación.

---

## 5. Los seis estados de producto (definición estricta)

1. **IMPLEMENTED_AND_VISIBLE** — solo con: spec clara, backend, frontend, desplegado,
   descubrible sin URL manual, flujo iniciable y completable, persistencia, refresh, relogin,
   denegación a no autorizados, runtime sin error y **evidencia de navegador**.
2. **IMPLEMENTED_BUT_NOT_EXPOSED** — frontend suficiente existe y backend existe, pero el
   usuario autorizado no la encuentra (navegación, menú, guard, enlace, rol, unidad, wiring o
   exposición incompleta). URL directa puede funcionar.
3. **FRONTEND_MISSING** — la capacidad requiere interfaz humana y no existe frontend
   suficiente para ejecutar el flujo.
4. **DEPLOYMENT_STALE** — con prueba fuerte: el frontend actual del repo contiene la
   capacidad, el build local la contiene, y el runtime sirve una versión anterior; la
   diferencia NO es de rol/empresa/unidad ni de caché de cliente.
5. **BROKEN_FLOW** — el usuario ve el inicio y no puede completar (botón inerte, guard
   equivocado, contrato divergente, 403 a autorizado, 500, loading infinito, no persiste).
6. **OWNER_DECISION_REQUIRED** — la expectativa no está definida en SPEC/OD (o hay dos
   contratos incompatibles). No se usa para evitar investigar.

### Precedencia

```
1. expectativa indefinida      → OWNER_DECISION_REQUIRED
2. local completo / runtime viejo → DEPLOYMENT_STALE
3. sin frontend suficiente      → FRONTEND_MISSING
4. frontend existe, no expuesto → IMPLEMENTED_BUT_NOT_EXPOSED
5. visible pero falla           → BROKEN_FLOW
6. todo funciona                → IMPLEMENTED_AND_VISIBLE
```

`SECONDARY_GAPS` se registran sin alterar el estado primario.

### Capacidades bloqueadas por credenciales

Las capacidades cuyo **único** hueco de evidencia sea la verificación autenticada contra el
runtime (sin defecto conocido) no reciben estado primario inventado: se registran como
`BLOCKED_AUTHENTICATED_VERIFICATION` **fuera** del conteo de los seis estados, con el bloqueo
`AUTHENTICATED_RUNTIME_BLOCKER` (§38 del encargo), y se solicita la cuenta al propietario.
No es un séptimo estado: es una fila pendiente de ejecución de la fase 7 del plan.

---

## 6. Actores, empresas y unidades a cubrir

Actores (semántica, no solo nombre — §40):

| Actor | Rol de negocio | Base |
|---|---|---|
| Global / Super Admin | autoridad global, sin empresa efectiva | `OD-14` |
| Administrador de Accesos | administra usuarios y unidades de su empresa; no se sirve a sí mismo | `OD-15` |
| Contraloría (Contralor Avícola) | aprueba/rechaza/audita; lee reversos | `OD-19` Aclar. A |
| Supervisor Avícola | revisa, corrige, solicita reverso | `GA-REM-007`, `GA-REM-041` |
| Operador de Granja | registra eventos de campo | `docs/02` |
| Usuario sin unidades (zero-BU) | usa el núcleo permitido; sin dato productivo | `OD-09.c` |

Unidades productivas (las cuatro, `OD-16.a`): `grandparent` (Progenitoras) · `breeder`
(Reproductoras) · `hatchery` (Incubadora) · `broiler` (Engorde).

Álgebra obligatoria (`OD-16`): encender empresa ≠ conceder usuario ≠ permiso RBAC ≠ pertenencia
del recurso. Casos: BU ON/grant OFF, BU OFF/grant ON, RBAC sin BU, BU sin RBAC, zero-BU.

---

## 7. Artefactos de salida (§108 del encargo, adaptados a `audit/frontend-runtime/`)

1. `MASTER_FRONTEND_RUNTIME_GAP_AUDIT_SPEC.md` (este documento)
2. `AUDIT_PLAN.md` · 3. `AUDIT_CHECKLIST.md` · 4. `AUDIT_TASKS.md`
5. `MASTER_PRODUCT_CAPABILITY_CATALOG.md`
6. `MASTER_FRONTEND_RUNTIME_GAP_MATRIX.md` + `.csv`
7. `BACKEND_CAPABILITY_MAP.md`
8. `FRONTEND_ROUTE_COMPONENT_MAP.md`
9. `NAVIGATION_ROLE_BU_MATRIX.md`
10. `FORM_API_CONTRACT_GAP_MATRIX.md`
11. `AUTHENTICATED_USER_JOURNEY_MATRIX.md`
12. `DEPLOYMENT_FRONTEND_FINGERPRINT.md`
13. `CERTIFICATION_SCOPE_RECONCILIATION.md`
14. `RUNTIME_CONSOLE_ERROR_SUMMARY.md`
15. `E2E_PRODUCT_COVERAGE_GAP.md`
16. `FRONTEND_REMEDIATION_DEPENDENCY_MAP.md`
17. `MASTER_FRONTEND_REMEDIATION_ROADMAP.md`
18. `MASTER_FRONTEND_RUNTIME_AUDIT_EVIDENCE.md`
19. `RUNTIME_SCREENSHOT_INDEX.md`
20. `evidence/` (capturas y artefactos)
21. Addendum fechado en `audit/remediation/REMEDIATION_BACKLOG.md` (reconciliación R-99/R-158;
    altas si proceden, con ID libre leído del backlog)
22. Dossiers de decisión del propietario — solo si aparecen expectativas indefinidas nuevas.

---

## 8. Criterios de cierre de la auditoría

- [ ] Todas las capacidades prometidas user-visible inventariadas y clasificadas (o bloqueadas por auth, contadas aparte).
- [ ] Invariante: TOTAL clasificable = suma de los seis estados; sin dobles estados primarios.
- [ ] Cada clasificación con evidencia: fuente spec + fuente código + fuente runtime (si aplica) + captura/red.
- [ ] R-98/R-99 buscados, verificados y deduplicados; regresiones referencian su cierre anterior sin reescribirlo.
- [ ] Reconciliación de certificaciones: cada cierre técnico relevante con su frontera aclarada.
- [ ] Journeys críticos J01–J18 clasificados (ejecutados o bloqueados con causa exacta).
- [ ] Grupos de causa raíz y roadmap con dependencias reales; primer tranche recomendado (NO iniciado).
- [ ] Cero modificaciones de código de producto (`git status` limpio salvo `audit/**`).
- [ ] Informe final con el formato exacto del encargo (§139).

## 9. Riesgos de la auditoría

| Riesgo | Mitigación |
|---|---|
| Sin credenciales del entorno compartido | `AUTHENTICATED_RUNTIME_BLOCKER` documentado; se solicita cuenta al propietario; no se adivina (§38) |
| Confundir caché del cliente con versión desplegada | fingerprint de servidor (`Last-Modified`, hash de asset) ya adjunto; §92 aplicado |
| Dar por bueno un cierre técnico backend como producto | regla de precedencia y reconciliación de frontera (§73/§119) |
| Inflar hallazgos duplicando R-98/R-99 | dedup obligatoria + registro fechado en backlog |
| Credenciales históricas en `GUIA_PRUEBAS_EN_VIVO.md` | prohibido usarlas contra el runtime (GA-REM-004 las rotó); política §38 |
