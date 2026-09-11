# GA-FE-02-A · EVIDENCIA DE CERTIFICACIÓN AUTENTICADA DEL RUNTIME (§117)

**Modo de la ejecución**: **`MODE_C · BLOCKED_AUTH`** · **Fecha**: 2026-09-11 ·
**Baseline**: `d120fdd` (== remoto) · **Padre**: GA-FE-02 (`48ffdbb`).

---

## 1 · Baseline

`main` · HEAD `d120fddcc0402630891e358d0bc41d81e717f1bb` == `origin/main` · worktree limpio ·
origin HTTPS · sin cambios de producto durante la ejecución (diff de producto = 0).

## 2 · Autoridad (`OD-20`)

`OD-20` (APPROVED, 2026-09-11) ya autorizó fase 9, GA-FE-02 y el E2E autenticado. **No se creó
Owner Decision nueva** (§1); este documento es el addendum de ejecución/certificación.
El propietario autorizó además en el encargo GA-FE-02-A la ejecución de estos flujos y, si
existiera un actor bootstrap legítimo, la creación de cuentas por flujos oficiales.

## 3 · Alcance

Certificación funcional autenticada de GA-FE-02 (contexto de empresa, BU de empresa, BU de
usuario, navegación admin mínima) sobre `https://avicola.globaldv.net` (ENV-01). No desarrollo.

## 4 · Regla de no-desarrollo (primera pasada)

Se respetó: **cero** ediciones de producto en esta ejecución. No hubo ver-fallo→editar.

## 5 · Fingerprint del runtime

```
ASSET      assets/index-C_aR7TJ6.js
SHA256     35ea38e2c3f41e783a7dc401962f61da0ae4010c34fd5da4dc1be3f9faa41bd8  (== build de 48ffdbb)
LM/ETag    Thu, 10 Sep 2026 23:39:07 GMT · "6aa33f9b-322"
ESTADO     Generación GA-FE-02 verificada AL INICIO (23:52:28Z) y re-verificada al cierre
```

## 6 · Modelo de autenticación

`POST /login` → tokens → `/me` por petición con empresa efectiva re-validada (`OD-11`). Sin MFA,
sin confirmación por email, `is_active` gobierna el acceso. Refresh de sesión por contrato;
cambios de acceso efectivos se resuelven por petición en servidor.
(Detalle: `GA_FE_02_A_CLARIFICATIONS.md`.)

## 7 · Procedencia de credenciales

**Ninguna credencial fue suministrada por mecanismo autorizado** (verificación acotada del 2026-09-10T23:53:23Z: 0 variables `GA_E2E_*`; sin sesión autenticada disponible). No se buscaron
credenciales, no se adivinaron, no se usó `admin/admin`, no hubo bypass ni acceso a DB.
**Búsqueda: NO · Adivinación: NO · Bypass: NO.**

**Resume 2026-09-11 (auto-provisioning autorizado)** — investigación COMPLETA de mecanismos
oficiales (`GA_FE_02_A_AUTH_PROVISIONING_MAP.md`): 6 mecanismos inventariados; los 5 oficiales
exigen una credencial bootstrap inyectada externamente (M3/M7: seeds con
`GA_BASELINE_ADMIN_PASSWORD`/`GA_SEED_*` y credential store de GUIA §1.1 — todos AUSENTES: 0)
o acceso server-side/DB (ausente y prohibido por §2). Sin registro/invitación (M6: 0 endpoints)
y sin sesión autenticada disponible (no se compartió ninguna). Determinación final de la causa:
**`BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED`** — cadena de evidencia A–F en el mapa.

## 8 · Matriz de cuentas de prueba

`GA_FE_02_A_TEST_ACCOUNT_MATRIX.md` — A/B/C/D `MISSING`; E `OPTIONAL_MISSING`.

## 9 · Empresa de prueba

No determinable sin sesión (`BLOCKED_AUTH`). Requisitos registrados en el doc de cuentas.

## 10 · Snapshot pre-test

`GA_FE_02_A_PRETEST_STATE.md` — registrado el estado del sistema; el snapshot funcional queda
pendiente de la reanudación (sin inventar datos).

## 11–20 · E2E-01…E2E-10

**Todos `BLOCKED_AUTH`** — matriz completa (31 escenarios) en `GA_FE_02_A_E2E_MATRIX.md`.
Ninguna fila se marcó PASS por medio indirecto (§102): unit tests, bundle markers y HTTP público
**no** sustituyen esta capa.

