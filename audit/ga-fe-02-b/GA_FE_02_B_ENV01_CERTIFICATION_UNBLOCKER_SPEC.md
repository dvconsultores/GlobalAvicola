# GA-FE-02-B · ENV-01 CERTIFICATION UNBLOCKER — SPEC DE GOBERNANZA

**Fase 9 · padre GA-FE-02 / GA-FE-02-A · 2026-09-11 · Autoridad: prompt GA-FE-02-B (decisiones
A–G explícitas del propietario) · Baseline de entrada: `0dfa20b` (D1 = `ea26b2e`) · Runtime:
`https://avicola.globaldv.net` · bundle `index--DbCa8Hk.js`**

> Esta spec **no crea semántica de negocio nueva**: F1 es inicialización de entorno de un modelo
> ya gobernado (`GA-REM-040 §2`, `OD-16.a`); F2 implementa `OD-15 §6` (rol canónico ya decidido);
> F4 expone `OD-14` en UI; F3 repara fixture malformada contra un invariante ya documentado.
> No requiere Owner Decision nueva (`GA-FE-02-B §2`).

---

## 1 · Alcance

| F | Problema | Tipo | Resolución |
|---|---|---|---|
| **F1** | Catálogo `BusinessUnit` vacío en ENV-01 (`GET /business-units` → `[]`; 4×404 candidatos) | ENV (data de plataforma) | **GA-FE-02-C §2 (autorización explícita)**: el catálogo se vuelve dato determinista de despliegue — migración de datos Alembic `y5z6a7b8c9d0` (solo catálogo; §4.2) |
| **F2** | Rol «Administrador de Accesos» ausente (13 roles, ninguno con `business_units:*`) | ENV (RBAC de plataforma) | Crear el rol canónico por **API oficial** (`POST /roles`) con exactamente 4 permisos |
| **F3** | `GET /users` 500 con ≥10 filas; ids 57–70 → 500 individual | DATA (fixture malformada) | Reparar emails inválidos (dominio reservado) por **API oficial** (`PUT /users/{id}`) + endurecer el seed |
| **F4** | Selector de empresa invisible para la autoridad global sin contexto (`CAP-SES-05`, `IMPLEMENTED_BUT_NOT_EXPOSED`) | CODE (frontend, mínimo) | Hacer alcanzable la selección exigida por `OD-14` (RED→fix mínimo en `Header`) — reutiliza `CAP-SES-05`, sin R-ID nuevo |

**Fuera de alcance (prohibido por la tranche)**: unidades nuevas · semántica nueva de permisos ·
bypass de auth · escrituras crudas a DB de auth · borrado de usuarios 57–70 · `GA-FE-03` ·
`R-181` · `R-182` · Wave B/C · SAP · ratificación `BU-D10`. `R-98`/`R-119` permanecen intactos.

## 2 · Hechos verificados que gobiernan las decisiones

1. `GET /business-units` **debe listar las cuatro siempre** (`admin.listar_habilitaciones`); `[]`
   ⇒ catálogo de plataforma vacío (no hay API de catálogo; se siembra server-side — Dockerfile
   copia `seeds/`; el entrypoint solo corre `alembic`).
2. Guard exacto de rutas BU (código): `read`→GET empresa/concesiones · `update`→PATCH enable/disable ·
   `create`→candidatos+conceder · `delete`→revocar. Candidatos exige `create` y **no** `users:read`
   (`router.py:157-171`; `OD-15 §6`).
3. `UserRead.email: Optional[EmailStr]`; pydantic valida con `check_deliverability=False` pero
   **rechaza dominios reservados** (`.local`). Prueba local reproducida con el venv del backend:
   `USERREAD_LOCAL FAIL: ValidationError (special-use or reserved)` · `USERREAD_FIXED OK`.
   `integration_seeds.USERS_DEF` (14 usuarios: 7 móvil + 7 web) usa `f"{username}@testing.local"`
   — coincide con los 14 ids 57–70 que devuelven 500. `baseline_seeds` ya documenta el invariante
   («EmailStr rechaza .test/.example/.local… el usuario resultaría ilegible por la API»).
4. Selector de empresa: `Header.tsx` renderiza el bloque selector+badge solo si
   `(activeCompanyName || user?.company_name)`; el bootstrap admin nace sin empresa persistida y
   sin contexto ⇒ **ningún control visible** (mismo root que `CAP-SES-05`/auditoría frontend).
