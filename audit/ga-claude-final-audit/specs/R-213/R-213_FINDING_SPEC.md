# R-213 · FINDING + SPEC (COMPACTO) — `/me` Y `/users` RESPONDEN 500 SI EL CORREO PERSISTIDO NO SUPERA `EmailStr`

| Campo | Valor |
|---|---|
| **ID** | **R-213** · P3 · **no bloquea** · Estado `SPEC_READY` |
| **Origen** | Sonda `me500_probe.log`; grupo B de GA-GOV-03; informe D (colateral) · Registro G-25 · HEAD `c0b4afc` · 2026-09-13 |
| **GA-REM** | a asignar; sin migración/endpoint/permiso · UAT: no |

## 1 · Contexto y evidencia

`auth/service.py:329` — `UserRead.model_validate(user)` lanza `ValidationError` (⇒ 500) para correos que `pydantic 2.13.4` + `email_validator 2.3.0` rechazan en lectura (`*.test`, `.invalid`, `.local`, `example.test`…): `evidence/backend_r188_me500.log:81` («GET /api/v1/me → 500»); `me500_probe.log`. La sonda nace del fixture de `test_r188_bu_lifecycle.py:79` (`…@e.test`) y afecta a `/me` y al listado `/users`. Impacto real: usuarios con correos heredados/legacy (o datos sembrados) dejan la sesión degradada (la UI muestra «No tiene permiso»/estado mudo).

## 2 · Causa raíz

Validación **estricta** en el camino de **lectura**: `UserRead.email: EmailStr` se valida también al serializar desde BD, donde pueden existir valores fuera de la política actual.

## 3 · Comportamiento actual → esperado

| Caso | Hoy | Esperado |
|---|---|---|
| `/me` con correo legacy | 500 | 200; correo mostrado tal cual (lectura tolerante `email: str` en el esquema de lectura) |
| `/users` con un correo legacy | 500 de la lista | 200; fila visible |
| Alta/edición con correo inválido | 422 (correcto) | **sin cambio**: la validación estricta se mantiene solo en escritura |

## 4 · Secciones §47 (resumen)

- **Alcance**: `auth/schemas.py` (esquemas de **lectura** con `str`; escritura con `EmailStr`), `auth/service.py` (sin cambio funcional; opcionalmente `model_validate` protegido), tests `test_r213_me_email_tolerance.py`.
- **Fuera**: saneamiento de correos históricos (política aparte); fixture R-188 (GA-GOV-03 lo corrige a `@example.com`).
- **FE**: sin cambio (el correo se pinta). **BE**: esquemas de lectura.
- **Contrato**: `/me` y `/users` dejan de responder 500 por este motivo; escritura sigue estricta.
- **Seguridad/tenant/BU/RBAC/Transacciones/Auditoría**: sin cambio (el `_acotar` sigue aplicando en la consulta).
- **i18n/UI/responsive/Migración/SAP**: sin cambio.
- **Compatibilidad**: 500→200 en lectura con dato legacy (corrección).
- **AC**: ver `R-213_AC_RED_E2E_UAT.md`. **Cierre**: AC verdes · suite R-188 (con fixture GA-GOV-03) verde.

## 5 · Dedup

GA-GOV-03 (grupo B) lo clasifica como TEST_DEFECT **más** R-213 de robustez; D lo lista como colateral. Sin registro previo propio en backlog (grep). **Nuevo** (registro G-25).

## 6 · Interdependencias

GA-GOV-03 (fixture; la suite R-188 depende de este fix para su caso «correo legacy» opcional) · R-195 (usuarios; lectura) · R-202 (misma familia auth).
