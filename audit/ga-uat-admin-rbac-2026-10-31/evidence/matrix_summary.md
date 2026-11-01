# AC-MX-01 · Matriz de autorización ejecutada (`SPEC 013`, `B4a`)

Generada por `backend/tests/test_uat_admin_rbac_matrix.py` con `GA_WRITE_MATRIX=1`.
Fecha (UTC): 2026-10-31T23:41:42+00:00.

## Totales

* rutas protegidas enumeradas por introspección: **229**
* pares `(modulo, accion)` exigidos por alguna ruta: **41**
* sondas ejecutadas: **2552** (ALLOW 965 · DENY 1528 · sin sesión 59)
* resultado: **PASS 2552 · FAIL 0**
* tiempo: rol_vacio 2.9 s, roles_producto 22.3 s, sin_sesion 0.2 s, un_permiso 9.2 s · total 34.6 s

## Por rol

| rol | ALLOW | DENY | PASS | FAIL |
|---|---|---|---|---|
| (anónimo) | 0 | 46 | 46 | 0 |
| MX-TEST-Administrador de Accesos-01daec03 | 7 | 222 | 229 | 0 |
| MX-TEST-Analista SAP-01daec03 | 93 | 136 | 229 | 0 |
| MX-TEST-Aprobador-01daec03 | 88 | 141 | 229 | 0 |
| MX-TEST-Auditor-01daec03 | 83 | 146 | 229 | 0 |
| MX-TEST-Operador de Granja-01daec03 | 64 | 165 | 229 | 0 |
| MX-TEST-Rol vacío-d3d0e7a0 | 0 | 229 | 229 | 0 |
| MX-TEST-Solo approvals:approve-53ab07a4 | 3 | 3 | 6 | 0 |
| MX-TEST-Solo approvals:reject-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo audit:read-53ab07a4 | 3 | 3 | 6 | 0 |
| MX-TEST-Solo business_units:create-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo business_units:delete-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo business_units:read-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo business_units:update-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo corrections:correct-53ab07a4 | 3 | 3 | 6 | 0 |
| MX-TEST-Solo corrections:read-53ab07a4 | 3 | 3 | 6 | 0 |
| MX-TEST-Solo cutover:apply-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo cutover:approve-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo cutover:create-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo cutover:read-53ab07a4 | 7 | 3 | 10 | 0 |
| MX-TEST-Solo cutover:submit-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo cutover:validate-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo dashboard:read-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo lots:create-53ab07a4 | 6 | 3 | 9 | 0 |
| MX-TEST-Solo lots:read-53ab07a4 | 5 | 3 | 8 | 0 |
| MX-TEST-Solo lots:update-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo masters:create-53ab07a4 | 21 | 3 | 24 | 0 |
| MX-TEST-Solo masters:delete-53ab07a4 | 20 | 3 | 23 | 0 |
| MX-TEST-Solo masters:read-53ab07a4 | 44 | 3 | 47 | 0 |
| MX-TEST-Solo masters:update-53ab07a4 | 22 | 3 | 25 | 0 |
| MX-TEST-Solo operations:create-53ab07a4 | 4 | 3 | 7 | 0 |
| MX-TEST-Solo operations:delete-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo operations:read-53ab07a4 | 7 | 3 | 10 | 0 |
| MX-TEST-Solo operations:update-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo reports:read-53ab07a4 | 15 | 3 | 18 | 0 |
| MX-TEST-Solo reversals:create-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo reversals:read-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo review:create-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo review:delete-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo review:read-53ab07a4 | 4 | 3 | 7 | 0 |
| MX-TEST-Solo review:review-53ab07a4 | 4 | 3 | 7 | 0 |
| MX-TEST-Solo review:update-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo sap:read-53ab07a4 | 12 | 3 | 15 | 0 |
| MX-TEST-Solo sap:send_sap-53ab07a4 | 8 | 3 | 11 | 0 |
| MX-TEST-Solo users:create-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Solo users:delete-53ab07a4 | 1 | 3 | 4 | 0 |
| MX-TEST-Solo users:read-53ab07a4 | 4 | 3 | 7 | 0 |
| MX-TEST-Solo users:update-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Super Administrador-01daec03 | 228 | 0 | 228 | 0 |
| MX-TEST-Super Administrador-ba412384 | 0 | 13 | 13 | 0 |
| MX-TEST-Supervisor Avícola-01daec03 | 92 | 137 | 229 | 0 |
| MX-TEST-Todo menos approvals:approve-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Todo menos approvals:reject-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos audit:read-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Todo menos business_units:create-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos business_units:delete-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos business_units:read-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos business_units:update-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos corrections:correct-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Todo menos corrections:read-53ab07a4 | 2 | 3 | 5 | 0 |
| MX-TEST-Todo menos cutover:apply-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos cutover:approve-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos cutover:create-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos cutover:read-53ab07a4 | 2 | 7 | 9 | 0 |
| MX-TEST-Todo menos cutover:submit-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos cutover:validate-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos dashboard:read-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos lots:create-53ab07a4 | 2 | 6 | 8 | 0 |
| MX-TEST-Todo menos lots:read-53ab07a4 | 2 | 5 | 7 | 0 |
| MX-TEST-Todo menos lots:update-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos masters:create-53ab07a4 | 2 | 21 | 23 | 0 |
| MX-TEST-Todo menos masters:delete-53ab07a4 | 2 | 20 | 22 | 0 |
| MX-TEST-Todo menos masters:read-53ab07a4 | 2 | 44 | 46 | 0 |
| MX-TEST-Todo menos masters:update-53ab07a4 | 2 | 22 | 24 | 0 |
| MX-TEST-Todo menos operations:create-53ab07a4 | 2 | 4 | 6 | 0 |
| MX-TEST-Todo menos operations:delete-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos operations:read-53ab07a4 | 2 | 7 | 9 | 0 |
| MX-TEST-Todo menos operations:update-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos reports:read-53ab07a4 | 2 | 15 | 17 | 0 |
| MX-TEST-Todo menos reversals:create-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos reversals:read-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos review:create-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos review:delete-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos review:read-53ab07a4 | 2 | 4 | 6 | 0 |
| MX-TEST-Todo menos review:review-53ab07a4 | 2 | 4 | 6 | 0 |
| MX-TEST-Todo menos review:update-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos sap:read-53ab07a4 | 2 | 12 | 14 | 0 |
| MX-TEST-Todo menos sap:send_sap-53ab07a4 | 2 | 8 | 10 | 0 |
| MX-TEST-Todo menos users:create-53ab07a4 | 2 | 2 | 4 | 0 |
| MX-TEST-Todo menos users:delete-53ab07a4 | 2 | 1 | 3 | 0 |
| MX-TEST-Todo menos users:read-53ab07a4 | 2 | 4 | 6 | 0 |
| MX-TEST-Todo menos users:update-53ab07a4 | 2 | 2 | 4 | 0 |

## `allow_no_sondeada`

* `POST /api/v1/approval-steps/seed-defaults` → `review:create`

## Pares del catálogo sin sonda ALLOW

* ninguno

## Rutas protegidas nunca sondeadas

* ninguna
