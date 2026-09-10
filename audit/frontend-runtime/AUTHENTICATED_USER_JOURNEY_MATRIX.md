# AUTHENTICATED USER JOURNEY MATRIX

**2026-09-10** · base `3808ed5` · runtime `avicola.globaldv.net` (ENV-01).

Estado de ejecución: **fase autenticada BLOQUEADA** (`AUTHENTICATED_RUNTIME_BLOCKER`, §38 del encargo: sin cuentas autorizadas no se adivina el resultado). Lo que **sí** está determinado es el primer punto de fallo estructural por capa (código + bundle + gobernanza), que se registra sin fingir ejecución.

Columnas: JOURNEY · ACTOR · PRECONDICIONES · ENTRADA UI · PASOS · ESPERADO · REAL (hasta donde consta) · PRIMER FALLO · BACKEND · FRONTEND · RUNTIME · CAPTURA · STATUS · FINDING.

## J01 · Login
- **Actor**: cualquiera · **Entrada**: `/login` (renderizada, `AUDIT_001`).
- **Esperado**: credenciales válidas → sesión → home según `view_type`.
- **Real**: superficie presente; API `/auth/login` operativa (probes). Flujo completo: **pendiente de cuenta**.
- **Status**: `BLOCKED_AUTH` · Finding: —.

## J02 · Seleccionar empresa (actor global)
- **Actor**: Super Admin · **Entrada**: dropdown de cabecera.
- **Esperado**: lista de empresas → elegir → token nuevo → datos y menú de la empresa elegida.
- **Real (estático)**: el selector existe y está desplegado; carga con `fetchCompanies()` al abrir; si falla queda «Cargando…» sin error; sólo se renderiza con `company_name` presente.
- **Primer fallo posible**: exposición (render condicionado / fallo silencioso). Funcionalidad: **pendiente de cuenta**.
- **Status**: `IMPLEMENTED_BUT_NOT_EXPOSED` · Finding: — (secundarios en matriz).

## J03 · Administrar unidades de la empresa (BU ON/OFF)
- **Actor**: Administrador de Accesos / Super Admin.
- **Entrada UI esperada**: pantalla `T-040-21` (fase 9). **No existe** — ni ruta, ni componente, ni menú.
- **Backend**: `GET /business-units` + `PATCH …/enable|disable` — **desplegado y vivo (401)**.
- **Primer fallo**: **paso 1 — no hay dónde entrar**. Jornada no iniciable.
- **Status**: `FRONTEND_MISSING` · Finding: fase 9 congelada (GA-REM-040).

## J04 · Conceder una unidad a un usuario
- **Actor**: Administrador de Accesos. · **Entrada esperada**: `T-040-22`. **No existe**.
- **Backend**: `grant-candidates` + `POST /users/{id}/business-units` — desplegado (401).
- **Primer fallo**: paso 1 — sin pantalla. · **Status**: `FRONTEND_MISSING`.

## J05 · Revocar una unidad a un usuario
- Igual que J04 (`DELETE`); sin UI. · **Status**: `FRONTEND_MISSING`.

## J06 · Administrar roles y permisos
- **Actor**: admin. · **Entrada**: `/roles` (local) — **ausente del runtime servido**.
- **Backend**: `/roles` + catálogo — desplegado.
- **Primer fallo (runtime)**: la ruta no existe en el router servido → con sesión cae a la home.
- **Status**: `DEPLOYMENT_STALE` (local completo) · Finding: R-99.

## J07 · Usuario zero-BU
- **Esperado (`OD-09.c`/`AC-H06`)**: puede usar el núcleo permitido; sin dato productivo; estado explícito «sin unidades».
- **Real**: no existe el estado ni el gating; el usuario vería el menú completo y recibiría 403/vanos al operar.
- **Status**: `FRONTEND_MISSING` (CAP-ADM-07). Ejecución runtime: `BLOCKED_AUTH`.

## J08 · Entrada Progenitoras (usuario autorizado)
- **Esperado**: hub → etapa → importación con plan tipado.
- **Real**: hub y etapas presentes en ambos bundles; **la importación no puede completarse en el runtime**: la UI 09-05 no envía `import_plan` → **400 BR-22**.
- **Status**: `DEPLOYMENT_STALE` + ruptura vigente (CAP-BU-02) · Finding: R-99.

