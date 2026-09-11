# GA-FE-02-A · E2E RESULTS MATRIX (§101)

Todos los estados son del **MODE_C · BLOCKED_AUTH** (paso 29 §133 → rama §79). No se ejecutó
ningún flujo autenticado; no existe fila "probada por otro medio" — prohibido (§102).

> **Actualización 2026-09-11 (resume de self-provisioning)**: la investigación obligatoria de
> mecanismos oficiales se completó (`GA_FE_02_A_AUTH_PROVISIONING_MAP.md`) y la causa raíz queda
> refinada: **`BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED`**. Todos los escenarios conservan su
> estado; ninguno cambió de clase.

> **Actualización 2026-09-11 (post-reporte F1 del propietario)**: la verificación del gate F1
> (que debía cerrar el bloqueo) encontró el catálogo **aún vacío** (`[]`, `count=0`; 4×404) ⇒
> **F1 = FAIL / BLOCKED** y el E2E permanece **sin corrida** (STOP §6). Los 31 escenarios siguen
> sin resultado real; el resto del entorno (F2/F3/F4/D1) quedó re-verificado verde.

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

---

# RESULTADOS REALES — corrida autenticada 2026-09-11 (GA-FE-02-C)

**Runtime**: `https://avicola.globaldv.net` · bundle `index-B2-tZnkI.js` (estable de inicio a
fin) · Empresa de prueba `Avícola Global C.A.` (id 1) · BU objetivo `broiler` (2 lotes
`L-BO-2026-05/06`) · Ruta productiva representativa: `GET /api/v1/lots` (RBAC `lots:read` +
row-scope por unidad) · Actores A–E según `GA_FE_02_A_TEST_ACCOUNT_MATRIX.md` (addendum C).
**Cada fila fue ejecutada contra el runtime real; ninguna por transitividad.**

## Resultados por escenario

| E2E | Descripción | Resultado | Evidencia |
|---|---|---|---|
| **E2E-01a** | E: selector visible sin contexto; 2 empresas; switch c1; contexto en header | **PASS** | 01_desktop_selector/switched · red switch 200 |
| **E2E-01b** | E: switch c1→c3→c1; hard refresh; /me 200; sin forbidden; sin estado obsoleto | **PASS** | 01b_dropdown/back · 01_hard_refresh (D1) |
| **E2E-01 (A–D)** | Cada actor con su propia sesión: login 200 + `/me` 200 (empresa 1; X en 3) | **PASS** | matriz de cuentas §8 |
| **E2E-02a** | A: navegación normal → «Acceso por unidad»; 4 unidades (Progenitoras·Reproductoras·Incubadora·Engorde); todas «Inactiva» | **PASS** | 02_nav_discoverability · 02_four_units_all_off |
| **E2E-02b** | A: habilitar Engorde por UI (diálogo «Activar unidad» → Confirmar) → «Activa»; fresh GET `broiler=true`; **otras 3 intactas** | **PASS** | 02_enable_dialog · 02_enabled_broiler |
| **E2E-02c** | Tras habilitar: **cero** concesiones creadas (catálogo/enablement ≠ concesión) | **PASS** | `/users/73/business-units` sin vivas |
| **E2E-02-refresh** | Hard refresh: estado persiste y coincide con backend | **PASS** | 02_refresh (persistencia) |
| **E2E-03a** | A: desactivar por UI → «Inactiva»; persiste tras refresh; **1 sola mutación por clic** | **PASS** | E2E03_disabled · PATCH disable=1 |
| **E2E-03b** | C (login fresco): concesión viva + RBAC sí, CBU OFF → **DENY** (0 filas) | **PASS** | MX-1 (abajo) |
| **E2E-03c/§44-§56 (E)** | Escritura del actor global: `POST /lots` → **403** (`R-163`); lectura global exenta por semántica certificada — ver **D-1** | **PASS / D-1 documentada** | GLOBAL-WRITE-DENY · sin persistencia |
| **E2E-03d** | Rehabilitar (AC-A06): la concesión almacenada vuelve a ser efectiva → ALLOW (2) | **PASS** | AC-A06-rehabilitar-devuelve |
| **E2E-04a** | B: distinción visual **empresa Activa / C «No concedida»** | **PASS** | 04_before_grant |
| **E2E-04b** | B: «Conceder» por UI → «Concedida»; fresh GET: concesión viva `is_effective=true` | **PASS** | 04_after_grant |
| **E2E-04c** | C: relogin fresco → `/me` `effective_business_units=["broiler"]` → `GET /lots` **ALLOW (2 filas)**; efecto **IMMEDIATE** | **PASS** | L-BO-2026-05/06 |
| **E2E-05a** | B: «Revocar» por UI (diálogo) → «No concedida»; sin vivas | **PASS** | 05_revoked |
| **E2E-05b** | C: relogin fresco → **DENY (0 filas)**; efecto **IMMEDIATE**; sin transitividad | **PASS** | E2E05-target-DENY |
| **E2E-06** | Auto-concesión: **no existe ruta** — B excluido de candidatos (backend), sin botón en UI, `POST` directo → **403** `OD-15.a`; sin fila ni auditoría de éxito | **PASS (triple capa)** | E2E06_self_no_grant_button · 403 |
| **E2E-07** | Cross-company: candidatos de c1 **no incluyen** a X (c3); `POST /users/75` → **404**; sin persistencia | **PASS** | E2E07 (n=26, 404, vivas X=0) |
| **E2E-08** | D autenticado: ruta protegida (alerta de permiso, sin superficie); `GET/PATCH/POST/DELETE` → **403×4**; sin persistencia | **PASS** | E2E08_forbidden · [403,403,403,403] · nota R-119 (D-2) |
| **E2E-09** | ON / sin concesión / RBAC sí → **DENY (0 filas)**; UI: empresa Activa + «No concedida» | **PASS** | MX-2 |
| **E2E-10** | OFF / concesión viva / RBAC sí → **DENY (0 filas)**; fila **conservada** (`revoked_at=null`, `is_effective=false`); UI: aviso «unidad inactiva», no implica acceso | **PASS** | MX-1 · E2E10_ui_unit_inactive_notice · BU-D10 |

