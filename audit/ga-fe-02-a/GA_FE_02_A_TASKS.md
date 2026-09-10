# GA-FE-02-A · TASKS ATÓMICAS (E2E)

Formato: ID · E2E · actor · precondiciones · estado BU/empresa · acción UI · request esperado ·
estado backend esperado · UI esperada · refresh · relogin · control negativo · evidencia ·
cleanup · estado. **Estado de todas: `BLOCKED_AUTH`** (MODE_C — sin credenciales autorizadas).

| ID | E2E | Actor | Precondición | Acción (UI) | Request esperado | Backend esperado | Refresh/Relogin | Negativo | Estado |
|---|---|---|---|---|---|---|---|---|---|
| T01 | E2E-01a | A | login bootstrap A; empresa de prueba asignada | login → shell → indicador de empresa → abrir Admin → verificar contexto | `GET /me` (permisos+empresa) · `GET /business-units` | 200; `effective_company_id` = empresa de prueba | refresh → mismo contexto | — | `BLOCKED_AUTH` |
| T02 | E2E-01b | A (si elegible) | actor con switch | selector de empresa → B → verificar B en UI y backend → volver a A | `POST /switch-company {id:B}` → `GET /me` | tokens nuevos; contexto B; **cero datos A** | refresh tras volver → A limpio | intentar empresa no autorizada (si fixture) → denegado | `BLOCKED_AUTH` |
| T03 | E2E-02a | A | BU objetivo OFF; concesiones de prueba registradas | abrir Admin → verificar 4 BUs → click Activar en la BU objetivo → confirmar | `PATCH /business-units/{code}/enable` | 200 `is_enabled:true`; **0 concesiones creadas** | refresh → sigue ON | — | `BLOCKED_AUTH` |
| T04 | E2E-02b | A | tras T03 | verificar las otras 3 BUs sin cambio | — | estados independientes | — | — | `BLOCKED_AUTH` |
| T05 | E2E-03a | A | BU objetivo ON | click Desactivar → confirmar | `PATCH /business-units/{code}/disable` | 200 `is_enabled:false`; concesiones **no** borradas | refresh → OFF | — | `BLOCKED_AUTH` |
| T06 | E2E-03b | C | grant almacenado del objetivo; BU OFF | C: intento productivo representativo | p.ej. `GET` productivo gobernado de esa BU | **DENY** (403/404 según contrato) | relogin C → mismo DENY | global (si hay credencial) → DENY | `BLOCKED_AUTH` |
| T07 | E2E-03c | A | BU OFF | el control plane sigue pudiendo reactivar | UI de la página accesible | re-enable posible (se restaura fixture) | — | — | `BLOCKED_AUTH` |
| T08 | E2E-04a | B | BU ON; C sin grant; B≠C | `/admin/unit-access` → candidatos → Conceder a C | `POST /users/{C}/business-units {code}` | 201; concesión viva | refresh → persiste | — | `BLOCKED_AUTH` |
| T09 | E2E-04b | C | tras T08 | relogin de C → BU efectiva | `GET /me` | `effective_business_units` incluye code | relogin exigido | — | `BLOCKED_AUTH` |
| T10 | E2E-04c | C | RBAC sí (fixture) | operación representativa | GET productivo gobernado | **ALLOW** | — | — | `BLOCKED_AUTH` |
| T11 | E2E-05a | B | C con grant vivo | Revocar → confirmar | `DELETE /users/{C}/business-units/{code}` | 200 `revoked_at` no nulo | refresh admin → revocado | — | `BLOCKED_AUTH` |
| T12 | E2E-05b | C | tras T11 | relogin C | `GET /me` | code **ausente** de efectivas | relogin | operación productiva → DENY | `BLOCKED_AUTH` |
| T13 | E2E-06 | B | B = Access Admin | abrir panel propio (si la UI lo permite) → verificar sin acción; petición directa | `POST /users/{B}/business-units {code}` | **403** (segregación) | — | sin fila, sin auditoría de éxito | `BLOCKED_AUTH` |
| T14 | E2E-07 | B | usuario de empresa C2 (si fixture seguro) | candidatos no lo listan; petición directa | `POST /users/{C2}/business-units` | **404/deny**; sin fuga | — | anti-enumeración | `BLOCKED_AUTH` (o `BLOCKED_FIXTURE` si no hay segunda empresa segura) |
| T15 | E2E-08 | D | D autenticado sin permisos | nav sin entrada accionable; ruta directa; API directa | `GET /business-units` | **403** | — | sin mutación posible | `BLOCKED_AUTH` |
| T16 | E2E-09 | A/C | BU ON; C sin grant; RBAC sí | UI: empresa Activa + usuario No concedida; C: operación | GET productivo | **DENY** | captura + red | — | `BLOCKED_AUTH` |
| T17 | E2E-10 | A/C | grant almacenado; BU OFF | UI: no implica acceso activo; C: operación | GET productivo | **DENY**; grant conservado | re-habilitar (restauración) | registrar BU-D10 observado (sin ratificar) | `BLOCKED_AUTH` |
| T18 | matriz 3D | A/C | 4 combinaciones BU/grant/RBAC | (según T16/T10/T17) | GET productivo | DENY, DENY, DENY, ALLOW | — | — | `BLOCKED_AUTH` |
| T19 | refresh ×5 | A/B | tras cada mutación | F5 | refetch natural | persistencia | — | — | `BLOCKED_AUTH` |
| T20 | mobile | A/B | viewport 390×844 | flujos críticos | — | acciones alcanzables | — | — | `BLOCKED_AUTH` |

## Notas

- Ningún task se ejecutó: no hay actor bootstrap ni credenciales autorizadas (paso 29 §133 →
  rama §79). No se abrió ninguna mutación; el ledger quedó vacío.
- Al entregarse las cuentas, estos tasks se ejecutan **en el orden §133** y cada uno produce
  request/estado/evidencia en `GA_FE_02_A_E2E_MATRIX.md` y `GA_FE_02_A_NETWORK_EVIDENCE.md`.
