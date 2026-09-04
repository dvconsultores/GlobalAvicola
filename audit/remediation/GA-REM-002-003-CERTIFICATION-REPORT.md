# GA-REM-002 · GA-REM-003 — CERTIFICATION REPORT (SECURITY CLUSTER)

| | |
|---|---|
| **GA-REM** | `GA-REM-002` (RBAC backend) · `GA-REM-003` (contexto de autorización y token) |
| **Wave** | 2 · **Stage 5** |
| **Fecha** | 2026-09-04 |
| **Hallazgos** | `R-25` · `R-36` · `R-42` · `R-43` · `R-44` |
| **Estado final** | **`CERTIFIED`** (Wave 2.5) — `R-44` resuelto y ambos caminos de base certificados |

---

## 1. Original findings

`GA-REM-002` — las 78 rutas del backend comprobaban únicamente que hubiera sesión. El
modelo de permisos existía (`Permission(role_id, module, action, scope_type)`), los roles
se sembraban con sus permisos, y **nada los leía**. Cualquier usuario autenticado podía
aprobar registros, exportar a SAP o desactivar maestros; el único control efectivo era que
la interfaz no mostrara el botón, y un `curl` bastaba para saltárselo.

`GA-REM-003` — la renovación de sesión emitía la mitad de los claims del login.

---

## 2. Implementation

### `GA-REM-002` · autorización declarada por ruta

`require_permission(modulo, accion)` en `app/auth/security.py`. Los permisos del rol viajan
ahora en el contexto del usuario —antes se cargaban solo para deducir `is_super_admin` y se
descartaban—. Sin sesión el resultado es `401`; con sesión y sin permiso, `403`. La
distinción importa: un `401` hace reintentar el login en balde.

Aplicada a **170 de 177 rutas**. Las 7 restantes son públicas con motivo declarado:
`/login` y `/refresh` (son cómo se obtiene la sesión), `/me` (la propia identidad),
`/switch-company` (el servicio valida que la compañía sea suya),
`/users/{id}/password` (la autorización depende de quién pide qué y la decide el servicio),
`/operations/event-types` (catálogo estático) y `/health`.

### `AC08` · el olvido rompe el arranque, no la seguridad

`app/authorization_coverage.py` enumera las rutas al importar la aplicación y **aborta el
arranque** si alguna no declara permiso ni consta como pública. No es formalismo: una ruta
nueva sin autorización reproduce en silencio el estado anterior a esta Wave.

La comprobación demostró su utilidad de inmediato: al activarla localizó dos rutas que se
habían escapado (`/masters/farms/{farm_id}/houses` y
`/masters/hatcheries/{hatchery_id}/incubators`).

### `R-36` · el filtro de compañía era fail-open

```python
if not is_super_admin and self.company_id:      # antes
if not is_super_admin:                          # ahora
```

Con la condición anterior, un usuario **sin compañía** no recibía filtro alguno y veía los
eventos de **todas** las empresas. La ausencia de compañía debe dar acceso a nada, no a
todo. Corregido en `get_events` y en `get_alerts`.

### `GA-REM-003` · el contexto se reconstruye, no se copia

`login` emitía `{sub, username, company_id, role_id, view_type}`; `refresh` emitía
`{sub, username}`. El backend no lo notaba —carga el usuario por `sub`— pero el frontend sí:
lee esos claims del token (`auth.store.ts:76`), de modo que tras renovar la sesión la
interfaz perdía la vista y la compañía.

Ambos comparten ahora `_claims_de(user)`, que **reconstruye desde la base**. Efecto
colateral deseable: si a un usuario le cambian el rol o la compañía, la renovación recoge
el cambio en lugar de arrastrar el estado del momento del login.

### `R-43` · el refresco nunca funcionó *(nuevo, P0)*

```
asyncpg.exceptions.UndefinedFunctionError:
  operator does not exist: integer = character varying
```

`refresh_token` comparaba `payload["sub"]` —cadena, como manda el JWT— contra `User.id`,
entero. PostgreSQL rechazaba la comparación y el endpoint respondía 500 **siempre**.
`get_current_user` sí convertía (`security.py:93`); esta ruta se quedó atrás.

Consecuencia en producción: **toda sesión moría al expirar el token de acceso, a los 30
minutos**, sin posibilidad de renovarla. Se descubrió al escribir el primer test que ejerce
la renovación.

---