## 21 · Company switch

`BLOCKED_AUTH` (sin actor con credencial de switch disponible legítimamente).

## 22 · Aislamiento sin datos obsoletos

`BLOCKED_AUTH` en runtime; cubierto a nivel de suite (refetch+limpieza probados en `48ffdbb`) —
no se acredita en runtime por esta ejecución.

## 23 · Matriz de 3 dimensiones

`BLOCKED_AUTH` los 4 casos (OFF/YES/YES · ON/NO/YES · ON/YES/NO · ON/YES/YES).

## 24–26 · Refresh · relogin · mobile

`BLOCKED_AUTH`.

## 27 · Red

Sin capturas de mutación — no hubo mutaciones. `GA_FE_02_A_NETWORK_EVIDENCE.md` no generado
(no hay tráfico autenticado que documentar). Tráfico público de preflight en §5.

## 28 · Consola

Contexto fresco de verificación pública: **0 errores fatales** (login renderiza). Sin sesión no
se recorrieron superficies autenticadas.

## 29 · Persistencia

`BLOCKED_AUTH` — sin mutaciones no hay claim de persistencia (regla §3: `TOAST ≠ PERSISTENCE`).

## 30 · Auditoría

`BLOCKED_AUTH` — sin mutaciones no hay entradas que verificar.

## 31 · Verdad de mutación denegada

`BLOCKED_AUTH` — no ejecutable; los controles negativos de UI equivalentes viven en la suite
(90/90) y los de servidor en backend certificado, **sin sustituir** el control autenticado.

## 32 · BU-D10

```
Observado en runtime: NADA (sin sesión)
Estado canónico: PENDING_RATIFICATION
Política ratificada por el propietario: NO
```

## 33 · Hallazgos

```
Reutilizados: 0 · Nuevos: 0 · De seguridad: 0
(no evaluable sin autenticación — no se registra ningún hallazgo especulativo)
```

## 34 · Estado final de los datos de prueba

`GA_FE_02_A_TEST_DATA_LEDGER.md` — vacío; 0 creados / 0 mutados / 0 usuarios reales tocados.

## 35 · Reconciliación de certificación

Sin cambio respecto al addendum de GA-FE-02 (§8 del `CERTIFICATION_SCOPE_RECONCILIATION`):
AUTHENTICATED E2E sigue `BLOCKED_AUTH`; **no se reclasifica** ninguna capacidad.

## 36 · Reclasificación en la auditoría maestra

No aplica: solo puede moverse a `IMPLEMENTED_AND_VISIBLE` con E2E autenticado verde (§105),
que no fue posible. El addendum existente (`GA_FE_02_ADDENDUM_MULTI_COMPANY_BU_ADMIN.md`)
permanece como está.

## 37 · Paquete Owner UAT

`GA_FE_02_OWNER_UAT.md` existente. **`UAT_READY = NO`** — la ruta crítica autenticada no está
verde todavía; enviar al propietario a validar un flujo no certificado está prohibido (§103).
`OWNER UAT: PENDING` (solo el propietario puede cambiarlo; §76/§127).

## 38 · Veredicto final

```
AUTHENTICATED RUNTIME:   BLOCKED_AUTH
COMPANY CONTEXT:         BLOCKED
COMPANY BUSINESS UNIT ADMIN: BLOCKED
USER BUSINESS UNIT ADMIN:    BLOCKED
SECURITY MATRIX:         BLOCKED
PERSISTENCE:             BLOCKED
RESPONSIVE:              BLOCKED
GA-FE-02: DEPLOYED_IMPLEMENTATION_COMPLETE / FUNCTIONAL_CERTIFICATION_BLOCKED_AUTH
          causa refinada (resume 2026-09-11): BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED
OWNER ACCEPTANCE: PENDING
```

## 39 · Siguiente tranche

No iniciar GA-FE-03. La siguiente acción es del propietario: **entregar las cuentas autorizadas
por el mecanismo que designe** (ver `GA_FE_02_REQUIRED_TEST_ACCOUNTS.md`); entonces GA-FE-02-A
se reanuda en el paso 30 del orden estricto y ejecuta los 31 escenarios.

## 40 · Git

Estado al cierre de redacción: commit de gobernanza de GA-FE-02-A (este paquete) + push.
Worktree limpio tras el commit; sin código de producto; sin cambios en `origin`.

---

