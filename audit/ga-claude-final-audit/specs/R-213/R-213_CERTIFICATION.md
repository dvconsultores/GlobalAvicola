# R-213 · CERTIFICACIÓN TÉCNICA LOCAL — `/me` y `/users` toleran correos legacy (lectura `str`, escritura `EmailStr`)

Fecha: 2026-09-14 · Programa: GA PRE-SAP (T11) · Política: **AOD-29 Clarification 01**.

## 1 · Paquetes y commits

| Fase | SHA | Contenido |
|---|---|---|
| C1 · RED | **`3bed31d`** | `test_r213_me_email_tolerance` BE 2F por causa exacta (`ValidationError` ⇒ 500 en `/me` y `/users`) + controles de escritura 422 verdes |
| C2 · Implementación | **`81de57f`** | `UserBase.email: str` (lectura tolerante) · `UserCreate.email: EmailStr` (escritura estricta; `UserUpdate` ya lo era) |

Sin migración/endpoint/permiso (AC-R213-06/07): solo esquemas de lectura.

## 2 · Gates locales (PASS)

| Gate | Resultado | Evidencia |
|---|---|---|
| BE targeted R-213 | **4/4** | `green/be-r213-green-targeted.log` |
| Guardianes (sesión/tenant/password/roles) | **52 passed** | `green/be-r213-guards.log` |
| BE suite completa | **1381 passed / 0 failed / 49 skipped** (23:10) | `green/be-r213-green-full.log` |

## 3 · Sensibilidad (restore `81de57f`)

S1 (lectura estricta) ⇒ `01`,`02` rojas · S2 (escritura sin override) ⇒ `03` roja
(los 2 «errors» del log S2 son teardown del fixture con el asalto inválido — la
aserción de contrato falla quirúrgicamente). Post-mutación **4/4**.

## 4 · Estado

- **R-213 = `CLOSED_TECHNICALLY`** · UAT no requerida (SPEC §4).
- T11 continúa con **R-218** y **R-220**.