## 3. AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| `AC01` | Un operador no puede aprobar | ✅ 403 |
| `AC02` | Un operador no puede borrar maestros | ✅ 403 |
| `AC03` | Un operador no puede exportar a SAP | ✅ 403 |
| `AC04` | Quien tiene el permiso pasa | ✅ operador registra; aprobador alcanza aprobaciones |
| `AC05` | El alcance de compañía se valida | ✅ incluye el caso `R-36` (usuario sin compañía) |
| `AC06` | 401 sin sesión, 403 sin permiso | ✅ |
| `AC07` | El control no depende de la interfaz | ✅ invocación directa |
| `AC08` | Ninguna ruta sin decisión; el olvido impide el arranque | ✅ **177/177**, 0 sin decisión |
| `AC09` | El Super Admin conserva su alcance | ✅ 5 módulos |

`GA-REM-003`: contexto conservado al renovar y recogido de la base ✅ · `R-43` ✅

## 4. Tests

`tests/test_rbac.py` — **21 PASS · 0 FAIL**: cobertura de rutas, 401/403, siete
prohibiciones parametrizadas del rol operador, permisos concedidos, alcance de compañía,
Super Admin, coherencia del catálogo de roles y las dos pruebas de renovación.

---

## 5. ⚠ PRERREQUISITO DE DESPLIEGUE — bloqueante

**El enforcement no puede activarse en producción hasta completar el catálogo de permisos
de la base de producción.**

Al contrastar lo que exigen las rutas con lo que conceden los roles reales apareció esto:

```
pares (modulo, accion) exigidos por rutas ....... 29
concedidos por los roles reales ................. 16
exigidos que NINGÚN rol concedía ................ 18
```

Entre ellos **`masters:read`, requerido por 40 rutas**: sin él no se pueden cargar granjas,
galpones, vacunas ni tipos de alimento, es decir, casi ninguna pantalla. Mientras nada
comprobaba los permisos, las definiciones de rol podían estar incompletas sin que se
notara; con el enforcement activo, **la aplicación quedaría inservible para todo usuario que
no sea Super Admin**.

Se completaron las definiciones en `seeds/dev_seeds.py` —derivadas de la función documentada
de cada rol en `docs/12 §3`, no de lo que resultara cómodo— y se añadió el test
`test_todo_permiso_exigido_lo_concede_algun_rol_o_es_de_super_admin`, que impide que la
brecha vuelva a abrirse en silencio. Trece permisos quedan como exclusivos del Super Admin,
enumerados de forma explícita: son operaciones de administración y no existe un rol
administrativo intermedio que ninguna fuente describa.

**Pero la base de producción conserva los permisos antiguos.** Antes de desplegar hace
falta:

1. inventariar los permisos por rol en producción;
2. aplicar el catálogo completo mediante migración de datos o procedimiento controlado;
3. verificar con una cuenta real de cada rol que las pantallas cargan;
4. solo entonces desplegar el enforcement.

Se registra como **`R-44` (bloqueante de despliegue)**. Por esto el estado es
`IMPLEMENTED` y no `CERTIFIED`: el código está completo y verificado, la condición de
entorno no.

---

## 6. Regression

| Métrica | Tras Stage 4 | **Tras Stage 5** |
|---|---|---|
| Recolectados | 168 | **189** |
| PASS | 167 | **188** |
| FAIL | 1 | **1** (`BR-14`, Stage 7) |

**Cero regresiones** pese a tocar 172 rutas. Quality gates 8/8 en verde.

---

## 7. Files changed

```
backend/app/auth/security.py            permisos en contexto; require_permission; tiene_permiso
backend/app/auth/service.py             _claims_de compartido; R-43
backend/app/authorization_coverage.py   nuevo — AC08
backend/app/main.py                     verificación de cobertura al arrancar
backend/app/dependencies.py             re-export de la autorización junto a la autenticación
backend/app/*/router.py (9 ficheros)    170 rutas con permiso declarado
backend/app/masters/router.py           el factory cubre ~90 rutas
backend/app/operations/service.py       R-36 en get_events y get_alerts
backend/seeds/dev_seeds.py              catálogo de permisos completado
backend/tests/test_rbac.py              nuevo — 21 tests
alembic/versions/**                     SIN CAMBIOS
frontend/**                             SIN CAMBIOS
```

## 8. Hallazgos anotados, no corregidos

| ID | Observación | Sev. | Destino |
|---|---|---|---|
| `R-42` | `get_current_bird_balance` no filtra por compañía: un `lot_id` ajeno devolvería saldo | P1 | `GA-REM-019` |
| `R-25` | `PUT /users/{id}` ya exige `users:update`; queda pendiente que un usuario pueda editar **su propio** perfil sin ser administrador | P2 | `GA-REM-019` |
| `R-44` | Catálogo de permisos de producción incompleto | **bloqueante** | prerrequisito de despliegue |

## 9. Final status

**`IMPLEMENTED`.** El enforcement es completo y está verificado: 177 de 177 rutas con
decisión de autorización, 21 tests en verde, cero regresiones. La certificación queda
condicionada a completar el catálogo de permisos en producción (`R-44`), que es una
condición del entorno y no del código.


