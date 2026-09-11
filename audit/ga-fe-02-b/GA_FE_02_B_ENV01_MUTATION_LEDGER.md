# GA-FE-02-B · ENV-01 MUTATION LEDGER

**Regla**: toda mutación de entorno (ENV-01) autorizada por GA-FE-02-B se registra aquí con
timestamp, actor/herramienta, target, BEFORE, operación, AFTER, reversibilidad, rollback, AC y
evidencia. **Sin credenciales, sin passwords, sin tokens.**

| # | Fecha | Actor/Tool | Target | BEFORE | Operación | AFTER | ¿Reversible? | Rollback | AC | Evidencia |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-09-11 | Agente · API oficial `POST /roles` (super admin, sin contexto) | ENV-01 · rol «Administrador de Accesos» | Ausente (13 roles activos) | Creación con los 4 permisos canónicos `business_units:read|update|create|delete` (scope `all`) | **id=35** · `company_id NULL` (plantilla de sistema) · exactamente 4 permisos; `GET /roles` total=14; único rol con módulo `business_units` | Sí — `PUT /roles/35` | Mantener como fixture canónico (rol de producto `R-113`/`OD-15 §6`) | AC-F2 | `ROLE_HTTP=201` + verificación `GET /roles`; respuesta en `/tmp/ga_role_create.json` (600) |
| 2 | 2026-09-11 | Agente · API oficial `PUT /users/{id}` (super admin situado en empresa 1) | ENV-01 · usuarios **57–70** (14: 7 móvil + 7 web) | `email=…@testing.local` ⇒ `GET /users/{id}` = **500** ×14; `GET /users` ≥10 filas = 500 | Reparación mínima del dominio del email (parte local = username; nuevo dominio `globalavicola.com`) | `PUT` = **200** ×14 con `username` verificado contra el seed (sin desviaciones) · `GET` = **200** ×14 · `limit=100` = 200 (23 usuarios) · default = 200 | Sí — restaurar `@testing.local` (valor original conocido) | Corrección de fixture malformada (invariante documentado en `baseline_seeds`) | AC-F3 | Antes: `/tmp/ga_f3_before.txt`; reparación: `/tmp/ga_f3_repair.txt`; respuestas por fila `/tmp/ga_f3_rep_*.json` (600). Nota: el primer barrido usó token sin contexto → 403/404 y el guard cortó SIN ninguna mutación; se repitió con `switch-company` a empresa 1 |
| 3 | 2026-09-11 | Agente · commit `b83d908` (repo; sin tocar ENV) | `backend/seeds/integration_seeds.py` + test de regresión | Plantilla de emails `@testing.local` | Dominio válido `@globalavicola.com` + guard de dominios reservados | Semilla endurecida (grep de reservados: 0 coincidencias) | Sí — revert del commit | Evitar recreación de la fixture (R-44) | AC-F3 | El runner backend exige `GA_TEST_ENV` + `GA_TEST_DATABASE_URL` aislados (no disponibles localmente); el test corre en CI de PRs |
| 4 | 2026-09-11 | Agente · commit `716d175` (F4) + deploy por pipeline | Frontend (`Header`/`auth.store`/locales/test) | Selector no renderizado sin nombre; nombre sin resolver con persistida `null` | Fix mínimo (condición de render + resolución de nombre) | RED→GREEN; TSC 0; Vitest 205/205; build OK | Sí — revert (deploy restaura) | — (sin mutación de ENV) | AC-F4 | Verificación runtime PASS (selector «Seleccionar empresa»; dropdown 2 empresas; switch a Avícola Global C.A. 200; nombre en header; /admin/unit-access «Empresa: Avícola Global C.A.»; hard-refresh `/me` 200 sin forbidden; móvil 390×844) — bundle `index-B2-tZnkI.js` |

## Política

- **F1** (catálogo): server-side (owner/ops) — al ejecutarse, registrar: comando, salida
  (`creadas: N`), postcondición `GET /business-units`. No crea habilitaciones ni concesiones.
- **F2** (rol): `POST /roles` (API oficial, super admin sin contexto → plantilla `company_id NULL`).
  Reversible (`PUT /roles/{id}`); estado preferido del fixture: rol activo canónico.
- **F3** (emails): `PUT /users/{id}` por fila (57–70). Reversible a `{username}@testing.local`
  (valor original conocido). Solo dominio del email; parte local conservada; sin tocar credenciales.
- **F4**: sin mutación de ENV (código; deploy por pipeline).
- **Actores A–E** (§8 spec): alta por `POST /users` (API oficial) con passwords generadas fuera del
  repo; asignación de rol canónico; concesiones por `POST /users/{id}/business-units`. Reversible:
  desactivar usuario (`DELETE /users/{id}`), revocar concesiones (`DELETE .../business-units/{code}`).
- **Concesiones/habilitaciones E2E**: por flujos oficiales; restauración documentada al cierre;
  las filas `CompanyBusinessUnit` deshabilitadas permanecen («apagada explícitamente ≠ nunca
  configurada») y se documentan como artefacto residual legible.
