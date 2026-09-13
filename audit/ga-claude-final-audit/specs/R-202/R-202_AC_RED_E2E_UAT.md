# R-202 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-202/evidence/`.

## 1 · Criterios de aceptación

| AC | Criterio | Test (RED) |
|---|---|---|
| AC-R202-01 | Super admin **sin contexto** → objetivo de otra empresa ⇒ 4xx fail-closed; sin cambio de contraseña | `test_r202_01` (rojo: 200) |
| AC-R202-02 | Super admin **situado** en la empresa del objetivo ⇒ 200 (control) | `test_r202_02` (verde) |
| AC-R202-03 | Admin de empresa con `users:update`, objetivo de su empresa ⇒ 200 | `test_r202_03` (rojo: 403) |
| AC-R202-04 | `users:update` + objetivo de otra empresa ⇒ 403/404 fail-closed | `test_r202_04` (rojo/verde) |
| AC-R202-05 | Titular con contraseña actual ⇒ 200 (control) | `test_p013_password` existente |
| AC-R202-06 | Auditoría con empresa efectiva del actor y objetivo | `test_r202_06` (rojo: empresa del objetivo) |
| AC-R202-07 | Sin migración/endpoint/permiso nuevo | revisión diff |
| AC-R202-08 | Regresión `test_p013_password.py` (8), `test_user_tenant_isolation.py` verdes | suites |

## 2 · Diseño RED

`backend/tests/test_r202_password_reset_scope.py`: casos 01-04 y 06 con tres actores (global sin contexto, global situado, admin de empresa) y dos empresas. Rojos exactos: 01 (200⇒4xx), 03 (403⇒200), 06 (empresa auditada). Ejecución con PG de pruebas; salida a `evidence/red/`.

## 3 · E2E (API)

`R202-RT-01…04`: mismas matrices por HTTP con contadores de cambio de contraseña (verificación de no-alcance). Artefacto `evidence/r202/runtime-{red,c3}.json`.

## 4 · UAT

**No requerida** (superficie de administración; el cambio no altera el flujo legítimo del titular ni del admin de su empresa). Verificación informativa opcional: admin de empresa restablece una contraseña de su ámbito.
