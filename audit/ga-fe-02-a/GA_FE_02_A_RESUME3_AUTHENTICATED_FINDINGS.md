# GA-FE-02-A · RESUME 3 — HALLAZGOS DEL PRIMER CONTACTO AUTENTICADO (ENV-01)

**Fecha**: 2026-09-11 · **Baseline de entrada**: `eaa0a35` · **Baseline de salida**: `ea26b2e` (D1) ·
**Runtime**: `https://avicola.globaldv.net` (ENV-01) · **Credencial bootstrap**: entregada por el
propietario e insertada en la terminal del agente (remedio **R1**; export en la MISMA sesión).
Higiene: historial de bash **desactivado durante el export**; valor jamás impreso; archivos
temporales `chmod 600`; sin persistencia en el repositorio.

---

## 1 · Ejecutado (autenticación REAL por el flujo oficial)

| Paso | Resultado |
|---|---|
| `POST /api/v1/login` (admin) | **200** — `access_token, refresh_token, expires_in, token_type` |
| `GET /api/v1/me` | **200** — `admin`, `is_super_admin=true`, 9 permisos comodín (`*:read|create|update|delete|review|correct|approve|reject|send_sap`), `effective_company_id=null` |
| `POST /api/v1/switch-company {1}` | **200** — sesión situada en «Avícola Global C.A.»; `/me` ⇒ `effective_company_id=1` |
| `GET /api/v1/roles` (sin/con contexto) | **200** — 13 roles activos; **ninguno** con `business_units:*`; «Administrador de Accesos» **no existe** |
| `GET /api/v1/business-units` (empresa 1) | **200 `[]`** — el contrato exige las CUATRO siempre (`admin.listar_habilitaciones`) |
| `GET /business-units/{grandparent,breeder,hatchery,broiler}/grant-candidates` | **404 ×4** — `"unidad de negocio '<code>'"` ⇒ catálogo de plataforma vacío |
| `GET /business-units` sin contexto (token original) | **403** `No hay empresa efectiva sobre la que administrar unidades de negocio` — fail-closed correcto (OD-11.c/OD-14.d) |
| `POST /users/1/business-units {grandparent}` (auto-concesión directa) | **403** `administrar el acceso no autoriza a concedérselo a uno mismo` (OD-15.a) — denegación sin rastro (§AC-I03) |
| `GET /lots`, `GET /operations` | **200** — endpoints hermanos sanos |
| UI navegador (login real) | Login **OK** → shell desktop autenticado; `/admin/unit-access` conforme al estado (pre-fix: ver D1; post-fix: EmptyState `admin.context.none`) |

## 2 · Defecto D1 — DETECTADO, REMEDIADO y DESPLEGADO (§7)

**Síntoma (runtime, pre-fix)**: tras **hard reload** en `/admin/unit-access`, un super admin
legítimo queda **denegado** con alert `admin.forbidden` persistente; la red **no muestra ninguna
llamada a `/me`**; el dashboard presenta sesión parcial (nombre de claims).

**Evidencia**:
- Red (playwright, reload + listener): `hits=[]` para `/api/v1/me`; `[role=alert]` =
  «No tiene permiso para administrar unidades de negocio.» persistente ≥4.5 s.
- Código: `App.tsx` `if (token && isLoading) fetchMe()` — con `auth.store` naciendo
  `isLoading: false` y **ningún** writer a `true`, el efecto jamás corre; la sesión se hidrata
  solo desde claims del JWT (`getInitialUser`) ⇒ sin `is_super_admin`/`permissions`/
  `effective_company_id` ⇒ `PermissionRoute` deniega.
- Git: condición introducida en `c38efb01` (2026-06-28; su propio comentario ya documentaba
  «fetchMe always runs when token exists»); init `isLoading: false` desde el primer commit.
- Reproducción directa: /me desde el navegador con el token de sesión responde **200** con
  `is_super_admin: true` — la sesión es válida; el problema es la restauración.

**Impacto GA-FE-02**: rompe el punto de **refresh** del encargo (denegación de superficies con
guard por permiso para CUALQUIER usuario tras un reload; `UnitAccessPage` cayendo a fail-closed
incorrecto; `UserBusinessUnitsButton` oculto).

**Remediación aplicada** (gobernada, sin Owner Decision, sin hotfix):
`isLoading: Boolean(accessToken)` + comentario de trazabilidad; test de regresión
`gaFe02.sessionBoot.test.ts` (**RED** `expected false to be true` → **GREEN**).
Gates: **Vitest 200/200 · tsc 0 · build ✓**. Commit `ea26b2e` (2 archivos, +62/−1); push
`eaa0a35..ea26b2e`.

