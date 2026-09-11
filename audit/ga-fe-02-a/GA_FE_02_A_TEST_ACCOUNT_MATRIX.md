# GA-FE-02-A · TEST ACCOUNT MATRIX (§16)

Sin contraseñas, sin tokens. Estado de esta ejecución: **ninguna cuenta disponible** (MODE_C).
Las columnas describen el objetivo; los valores se completarán en la reanudación autenticada.

> **Addendum GA-FE-02-C (2026-09-11) — corrida autenticada COMPLETA.** Los actores A–E
> quedaron provisionados y verificados (§8 abajo). Las cuentas sintéticas fueron **dadas de
> baja al cierre** conforme a §76 (ver estado final) y los roles temporales de fixture
> quedaron `is_active=false`; el rol canónico 35 permanece activo e intacto.

| ACTOR_ID | TEST USER | CREATED/EXISTING | COMPANY | ROLE(S) | PERMISSIONS | COMPANY BU GRANTS | PURPOSE | CAN SWITCH COMPANY? | CAN MANAGE COMPANY BU? | CAN MANAGE USER BU? | CAN OPERATE PRODUCTIVE BU? | SELF-GRANT TARGET? | AUTH AVAILABLE? | MFA? | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A · COMPANY_BU_ADMIN | (a definir) | EXISTING o creado por flujo oficial | Empresa de prueba | rol con `business_units:update` (p. ej. Administrador de Accesos o admin de empresa con ese permiso) | `business_units:read` · `business_units:update` | n/a | habilitar/apagar BU de empresa | solo si es super admin (solo el comodín puede) | **SÍ** | solo si además tiene `:create/:delete` | no por rol | no aplica | **MISSING** | no | `BLOCKED_AUTH` |
| B · ACCESS_ADMIN | (a definir) | EXISTING o creado por flujo oficial | misma empresa | «Administrador de Accesos» (sembrado) | exactamente `business_units:read|update|create|delete` — **sin** `users:read` | n/a | conceder/revocar a otros | **NO** (403 backend) | sí, por `:update` (mismo permiso gobierna ambos hoy — BU-D07 pendiente) | **SÍ** | **NO** | no puede concederse a sí mismo (403) | **MISSING** | no | `BLOCKED_AUTH` |
| C · TARGET_OPERATIONAL_USER | (a definir) | EXISTING o creado por flujo oficial | misma empresa | rol operativo existente | RBAC de la capacidad representativa (p. ej. lectura productiva gobernada) | objetivo: **NO** al inicio (fixture de alta información: hatchery YES) | recibir/revocar y verificar efecto real | no | no | no | sí, según matriz 3D | no | **MISSING** | no | `BLOCKED_AUTH` |
| D · UNAUTHORIZED_CONTROL | (a definir) | EXISTING o creado por flujo oficial | misma empresa | rol sin administración de acceso | sin `business_units:*` | n/a | probar denegación de superficies/acciones admin | no | no | no | n/a para la certificación | no | **MISSING** | no | `BLOCKED_AUTH` |
| E · GLOBAL_ACTOR (opcional) | (solo si existe credencial legítima) | EXISTING | — | Super Administrador (comodín) | `*` | n/a | fail-closed sin contexto; contexto situado; BU OFF deniega también al global | **SÍ** (único con derecho) | sí | sí (a otros) | no si BU OFF | no puede auto-concederse | **OPTIONAL_MISSING** | no | `OPTIONAL — no bloquea el resto (§46)` |

## Requisitos transversales de la fixture

```
1 empresa de prueba SEGURA (no productiva activa; preferible dedicada).
Estado sugerido: grandparent ON · breeder OFF · hatchery ON · broiler OFF.
Target C: RBAC SÍ para la capacidad representativa; BU objetivo con grant NO.
Segunda empresa de prueba solo si existe un usuario seguro de ella para E2E-07;
si no, ese subcaso se marca BLOCKED_FIXTURE (no bloquea toda la suite — §38).

## Addendum 2026-09-11 (reanudación 3 — primer contacto autenticado)

- **Bootstrap disponible y verificado**: identidad `admin` (Super Administrador, 9 comodines),
  login/`me`/`switch-company` 200. Empresas visibles: «Avícola Global C.A.» (id 1) y
  «Avícola Del Sur C.A.» (id 3).
- **Actor B — `BLOCKED_FIXTURE`**: el rol «Administrador de Accesos» NO existe en ENV-01 (13
  roles activos, ninguno con `business_units:*`); crear roles está prohibido por el encargo (F2).
- **Actores C/D** — provisionables como usuarios (roles operativos existentes), pero sus flujos
  E2E quedan bloqueados por F1 (catálogo BU vacío: `[]` + 4×404).
- **Actor E** — cubierto por el bootstrap (comodín, sin empresa persistida; fail-closed 403
  verificado sin contexto).
- Evidencia: `GA_FE_02_A_RESUME3_AUTHENTICATED_FINDINGS.md`; remediación D1: commit `ea26b2e`.

## Addendum GA-FE-02-B (2026-09-11) — disponibilidad en ENV-01

- Bootstrap `admin` (super, comodín) — verificado (login/`me`/`switch-company` 200).
- **Actor B**: rol canónico «Administrador de Accesos» **creado y disponible** (id=35; exactamente
  `business_units:read|update|create|delete`, plantilla de sistema) — GA-FE-02-B **F2 CLOSED**.
- **Actores A/C/D/E**: NO provisionados — la fixture E2E depende de **F1** (catálogo BU, pendiente
  server-side) ⇒ permanecen `BLOCKED` hasta ejecutar F1 y reanudar la certificación completa.
- `GET /users` operativo tras F3 (0 filas 500; 23 usuarios en empresa 1).

### Verificación 2026-09-11 (post-reporte F1)

Gate F1 **FALLÓ**: el catálogo sigue `[]` en ENV-01 (`count=0`; 4×404; `is_active default=True`
descarta «inactivas») ⇒ actores A–D **NO provisionados** (E2E STOP §6). El resto del entorno:
rol id=35 disponible · F2/F3/F4/D1 re-verificados verdes.
```

