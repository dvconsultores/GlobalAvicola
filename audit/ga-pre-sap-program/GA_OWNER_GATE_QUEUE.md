# GA · PRE-SAP — COLA DE GATES DEL PROPIETARIO (OWNER GATE QUEUE)

Fecha: 2026-09-13 · Estado de ejecución: **`PROGRAM_EXECUTION_BLOCKED_BY_OWNER_GATE`** · **Único gate inmediato: G-01 (AC-06)**.
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
| **Estado** | `WAITING_ON_OWNER` |
| **Qué desbloquea** | AC-06 PASS → GA-GOV-03 `CLOSED_FUNCTIONALLY_CERTIFIED` → **T1 CLOSED** → QUALITY_GATES_READY = YES → **T2 arranca automáticamente** (fundación de seguridad; OD-13.c ya resuelta — sin decisión pendiente). |

> **Nota (2026-09-13 06:20 +0200; re-verificado 06:25 +0200 tras «LISTO» del propietario)** — verificación del agente: la «sesión autenticada del navegador integrado» declarada **no está presente en el contexto del navegador que las herramientas del agente pueden usar** (navegación fresca al repo privado → 404 + «Sign in»; sin `gh`/tokens; sin página adicional compartida). Hasta que la sesión se complete EN ese contexto (la pestaña controlada ya está en la página de login de GitHub) o se entreguen los 5 valores, AC-06 no puede observarse — **no se fabrica evidencia**. Con la sesión activa, el agente lee el run y cierra AC-06 sin más intervención.

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

## Gates programados (referencia §25 del roadmap — no accionables hoy)

| Ref | Qué decide | Tranche | Estado |
|---|---|---|---|
| `OD-13.c` | ¿Autoridad global `("*", all)` en roles de inquilino? | T2 | **RESUELTA — verificada** (`specs/remediation/OD-13-…§3`, VIGENTE); no requiere acción del propietario |
| `AOD-13` | Módulos activables por empresa (incubadora) | T3 | `SCHEDULED` (antes de T3) |
| `AOD-16` | Captura offline móvil v1 (`idempotency_key`) | T5 | `SCHEDULED` (antes de T5) |
| `AOD-14` | Evidencia obligatoria en captura | T8 | `SCHEDULED` (antes de T8) |
| `OD-19 §18` · `AOD-17` · `AOD-18` | UI de reverso · semántica `CORRECTED` · cancelación | T10 | `SCHEDULED` (antes de T10) |
| `OD-10.c` | UI activación manual / clasificación pendiente | T11 | `SCHEDULED` (antes de T11) |
| `AOD-08` · `AOD-10` | Cierre/FCR y fórmulas KPI (Wave C) | T12 | `SCHEDULED` (antes de T12) |
| `GA-UAT-09` | Retry R-153/R-189 (UAT del propietario) | T13 | `SCHEDULED` (antes de T13) |
| Varias (SAP) | `AOD-20/22/24/15`, `OD-24`, `AOD-19`, `R-156/R-177/R-125/R-127.b/R-155` | Fase SAP | `SCHEDULED` (no pre-SAP) |

*(No se presentan paquetes de decisión ahora: ninguna bloquea el trabajo actual; se entregarán con su tranche — §47/§48.)*