5. Acceso server-side del agente: **no existe** mecanismo autorizado desde esta estación
   (`docker` ausente; runtime en `84.247.161.106`; sin shell/SSH provisto; prohibido buscar
   credenciales) ⇒ F1 se clasifica `BLOCKED_SERVER_ACCESS_F1` con comando canónico exacto (§4).

## 3 · ACCESS_ADMIN_PERMISSION_MATRIX (F2 — permisos exactos, solo existentes)

| Operación | Ruta (fuente) | Permiso exigido | Spec fuente | ¿Requerido por el rol? |
|---|---|---|---|---|
| Ver configuración de unidades | `GET /api/v1/business-units` | `business_units:read` | `OD-16 §7`, `GA-REM-040` fase 7 | **SÍ** |
| Ver concesiones de un usuario | `GET /api/v1/users/{id}/business-units` | `business_units:read` | `AC-B07` | **SÍ** |
| Habilitar/deshabilitar BU de empresa | `PATCH /business-units/{code}/enable|disable` | `business_units:update` | `OD-16 §7`, `AC-A03` | **SÍ** (figura canónica; BU-D07 pendiente no se toca) |
| Listar candidatos | `GET /business-units/{code}/grant-candidates` | `business_units:create` | `R-129`, `AC-H15` | **SÍ** |
| Conceder | `POST /users/{id}/business-units` | `business_units:create` (+segregación `OD-15.a`) | `AC-B01` | **SÍ** |
| Revocar | `DELETE /users/{id}/business-units/{code}` | `business_units:delete` | `AC-B05` | **SÍ** |
| — | — | `users:read` · comodín · productivos | `OD-15 §6` | **NO — jamás** |

`scope_type="all"`; **ningún permiso nuevo** (los cuatro pares módulo:acción ya son canónicos);
**sin rol nuevo de semántica** — el rol ES «Administrador de Accesos» (nombre canónico `R-113`).

## 4 · F1 — Ejecución y Postcondición

> **Histórico (§4/§4.1): superado por §4.2** (`GA-FE-02-C`). La vía manual quedó agotada: dos
> reportes de ejecución del propietario **no observables** en runtime (3.ª verificación:
> `[]`/`count=0`) y acceso server-side no autorizado desde esta estación
> (`BLOCKED_SERVER_ACCESS_F1`). Se conserva como registro.

**Ejecución**: server-side únicamente (comando canónico para owner/ops — `BLOCKED_SERVER_ACCESS_F1`
desde esta estación):

```bash
docker exec -i globalavicola-backend python - <<'PY'
import asyncio
from app.database import async_session
from seeds.baseline_seeds import sembrar_unidades_de_negocio

async def main():
    async with async_session() as s:
        creadas = await sembrar_unidades_de_negocio(s)
        await s.commit()
        print('unidades de negocio creadas:', creadas)

asyncio.run(main())
PY
```

**§4.1 · Retry 2026-09-11 con self-check (obligatorio)** — tras el reporte del propietario el
catálogo seguía vacío; ejecutar ESTA versión (agrega conteo y códigos para verificación en la
misma salida):

```bash
docker exec -i globalavicola-backend python - <<'PY'
import asyncio
from sqlalchemy import select, func
from app.database import async_session
from app.business_units.models import BusinessUnit
from seeds.baseline_seeds import sembrar_unidades_de_negocio

async def main():
    async with async_session() as s:
        creadas = await sembrar_unidades_de_negocio(s)
        await s.commit()
        n = (await s.execute(select(func.count()).select_from(BusinessUnit))).scalar_one()
        codigos = sorted((await s.execute(select(BusinessUnit.code))).scalars().all())
        print('creadas:', creadas, '· filas_catalogo:', n, '· codigos:', codigos)

asyncio.run(main())
PY
```

Esperado: `creadas: 4 · filas_catalogo: 4 · codigos: ['breeder', 'broiler', 'grandparent',
'hatchery']`. Si `filas_catalogo` siguiera 0: el contenedor apunta a otra base — comprobar
`docker logs --tail 20 globalavicola-backend` (el entrypoint imprime «target: host/db»).

**Invariantes del seed** (verificados en código, §9 del encargo): idempotente por `code`; crea
**solo** filas `BusinessUnit`; **cero** `CompanyBusinessUnit`; **cero** `UserBusinessUnit`; no
toca roles/permisos/empresas.