# ADENDA — 2026-09-11 · GA-FE-02-C · CORRIDA AUTENTICADA COMPLETA Y CERTIFICACIÓN

> Esta adenda **supera los §36–39 anteriores** para la certificación funcional: la ruta
> crítica autenticada ya no está bloqueada. Lo anterior queda como registro histórico del
> bloqueo y su resolución (D1→F4→F1).

## 41 · Ruta crítica resuelta (histórico inmediato)

| Hito | Estado | Dónde |
|---|---|---|
| D1 (hidratación de sesión) | CLOSED | `ea26b2e` · verificación runtime en esta corrida (hard refresh) |
| F2 (rol «Administrador de Accesos») | CLOSED | rol id=35 · 4 permisos exactos |
| F3 (emails `.local` ⇒ 500) | CLOSED | 14/14 reparadas · seed endurecido `b83d908` |
| F4 (selector de empresa) | CLOSED | `716d175` · re-verificado en UI en esta corrida |
| **F1 (catálogo canónico)** | **CLOSED** | **migración de datos `y5z6a7b8c9d0`** por pipeline normal (`GA-REM-024`); postcondición runtime 4/4 — spec §4.2.2 |

## 42 · Corrida de certificación (resultados)

Autorización GA-FE-02-C · modo autónomo · baseline de producto `b4d8c3a` (C2) + cierres.
Todo ejecutado contra `https://avicola.globaldv.net` con el bundle **`index-B2-tZnkI.js`**
estable de inicio a fin (sin movimiento de generación — §79).

- **E2E-01…10 + variantes: 33 PASS / 0 FAIL / 0 BLOCKED** — matriz completa en
  `GA_FE_02_A_E2E_MATRIX.md` (sección «RESULTADOS REALES»).
- **Matriz 3D: 4/4** — `OFF/YES/YES→DENY` · `ON/NO/YES→DENY` · `ON/YES/NO→403 DENY` ·
  `ON/YES/YES→ALLOW(2)` — con actores y estados reales, sin inferencia.
- **Refresh 5/5 · Relogin 2/2 (IMMEDIATE/IMMEDIATE) · Desktop PASS · Móvil 390×844 PASS.**
- **Persistencia PASS** (fresh GET + refresh por mutación) · **Auditoría PASS** (14+15 filas
  con actor/empresa/objetivo/acción/timestamp) · **Consola: 0 fatales** · **UX de fallo PASS**
  · **Doble acción PASS** (1 mutación por clic).
- **Seguridad (stop conditions §68): todas negativas.** Auto-concesión: no existe ruta (3
  capas) · cross-company: 404 · D no muta (403×4) · OFF/NO/RBAC-NO: DENY real · sin mezcla de
  tenants · sin estado obsoleto tras switch. Dos incidencias documentadas (no defectos):
  **D-1** lectura global exenta (excepción certificada GA-REM-002; escrituras cerradas R-163),
  **D-2** tarjeta del hub para D (alcance conocido R-119, ruta protegida). Observación D-3
  (filtro `module` de `/audit` con valores fuera del enum → 500; valores canónicos → 200) y
  D-4 (fail-closed del home para roles sin `dashboard:read`) quedan registradas sin remediar
  (fuera de alcance; sin hotfix — §68/§70).
- **Fixtures**: actores A–E + X provisionados por API oficial, logins independientes 5/5;
  **restauración completa** (CBU todas OFF; sin concesiones vivas; usuarios sintéticos dados
  de baja; roles temporales desactivados; rol 35 intacto) — ledger de datos §76.
- **Higiene**: 0 credenciales impresas/commiteadas; 0 tokens en documentos; `/tmp` destruido
  al cierre; navegador de E2E cerrado.

## 43 · Gates finales (§78)

```
TypeScript (tsc -b --noEmit) ........ 0 errores            PASS
npm run build ....................... ✓ built             PASS
Vitest .............................. 205/205 (21 files)  PASS
Backend dirigido (migración F1) ..... 6/6 passed          PASS
compileall (app/seeds/tests/alembic)  OK                  PASS
Cadena Alembic ...................... 1 head / 1 base · 37 revisiones  PASS
Runtime F1 ........................... 4/4 canónicas      PASS
F2 / F3 / F4 / D1 .................... PASS (re-verificados post-deploy)
E2E autenticado ...................... PASS (33/33 con D-1..D-4 documentadas)
Runtime estable ...................... index-B2-tZnkI.js idéntico inicio/fin
```

