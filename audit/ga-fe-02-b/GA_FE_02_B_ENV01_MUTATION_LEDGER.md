# GA-FE-02-B · ENV-01 MUTATION LEDGER

**Regla**: toda mutación de entorno (ENV-01) autorizada por GA-FE-02-B se registra aquí con
timestamp, actor/herramienta, target, BEFORE, operación, AFTER, reversibilidad, rollback, AC y
evidencia. **Sin credenciales, sin passwords, sin tokens.**

| # | Fecha | Actor/Tool | Target | BEFORE | Operación | AFTER | ¿Reversible? | Rollback | AC | Evidencia |
|---|---|---|---|---|---|---|---|---|---|---|
| — | — | — | *(vacío al cierre del COMMIT 1 — las entradas se añaden al ejecutar F2/F3)* | — | — | — | — | — | — | — |

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
