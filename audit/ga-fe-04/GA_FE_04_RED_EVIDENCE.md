# GA-FE-04 · Evidencia RED (pre-implementación)

Fecha: 2026-09-11 · Generación congelada: bundle `index-CElqNz3R.js` (producto GA-FE-03, sin gates intra-pantalla)
Actor pre-fix: `ga-fe04-r` (id 98, rol 41 «GA-FE04 TEST READ-ONLY ADMIN»: `dashboard:read` + `users:read` + `masters:read`, sin unidades de negocio)

## 1 · RED de pruebas (Vitest) — 10 fallas objetivo + 1 módulo ausente

Comando: `npx vitest run` (suite completa) → **258 tests · 248 passed · 10 failed · 34 archivos (26 ok / 8 con fallas objetivo)**.

| Archivo | Caso | Tipo | Estado |
|---|---|---|---|
| `src/auth/__tests__/gaFe04.actionAuthority.test.tsx` | import `../actionAuthority` | módulo ausente | FAIL (RED por diseño) |
| `src/pages/users/__tests__/gaFe04.usersGates.test.tsx` | R (`users:read`) sin controles de escritura | objetivo | FAIL (RED) |
| ídem | control con `users:*` ve Crear/editar/eliminar | control | PASS |
| `src/pages/masters/__tests__/gaFe04.mastersGates.test.tsx` | R (`masters:read`) sin Nuevo/Editar/Eliminar | objetivo | FAIL (RED) |
| ídem | control con `masters:*` | control | PASS |
| `src/pages/approvals/__tests__/gaFe04.approvalGates.test.tsx` | sin permisos ⇒ sin Aprobar/Rechazar | objetivo | FAIL (RED) |
| ídem | `approvals:approve` sin `reject` ⇒ Rechazar oculto | objetivo | FAIL (RED) |
| ídem | control approve+reject+review | control | PASS |
| `src/pages/review/__tests__/gaFe04.reviewGates.test.tsx` | `review:read` ⇒ sin Iniciar/Completar/Devolver | objetivo | FAIL (RED) |
| ídem | control `review:review` | control | PASS |
| `src/pages/sap/__tests__/gaFe04.sapGates.test.tsx` | `sap:read` ⇒ sin Consolidar/Exportar | objetivo | FAIL (RED) |
| ídem | control `sap:send_sap` | control | PASS |
| `src/pages/lots/__tests__/gaFe04.lotsGates.test.tsx` | `lots:read` ⇒ sin CTA Nuevo lote | objetivo | FAIL (RED) |
| ídem | control `lots:create` | control | PASS |
| `src/__tests__/gaFe04.routeParity.test.tsx` | R en `/lots/new`, `/operations/new`, `/review/:id/correct` ⇒ negativa | objetivo ×3 | FAIL (RED) |
| ídem | control C con `create` en su unidad ⇒ permitido | control | PASS |

Fallas sin daño colateral: 248 pruebas preexistentes siguen en verde.

## 2 · RED de runtime (pre-fix, producción)

### 2.1 UI — el actor de solo lectura VE controles de escritura (defecto R-98)

| Pantalla | Hallazgo R (`ga-fe04-r`) | Captura |
|---|---|---|
| `/masters/farms` | `Nuevo`=1 · `Editar`=7 · `Eliminar`=7 botones visibles | `evidence/red/RED_masters_farms_R_write_controls_visible.png` |
| `/users` | botón `Crear`=1 visible (y chips de estado «Activo» accionables) | `evidence/red/RED_users_R_create_visible.png` |

### 2.2 API — el backend SÍ es la autoridad (403), lo que confirma «ocultar no es autorizar»

Con el token de `ga-fe04-r`:

| Llamada | Resultado |
|---|---|
| `GET /users?limit=5` | 200 (lectura permitida) |
| `PUT /masters/farms/1` | **403** `Permiso requerido: masters:update` |
| `POST /masters/farms` | **403** `Permiso requerido: masters:create` |
| `DELETE /masters/farms/1` | **403** `Permiso requerido: masters:delete` |
| `POST /users` | **403** `Permiso requerido: users:create` |

### 2.3 `/me` del actor R

`is_super_admin=false` · `permissions=['dashboard:read','masters:read','users:read']` · sin CBU/GBU.

## 3 · Conclusión RED

La brecha R-98 queda demostrada por **dos vías independientes**: la UI muestra acciones de escritura a quien no puede ejecutarlas (10 fallas objetivo de Vitest + capturas), mientras el backend mantiene la autoridad (403). La solución debe ocultar/deshabilitar por **permiso de acción**, no por rol ni por nombre de usuario, y mantener la autoridad del servidor.

> Nota de ID real: la asignación de fixtures en producción dio rol **41** = «GA-FE04 TEST READ-ONLY ADMIN» (el borrador de matriz preveía 41/42 en otro orden). El rol duplicado 42 fue desactivado en la misma sesión. La matriz de actores se reconcilia con los IDs reales en la fase de certificación.
