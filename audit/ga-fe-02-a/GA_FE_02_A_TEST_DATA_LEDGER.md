# GA-FE-02-A · TEST DATA LEDGER (§100)

**Estado: VACÍO** — no se creó, mutó ni eliminó ningún dato en esta ejecución (`MODE_C ·
BLOCKED_AUTH`). No hubo mutaciones; no hay nada que restaurar.

| ITEM | TYPE | ID | CREATED/EXISTING | INITIAL STATE | MUTATIONS | FINAL STATE | RESTORED? | OWNER | SAFE TO RETAIN? |
|---|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | — | — | — |

```
Datos creados ................. 0
Datos mutados ................. 0
Usuarios reales tocados ....... 0
Concesiones creadas ........... 0
Business Units alteradas ...... 0
BU-D10 ........................ PENDING_RATIFICATION (intacto; nada observado)
```

Al reanudar la certificación autenticada, cada artefacto de prueba se registrará aquí con el
prefijo `GA_FE_02_E2E_<timestamp>` y se restaurará al estado del snapshot previo (§72).
Nunca se almacenan credenciales en este ledger.

**Actualización 2026-09-11 (resume de self-provisioning)**: el ledger SIGUE VACÍO — la pasada
se detuvo en `BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED` (investigación completa en
`GA_FE_02_A_AUTH_PROVISIONING_MAP.md`): 0 cuentas creadas · 0 mutaciones · 0 usuarios reales
tocados.

---

## Addendum GA-FE-02-C (2026-09-11) — ledger de la corrida de certificación

**Todo por flujos oficiales** (API/UI autenticadas). Sin SQL manual, sin `docker exec`, sin
SSH. Cada fila con evidencia en `GA_FE_02_A_NETWORK_EVIDENCE.md` y auditoría de aplicación
(`GET /audit`). Los sondeos de selección de BU (fase de fixture previa, 4 concesiones
creadas+revocadas) quedan como historia revocada en la misma auditoría.

| ITEM | TIPO | ID/CLAVE | ESTADO INICIAL | MUTACIONES (corrida) | ESTADO FINAL | RESTAURADO |
|---|---|---|---|---|---|---|
| Company BU · broiler (c1) | habilitación | `broiler` | `false` | enable ×3 (A-UI, A-UI-re, admin-API-prep) · disable ×3 (A-UI, mobile-UI, restauración) | **`false`** | **SÍ** |
| Company BU · otras 3 | habilitación | `breeder/grandparent/hatchery` | `false` | ninguna (verificado intactas en E2E-02c) | `false` | SÍ (nunca tocadas) |
| Concesión C→broiler | `UserBusinessUnit` (73) | broiler | sin concesiones vivas | grant ×2 (B-UI · B-API) · revoke ×2 (B-UI · B-Móvil) | **sin vivas** (`revoked_at` en historia) | **SÍ** |
| Concesión D→broiler | `UserBusinessUnit` (74) | broiler | sin concesiones | grant ×1 (B-API, MX-3) · revoke ×1 (B-API) | sin vivas | SÍ |
| Auto-concesión B→B | intento | 72 | — | **403** — sin fila, sin auditoría de éxito | — | n/a |
| Concesión B→X (75, c3) | intento | 75 | — | **404** — sin fila, sin persistencia | — | n/a |
| Usuarios sintéticos | `users` | 71–75 | creados (POST /users oficiales) | baja al cierre (DELETE /users/{id} → `is_active=false`; login posterior **403**) | inactivos (§76) | n/a (fixtures) |
| Roles temporales | `roles` | 36/37/38 | creados (`POST /roles`, solo permisos canónicos) | desactivados (`PUT /roles/{id}` → `is_active=false`) | inactivos | n/a (fixtures) |
| Rol canónico | `roles` | 35 | activo (F2) | **ninguna** en la corrida | activo, idéntico | — |
| Lote de escritura global | intento | `GA-FE02-WRITE-DENY-1` | — | **403** (R-163) — sin fila | — | n/a |
| Auditoría | `audit_logs` | — | 71 filas | +14 `config_change`/`company_business_unit` · +15 `permission_change`/`user_business_unit` (actor/empresa/objetivo/timestamp) | append-only, conservada | n/a (historia) |

```
Datos de negocio reales tocados .. 0 (empresa 1 es empresa de certificación)
Usuarios humanos modificados ...... 0
Eliminaciones ..................... 0 (todo es historial conservado o baja lógica)
Credenciales en este ledger ....... 0
BU-D10 ............................ OBSERVED_RUNTIME_BEHAVIOR: con CBU OFF y concesión viva,
                                    la fila se conserva con is_effective=false (rehabilitar la
                                    devuelve — AC-A06). OWNER_RATIFIED_POLICY: NONE.
```
