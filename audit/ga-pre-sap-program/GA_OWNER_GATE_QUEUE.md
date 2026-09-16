# GA · PRE-SAP — COLA DE GATES DEL PROPIETARIO (OWNER GATE QUEUE)

Fecha: 2026-09-14 · Estado de ejecución: **`T1 CLOSED — T2 CLOSED — T3 CLOSED_TECHNICALLY / OWNER_GATE_PENDING_AOD13 — T4 CLOSED_TECHNICALLY — T5 CLOSED_TECHNICALLY — T6 CLOSED_TECHNICALLY — T7 CLOSED_TECHNICALLY — T8 CLOSED_TECHNICALLY — **T9 CLOSED_TECHNICALLY** (R-215 `cd2e7bc` · R-196 `571b4d5` · R-195 `bcfdebd`; remoto `e515858`)`** · **AOD-29 (2026-09-14): GitHub Actions retirado del camino de certificación PRE-SAP — `PUSH = REQUIRED` (**AOD-29 Clar. 01** — GitHub ACTIVO como remoto; lo retirado es Actions; los push certificados se sincronizan y no disparan Actions); gates locales reproducibles; evidencia dependiente de Actions = `NOT_APPLICABLE_BY_OWNER_DECISION`; históricos intactos (`GA_OWNER_DECISION_AOD29_GITHUB_ACTIONS_RETIRED.md`)** · **G-01 (AC-06) CERRADO — run #10 `34764423545` verde (evidencia histórica)** · **G-06 encolado (credenciales runtime — bloquea C3 de R-199/R-201/R-202/R-203/R-204/R-190/R-205/R-191/R-206/R-209/R-210/R-194/R-192/R-193/R-211/P1-12/R-198/R-219 y verificación visual R-216)** · **AOD-13 accionable (único pendiente de R-221/AC-04 en T3)** · **Confirmatorias nuevas: AOD-25/AOD-26 (R-194 C-01/C-02), AOD-27 (R-192 C-01/C-05) y AOD-28 (R-211 C-02) — no bloquean**.
Regla (§47/§48): los gates se acumulan aquí y se presentan consolidados; no se re-solicitan en bucle. Acciones humanas mínimas y deterministas (§50).

## G-01 · GA-GOV-03 · AC-06 — Evidencia externa de CI · **INMEDIATO (bloquea todo el programa)**

