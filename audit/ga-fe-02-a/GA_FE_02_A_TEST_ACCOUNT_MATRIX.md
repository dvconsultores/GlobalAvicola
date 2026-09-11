# GA-FE-02-A · TEST ACCOUNT MATRIX (§16)

Sin contraseñas, sin tokens. Estado de esta ejecución: **ninguna cuenta disponible** (MODE_C).
Las columnas describen el objetivo; los valores se completarán en la reanudación autenticada.

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