**AC-F1**: (1) `GET /business-units` → 4 filas `grandparent·breeder·hatchery·broiler`
(`is_enabled=false` — sin fila de empresa, correcto); (2) códigos únicos, sin quinta unidad;
(3) `GET /business-units/{code}/grant-candidates` → 404 mientras no haya habilitación (contrato
«unidad apagada no tiene candidatos») → tras E2E-02 (enable) → 200; (4) re-ejecutar el comando →
`creadas: 0` (idempotencia); (5) ninguna empresa queda habilitada ni ningún usuario con concesión.

## 4.2 · F1 — Remediación autónoma `GA-FE-02-C`: catálogo como dato determinista de despliegue

**Autorización**: prompt `GA-FE-02-C §2` (explícita del propietario). **Dedup**: enmienda a F1;
no crea finding, ni Owner Decision, ni R-ID — las cuatro unidades ya están gobernadas
(`GA-REM-040 §2`, `OD-16.a`; mapping intacto: grandparent=Progenitoras, breeder=Reproductoras,
hatchery=Incubadora, broiler=Engorde; `is_active` según modelo).

**Clasificación**: `MISSING_CANONICAL_BASELINE_DATA` — el catálogo dependía de una siembra
manual/opcional que el ciclo de despliegue determinista no garantizaba.

**Mecanismo — `ALEMBIC_DATA_MIGRATION`** (verificado en fuente, §10): `docker-push-backend.yml`
se dispara con `backend/**`; `Dockerfile` copia `alembic/`; `docker-entrypoint.sh` ejecuta
`alembic upgrade head` **antes de servir** (`GA-REM-024`); Watchtower recrea `:latest`.
Requisito normativo:

> Tras un despliegue **normal** (commit → push → auto-deploy → arranque) sobre cualquier base
> en la revisión anterior o posterior, las **cuatro filas canónicas** del catálogo
> `business_units` DEBEN existir. Sin `docker exec`, sin SQL manual, sin paso de operador.

**Supersesión registrada**: el docstring de `p6q7r8s9t0u1` dejó escrito «una migración que
inserta catálogo obliga a mantener el dato en dos sitios» y sembró solo en `seeds/`. Queda
superado: la fuente única se conserva con el patrón ya del repo — **el seed importa la
constante de la migración** (como ya hace con la matriz RBAC de `l2m3n4o5p6q7`). Sin segundo
sitio donde el dato pueda divergir.

**Diseño de la migración** (`y5z6a7b8c9d0`, `down_revision = x4y5z6a7b8c9` — head vigente,
36 revisiones, 1 head):

- Datos locales de la migración (`UNIDADES_CANONICAS`); **sin** importar modelos ORM de la app.
- `SELECT code` + `INSERT` solo de códigos ausentes: idempotente; soporta vacío/parcial/completo;
  portable PostgreSQL + SQLite (para el test dirigido).
- **No** actualiza filas existentes (no reescribe `name_key`/`bird_type` presentes).
- `is_active`/`created_at` por defaults de esquema (`p6q7r8s9t0u1`: `uq_business_unit_code`;
  `is_active server_default true`).
- **Downgrade = NO-OP intencional** (precedente `l2m3n4o5p6q7`): borrar filas canónicas podría
destruir referencias (`company_business_units`, `user_business_units`, histórico); es baseline
aditivo — no hay estado anterior que restaurar.

**AC-F1 (1–17)**:

| AC | Criterio | Evidencia |
|---|---|---|
| 01 | Crea exactamente los 4 códigos canónicos | test vacío→4 + runtime |
| 02 | No duplica filas existentes | unique `code` + test |
| 03 | Idempotente | test doble pasada |
| 04 | Estado parcial se completa (solo ausentes) | test parcial |
| 05 | Sin quinta unidad | test exactamente 4 |
| 06 | Cero `CompanyBusinessUnit` creadas | test tablas-adyacentes + invariantes runtime |
| 07 | Cero `UserBusinessUnit` | íd. |
| 08 | Cero asignaciones de rol | diff de migración (no toca `users`/`roles`) |
| 09 | Cero definiciones de permiso | diff (no toca `permissions`) |
| 10 | Cero cambios RBAC | íd. |
| 11 | Cero cambios de empresa | íd. |
| 12 | Cero cambios SAP | íd. |
| 13 | Runtime: `GET /business-units` = 4 (empresa efectiva autorizada) | §4.2.1 |
| 14 | Segundo arranque no duplica | test + arranques reales con revisión ya aplicada |
| 15 | Catálogo completo intacto | test completo |
| 16 | Columnas/constraints según esquema real | `p6q7r8s9t0u1` + réplica en test |
| 17 | Sin operación manual de servidor | pipeline normal |

