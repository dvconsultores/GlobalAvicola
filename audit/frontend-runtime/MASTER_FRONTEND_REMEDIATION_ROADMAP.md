# MASTER FRONTEND REMEDIATION ROADMAP

**2026-09-10** · base `3808ed5` · **NO iniciado** — este documento propone; no implementa.

Orden derivado de la evidencia (§90 del encargo), no predeterminado. La primera pregunta es «¿qué debe existir para que el propietario entre y vea un producto coherente?».

## Tranche 1 — `GA-FE-01 · Paridad de despliegue (R-99 recovery)` ← PRIMERO RECOMENDADO

| Campo | Valor |
|---|---|
| **Resultado para el usuario** | Todo lo entregado desde el 2026-09-05 vuelve a ser visible (roles, maestros, curvas, notificaciones, áreas, agua, plan de abuelas, cuadre B01, B13, catálogo de incubadora) **y los tres flujos hoy rechazados dejan de dar 400** (BR-20/21/22) |
| **Findings** | `R-99` (causa raíz demostrada) · `R-158` (los 6 errores que rompen `npm run build`) |
| **Estado actual** | Artefacto congelado; toda entrega de frontend falla en CI en `RUN npm run build` |
| **Backend listo** | Sí — ni un cambio |
| **Trabajo frontend** | Eliminar 6 errores TS (2 imports sin uso en `AuditPage.tsx`; `areas/setAreas/areaRes` + índice de tupla en `LotFormPage.tsx`); `npm run build` verde |
| **Rutas/componentes** | Sin cambios funcionales |
| **Integraciones API** | Ninguna nueva |
| **Navegación** | Sin cambios |
| **RBAC/BU** | Sin cambios |
| **E2E requerido** | Comparación de fingerprint (hash del bundle servido vs `main`) + smoke de BR-20/21/22 |
| **Decisiones del propietario** | **NINGUNA** |
| **Dependencias** | Ninguna |
| **Riesgo** | Mínimo (compilación, no lógica) |
| **Puerta de cierre** | `npm run build` verde en CI · artefacto servido ≠ 09-05 · los tres flujos dejan de devolver 400 con datos de auditoría · R-99 cerrado con evidencia |

## Tranche 2 — `GA-FE-02 · Autorización y construcción de la fase 9 (shell multiempresa)`

| Campo | Valor |
|---|---|
| **Resultado para el usuario** | El Administrador de Accesos entra, ve **las 4 unidades de su empresa** y las enciende/apaga; concede y revoca unidades a usuarios; el Super Admin tiene su selector |
| **Findings** | `GA-REM-040` `T-040-21`/`T-040-22` · aportes: G2 + G3 + G4 |
| **Estado actual** | Fase 9 `TECHNICALLY READY · FROZEN` (autorización del propietario: NO) |
| **Backend listo** | Sí (`business_units:*`, `grant-candidates`, sesión fase 8) |
| **Trabajo frontend** | Pantallas nuevas: unidades por empresa (`GET /business-units`, enable/disable) · unidades por usuario (`grant-candidates`, POST/DELETE) · mapa i18n · responsive (`AC-H08/09`) · sin `users:read` (contrato duro) |
| **E2E requerido** | J03/J04/J05 + permutaciones OD-16 (BU ON/OFF × grant ON/OFF) + negativas (self-grant prohibido) |
| **Decisiones del propietario** | **Autorizar la fase 9** · `BU-D07` (comercial vs operativo) puede esperar sin bloquear |
| **Dependencias** | Tranche 1 (utilidad: sin paridad, no se despliega) |
| **Riesgo** | Medio (superficie administrativa nueva) |
| **Puerta de cierre** | Flujo completo con persistencia, refresh y relogin; efecto real en navegación del usuario afectado |

## Tranche 3 — `GA-FE-03 · Navegación dinámica + controles de flujo pendientes`

| Campo | Valor |
|---|---|
| **Resultado para el usuario** | El menú muestra solo lo que el usuario puede hacer (permisos + unidades); estado «sin unidades» distinguible; **envío/reenvío a revisión disponible**; reverso visible |
| **Findings** | `T-040-23`/`T-040-24` · `R-119/R-98` · **`R-181`** · G5 + G6 |
| **Estado actual** | Sin modelo de permisos (0 `hasPermission`); `operationsService.submit` sin llamadores |
| **Backend listo** | Sí (sesión fase 8 · `submit` · `reversals`) |
| **Trabajo frontend** | Filtro de menú por `permissions`+`effective_business_units` · estado zero-BU · control «Enviar a revisión/Reenviar» en detalle y móvil · pantalla de reverso · `statusColors` con `REVERSED` |
| **E2E requerido** | J07/J16 + J14 (reenvío) + navegación por rol |
| **Decisiones** | Ninguna nueva |
| **Dependencias** | Tranche 2 (mismo shell) |
| **Riesgo** | Medio |

