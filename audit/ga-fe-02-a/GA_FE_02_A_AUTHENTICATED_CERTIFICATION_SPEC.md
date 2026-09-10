# GA-FE-02-A · SPEC DE CERTIFICACIÓN AUTENTICADA DEL RUNTIME (ADDENDUM DE EJECUCIÓN)

**Padre**: GA-FE-02 (implementación `48ffdbb`; cierre `d120fdd`) · **Autoridad**: `OD-20`
(ya autorizó fase 9 y GA-FE-02, incluido el E2E autenticado) · **Baseline reportado**:
`d120fddcc0402630891e358d0bc41d81e717f1bb` · **Tipo**: addendum de certificación — **no es
desarrollo de producto**.

> Según §1 del encargo: **no se crea una nueva Owner Decision**; `OD-20` ya autoriza estos
> flujos. Este documento es el addendum de ejecución/certificación exigido por la convención
> documental del repositorio.

---

## 1 · Objetivo de certificación

Convertir `GA-FE-02 = DEPLOYED_IMPLEMENTATION_COMPLETE / FUNCTIONAL_CERTIFICATION_BLOCKED_AUTH`
en `GA-FE-02 = FUNCTIONALLY_CERTIFIED` **solo si** existe evidencia autenticada real de los
flujos `E2E-01…E2E-10` sobre el runtime desplegado (`https://avicola.globaldv.net`, ENV-01).
No es nuevo desarrollo, no es GA-FE-03, no es auditoría estática.

## 2 · Reglas de la tranche

- Primera pasada = **CERTIFICATION ONLY**; ningún fallo se arregla en caliente (§9).
- `UNIT TEST ≠ E2E` · `MOCK ≠ RUNTIME` · `TOAST ≠ PERSISTENCE` · `FRONTEND STATE ≠ BACKEND
  TRUTH` (§3); las capas ya probadas (spec/impl/tsc/build/vitest/deploy/parity) **no sustituyen**
  la capa autenticada.
- Credenciales: solo suministradas por mecanismo autorizado o sesión autenticada explícitamente
  disponible (§13). Prohibido: buscar, adivinar, `admin/admin`, bypass, DB directa, reset de
  usuarios reales, desactivar MFA.
- Las cuentas de prueba solo pueden crearse/ajustarse mediante flujos oficiales del producto y
  **solo si** existe un actor autorizado ya disponible (§14).
- `BU-D10` permanece `PENDING_RATIFICATION`: observar comportamiento NO ratifica política (§21).
- Datos de prueba: mínimos, reversibles, en ENV-01, con snapshot previo y ledger (§19–20, §100).
- Restauración final segura; sin tocar datos de usuarios reales (§72).

## 3 · Modos posibles y modo de esta ejecución

```
MODE_A  AUTH_AVAILABLE_CERTIFICATION          ← no alcanzado
MODE_B  AUTH_PROVISIONED_CERTIFICATION        ← no alcanzado (no había actor bootstrap)
MODE_C  BLOCKED_AUTH                          ← **MODO DE ESTA EJECUCIÓN**
MODE_D  RUNTIME_NOT_CURRENT                   ← no (runtime = GA-FE-02, verificado)
MODE_E  GA_FE_02_DEFECT_FOUND                 ← no evaluable sin autenticación
MODE_F  SECURITY_DEFECT_FOUND                 ← no evaluable sin autenticación
```

## 4 · Actores de prueba (objetivo) y Company de prueba

Ver `GA_FE_02_A_TEST_ACCOUNT_MATRIX.md` y `GA_FE_02_REQUIRED_TEST_ACCOUNTS.md` (actualizado).
Resumen: **A** Company-BU Admin (`business_units:read|update`) · **B** Access Admin (los cuatro
`business_units:*`, sin `users:read` por diseño) · **C** Target operational user (misma Company;
RBAC de la capacidad representativa; sin grant inicial de la BU objetivo) · **D** Unauthorized
control (sin permisos `business_units:*`) · **E** Global actor (opcional; solo si existe
credencial legítima). Company de prueba: dedicada o reutilizada, **nunca** una empresa
productiva activa; estado sugerido de alta información `ON/OFF/ON/OFF`.