---

# ADDENDUM — Wave 2.5 · `R-44` resuelto y certificación completada

La Wave 2 dejó `GA-REM-002` en `IMPLEMENTED` por una razón concreta: el código estaba
completo y verificado, pero **la base de producción conservaba la matriz de permisos
histórica**, y desplegar el enforcement sobre ella habría dejado a todo usuario que no
fuese Super Admin con 403 en casi toda la aplicación.

## Lo que faltaba, y por qué las semillas no bastaban

```
SEED  ≠  PRODUCTION DATA MIGRATION
```

Actualizar `dev_seeds.py` sirve a instalaciones nuevas y no toca una base existente. La
reconciliación tenía que ser una **migración de datos**.

Pero antes había un problema mayor, que la Wave 2.5 descubrió al buscar dónde colocarla:
**el despliegue no ejecutaba migraciones en absoluto** (`GA-REM-024`). Sin resolver eso, ni
la reconciliación ni las migraciones de enum de la Wave 2 habrían llegado a producción.

## Mecanismo elegido

`alembic/versions/l2m3n4o5p6q7_reconcile_role_permissions.py`, una migración de datos
**transaccional**, válida porque `GA-REM-024` garantiza ahora el orden:

```
container start -> alembic upgrade head -> uvicorn
```

No se eligió por comodidad: se eligió porque el orden quedó demostrado con evidencia
—Dockerfile, entrypoint, compose— y no supuesto.

## Criterios de la reconciliación

| Criterio | Cómo se cumple |
|---|---|
| Solo añade | ninguna sentencia `DELETE`; un test comprueba que las 33 asociaciones históricas siguen ahí |
| Mínimo privilegio | cada permiso va al rol cuya responsabilidad documenta `docs/12 §3`. 13 operaciones de administración siguen siendo exclusivas del Super Admin |
| Idempotente | inserta solo lo ausente; verificado por ausencia de duplicados y por recuento estable |
| Tolerante | si una instalación renombró o eliminó un rol, se omite sin fallar |
| No toca personas | 6/6 usuarios conservados con su rol original |

## Certificación — los seis requisitos

| Requisito | Resultado |
|---|---|
| `RBAC CODE PASS` | ✅ 177/177 rutas con decisión declarada; 21 tests |
| `FRESH INSTALL PASS` | ✅ `PATH A` — 229 PASS |
| `EXISTING DB UPGRADE PASS` | ✅ `PATH B` — 35 PASS desde el estado anterior a la Wave 2 |
| `ROLE MATRIX PASS` | ✅ `RBAC_ROLE_PERMISSION_MATRIX.md`, 29 permisos con destino justificado |
| `NON-SUPERADMIN ACCESS PASS` | ✅ 13 comprobaciones de acceso real por rol tras la actualización |
| `NEGATIVE PERMISSION TESTS PASS` | ✅ 8 comprobaciones de denegación; el Auditor sin una sola acción de escritura |

## `R-48` — hallazgo nuevo de la Wave 2.5

El camino de actualización destapó otro defecto que la instalación nueva no podía revelar:
**`switch-company` no tenía ningún efecto.** Emitía el token con la compañía elegida y
`get_current_user` lo descartaba, leyendo siempre la de la base.

Para un usuario normal eso es correcto y es la propiedad que sostiene el aislamiento
multiempresa: un token no puede reclamar una compañía ajena. Pero el Super Admin **no
pertenece a ninguna compañía**, y `switch-company` existe precisamente para que pueda
situarse en una. Con el enforcement activo, la consecuencia era que **nadie podía crear un
lote**: solo el Super Admin tiene `lots:create`, y no tenía compañía en la que crearlo.

Corregido honrando el claim **solo para quien ya puede operar sobre cualquier compañía**.
No concede ningún privilegio nuevo: únicamente acota dónde escribe. Dos tests fijan ambos
lados —que el cambio surte efecto y que un usuario normal no puede reclamar una compañía
ajena—.

## `OD-04` — decisión abierta, no bloqueante

`docs/12 §3` describe un **Administrador** distinto del Super Admin. El catálogo de roles no
lo tiene, y no se inventa. Las 13 operaciones de administración quedan en el Super Admin.

Si se crea ese rol, **`R-50` debe resolverse antes**: `company_id` es fijable desde el
cliente en 19 esquemas de maestros, hoy inocuo porque solo el Super Admin alcanza esas
rutas y está facultado para operar entre compañías.

## Estado final

**`CERTIFIED`.** El enforcement es completo, el catálogo de roles es coherente con él, y la
reconciliación está probada sobre una base que reproduce una instalación existente.