## Tranche 4 — `GA-FE-04 · Empresas y flujos de decisión pendiente`

| Campo | Valor |
|---|---|
| **Resultado** | Administración de empresas conforme a la decisión del propietario; lote de abuelas automático según `AOD-25` |
| **Findings** | `R-124`/`AOD-06` · `R-153`/`AOD-25` |
| **Estado** | Decide el propietario |
| **Dependencias** | Decisiones; puede reutilizar el shell del Tranche 2 |

## Tranche 5 — `GA-FE-05 · Verificación autenticada + guardia de paridad (continuo)`

| Campo | Valor |
|---|---|
| **Resultado** | Cierre de las 15 filas `BLOCKED_AUTH` y de los journeys; detección temprana de recaídas de despliegue |
| **Findings** | G0 + G8 |
| **Trabajo** | Cuentas autorizadas → corrida autenticada (fase 7 del plan) · sonda de fingerprint en CI (solo lectura; no toca EX-01) |
| **Dependencias** | Cuentas del propietario (G0) |

## Prioridad transversal

1. Paridad de despliegue (T1) — **sin esto, nada de lo demás se ve**.
2. Shell administrativo multiempresa (T2) — el corazón del «producto multiempresa» del propietario.
3. Exposición/navegación (T3) — que cada rol vea su producto.
4. Decisiones + empresas (T4).
5. Verificación y guardia (T5) — continuo desde ya.

No se implementa ninguno. **Primer tranche recomendado: `GA-FE-01` (paridad de despliegue), y no se inicia aquí.**

---

## Addendum fechado · 2026-09-11 · ejecución del roadmap

```
T1 · GA-FE-01 (paridad de build+despliegue)     → CLOSED / CERTIFIED (R-158 · R-99)
T2 · GA-FE-02 (shell administrativo multiempresa) → ENTREGADO en esta tranche: contexto de
     empresa efectivo + switch · Company BU admin (cuatro unidades) · User BU grants
     (candidatos + panel) · navegación admin mínima por permiso · desplegado byte a byte.
     Autenticado: BLOCKED_AUTH (cuentas pendientes del propietario).
T3 · GA-FE-03 (R-98/R-119, navegación dinámica global) → NO INICIADO (siguiente candidato)
T4 · GA-FE-04 (decisiones + empresas)            → NO INICIADO
T5 · GA-FE-05 (verificación autenticada continua) → requisitos de cuentas emitidos
     (GA_FE_02_REQUIRED_TEST_ACCOUNTS.md); primer candidato al recibirse las credenciales.
```

La prioridad transversal no cambia; T1 y T2 quedan cumplidos en su frontera declarada
(implementación+despliegue; certificación funcional pendiente de cuentas).

---

## Addendum fechado · 2026-09-11 (tarde) · ejecución del roadmap (continuación)

```
T3 · GA-FE-03 (navegación dinámica global)      → CLOSED / CERTIFIED (R-119; residuo P-13 → R-98)
T3 · GA-FE-04 (autoridad de acción + P-13)      → CLOSED / CERTIFIED (R-98) / OWNER_ACCEPTED (GA-UAT-02)
T3 · GA-FE-05 (envío/reenvío a revisión, R-181) → CLOSED / CERTIFIED / OWNER_ACCEPTED (GA-UAT-03)
T3 · GA-FE-06 (contrato de alta de lote, R-182) → CLOSED / CERTIFIED / **OWNER_ACCEPTED** (GA-UAT-04, «A) ACEPTO GA-FE-06»)
     Entrega: planned_close_date + area_id capturados→enviados→persistidos→visibles; selector
     de área por empresa; SLA «lote próximo a cierre» con fuente reparada (§3 capas de evidencia).
     GA-FE-06-A (seguridad): el backend deniega área de otra empresa en alta y edición
     (`BR-07`, fail-closed); N-1/R-183 absorbido y cerrado. Observación aceptada: sin
     entrada de menú para «Lotes» (candidato UX P2). R-184 (kpi/ipe 500): SEPARATE/UNCHANGED.
```

BU-D10 sigue PENDING_RATIFICATION · Wave B PAUSED · Wave C/SAP NOT STARTED.
Ninguna otra tranche queda iniciada.

---

## Addendum fechado · 2026-09-11 · GA-GOV-01 (triage post-UAT-04; solo gobernanza)