**§4.2.1 Verificación post-deploy (obligatoria)**: autenticar → empresa segura →
`GET /business-units` → **count=4**, códigos `[breeder, broiler, grandparent, hatchery]`,
`is_enabled=false` (catálogo ≠ habilitación). Efectos colaterales: CBU/UBU/roles/permisos sin
cambio (rol id=35 intacto). Idempotencia: AC14 por test + arranques posteriores del pipeline.

**Plan/Tasks F1 (`GA-FE-02-C §24–26`)** — estado al cierre de cada fase:

| # | Tarea | Estado (2026-09-11) |
|---|---|---|
| T1 | Test dirigido (RED válido: migración ausente) | **DONE** — RED 6/6 (`tests/test_migration_bu_catalog.py`) |
| T2 | Migración `y5z6a7b8c9d0` + `UNIDADES_CANONICAS` + `_sembrar_catalogo` + downgrade NO-OP | **DONE** — C2 `b4d8c3a` |
| T3 | Seed importa la fuente única (sin segundo sitio) | **DONE** — C2 (`_unidades_de_negocio_de_la_migracion`) |
| T4 | Tests dirigidos GREEN (SQLite en memoria; guarda `GA-REM-014`) | **DONE** — 6/6 passed |
| T5 | Integridad de cadena (1 head) + `compileall` | **DONE** — heads=`[y5z6a7b8c9d0]`, 37 revisiones; OK |
| T6 | COMMIT C2 + push → pipeline normal | **DONE** — `28e95bb` (C1) + `b4d8c3a` (C2) |
| T7 | Postcondición runtime §4.2.1 | **DONE** — §4.2.2 |
| T8 | Ledger + gap matrix + cierre F1 | **DONE** — este commit |

**§4.2.2 Resultado runtime (2026-09-11)** — la migración se aplicó por el **pipeline normal**
(push `b4d8c3a` → imagen backend → Watchtower → entrypoint `alembic upgrade head`), sin
ejecución manual alguna:

- `GET /business-units` empresa 1 → **4 filas**: `(breeder, businessUnits.breeder, false)` ·
  `(broiler, businessUnits.broiler, false)` · `(grandparent, businessUnits.grandparent, false)` ·
  `(hatchery, businessUnits.hatchery, false)` — códigos exactos, sin quinta unidad, sin
  duplicados, `is_enabled=false` (catálogo ≠ habilitación). [AC01–05, 13, 16]
- Empresa 3 → **mismo catálogo global** (4 filas, todas `false`) — sin duplicación por tenant. [AC13]
- Candidatos `{code}/grant-candidates` → **404 ×4** (contrato: unidad apagada no tiene
  candidatos).
- Sin efectos colaterales: CBU de empresa **sin crear** (0 habilitaciones), UBU **sin crear**,
  `GET /roles` = 14 con rol 35 intacto (4 permisos exactos), `GET /users` = 200 (23 filas;
  ids 57–70 presentes) — RBAC/permisos/empresas/SAP sin cambio. [AC06–12]
- Idempotencia: test dirigido AC03/AC14 (doble pasada, parcial, completo) + el propio arranque
  del pipeline que re-ejecuta `upgrade` sobre revisión ya aplicada sin duplicar.
- IDs de fila no expuestos por el contrato (`HabilitacionRead`: `code/name_key/is_enabled`).

F1 queda **CLOSED**; `GA-FE-02-B` **CLOSED**; ENV-01 **READY FOR GA-FE-02** (sin certificar todavía).

## 5 · F2 — Creación del rol (API oficial)

`POST /api/v1/roles` como Super Administrador **sin contexto** (→ plantilla de sistema,
`company_id NULL`; `OD-13.b`/`OD-13.e`), cuerpo:

```json
{"name": "Administrador de Accesos", "description": "Administración del acceso por unidad de negocio",
 "permissions": [
   {"module": "business_units", "action": "read",   "scope_type": "all"},
   {"module": "business_units", "action": "update", "scope_type": "all"},
   {"module": "business_units", "action": "create", "scope_type": "all"},
   {"module": "business_units", "action": "delete", "scope_type": "all"}]}
```

