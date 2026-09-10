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
GA-FE-02: DEPLOYED_IMPLEMENTATION_COMPLETE / FUNCTIONAL_CERTIFICATION_BLOCKED_AUTH  (sin cambio)
OWNER ACCEPTANCE: PENDING
```

## 39 · Siguiente tranche

No iniciar GA-FE-03. La siguiente acción es del propietario: **entregar las cuentas autorizadas
por el mecanismo que designe** (ver `GA_FE_02_REQUIRED_TEST_ACCOUNTS.md`); entonces GA-FE-02-A
se reanuda en el paso 30 del orden estricto y ejecuta los 31 escenarios.

## 40 · Git

Estado al cierre de redacción: commit de gobernanza de GA-FE-02-A (este paquete) + push.
Worktree limpio tras el commit; sin código de producto; sin cambios en `origin`.