```
OBS-UAT-01 «Lotes sin entrada de menú»      → UX_ENHANCEMENT_ONLY · P2 · sin R
     (estado ya inventariado en GA-FE-03 §34 «rutas sin fuente de menú»; decisión
      «sin entradas nuevas salvo Roles» — no reabre R-119 ni GA-FE-03)
OBS-UAT-04 «área en baja lógica seleccionable» → OWNER_DECISION_REQUIRED · P3 · sin R
     (silencio canónico sobre elegibilidad por estado; opciones A/B/C con default B)
OBS-UAT-06 «área ausente del detalle»       → ACCEPTED_DESIGN (GA-FE-06-C15)
UAT-11 «SLA sin superficie a demanda»      → NOT_A_DEFECT (N/A_BY_DESIGN)
R-184                                       → SEPARATE_OPEN (sin relación)
```

Candidato natural para la próxima iteración de navegación: entrada de «Lotes» + filtro
de selección por estado (sujeto a la decisión del propietario sobre OBS-UAT-04).

---

## Addendum fechado · 2026-09-11 · GA-FE-07 (OD-21 · R-185 · elegibilidad por estado)

```
GA-FE-07 (elegibilidad de referencias nuevas por estado) → CLOSED / CERTIFIED
     Decisión OD-21 («Option C»): inactivo (baja lógica) NO sirve para referencias nuevas;
     la historia se conserva. Implementación Área→Lote: alta/edición DENY con inactiva
     («Área inactiva», BR-07), detección de cambio H1–H5, selector transaccional solo
     activas, administración intacta. R-185 CLOSED_OWNER_ACCEPTED.
     Commits C1 511c419 · C2 5a5bb3f · generación index-BUthrUt9.js / backend 5a5bb3f.
     GA-GOV-01 OBS-UAT-04: RESUELTA. Owner UAT corta EJECUTADA (GA-UAT-05, 2026-09-11):
     decisión A) ACEPTO GA-FE-07 → R-185 CLOSED_OWNER_ACCEPTED · OD-21 RATIFIED.
```

## Addendum fechado · 2026-09-11 · R-184 (KPI/IPE — semántica temporal + 500)

```
R-184 (SEMÁNTICA TEMPORAL DEL IPE) → CLOSED (técnico)
     Causa raíz: date − datetime en get_kpi_ipe ⇒ 500 en todo lote con start_date.
     Fix: _dia() canónico en age_days (C2 3f88f94; backend-only; fórmula intacta).
     Runtime E2E-01…12 14/14 · UI tarjeta IPE 556.6 visible (desktop/móvil).
     Candidatos registrados sin implementar: R-186 (production-index misma clase) ·
     observación de escala fórmula-vs-bandas. Owner UAT EJECUTADA (GA-UAT-06, 2026-09-11):
     decisión A) ACEPTO R-184 → R-184 CLOSED_OWNER_ACCEPTED.
```

## Addendum fechado · 2026-09-11 · GA-GOV-02 (triage de residuales post-R184)

```
R-186 (ex «candidato») → FORMAL_OPEN_FINDING (P2 · OPEN)
     GET /reports/kpis/production-index → 500 con start_date (misma clase que R-184,
     endpoint propio; dedup DISTINCT; ID siguiente libre tras R-185). Sin implementar.
OBSERVACIÓN de escala del IPE (fórmula vs bandas) → OWNER_DECISION_REQUIRED
     (1 decisión; A/B/C con recomendación A; sin finding hasta decidir; sin implementar).
PRIORIDAD: P1 tranche R-186 · P2 decisión del propietario · P3 OBS-UAT-01.
Intactos: R-184/GA-UAT-06, GA-FE-02..07, R-181/182/185, OD-21, OBS-UAT-01, BU-D10.
```

## Addendum fechado · 2026-09-11 · R-186 (G-05 production-index — 500 temporal)

```
R-186 (ex «candidato») → CLOSED (técnico)
     Causa: date − datetime en get_kpi_production_index ⇒ 500 en todo lote con start_date.
     Fix: _dia() canónico (mismo helper de R-184; C2 0309225; backend-only; fórmula intacta).
     Runtime E2E-01…13 + R-184 = 14/14 (determinista 5.1 exacto; seguridad OD-16 PASS).
     OWNER UAT NOT REQUIRED (API_ONLY). G-06/R-184 intactos (556.6). Sin UI nueva.
```

Ninguna otra tranche iniciada. OBS-UAT-01 (navegación) sigue P2 sin R; R-184 SEPARATE_OPEN.