| Campo | Valor |
|---|---|
| **Tipo** | `PRIVATE_EXTERNAL_EVIDENCE` |
| **Por qué solo humano** | Repo privado; el entorno del agente no tiene sesión/canal autenticado de GitHub (navegador integrado sin login → 404; sin `gh`/`glab`; sin tokens; API anónima 404). §9/§58 prohíben fabricar evidencia externa y la spec no admite excepción. |
| **Tranche afectada** | T1 (cierre) → habilita T2-T13 |
| **Procesos afectados** | Todos (gate de programa) |
| **Acción mínima** | **A)** Iniciar sesión en GitHub *usted mismo* en la pestaña del navegador integrado de VS Code (el agente lee el run y transcribe lo observado; el agente no maneja credenciales) — **o B)** pegar los 5 valores: `Run URL` · `Run ID` · nombre exacto artefacto backend · nombre exacto artefacto frontend · `timestamp` (YYYY-MM-DD HH:MM ±hh:mm). |
| **Evidencia exacta** | Run «Quality Suite (push)» del SHA `66be1c1`: URL + ID; conclusión `success`; `backend-suite` `success`; `frontend-suite` `success`; artefactos con nombre exacto; JUnit/log presentes. *(Ya declarados por el propietario: workflow/evento/rama/SHA y las tres conclusiones; siguen pendientes los 5 valores concretos: URL, ID, nombres de artefactos, timestamp.)* |
| **¿Continúa trabajo independiente?** | **NO** (T2-T13 dependen de T1) |
| **Estado** | `CLOSED` (2026-09-13 ~17:25 +0200 — run #10 `34764423545` `60e9d9d`: ambas suites verdes; artefactos sha256-verificados) |
| **Qué desbloquea** | AC-06 PASS → GA-GOV-03 `CLOSED_FUNCTIONALLY_CERTIFIED` → **T1 CLOSED** → QUALITY_GATES_READY = YES → **T2 arranca automáticamente** (fundación de seguridad; OD-13.c ya resuelta — sin decisión pendiente). |

> **Nota (2026-09-13 15:45 +0200 — actualiza las anteriores)** — observación directa (sesión autorizada): **runs en ROJO** (incl. `66be1c1`) ⇒ **AC-06 = FAIL observado** (sin fabricación). **Remediación CI completa (solo workflow)**: backend — `pip install -e` flat-layout ⇒ **C3**; frontend — peer `@testing-library/dom` ausente por `--legacy-peer-deps` (27 fallos; clasificado con el JUnit real del run #1) ⇒ **C4**; ambos pusheados y validados en CI (run #8: `frontend-suite` **VERDE**, 1m28s — primera suite verde). Backend run #7 clasificado: `25F/1192P/58S`, todos por flag SAP ⇒ **C5** (`FEATURE_SAP_ENABLED: "true"` en el paso de suite; A/B local 201→211) pusheado. Run #9 (`34761309595`): C5 ✓ (`1F/1225P/49S`; 24/25 resueltos) · fallo restante = **TEST_DEFECT nº38** (`r188` leía eventos sin `ORDER BY`) ⇒ **C6** (test determinista; local 10/10). **DESENLACE: run #10 `34764423545` (`60e9d9d`) = `Success`** (backend ✅ 21m42s · frontend ✅ 1m22s; artefactos descargados, sha256 == digest) ⇒ **AC-06 = PASS ⇒ G-01 CERRADO ⇒ T1 CLOSED.**

## Pista OPS (paralela, owner/ops — arrancable ya; bloquea T13, no a T2-T13)

### G-02 · OPS-01 · R-52/RES-05 — Volumen `avicola-media` (durabilidad de evidencias)

| Campo | Valor |
|---|---|
| **Tipo** | `OPERATIONS` (host) |
| **Por qué solo humano/ops** | Acción de despliegue puntual en el host (`docker compose up -d backend`); Watchtower no relee el compose; sin acceso al host desde el agente |
| **Acción mínima** | Recrear el backend con el volumen en una ventana operativa y verificar persistencia de la evidencia |
| **Evidencia exacta** | Registro de la recreación + verificación de que la evidencia sobrevive a la recreación (cierre de R-52) |
| **¿Continúa trabajo independiente?** | SÍ |
| **Estado** | `QUEUED` |

### G-03 · OPS-02 · GA-REM-004 AC03 — Rate limit en runtime (6→429)

| Campo | Valor |
|---|---|
| **Tipo** | `OPERATIONS` (runtime) |
| **Por qué solo humano/ops** | Asignada a operaciones por el certification report (`BLOCKED_EXTERNAL`, 2026-09-03); requiere entorno desplegado y semántica de clave por proxy (GAP-11) |
| **Acción mínima** | Con `FEATURE_RATE_LIMIT_ENABLED=true` efectivo en el contenedor: verificar «6 intentos de login en <1 min desde la misma IP → el 6.º responde 429» y documentar el umbral |
| **Evidencia exacta** | Observación fechada del 429 + nota de clave por proxy |
| **¿Continúa trabajo independiente?** | SÍ |
| **Estado** | `QUEUED` |

### G-04 · OPS-03 · GA-REM-004 AC07 — BD: rol de privilegios mínimos + SSL

| Campo | Valor |
|---|---|
| **Tipo** | `OPERATIONS` (infraestructura) |
| **Por qué solo humano/ops** | `DEFERRED` fuera del repositorio (certification report); requiere host/BD |
| **Acción mínima** | Sustituir el rol superusuario por un rol de aplicación con privilegios mínimos y exigir transporte cifrado |
| **Evidencia exacta** | Inspección del rol efectivo (no superusuario) + cadena de conexión con SSL |
| **¿Continúa trabajo independiente?** | SÍ |
| **Estado** | `QUEUED` |

### G-05 · OPS-04 · P1-6 — Respaldo comprobado + política de migraciones

| Campo | Valor |
|---|---|
| **Tipo** | `OPERATIONS` (infraestructura) |
| **Por qué solo humano/ops** | `release blocker` de infraestructura; requiere host |
| **Acción mínima** | Ejecutar y **comprobar** un ciclo respaldo/restauración y documentar la política de migraciones |
| **Evidencia exacta** | Evidencia operativa del ciclo ejecutado (alta, restauración verificada, política) |
| **¿Continúa trabajo independiente?** | SÍ |
| **Estado** | `QUEUED` |

### G-06 · T2/T3 · Credenciales runtime para las sondas C3 (R-199, R-201, R-202, R-203, R-204)

| Campo | Valor |
|---|---|
| **Tipo** | `PRIVATE_EXTERNAL_EVIDENCE` (runtime) |
| **Por qué solo humano** | El agente no dispone de credenciales runtime con `users:read/create/update` ni super admin (UAT-09 = Operador/Aprobador R-153) y no se buscan ni fabrican credenciales |
| **Acción mínima** | **A)** Proveer una credencial **efímera** de administrador de empresa 1 (users:read/create/update) o super admin, destruible tras las sondas — **o B)** ejecutar los scripts de sondas facilitados (E2E de cada certificación: R-199, R-201, R-202, R-203, R-204) y devolver la salida |
| **Evidencia exacta** | Códigos observados por sonda + inventario §12 de R-203 = 0 filas |
| **¿Continúa trabajo independiente?** | **SÍ** — T3 avanza (R-201/R-203/R-204/R-216 cerradas técnicamente); las cinco C3 quedan `PENDIENTE_G-06` documentadas por spec |
| **Estado** | `QUEUED` (alcance ampliado a T3) |
| **Qué desbloquea** | El cierre runtime (C3) de R-199/R-201/R-202/R-203/R-204; no bloquea C1/C2 ni el resto de T3 |