## Matriz 3D (runtime real, 4/4)

| Caso | Company BU | User BU | RBAC | Petición | Resultado |
|---|---|---|---|---|---|
| **MX-1** | OFF | YES | YES | `GET /lots` (C) | **DENY** — 200, 0 filas |
| **MX-2** | ON | NO | YES | `GET /lots` (C) | **DENY** — 200, 0 filas |
| **MX-3** | ON | YES | NO | `GET /lots` (D) | **DENY** — **403** (RBAC) |
| **MX-4** | ON | YES | YES | `GET /lots` (C) | **ALLOW** — 2 filas `L-BO-2026-05/06` |

Dimensiones independientes: **YES** (cada caso usa actores/estados reales verificados por
`GET /users/{id}/business-units` y `/business-units` antes y después).

## Refresh · Relogin · Desktop · Móvil

| Bloque | Resultado |
|---|---|
| Refresh tras switch (E) | **PASS** — contexto correcto |
| Refresh tras enable/disable (A) | **PASS** — estado real persistido |
| Refresh tras concede/revoke (B; desktop y móvil) | **PASS** — filas reconciliadas |
| Relogin C tras concesión | **PASS** — ALLOW **IMMEDIATE** |
| Relogin C tras revocación | **PASS** — DENY **IMMEDIATE** |
| Desktop 1440×900 | **PASS** — flujos completos (16 capturas) |
| Móvil 390×844 | **PASS** — 4 unidades visibles; toggle y concesión/revocación operables; sin overflow (delta=0); sin modal bloqueado; 5 capturas |

## Persistencia · Auditoría · Consola · UX de fallo · Doble acción

| Bloque | Resultado |
|---|---|
| Persistencia (BEFORE/ACTION/RESPONSE/fresh GET/refresh/FINAL UI por mutación) | **PASS** |
| Auditoría: `config_change`/`company_business_unit` **14 filas**; `permission_change`/`user_business_unit` **15 filas**; con actor, empresa, objetivo, acción y timestamp; negativas **sin** fila de éxito | **PASS** |
| Consola: sin `pageerror`; solo 403 esperados (fetches fail-closed de actores de fixture) | **PASS** |
| UX de mutación fallida: 403 auto-concesión → sin éxito falso; estado reconciliado por refetch | **PASS** |
| Doble acción: 1 clic = **1** mutación (PATCH disable=1 en la ventana) | **PASS** |

