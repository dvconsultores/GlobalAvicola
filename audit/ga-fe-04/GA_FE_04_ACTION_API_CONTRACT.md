# GA-FE-04 · CONTRATO ACCIÓN ↔ API ↔ AUTORIDAD

Capa de **descubribilidad** (frontend). El backend permanece autoridad final (§15/§57).
`can` = `useCan()`/`canPerformAction` sobre el vocabulario único de permisos (`auth/permissions`
espejo de `tiene_permiso`) + dimensiones BU de `auth/navigation` cuando aplica.

| Acción | VISIBLE cuando | Deshabilitada cuando | API | Método | Permiso backend | Guardas backend | Autorizado | No autorizado |
|---|---|---|---|---|---|---|---|---|
| U1/U2 alta usuario | `users:create` | — | `/users` | POST | users:create | inquilino; rol asignable | 201 | 403 (vía UI: oculto) |
| U3/U4/U5 editar/contraseña/toggle | `users:update` | objetivo inactivo donde aplique | `/users/{id}` | PUT/POST | users:update | inquilino; self-restricciones existentes | 200/204 | 403 |
| U6 desactivar | `users:delete` | actor==objetivo (política existente) | `/users/{id}` | DELETE | users:delete | inquilino | 204 | 403 |
| R1/R2 rol alta/edición | `users:create` (alta) / `users:update` (edición) | — | `/roles`·`/roles/{id}` | POST/PUT | users:create/update | plantillas de sistema visibles; alta permitida según contrato | 201/200 | 403 |
| R3 desactivar rol | `users:update` | — | `/roles/{id}` | PUT | users:update | ídem | 200 | 403 |
| M1 maestro alta | `masters:create` | — | `/masters/{entity}` | POST | masters:create | inquilino | 201 | 403 |
| M2 maestro edición | `masters:update` | — | `/masters/{entity}/{id}` | PUT | masters:update | inquilino | 200 | 403 |
| M3 maestro borrado | `masters:delete` | — | `/masters/{entity}/{id}` | DELETE | masters:delete | inquilino | 204 | 403 |
| W1 cargar curva | `masters:create` | — | `/masters/weight-curves` | POST | masters:create | valida tabla | 201 | 403/400 |
| W2 activar curva | `masters:update` | — | `/masters/weight-curves/{id}/activate` | PUT | masters:update | — | 200 | 403 |
| L1 CTA nuevo lote | `lots:create` | — | (navega) | — | destino lots:create | — | — | — |
| L2 guardar lote | `lots:create` (ruta) | — | `/lots` | POST | lots:create | inquilino+BUs del actor | 201 | 403 |
| L3 cerrar lote | `lots:create` | reglas de cierre (`GA-REM-036`/`029`) intactas | `/lots/{id}/close` | POST | lots:create | resource-state | 200 | 403/409 |
| L4 añadir fase | `lots:create` | — | `/lots/{id}/phases` | POST | lots:create | — | 201 | 403 |
| L5 resolver alerta | `operations:update` | — | `/operations/alerts/{id}/resolve` | PATCH | operations:update | — | 200 | 403 |
| O2 guardar operación | `operations:create` (ruta) | validaciones de formulario | `/operations` | POST | operations:create | BU del lote (R-163) | 201 | 403 |
| O3 subir evidencia | `operations:create` | — | `/operations/{id}/evidences` | POST | operations:create | vínculo/subida existente | 201 | 403 |
| O4 borrar evidencia | `operations:delete` | — | `…/evidences/{eid}` | DELETE | operations:delete | — | 204 | 403 |
| O6 cancelar (si UI) | `operations:create` | estado del evento | `/operations/{id}/cancel` | POST | operations:create | resource-state | 200 | 403 |
| V1/V2 revisar | `review:review` | estado del evento | `/review/start|complete|return` | POST | review:review | resource-state + ámbito | 200 | 403 |
| V3 lote de revisión | `review:review` | — | `/review/batches` | POST | review:review | — | 201 | 403 |
| V4 corregir | `corrections:correct` | — | (navega) | — | destino corrections:correct | — | — | — |
| V5 ídem V1/V2 en detalle | `review:review` | ídem | ídem | POST | review:review | ídem | 200 | 403 |
| V6 aprobar | `approvals:approve` | estado=corrected | `/approvals/approve` | POST | approvals:approve | resource-state | 200 | 403 |
| V6r rechazar | `approvals:reject` | ídem | `/approvals/reject` | POST | approvals:reject | observations | 200 | 403 |
| V7 guardar corrección | `corrections:correct` (ruta+acción) | — | `/corrections` | POST | corrections:correct | vínculo | 201 | 403 |
| V9 rechazar (panel) | `approvals:reject` | — | `/approvals/reject` | POST | approvals:reject | — | 200 | 403 |
| V10 batch + selección | `review:review` | — | `/approvals/batch-*` | POST | **review:review** | — | 200 | 403 |
| G1/G2/G3 SAP mutaciones | `sap:send_sap` | — | `/sap/consolidate|export|retry` | POST | sap:send_sap | — | 200 | 403 |
| G4 import refs (si UI) | `sap:send_sap` | — | `/sap/references/import` | POST | sap:send_sap | — | 201 | 403 |

**Notas canónicas respetadas**:
- `V6`/`V9`: aprobar y rechazar son **permisos distintos** (approvals:approve / approvals:reject);
  el gate NO los unifica.
- `V10`: el batch usa `review:review` (contrato del router); el gate sigue el contrato, no la intuición.
- `L3/L4`: ambos usan `lots:create` (contrato del router), aunque su semántica parezca «update».
- `O5` (`submit`) **no se toca**: `EXCLUDED_R181`.
- La guarda de ruta se valida **independientemente** del botón: un deep link sin autoridad recibe
  la negativa visual (`common.noPermission`, GA-FE-03) y el backend responde 403 igualmente.