**§D1.5 Verificación post-deploy (Watchtower)** — **VERIFICADA (2026-09-11)**: el runtime pasó a
`index--DbCa8Hk.js` (idéntico al build local). En vivo, recargando `/admin/unit-access`:
`/api/v1/me` **dispara y responde 200** (antes: 0 llamadas), **0 alertas** `admin.forbidden`
(antes: alerta persistente ≥4.5 s) y la página renderiza el fail-closed correcto «Sin empresa
seleccionada — Seleccione una empresa para administrar sus unidades y accesos». Capturas
desktop y móvil 390×844 registradas en la sesión de certificación.

## 3 · Gaps de ENV-01 (bloqueantes de la certificación — acción server-side)

**F1 · Catálogo `BusinessUnit` VACÍO.** Evidencia §1 (`[]` + 4×404). El catálogo lo siembra
`baseline_seeds.sembrar_unidades_de_negocio` (4 filas; `GA-REM-040 §2`) y **no existe API de
catálogo** — ningún mecanismo oficial de cliente puede crearlo ⇒ E2E-02…E2E-10 + matriz 3D =
`BLOCKED_FIXTURE`.

**F2 · Rol «Administrador de Accesos» AUSENTE.** El rol canónico (`PERMISOS_ADMINISTRADOR_DE_ACCESOS`,
R-113/OD-15 §6) no está entre los 13 roles; el encargo **prohíbe crear roles/permisos** ⇒
**Actor B = BLOCKED_FIXTURE** (flujos de concesión/revocación/auto-concesión/candidatos como B).

**F3 · `GET /users` responde 500 (runtime).** La lista falla con ≥10 filas del tenant
(bisect: límite 9 → 200, límite 10 → 500; `skip=9&limit=1` → 500). Sondeo individual: ids
**57–70 → 500** (14 filas ilegibles), 2–10 → 200, 71–120 → 404. `UsersPage` y listados
dependientes caen; `grant-candidates` proyecta solo columnas (id/username/nombre) → no hereda el
fallo (riesgo residual a validar post-seed). Causa exacta no determinable desde el cliente
(probable dato inválido en esas filas — p. ej. email no validable).

**F4 · Selector de empresa no visible para admin sin contexto** (observación, sin fix). El bloque
del selector en `Header.tsx` solo se renderiza si `activeCompanyName || user.company_name`; el
admin sembrado (sin empresa) no tiene control UI para situarse (la API `switch-company` sí
funciona). Afecta E2E-01b en UI; decisión de diseño pendiente del propietario.

## 4 · Estado de la matriz E2E en esta pasada

| Escenario | Estado | Evidencia |
|---|---|---|
| E2E-01 contexto/switch | **PARCIAL-PASS** (API 200; fail-closed 403; UI login OK; punto de refresh = D1 → remediado) | §1, §2 |
| E2E-01b switch en UI | **BLOCKED_FIXTURE (F4)** — API OK | §3 |
| E2E-02 … E2E-10 (+efectos, negativos, 3D) | **BLOCKED_FIXTURE (F1/F2)** | §3 |
| E2E-06 (petición directa) | **PARCIAL-PASS** — 403 auto-concesión sin rastro | §1 |
| refresh/relogin/persistencia/red/auditoría/móvil | **BLOCKED_FIXTURE** (sin superficies operables) | §3 |

## 5 · Clasificación

```
AUTH ............. OK — login/me/switch reales (credencial del propietario, flujo oficial)
GA-FE-02 ......... NO CERTIFICADO — MODE_E · GA_FE_02_DEFECT_FOUND (D1) × fixture ENV-01 (F1/F2)
D1 ............... REMEDIADO + desplegado (re-ejecución TOTAL del set E2E pendiente hasta F1/F2,
                   requisito §7 de la rama de remediación)
Guardrails ....... sin bypass · sin hotfix · sin DB directa · sin credenciales impresas o
                   persistidas · BU-D10 intacto · R-98/R-119/R-181/R-182 intactos · GA-FE-03 no iniciada
```

## 6 · Remediación requerida (propietario/ops — server-side, fuera del alcance del agente)

1. **ENV-01**: sembrar el **catálogo de unidades** (4 filas) y el **rol «Administrador de
   Accesos»** (baseline de plataforma) — o autorizar explícitamente la creación del rol por API
   oficial (el catálogo NO tiene API; requiere seed server-side).
2. **ENV-01**: investigar/corregir las filas 57–70 de `users` (HTTP 500).
3. **Re-ejecutar GA-FE-02-A** (plan congelado §3 del execution doc): E2E-01…E2E-10, matriz 3D,
   refresh, móvil 390×844, auditoría/red — D1 ya no debería reproducirse.
4. (Opcional, decisión de producto) F4: renderizar el selector para `is_super_admin` aunque no
   exista nombre de empresa.
