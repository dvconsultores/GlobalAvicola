# GA-FE-02-A · E2E RESULTS MATRIX (§101)

Todos los estados son del **MODE_C · BLOCKED_AUTH** (paso 29 §133 → rama §79). No se ejecutó
ningún flujo autenticado; no existe fila "probada por otro medio" — prohibido (§102).

> **Actualización 2026-09-11 (resume de self-provisioning)**: la investigación obligatoria de
> mecanismos oficiales se completó (`GA_FE_02_A_AUTH_PROVISIONING_MAP.md`) y la causa raíz queda
> refinada: **`BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED`**. Todos los escenarios conservan su
> estado; ninguno cambió de clase.

| E2E_ID | AC | ACTOR | COMPANY | COMPANY_BU | USER_GRANT | RBAC | ACCIÓN | RESULTADO | FAILURE CLASS |
|---|---|---|---|---|---|---|---|---|---|
| E2E-01a | AC-COMP-01 | A | prueba | — | — | — | login → contexto de empresa visible → página admin | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-01b | AC-COMP-02/03 | A (elegible) | A↔B | — | — | — | switch → contexto B → volver A | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-01c | AC-COMP-04/05 | A | A↔B | mixto | — | — | sin datos obsoletos tras switch | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-01d | AC-COMP-06 | E (opcional) | — | — | — | — | global sin contexto → fail closed | `BLOCKED_AUTH` (OPTIONAL) | AUTH_CREDENTIAL_MISSING |
| E2E-02a | AC-CBU-02/03/04/06 | A | prueba | OFF→ON | — | — | ver 4 BUs → habilitar → refresh → persistencia | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-02b | AC-CBU-08 | A | prueba | una ON | sin cambio | — | habilitar no crea concesiones | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-02c | independencia | A | prueba | mixto | — | — | otras 3 BU sin cambio | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-03a | AC-CBU-05/06 | A | prueba | ON→OFF | — | — | apagar → refresh → persistencia | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-03b | AC-CBU-09 | A | prueba | OFF | almacenado | — | no borrado inventado de concesiones | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-03c | AC-CBU-10 | C | prueba | OFF | — | sí | operación productiva → DENY | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-03d | AC-CBU-11 | A | prueba | OFF | — | — | control plane puede reactivar | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-04a | AC-UBU-05/06 | B | prueba | ON | C: no→sí | — | conceder → fresh GET → refresh | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-04b | AC-UBU-07 | C | prueba | ON | sí | sí | relogin → BU efectiva | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-04c | AC-UBU-07b | C | prueba | ON | sí | sí | operación representativa → ALLOW | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-05a | AC-UBU-08/09 | B | prueba | ON | sí→revocado | — | revocar → refresh → persistencia | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-05b | AC-UBU-10 | C | prueba | ON | revocado | sí | relogin → sin BU efectiva → DENY | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-06a | AC-UBU-11 (UI) | B | prueba | — | — | — | UI sin acción de self-grant | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-06b | AC-UBU-11 (API) | B | prueba | ON | — | — | petición directa de auto-concesión → 403 | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-07a | AC-UBU-12 (UI) | B | A | ON | — | — | usuario de otra empresa fuera de candidatos | `BLOCKED_AUTH` (o `BLOCKED_FIXTURE` si no hay C2) | AUTH_CREDENTIAL_MISSING |
| E2E-07b | AC-UBU-12 (API) | B | A | ON | — | — | petición directa cross-company → deny | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-08a | AC-NAV-03 | D | prueba | — | — | no | nav sin entrada accionable | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-08b | AC-NAV-04 | D | prueba | — | — | no | ruta directa protegida (actor autenticado) | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-08c | AC-UBU-13 | D | prueba | — | — | no | API directa → 403 | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-09a | AC-UBU-04 | A | prueba | ON | C: no | — | UI: empresa Activa + usuario No concedida | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-09b | AC-UBU-15b | C | prueba | ON | no | sí | operación → DENY | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-10a | AC-UBU-17 | A | prueba | OFF | almacenado | — | UI no implica acceso activo | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-10b | AC-UBU-17b | C | prueba | OFF | almacenado | sí | operación → DENY; grant conservado | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| E2E-10c | BU-D10 | A | prueba | OFF→ON | almacenado | — | re-habilitar: OBSERVAR (sin ratificar) | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| MX-1 | matriz 3D | C | prueba | OFF | YES | YES | operación → DENY | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| MX-2 | matriz 3D | C | prueba | ON | NO | YES | operación → DENY | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| MX-3 | matriz 3D | C | prueba | ON | YES | NO | operación → DENY | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| MX-4 | matriz 3D | C | prueba | ON | YES | YES | operación → ALLOW | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| RF-1…5 | refresh (§47) | A/B | — | — | — | — | F5 tras cada mutación | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| RL-1,2 | relogin (§48) | C | — | — | — | — | relogin tras grant/revoke | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |
| MOB-1…3 | mobile (§52) | A/B | — | — | — | — | 390×844 flujos críticos | `BLOCKED_AUTH` | AUTH_CREDENTIAL_MISSING |

**Resumen**: 31 escenarios planificados · 0 PASS · 0 FAIL · **31 `BLOCKED_AUTH`**
(1 con posible subcaso `BLOCKED_FIXTURE`) · 0 infracciones de validez (no se ejecutó nada).

Al reanudar, esta matriz se sustituye por la corrida real (mismo esqueleto, con columnas de
request/HTTP/UI/persistida/capturas/red/auditoría y RESULTADO por fila).
