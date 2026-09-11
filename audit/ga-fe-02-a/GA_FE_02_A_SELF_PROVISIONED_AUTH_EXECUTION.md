# GA-FE-02-A · SELF-PROVISIONED AUTH EXECUTION (§28)

**Fecha**: 2026-09-11 · **Baseline**: `fad6463` (== remoto) · **Autorización**: explícita del
propietario para que el agente cree por sí mismo las cuentas A–D mediante **mecanismos oficiales**.
**Resultado de esta pasada**: `BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED` — la investigación
obligatoria (§3/§5) se ejecutó COMPLETA y su cadena de evidencia demuestra que **no existe vía
oficial de auto-provisioning desde este entorno** sin una credencial bootstrap inyectada.

## 1 · Autorización registrada

El propietario autorizó: crear cuentas de prueba (solo por mecanismos oficiales), crear datos de
prueba mínimos y reversibles en ENV-01, asignar roles/permisos **existentes**, configurar BUs de
una Company de prueba, conceder/revocar, probar refresh/relogin/negativos/móvil, capturar
evidencia, preparar UAT y certificar. Prohibido: inventar credenciales, buscar secretos, tocar
usuarios reales, crear permisos/roles nuevos, resolver BU-D10, desarrollar GA-FE-03/R-181/R-182,
reanudar Wave B/C/SAP. **Todo respetado.**

## 2 · Mecanismo descubierto y por qué el bloqueo persiste

Mapa completo: `GA_FE_02_A_AUTH_PROVISIONING_MAP.md`. Resumen:

```
M1 UI /users y M2 API /users ....... OFICIALES, requieren users:create AUTENTICADO
M3 Seeds bootstrap (server-side) ... oficiales; password SOLO desde entorno
                                     (GA_BASELINE_ADMIN_PASSWORD / GA_SEED_*) → AUSENTES (0)
M4 CLI (environment_reset, etc.) ... requieren DB/shell del servidor → AUSENTES (0);
                                     DB directa PROHIBIDA por §2
M5 Fixtures de test ................ base AISLADA local (GA-REM-014); no alcanza ENV-01
M6 Registro/invitación ............. NO EXISTE (0 endpoints)
M7 Credential store externo ........ LA vía canónica (GUIA §1.1 + GA-REM-004) → nada inyectado
Sesión autenticada disponible ...... NINGUNA (página compartida en /login; no se compartió otra)
```

Por qué es seguro y correcto no improvisar: `GA-REM-004` (CERTIFIED) prohíbe credenciales en el
repositorio y define la entrega por canal externo; `§2` prohíbe DB directa/JWT/backdoor; y `§5`
exige demostrar A–D antes de aceptar el bloqueo — **demostrado con evidencia**.

## 3 · Cuentas a crear EN CUANTO exista bootstrap (plan congelado, auto-ejecutable)

| Alias | Username propuesto | Rol/permisos (canónicos existentes) | Company | Estado inicial requerido |
|---|---|---|---|---|
| ACTOR_A_CBU_ADMIN | `ga-fe02-a-<ts>` | «Administrador de Accesos» (o admin de empresa): `business_units:read` + `update` (+ nota: ese rol sembrado incluye también `create/delete` — se documentará y la separación A/B se probará con la frontera real) | Company de prueba | — |
| ACTOR_B_ACCESS_ADMIN | `ga-fe02-b-<ts>` | «Administrador de Accesos»: exactamente `business_units:read·update·create·delete`, SIN `users:read` | misma | — |
| ACTOR_C_TARGET_OPERATIONAL | `ga-fe02-c-<ts>` | rol operativo existente con RBAC productivo para la capacidad representativa (p.ej. `operations:read`/`lots:read` según contrato de enforzamiento G/H) | misma | **target User BU = NO**; RBAC = YES |
| ACTOR_D_UNAUTHORIZED | `ga-fe02-d-<ts>` | rol mínimo (view_type web, sin `business_units:*`) | misma | — |
| ACTOR_E_GLOBAL | — | solo si el mecanismo canónico lo permite sin fabricar comodín | — | `OPTIONAL_MISSING` esperado |

RBAC productivo de C: elegir capacidad BU-scoped no destructiva (lectura/lista) de las enforzadas
por `GA-REM-040` enmiendas G/H (`operations` / `lots`); la ruta representativa exacta se fija en
la ejecución con la matriz de contrato. BU objetivo: una de las cuatro (p.ej. `breeder`), probando
ON→OFF→ON con restauración.

## 4 · Estrategia de secretos (ya definida, se usará al reanudar)

```
Password bootstrap ......... se recibe por canal externo (env var); NO se imprime; NO se guarda
Passwords de A–D ........... aleatorios fuertes, generados y guardados SOLO en archivo temporal
                             /tmp con chmod 600 + gitignored por ubicación (fuera del repo);
                             se eliminan al cierre si no se retienen las cuentas
Evidencia .................. sin passwords/tokens (redactada)
```

## 5 · Política de limpieza y UAT

`GA_FE_02_A_TEST_DATA_LEDGER.md` (vacío hoy) registrará cada artefacto `GA_FE_02_E2E_<ts>`;
restauración por flujos oficiales; cuentas A–D retenibles como fixture de regresión ENV-01
(RETAINED_TEST_FIXTURE) con credenciales fuera del repo. UAT: `UAT_READY` se activará SOLO con
E2E verde (§81); hoy `NO`.

## 6 · Plan y ejecución de esta pasada

`GA_FE_02_A_PLAN.md` (28 fases del encargo) — esta pasada cubrió: fases 1–4 (preflight, gates,
lecturas, **descubrimiento de provisioning completo**), y la determinación §5 con cadena de
evidencia; fases 5–8 quedan listas para dispararse con el bootstrap; 9 (E opcional) clasificada;
10–25 planificadas y bloqueadas por la misma causa raíz; 26–28 ejecutadas como cierre
(`BLOCKED_AUTH_BOOTSTRAP_CREDENTIAL_REQUIRED`).

## 7 · Lo que NO se hizo (y no se hará)

```
Auth bypass .............. NO
DB directa / seeds ........ NO
JWT fabricado ............. NO
admin/admin ............... NO usado
Búsqueda de secretos ...... NO (solo verificación de PRESENCIA de variables documentadas)
Adivinación ............... NO
Usuarios reales tocados ... NO (0)
Producto modificado ....... NO (diff de producto = 0)
```
