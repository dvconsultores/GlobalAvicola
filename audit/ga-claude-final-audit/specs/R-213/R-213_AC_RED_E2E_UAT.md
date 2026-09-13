# R-213 · AC · RED · E2E · UAT (COMPACTO)

HEAD `c0b4afc` · Artefactos bajo `specs/R-213/evidence/`.

## 1 · Criterios de aceptación

| AC | Criterio | Test (RED) |
|---|---|---|
| AC-R213-01 | `/me` con correo legacy en BD ⇒ 200 (correo tal cual) | `test_r213_01` (rojo: 500) |
| AC-R213-02 | `/users` con una fila de correo legacy ⇒ 200 (fila visible) | `test_r213_02` (rojo: 500) |
| AC-R213-03 | Alta con correo inválido ⇒ 422 (escritura estricta intacta; control) | `test_r213_03` (verde) |
| AC-R213-04 | Edición con correo inválido ⇒ 422 (control) | `test_r213_04` (verde) |
| AC-R213-05 | `/me` con correos normales ⇒ idéntico (control) | `test_session_payload.py` |
| AC-R213-06 | Sin migración/endpoint/permiso; lectura `str`, escritura `EmailStr` | revisión diff |
| AC-R213-07 | Regresión: `test_user_tenant_isolation.py`, `test_p013_password.py`, `test_role_administration.py` verdes | suites |

## 2 · Diseño RED

`backend/tests/test_r213_me_email_tolerance.py`: insertar usuario con `…@e.test` (o `.local`) por fixture directa en BD; `GET /me` y `GET /users` (rojo: 500); alta inválida 422 (verde). Ejecución PG de pruebas; salida `evidence/red/`.

## 3 · E2E (API)

`R213-RT-01…03`: `/me` legacy 200; `/users` 200; alta inválida 422. Artefacto `evidence/r213/runtime-{red,c3}.json`.

## 4 · UAT

**No requerida.** Verificación informativa: sesión con un usuario de correo legacy ya no queda degradada.