---

## Addendum GA-FE-02-C (2026-09-11) — ejecución autenticada real

**Empresa de prueba**: `Avícola Global C.A.` (id **1**, empresa de certificación de ENV-01) ·
empresa extranjera para E2E-07: `Avícola Del Sur C.A.` (id **3**). Sin contraseñas en este
documento; credenciales sintéticas efímeras (solo `/tmp`, 600, destruidas al cierre).

| ACTOR | USERNAME | ID | COMPANY | ROL | PERMISOS EFECTIVOS | ESTADO INICIAL | LOGIN INDEP. | PROPÓSITO | FINAL |
|---|---|---|---|---|---|---|---|---|---|
| A · COMPANY_BU_ADMIN | `ga-fe02-a` | 71 | 1 | **GA-FE02 TEST CBU ADMIN** (id 36, TEMPORAL) | `business_units:read` · `business_units:update` · `dashboard:read` | sin concesiones | **200** · `/me` 200 | habilitar/apagar BU de empresa (E2E-02/03) | dado de baja (§76) |
| B · ACCESS_ADMIN | `ga-fe02-b` | 72 | 1 | **Administrador de Accesos** (id 35, CANÓNICO `OD-15 §6`) | `business_units:read`·`update`·`create`·`delete` — sin `users:*` | sin concesiones | **200** · `/me` 200 | candidatos · conceder · revocar · auto-concesión (E2E-04/05/06) | dado de baja |
| C · TARGET_OPERATIONAL | `ga-fe02-c` | 73 | 1 | **GA-FE02 TEST PRODUCTIVE** (id 37, TEMPORAL) | `lots:read` (capacidad productiva representativa) | **sin** concesión de broiler | **200** · `/me` 200 | sujeto controlado de la matriz 3D (ALLOW/DENY reales) | dado de baja |
| D · UNAUTHORIZED | `ga-fe02-d` | 74 | 1 | **GA-FE02 TEST CORE** (id 38, TEMPORAL) | `dashboard:read` (entra a la app; cero admin; cero productivo) | sin concesiones | **200** · `/me` 200 | controles negativos autenticados (E2E-08 · MX-3) | dado de baja |
| X · FOREIGN_FIXTURE | `ga-fe02-x` | 75 | **3** | GA-FE02 TEST CORE (id 38) | `dashboard:read` | sin concesiones | **200** · `/me` 200 | fixture de otra empresa para E2E-07 | dado de baja |
| E · GLOBAL | `admin` (bootstrap) | 1 | — | Super Administrador | comodines `*` (9) | sin contexto | **200** · `/me` 200 | contexto situado · fail-closed · frontera global | cuenta preexistente (no tocada) |

**Fronteras verificadas en la corrida** (detalle en `GA_FE_02_A_E2E_MATRIX.md`):

- A **no** tiene `business_units:create/delete` → sus intentos de User-BU habrían sido 403
  (frontera CBU-admin ≠ User-BU-admin; §53).
- B posee las 4 acciones canónicas y aun así: **no puede auto-concederse** (403 `OD-15.a`) y
  **no gana acceso productivo** por su rol (sus lecturas productivas serían row-scope vacío; no
  se mutó su caso). Honestidad de capacidades: el rol 35 incluye `update` (plano de control),
  que **no** es autoridad productiva.
- C: capacidad productiva real vía `lots:read` + concesión + habilitación (matriz 3D completa).
- D: cero `business_units:*` → UI protegida y API 403×4.
- Roles temporales 36/37/38: compuestos **solo** de permisos canónicos existentes (§29);
  creados por API oficial (`POST /roles`), desactivados al cierre (`PUT /roles/{id}`,
  `is_active=false`). No son roles de negocio.

```
Usuarios sintéticos creados ..... 5 (71–75)
Logins independientes 200 ....... 5/5 (sesiones propias; sin copia de tokens)
Roles temporales creados ........ 3 (36/37/38 · solo permisos canónicos)
Rol canónico 35 ................. intacto y activo (4 permisos exactos)
Credenciales en repo/docs ....... 0
```