## 44 · Reconciliación de capas (§82)

| Capa | Resultado |
|---|---|
| Backend técnico | **CERTIFIED** (contratos BU + segregación + row-scope; migración determinista) |
| Frontend | **PASS** (consolas admin alcanzables/protegidas; distinción de estados; móvil operable) |
| Deployment | **PASS** (pipeline normal aplicó migración + bundle estable) |
| Authenticated E2E | **PASS** |
| Security | **PASS** (stop conditions negativas; D-1 declarada certificada) |
| Persistence | **PASS** |
| Responsive | **PASS** |
| Owner UAT | **READY — PENDING** (solo el propietario puede aprobar) |

## 45 · Decisión de certificación (§83)

```
F1 CLOSED · F2 CLOSED · F3 CLOSED · F4 CLOSED · D1 CLOSED
GA-FE-02-B CLOSED · ENV-01 READY FOR GA-FE-02: YES
A/B/C/D READY (en la corrida) · E verificado
E2E-01…10 PASS · 3D 4/4 · refresh/relogin/desktop/mobile/network/persistence/audit PASS
GA-FE-02 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING
OWNER_UAT_READY = YES · Owner Acceptance: PENDING
```

## 46 · Límites del programa (intactos)

```
R-98 / R-119 / R-181 / R-182 ... UNCHANGED (D-2 documenta R-119 sin reabrirlo)
BU-D10 ........................ PENDING_RATIFICATION (observado, no decidido)
Wave B ........................ PAUSED
Wave C ........................ NOT STARTED
SAP ........................... NOT STARTED
GA-FE-03 ...................... ELIGIBLE_BUT_NOT_STARTED (no iniciada)
```

---

## 47 · Addendum GA-FE-02-D (2026-09-11) — D-1 reclasificado y CORREGIDO (OD-16)

`D-1` dejó de ser «excepción documentada»: la reconciliación contra `OD-16`
(`audit/ga-fe-02-d/GA_FE_02_D_OD16_GLOBAL_READ_RECONCILIATION.md`) estableció que la lectura
del actor global sobre `/lots` (y la familia: operations/review/dashboard/reports) es **dato
productivo** y que la puerta de habilitación por empresa es absoluta también para él ⇒
`SECURITY_DEFECT` (CASE 3). Corregido en `9ffc5ec` (resolutor `unidades_de_alcance_productivo`
+ remoción de los 8 atajos) y verificado en runtime post-deploy: **OFF → cero/404 en todas las
superficies productivas; ON → solo las habilitadas** (batería 21/21 · MX 12/12 · spots F2/F3 ·
bundle estable). Estado final: `GA-FE-02 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING` ·
`OWNER_UAT_READY=YES`. La excepción fase-3/`GA-REM-002` queda **superada para LECTURAS
productivas**; la escritura (`R-163`) y el plano de control permanecen intactos.

---

## 48 · Addendum GA-FE-02-E (2026-09-11) — RECERTIFICACIÓN FINAL sobre la generación corregida

Tras los cambios de producto de GA-FE-02-D (`9ffc5ec`), se ejecutó **un rerun completo de
GA-FE-02-A desde cero** contra la generación desplegada (`ccb47b5`, bundle
`index-B2-tZnkI.js`), sin transitividad: preflight (TSC 0 · build ✓ · Vitest 205/205 · backend
dirigido 7/7) · fixtures e (77–81; roles 36/37/38 reactivados/desactivados; rol 35 intacto) ·
E2E-01…10 desktop **46/46** + móvil **10/10** · matriz 3D **4/4** · GLOBAL OFF read/write DENY ·
refresh/relogin · regresión OD-16 familia completa **22/22** (OFF→0/404/403; ON→solo
`L-BO-2026-05/06`) · auditoría 1:1 (A×5 · B×6 · actor global×3; denegadas → 0 filas) ·
restauración total (CBU 4×OFF; usuarios 77–81 baja → login 403; sin concesiones vivas) ·
restore §. Resultado: **`GA-FE-02-A: PASS_FINAL_GENERATION`** — `GA-FE-02:
FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING` · `OWNER_UAT_READY: YES`. Detalle:
`audit/ga-fe-02-e/GA_FE_02_E_FINAL_GENERATION_RECERTIFICATION.md`. `GA-FE-03` no iniciada;
`BU-D10` sigue `PENDING_RATIFICATION` (`OWNER_RATIFIED_POLICY: NONE`).