## J09 · Entrada Reproductoras
- **Esperado**: recepción con cuadre y pesos.
- **Real**: **400 BR-20 en el runtime** con la UI servida (faltan los tres datos). Captura general del BU sigue disponible.
- **Status**: `DEPLOYMENT_STALE` + ruptura vigente (CAP-OPS-02).

## J10 · Entrada Incubadora
- **Esperado**: carga/despacho/nacimiento/mortalidad/descarte.
- **Real**: **nacimiento → 400 BR-21**; catálogo sin mortalidad/descarte (R-171) en el runtime; despacho con riesgo 400 (BR-02).
- **Status**: `DEPLOYMENT_STALE` + rupturas (CAP-OPS-04/06, CAP-BU-03).

## J11 · Entrada Engorde
- **Esperado**: operación de engorde (mortalidad inicial, agua, pesos).
- **Real**: captura general presente; **agua sin captura** (B05 local); resto pendiente de cuenta.
- **Status**: `DEPLOYMENT_STALE` (CAP-OPS-05) + `BLOCKED_AUTH` (general).

## J12 · Crear evento operativo
- **Esperado**: wizard → guardar → evento `REGISTERED`.
- **Real**: existe en ambos; en runtime las variantes B01/B13/BR-22 fallan (J08–J10). General: pendiente cuenta.
- **Status**: mixto (filas propias) · Finding: R-99 + BR-20/21/22.

## J13 · Editar evento
- **Esperado**: editar permitidos según estado; revalidar reglas.
- **Real**: paridad local certificada (R-176); runtime pre-fix. `BLOCKED_AUTH` para evidencia.
- **Status**: `BLOCKED_AUTH` (+ secundario stale).

## J14 · Corregir un devuelto/rechazado
- **Esperado**: operador corrige (CorrectionForm) → CORRECTED → aprobador decide; reenvío explícito disponible.
- **Real**: corrección existe en ambos; **reenvío explícito sin control UI en ninguna generación** (R-181); en el runtime el flujo pre-R-135 convive con backend nuevo.
- **Status**: `FRONTEND_MISSING` (CAP-OPS-08) + `BLOCKED_AUTH` (corrección).

## J15 · Revisar / Aprobar / Rechazar
- **Esperado**: cola → decidir con motivo; una sola decisión efectiva (R-166).
- **Real**: superficies presentes; backend nuevo (FOR UPDATE) desplegado; evidencia de flujo: `BLOCKED_AUTH`.
- **Status**: `BLOCKED_AUTH`.

## J16 · Reverso (solicitar / procesar)
- **Esperado**: Supervisor solicita; Contraloría/plano de revisión aprueba; estado REVERSED visible.
- **Real**: backend desplegado (R-136/OD-19); **sin pantalla** (fase 9, gobernado); `statusColors` sin `REVERSED`.
- **Status**: `FRONTEND_MISSING` (CAP-OPS-09).

## J17 · Evidencias (subir/ver)
- **Esperado**: adjuntar en el detalle; descargar; clasificar.
- **Real**: presente en ambos bundles; **R-52**: el volumen no está montado en el shared → evidencias efímeras al recrear contenedor.
- **Status**: `BLOCKED_AUTH` + secundario R-52 (P1 runtime).

## J18 · Cambiar de empresa sin datos obsoletos
- **Esperado (`OD-14`/`R-126`/`R-48`)**: A→B → datos y permisos de B; B→A sin residuos.
- **Real**: `switchCompany` re-emite tokens y re-`fetchMe` (diseño correcto); stores de páginas refrescan al montar. Verificación de aislamiento en runtime: `BLOCKED_AUTH`.
- **Status**: `BLOCKED_AUTH` (diseño presente; evidencia pendiente).

## Resumen

| Bucket | Journeys |
|---|---|
| `FRONTEND_MISSING` (no iniciables) | J03, J04, J05, J07, J16 (+J14 en su parte de reenvío) |
| `DEPLOYMENT_STALE` con ruptura vigente | J08, J09, J10 (+J06) |
| `BLOCKED_AUTH` (ejecución pendiente) | J01, J02 (funcional), J06 (parcial), J11–J15, J17, J18 |

Ningún journey se declara aprobado sin ejecución autenticada; ninguno se declara roto sin evidencia (los tres rojos de J08–J10 están probados por contrato: schema/validator del backend nuevo × payload de la UI vieja, reproducible).