**AC-F2**: (1) rol legible en `GET /roles` (14 activos) con **exactamente** esos 4 permisos;
(2) sin comodín, sin `users:*`, sin cadena productiva; (3) `company_id NULL` (plantilla),
asignable por la regla `_rol_asignable` (no reparte autoridad global); (4) **ningún usuario
humano** asignado en esta tranche (solo Actor B en §8); (5) `0` definiciones de permiso nuevas.

## 6 · F3 — Diagnóstico, Clasificación y Reparación (DATA)

**Clasificación: `DATA` (fixture malformada), con endurecimiento de fixture (código de seeds).**
Cadena de evidencia en `F3_USERS_500_DIAGNOSTIC_MATRIX.md` (runtime + fuente + reproducción local).

**Reparación (mínima, por API oficial, fila a fila — sin borrado, sin tocar credenciales)**:
para cada id 57–70 → `PUT /api/v1/users/{id}` con `{"email": "<username>@globalavicola.com"}`
(local parte = username según seed; el propio `PUT` devuelve `UserRead` y **verifica** id↔username
antes de continuar con el siguiente). Registro BEFORE/AFTER por fila en el ledger.

**Endurecimiento**: `integration_seeds.py` deja de generar `.local` (dominio válido
`globalavicola.com`) + test de regresión de seeds (guard de dominios reservados).

**AC-F3**: (1) cada id 57–70 → `GET` 200 (antes 500); (2) `GET /users` (default y `limit=100`)
→ 200 sin 500; (3) tenant/rol/estado sin cambio; **ninguna** contraseña o hash tocado;
(4) emails únicos y válidos; (5) seed endurecido + regresión añadida.

## 7 · F4 — Selector de empresa (fix mínimo, RED→GREEN) — reutiliza `CAP-SES-05`

**Comportamiento exigido (OD-14)**: actor con capacidad de cambiar empresa (autoridad global) y
`effective_company_id = null` ⇒ **control de selección visible** en la UI normal; actor sin esa
capacidad ⇒ sin selector; tras seleccionar ⇒ `switch-company` + contexto visible + superficies
de inquilino usables; tras hard-refresh ⇒ sigue correcto (semántica de sesión).

**RED** (nuevo test, `gaFe02b.companySelector.test.tsx`): super admin sin contexto ⇒ selector
presente (**falla hoy**); usuario común ⇒ ausente; super admin con nombre ⇒ presente.
Además, ajuste mínimo en `auth.store.fetchMe` para resolver el **nombre** de la empresa efectiva
cuando la persistida es `null` (bootstrap admin) — cubierto por test de sesión.

**Fix mínimo**: `Header.tsx` — renderizar el bloque cuando `isSuperAdmin` aunque no haya nombre
(con placeholder i18n `company.select`), sin tocar navegación global (`R-98`/`R-119` intactos).

**AC-F4**: RED→GREEN + tsc + Vitest + build; deploy por pipeline; runtime: selector visible para
admin sin contexto; oculto para actor sin autoridad; `switch-company` 200; empresa actual
visible; hard-refresh correcto; `/admin/unit-access` operable con empresa elegida.

## 8 · Actores de prueba (después de F1+F2; plan GA-FE-02-A sin rediseño)

| Actor | Username | Rol | Company | Requisito |
|---|---|---|---|---|
| A · Company-BU Admin | `ga-fe02-a-<ts>` | «Administrador de Accesos» (nuevo, canónico) | 1 | jornada E2E-02/03 |
| B · Access Admin | `ga-fe02-b-<ts>` | «Administrador de Accesos» | 1 | candidatos/conceder/revocar/auto-concesión |
| C · Target operativo | `ga-fe02-c-<ts>` | rol operativo existente (operaciones/lotes) | 1 | sin concesión inicial de la BU objetivo |
| D · No autorizado | `ga-fe02-d-<ts>` | rol existente sin `business_units:*` | 1 | deny de superficies admin |
| E · Global (opcional) | bootstrap `admin` | Super Administrador | — | fail-closed / contexto situado |

Passwords: generadas localmente (fuertes), solo en `/tmp` (600) — **nunca** en repo/docs/capturas.
La coexistencia A/B (mismo rol canónico; el producto hoy no separa «solo-empresa» de
«solo-usuarios», `BU-D07` pendiente) se documenta como frontera real, sin inventar semántica.

## 9 · Re-certificación GA-FE-02-A (re-run TOTAL, sin transitividad)