## Gates programados (referencia §25 del roadmap — no accionables hoy)

| Ref | Qué decide | Tranche | Estado |
|---|---|---|---|
| `OD-13.c` | ¿Autoridad global `("*", all)` en roles de inquilino? | T2 | **RESUELTA — verificada** (`specs/remediation/OD-13-…§3`, VIGENTE); no requiere acción del propietario |
| `AOD-13` | **`farm_inspection` sin lote: ¿qué unidad tiene?** (micro-decisión C-02 de R-221; opciones: **(A)** derivarla de la granja/galpón declarados cuando declaran cadena única — recomendada, con fallback B; **(B)** exigir clasificación previa siempre; **(C)** mantener statu quo «alguna unidad» + bandeja). Contexto: `hatchery_inspection` sin lote ya deriva `hatchery` sin esperar decisión (tipo inequívoco, regla R-153 extendida); la habilitación por empresa gobierna el registro. | T3 | **`ACCIONABLE` — único pendiente para cerrar R-221/AC-R221-04 (rider de T3).** R-201/R-203/R-204/R-216 cerradas; R-221 C1/C2 (AC-01/02/03) en marcha sin depender de esto |
| `AOD-16` | Captura offline móvil v1 (`idempotency_key`) | T5 | `SCHEDULED` (antes de T5) |
| `AOD-14` | Evidencia obligatoria en captura | T8 | `SCHEDULED` (antes de T8) |
| `OD-19 §18` · `AOD-17` · `AOD-18` | UI de reverso · semántica `CORRECTED` · cancelación | T10 | `SCHEDULED` (propietario; lote §25). OD-19 §18 **cumplido técnicamente** (R-207 `00d4bea`); `AOD-17` (multinivel) mantiene **R-142 diferida** (condición no cumplida en T10); `AOD-18` (cancelación) sigue pendiente |
| `AOD-19bis (R-190 C-03)` | **Opcional**: ¿persistir `house_id` en el lote al aprobar la primera recepción de un lote sin galpón (alternativa B), para que los eventos posteriores lo hereden sin selector? Implementación vigente = **A** (derivación en el asistente, sin tocar el lote); B sería un anexo (cambia el modelo al aprobar y toca OD-25(B)). | T5+ | `SCHEDULED OPTIONAL` — no bloquea; si se elige B, se especifica como anexo |
| `AOD-21 (R-210 C-01)` | **Confirmatoria**: «el pesaje se captura en gramos» — la implementación ya opera en g (curva/evaluación/i18n); el propietario confirma y queda registrado (acta). Si eligiera kg, se especificaría conversión explícita (C-02). | T5+ | `SCHEDULED CONFIRMATORIA` — no bloquea (por defecto A=g) |
| `AOD-25 (R-194 C-01)` | **Confirmatoria (A/B)**: la recepción de huevos y el despacho de pollitos (etapa incubadora, `location_events`) llevan la granja/galpón del **lote incubadora** (A, implementado) — alternativa B: eximir la etapa de BR-08 por decisión. | T6+ | `SCHEDULED CONFIRMATORIA` — no bloquea (por defecto A) |
| `AOD-26 (R-194 C-02)` | **Confirmatoria (capturar/derivar)**: `arrival_date` de la recepción capturada con default `event_date` (A, implementado) — alternativa: derivarla siempre en servidor. | T6+ | `SCHEDULED CONFIRMATORIA` — no bloquea (por defecto A) |
| `AOD-27 (R-192 C-01/C-05)` | **Confirmatoria (regla de negocio)**: `REVERSED` es estado terminal **decidido** a efectos de R7 (un reverso aprobado no impide el cierre) y un pesaje/alimento revertido no cuenta para BR-05 — defectos «sí» implementados (C-01/C-05); si el propietario veta, la alternativa es una acción explícita de descarga (fuera de `OD-19`). | T7+ | `SCHEDULED CONFIRMATORIA` — no bloquea (por defecto sí) |
| `AOD-28 (R-211 C-02)` | **Confirmatoria (A/B)**: capacidad del galpón **por evento** (A, implementado — corrige el falso positivo del reparto multi-galpón; residual de concurrencia documentado) vs **acumulada entre eventos vigentes** (B — requiere consulta agregada + acuerdo de concurrencia). | T7+ | `SCHEDULED CONFIRMATORIA` — no bloquea (por defecto A) |
| `AOD-29` | **Decisión del propietario (informativa — NO es gate pendiente)**: GitHub Actions deja de ser gate obligatorio de nuevas tranches PRE-SAP (costo de minutos); certificación con **gates locales reproducibles**; evidencia dependiente de Actions ⇒ `NOT_APPLICABLE_BY_OWNER_DECISION`; `PUSH = REQUIRED` (**AOD-29 Clar. 01**: GitHub ACTIVO como remoto; Actions retirado; el push certificado no debe disparar Actions). Registro: `GA_OWNER_DECISION_AOD29_CLARIFICATION_01_PUSH_PRESERVED.md`. | Todas (T8+) | **RESUELTA (2026-09-14) · ACLARADA (Clar. 01)** |
| `OD-10.c` | UI activación manual / clasificación pendiente | T11 | `SCHEDULED` (antes de T11) |
| `AOD-08` · `AOD-10` | Cierre/FCR y fórmulas KPI (Wave C) | T12 | **`DECIDED (OWNER, 2026-09-16)`** — `GA_OWNER_DECISION_WAVE_C_FORMAL.md`: R-131 corregir (FCR=alimento/ganancia, OD-22 sin cambio) · edad cerrada aprobada · R-132 aprobada (base=apertura+entradas, UNKNOWN≠0) · R-133/R-134 `DEFERRED_FUNCTIONAL_DEFINITION` (retirar de superficies certificadas) · R-141 corregir (mismo filtro que R-218). GA-REM-022 autorizada a completarse |
| `GA-UAT-09` | Retry R-153/R-189 (UAT del propietario) | T13 | `SCHEDULED` (antes de T13) |
| Varias (SAP) | `AOD-20/22/24/15`, `OD-24`, `AOD-19`, `R-156/R-177/R-125/R-127.b/R-155` | Fase SAP | `SCHEDULED` (no pre-SAP) |

*(No se presentan paquetes de decisión ahora: ninguna bloquea el trabajo actual; se entregarán con su tranche — §47/§48.)*