## 5 · Alcance de verificación (E2E-01…E2E-10 + transversales)

```
E2E-01 contexto de empresa (+switch si aplica; sin datos obsoletos)     §28-29
E2E-02 habilitar BU de empresa (cuatro estados independientes; 0 grants) §30-31
E2E-03 apagar BU (persistencia; sin borrado inventado; denegación productiva; control plane
       sigue pudiendo reactivar)                                          §32-33
E2E-04 conceder BU a usuario (request exacto; fresh GET; refresh)          §34
E2E-04b efecto en el usuario objetivo (relogin; RBAC ya presente)          §35
E2E-05 revocar (persistencia; efecto; denegación)                          §36
E2E-06 auto-concesión (UI + petición directa; sin rastro)                  §37
E2E-07 objetivo de otra empresa (candidatos + petición directa)            §38
E2E-08 actor no autorizado (nav, ruta directa, API)                        §39
E2E-09 BU ON + sin grant ⇒ denegado; UI muestra empresa activa y usuario sin concesión §40
E2E-10 grant almacenado + BU OFF ⇒ no efectivo; denegación productiva      §41
Matriz de 3 dimensiones: OFF/YES/YES → DENY · ON/NO/YES → DENY · ON/YES/NO → DENY ·
       ON/YES/YES → ALLOW                                               §83, §125
Refresh en los 5 puntos · relogin del objetivo · sesión (IMMEDIATE/AFTER_REFRESH/AFTER_RELOGIN)
Mobile 390×844 · red · consola · auditoría · denegaciones sin falso éxito   §47-58
```

## 6 · Validez (R-72) y evidencia

Cada prueba debe probar los 13 puntos de §25 (autenticación real, fixture correcta, página
alcanzada, precondiciones, la aserción observa el AC y puede fallar, sin fallback de login,
contexto de empresa/BU/permiso, runtime real desplegado, persistencia cuando aplique). Evidencia:
matriz E2E, red, capturas, consola, auditoría, ledger de datos. **Sin evidencia ≠ certificación.**

## 7 · Manejo de fallos y rama de remediación

Clasificación obligatoria por taxonomía de §67. `SECURITY STOP` ante cualquiera de los supuestos
de §68. Rama de remediación SOLO si el defecto pertenece a GA-FE-02, está gobernado y no exige
Owner Decision: registrando → AC → RED → fix mínimo → gates → commit → push → deploy → **re-ejecutar
TODO el set E2E**. Nunca hotfix al runtime (§71).

## 8 · Niveles de cierre

```
AUTHENTICATED_E2E: PASS (con hueco global opcional documentado si aplica y no exigido por UI)
GA-FE-02: FUNCTIONALLY_CERTIFIED / FUNCTIONALLY_CERTIFIED_OWNER_ACCEPTANCE_PENDING
         (Owner UAT ≠ PASS hasta que el propietario lo valide — §76/§127)
Si falta cualquier AC crítico: PARTIAL / BLOCKED_<CAUSA> — sin umbral aritmético (§78)
```

## 9 · Resultado de esta ejecución

**`MODE_C · BLOCKED_AUTH`** (§79): no existe credencial autorizada ni actor bootstrap disponible;
no se creó código ni se modificó producto; se emiten/actualizan los requerimientos de cuentas.
Estado final: `GA-FE-02 = DEPLOYED_IMPLEMENTATION_COMPLETE / FUNCTIONAL_CERTIFICATION_BLOCKED_AUTH`
(sin cambio). La certificación **no es evaluable** hasta recibir las cuentas — y no se sustituye
por repetir las capas ya probadas.