Tras F1–F4: provisionar A–E (§8) → pre-test state → **congelar generación** de producto →
E2E-01…E2E-10 + matriz 3D dura (`OFF/YES/YES→DENY` · `ON/NO/YES→DENY` · `ON/YES/NO→DENY` ·
`ON/YES/YES→ALLOW`) + refresh/relogin/móvil 390×844/red/persistencia/auditoría/reconciliación →
restauración segura + ledger → evidencia → UAT. La evidencia previa queda **histórica**: no se
combina con la nueva (`§43`). Si un push de producto aterriza a mitad del E2E → **STOP** y
reiniciar contra el nuevo baseline.

**Security stop (`§44`)**: auto-concesión lograda · cross-company logrado · mutación por actor no
autorizado · BU OFF con acceso productivo · sin concesión con acceso · sin RBAC con acceso ·
mezcla de tenants · selector expuesto a actor sin autoridad ⇒ EVIDENCIA → FINDING → SPEC, sin
hotfix.

## 10 · Rollback / Reversibilidad

| F | Reversión |
|---|---|
| F1 | No invertible por API (catálogo de producto); es aditivo e idempotente — no requiere reversión |
| F2 | `PUT /roles/{id}` (desactivar/quitar permisos) o mantener como fixture canónico (estado preferido) |
| F3 | Restaurar email original conocido (`<username>@testing.local`) por la misma API (reversible, documentado) |
| F4 | Revert del commit (próximo deploy restaura comportamiento previo) |

## 11 · Artefactos y orden de commits (`§49–50`)

1. **COMMIT 1 (este)**: esta spec + `GA_FE_02_B_GAP_MATRIX.md` + `F3_USERS_500_DIAGNOSTIC_MATRIX.md`
   + `GA_FE_02_B_ENV01_MUTATION_LEDGER.md` (esqueleto). **Cero producto.**
2. Ejecuciones ENV (F2/F3) con entradas de ledger (mismas sin producto) → commit de evidencia ENV.
3. F3 endurecimiento (seeds+test) y F4 (RED+fix) → commits de implementación; push; deploy.
4. Re-certificación completa → commit final de evidencia/certificación.

## 12 · Checklist de cierre

`F1 CLOSED` ⇒ 4 unidades + invariantes · `F2 CLOSED` ⇒ rol exacto 4 permisos · `F3 CLOSED` ⇒ 0
filas 500 + seed endurecido · `F4 CLOSED` ⇒ selector alcanzable + contexto + refresh · E2E
completo verde ⇒ `GA-FE-02 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING`. Cualquier otro
resultado: reportar el bloqueo exacto, sin certificar por partes.

## 13 · Estado de ejecución (2026-09-11)

```
F1 ... **CLOSED** — remediación autónoma `GA-FE-02-C` aplicada por pipeline normal: migración
       `y5z6a7b8c9d0` en el arranque del backend (`GA-REM-024`). Runtime verificado
       (2026-09-11): `GET /business-units` c1/c3 = **4** filas canónicas
       (`breeder·broiler·grandparent·hatchery`; `is_enabled=false`; candidatos 404×4; sin
       CBU/UBU/roles/permisos nuevos). Evidencia: §4.2.2 + ledger #7. Commits C1 `28e95bb`
       + C2 `b4d8c3a`.
F2 ... CLOSED — rol id=35 · exactamente business_units:read|update|create|delete (all) ·
       company_id NULL (plantilla) · GET /roles=14 · sin comodín/users/productivos ·
       sin asignaciones a humanos (0) — re-verificado post-deploy F1
F3 ... CLOSED — 14/14 filas 57–70 reparadas por API oficial (BEFORE 500 → AFTER 200);
       listados 200 (23 usuarios); invariantes intactos; seed endurecido `b83d908` + regresión
       — re-verificado post-deploy F1 (users 200; 57–70 presentes)
F4 ... CLOSED — `716d175` desplegado; verificación runtime autenticada PASS (selector alcanzable
       «Seleccionar empresa»; dropdown con empresas; switch-company 200; nombre resuelto por
       catálogo incluida persistida `null`; hard-refresh `/me` 200 sin forbidden; móvil 390×844).
       Evidencia: `GA_FE_02_B_F4_SELECTOR_EVIDENCE.md`

GA-FE-02-B ... **CLOSED** — F1–F4 cerrados con evidencia runtime; ENV-01 READY FOR GA-FE-02: YES
       (la certificación funcional GA-FE-02-A continúa — ver §9).
```