## Divergencias y observaciones (honestidad de la corrida)

- **D-1 · Lectura productiva del actor global (E) — CORREGIDO en GA-FE-02-D.** Con contexto c1
  y unidades OFF, el bootstrap leía filas productivas (lotes 8 · eventos 34 · revisión 8 ·
  panel 34). **GA-FE-02-D** lo reconcilió contra `OD-16`: la lectura es **dato productivo** y
  la puerta de habilitación es absoluta **también para la autoridad global** ⇒
  `SECURITY_DEFECT` (CASE 3), corregido con el resolutor `unidades_de_alcance_productivo` +
  la remoción de los 8 atajos (commit `9ffc5ec`). Runtime post-deploy: **OFF → cero/404 en
  todas las superficies productivas; ON → solo las habilitadas** (batería 21/21 + MX 12/12).
  Evidencia: `audit/ga-fe-02-d/GA_FE_02_D_OD16_GLOBAL_READ_RECONCILIATION.md` §13. La antigua
  clasificación como «excepción certificada (fase 3 / GA-REM-002)» queda **superada** para
  LECTURAS productivas: una certificación anterior no anula una decisión posterior del
  propietario.
- **D-2 · Tarjeta de hub visible para D (R-119).** El grid de `/menu/settings` no filtra por
  permiso (el sidebar sí): D ve la tarjeta, la ruta responde protegida (alerta, sin
  superficie). Es exactamente el alcance de **R-119** (navegación por permisos), declarado
  **UNCHANGED** en esta tranche. Registrado, no reabierto.
- **D-3 · Robustez del filtro `module` de `/audit`.** Valores fuera del enum PostgreSQL
  (`AuditModule`) → **500** (p. ej. `module=business_units`/`audit`); valores canónicos
  (`users`, `config`, `auth`, `lots`, `operations`) → 200. Observación de robustez **no
  bloqueante** (la verificación de auditoría de GA-FE-02 se hizo con filtros canónicos);
  queda registrada para backlog.
- **D-4 · Aterrizaje del home para roles administrativos mínimos.** A (pre-fix de fixture) y
  B (rol 35 canónico **sin** `dashboard:read` por diseño `OD-15 §6`) ven «Permiso requerido:
  dashboard:read | Reintentar» en `/` — **fail-closed correcto** y sidebar navegable; la
  superficie GA-FE-02 no está afectada. No se modifica el rol canónico ni se añade permiso
  nuevo (R-98/R-119 intactos).

```
Escenarios ejecutados contra runtime real ...... 31 filas de matriz + variantes E2E-02/03/04/05
PASS ........................................... 33
PASS con incidencia documentada (D-1..D-4) ..... 2 (E-global lectura; D hub R-119)
FAIL ........................................... 0
BLOCKED_AUTH / BLOCKED_FIXTURE ................. 0 (histórico de intentos previos, superado)
Sin transitividad / sin combinación con corridas previas ...... CONFIRMADO
```

---

## RERUN FINAL · GA-FE-02-E (2026-09-11) — sin transitividad

Repetición **completa** de esta matriz contra la generación corregida (`ccb47b5` · bundle
`index-B2-tZnkI.js` · backend con `9ffc5ec`), desde cero y con fixtures nuevos (e: 77–81):
E2E-01…10 desktop **46/46 PASS** · móvil **10/10 PASS** · matriz 3D **4/4** · D-1 (E-global
lectura) **ya no es incidencia**: `PASS` estricto con **read DENY total** con CBU OFF. Las
incidencias D-2/D-3/D-4 se mantienen documentadas en backlog sin cambio (no bloqueantes; sin
reapertura en esta tranche). Resultados por escenario en
`audit/ga-fe-02-e/GA_FE_02_E_FINAL_GENERATION_RECERTIFICATION.md` §5–§13.
