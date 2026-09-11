# GA-FE-03 · SPEC — NAVEGACIÓN DINÁMICA Y DESCUBRIBILIDAD POR PERMISO

**Tranche**: GA-FE-03 (Fase 9) · **Fecha**: 2026-09-11 · **Baseline de entrada**: `5a3acc9`
(main == remoto; worktree limpio; bundle `index-B2-tZnkI.js`; health 200) · **Metodología**: Spec
Development (`GA-REM-001`) — SPECIFY → CLARIFY → PLAN → CHECKLIST → TASKS → ANALYZE →
IMPLEMENT → CONVERGE → CERTIFY. **Sin AC no hay implementación; sin E2E autenticado no hay
certificación.**

---

## 1 · Contexto

La navegación del frontend es hoy **parcialmente estática**: `navigationConfig.ts` declara un
único campo `permission` (usado solo por la entrada GA-FE-02 «Acceso por unidad»), el
`Sidebar`/`MobileDrawer` filtran **solo** las entradas que declaran permiso, el `MenuHubPage`
consume `NAV_ITEMS` **sin filtrar**, el `Dashboard` pinta atajos productivos sin política, y
ninguna ruta administrativa salvo `/admin/unit-access` tiene guarda de permiso. El contrato de
sesión (`/me` → `GA-REM-040` fase 8, `AC-H11…H14`) **ya expone todo lo necesario**:
`permissions`, `effective_company_id`, `company_business_units`, `granted_business_units`,
`effective_business_units`. `GA-FE-02` certificó el plano productivo del backend (incluida la
puerta absoluta `Company BU OFF` tras el fix D-1/`9ffc5ec`). `R-98` y `R-119` permanecen
abiertos desde la fase 8 (`GA-REM-040 T-040-23` es el trabajo de esta tranche).

## 2 · Problema

El menú **enseña puertas cerradas**: un usuario sin permiso ve entradas y al pulsarlas recibe
403/vacíos (`R-119`); el hub de menú muestra hijos no autorizados (`D-2` de GA-FE-02);
los atajos del Dashboard no obedecen política alguna; un usuario con cero unidades ve las
mismas entradas productivas que uno operativo; y la navegación no reacciona de forma explícita
a empresa, habilitación de unidad de empresa ni concesiones. Nada de esto es un agujero de
seguridad — el backend es la autoridad y niega — pero es **producto inconsistente**: la
descubribilidad no refleja la autoridad real. `R-98` (ocultar acciones de escritura por
permiso) es el residuo transversal del mismo modelo; su parte de navegación se cierra aquí.

## 3 · Alcance

1. **Modelo canónico único** de capacidades de navegación (una definición declarativa, un
   evaluador compartido por Sidebar, MobileDrawer, MobileNav, MenuHub y atajos de Dashboard).
2. **Política de visibilidad** por dimensión: RBAC (permiso), contexto de empresa, habilitación
   de unidad de empresa, concesión de unidad de usuario, autoridad global (comodín canónico).
3. **Integración en todas las fuentes de navegación** actuales: Sidebar, MobileDrawer,
   MobileNav, MenuHub (`/menu/:key`), tarjetas de procesos del Dashboard y atajos accionables.
4. **Guardas de ruta independientes** para las superficies con permiso canónico inequívoco
   (consistencia ruta↔menú, sin reemplazar la autoridad del backend).
5. **Grupos vacíos** desaparecen; paridad semántica desktop/móvil; i18n ES/EN completo.
6. **Descubribilidad administrativa**: entradas existentes + `Roles` (ruta activa sin entrada).
7. **Certificación autenticada** de la matriz de actores A–E, Z (cero unidades) y P
   (negativo RBAC), más la matriz 3D de navegación y la seguridad de deep links.

## 4 · Fuera de alcance (explícito)

`R-181` (submit/resubmit) y `R-182` (LotForm `planned_close_date`/`area_id`) **UNCHANGED** — si
el inventario los encuentra, se marcan `OUT_OF_SCOPE_OPEN_FINDING` sin cerrarlos. No se
implementa: SAP (P-08 `BLOCKED_EXTERNAL`), Wave B/C, procesos productivos nuevos, reglas de
negocio nuevas, tipos de unidad nuevos, semántica RBAC nueva, modelo de autenticación nuevo,
modelo de empresa nuevo, semántica Usuario-BU nueva, ratificación `BU-D10`, ni el flujo
completo de reverso (solo se representa en navegación si ya es ruta gobernada y visible; hoy
**no existe ruta frontend** → se clasifica aparte y **no se implementa**). No se crean
entradas nuevas de producto más allá de `Roles` (descubribilidad de ruta activa existente).
Backend/migraciones: **esperado 0** (contrato `/me` suficiente).

## 5 · Hallazgos existentes (dedup)

| Finding | Ámbito | Relación con GA-FE-03 |
|---|---|---|
| `R-119` (P1) | «el frontend no comprueba permisos en ninguna pantalla»; navegación estática; `docs/02 §3.1.3` exige «módulos accesibles» | **Raíz directa de esta tranche** (`T-040-23`, `CAP-ADM-06`). Cierre individual en `GA_FE_03_R119_RECONCILIATION.md` |
| `R-98` (P2) | «ninguna pantalla oculta acciones de escritura por permiso»; residuo transversal de `P-13` | Mismo modelo raíz; su parte de **navegación accionable** se cierra aquí; la de **acciones dentro de pantalla** excede GA-FE-03 → evaluación individual en `GA_FE_03_R98_RECONCILIATION.md` |
| `H360-F01` | ocultar acciones sin permiso | Mapeado a `R-98`/`R-119` (sin ID nuevo) |
| `D-2` (GA-FE-02-A) | tarjeta del hub para D (R-119) | Parte del alcance (MenuHub) |
| `D-3` / `D-4` (GA-FE-02-A) | `/audit?module=` 500; home fail-closed sin `dashboard:read` | **No** se tocan (backlog; no bloquean) |
| `R-121` | roles acotados por empresa | **CERRADO** (`OD-13`); no se reabre |
| `R-139` / `R-163` | alcance productivo / habilitación absoluta en escritura | Vigentes; la navegación **no** los altera |
| `BU-D10` | reactivación de concesión | `PENDING_RATIFICATION` — la navegación representa el acceso **efectivo actual**; no decide ciclo de vida |
| `CAP-ADM-06` / `CAP-ADM-07` | navegación adaptada / estado «sin unidades» | `CAP-ADM-06` objetivo de esta tranche; `CAP-ADM-07` (aviso explícito) **no** es AC — el zero-BU se resuelve ocultando, sin error |

## 6 · Gobernanza aplicada

`OD-09` (control ≠ operación; transversalidad por permiso, nunca por nombre), `OD-10`
(clasificación pendiente), `OD-11`/`OD-14` (empresa efectiva; `CONTROL_GLOBAL` vs `INQUILINO`;
sin contexto no hay unión), `OD-15` (segregación; Access Admin sin acceso productivo), `OD-16`
(cuatro unidades; **encender ≠ conceder**; apagar prevalece; sin acceso implícito), `R-121`
(semántica de permisos canónica), `R-139`/`R-163` (escritura productiva), fix `D-1`
(lectura productiva del actor global acotada), `GA-REM-002` (enforcement en backend),
`GA-REM-040 §14` (contrato de sesión).

**Invariante central**: la navegación **refleja** autoridad; **no la sustituye**. Ocultar un
enlace no protege una ruta: las guardas de ruta y el backend se validan de forma **independiente**.

## 7 · Modelo de actor

| Actor | Identidad | Autoridad | Uso en GA-FE-03 |
|---|---|---|---|
| `E` Global | bootstrap (`admin`) | comodín `("*", all)` (`is_super_admin`) | selector de empresa; control global; productivo global condicionado a BU ON |
| `A` Company-BU Admin | sintético, rol temporal `business_units:read|update` (+`dashboard:read`) | plano de control de unidades de empresa | descubre su superficie; sin productivo propio |
| `B` Access Admin | sintético, **rol canónico 35** (`Administrador de Accesos`, 4 permisos) | administración de acceso por unidad | descubre su superficie; sin productivo |
| `C` Productivo | sintético, rol temporal (`lots:read` + `operations:read` + `dashboard:read`) | operación productiva con concesión | matriz 3D, grant/revoke, enable/disable |
| `D` Autenticado sin autoridad | sintético, rol temporal (`dashboard:read`) | CORE mínimo | negativas de descubribilidad y deep links |
| `Z` Cero unidades | sintético, rol temporal (`dashboard:read`) | autenticado sin concesiones | CORE sí, productivo no |
| `P` Negativo RBAC | sintético, rol temporal (`dashboard:read`) + concesión de unidad | BU+concesión, sin permiso productivo | tercera dimensión de la 3D |

Todos sintéticos, por mecanismos oficiales (`POST /users`, `POST /roles`, `POST/DELETE
/users/{id}/business-units`), credenciales efímeras fuera del repo, baja al cierre. Rol 35
intacto. Cero usuarios humanos tocados.

## 8 · Taxonomía de capacidades

| Clase | Definición | Dependencias | Miembros (navegación) |
|---|---|---|---|
| `CORE` | capacidades núcleo de sesión/perfil/inicio | RBAC si declara permiso | `dashboard` (`dashboard:read`), `profile` |
| `CONTROL_PLANE` | administración de la aplicación | RBAC; **jamás** exige BU de usuario | `users`, `roles`, `masters`, `audit`, `unit-access` |
| `PRODUCTIVE` | operación sobre datos productivos | **RBAC + BU (empresa ∩ concesión o regla global)** | `poultry` (+4 unidades), `review`, `approvals` |
| `REPORTING` | reportes/indicadores sobre dato productivo | RBAC + BU (igual que productivo: `D-1` probó que «solo lectura» ≠ plano de control) | `reports` (+2 hijos), `reports/sap` |
| `INTEGRATION` | superficies de integración existentes | RBAC | `sap` (+4 hijos) |
| `GLOBAL_CONTROL` | control global (catálogo de empresas, contexto) | autoridad global (`OD-14`) | selector de empresa (Header — no es `NavItem`) |

Clasificación derivada del **comportamiento del recurso** (permiso backend + dimensión BU en
los servicios), no del icono ni del nombre. `BirdTypeEnum` no es ACL; la unidad de negocio no
es el módulo RBAC (`OD-09 §1`).

## 9 · Política de navegación (contrato de visibilidad)

Para cada `NavItem`, con `session = {is_super_admin, permissions, effective_company_id,
company_business_units, effective_business_units}`:

```
A.  item.permission && !hasPermission(session, permission)          → HIDDEN
B.  item BU-específico (businessUnit = bu):
      normal:  bu ∉ effective_business_units                        → HIDDEN
      global:  effective_company_id == null  OR
               bu ∉ company_business_units                          → HIDDEN
    item BU-dependiente «any» (productivo/reporting multi-unidad):
      normal:  effective_business_units == ∅                        → HIDDEN
      global:  effective_company_id == null  OR
               company_business_units == ∅                          → HIDDEN
C.  contenedor con hijos visibles == 0                              → HIDDEN (grupo vacío)
D.  resto                                                           → VISIBLE
```

- El **comodín canónico** (`is_super_admin` ⇒ permiso concedido) se apoya en el helper espejo
  de `tiene_permiso` (`R-121`); `company_id NULL` de un rol **no** es autoridad global.
- Sin sesión (`user == null`) nada se pinta (login).
- `view_type` conserva su recorte de presentación móvil **antes** de la evaluación.
- La política aplica igual a Sidebar, MobileDrawer, MobileNav, MenuHub y atajos de Dashboard.

## 10 · Política de ruta (`§25` separa tres capas)

```
NAV_VISIBLE_WHEN        ⊆ ROUTE_ALLOWED_WHEN  (la navegación nunca es más permisiva)
ROUTE_ALLOWED_WHEN      = sesión + permiso canónico de la ruta (guarda independiente)
PRODUCTIVE_DATA_ALLOWED = autoridad backend (tenant + BU ON + concesión/global + RBAC + recurso)
```

Se añaden guardas de ruta (`CapabilityRoute`/`PermissionRoute`, **por permiso, nunca por rol**)
a las rutas con permiso canónico inequívoco: `/users` y `/roles` (`users:read`), `/audit`
(`audit:read`), `/masters/*` (`masters:read`), `/sap` (`sap:read`), `/review*` (`review:read`),
`/approvals` (`approvals:approve`), `/reports*` (`reports:read`), `/poultry/*` (BU efectiva de
la unidad de la URL). Las guardas **no** dependen del estado del menú y **no** reemplazan al
backend: un actor denegado que escribe la URL a mano es denegado igualmente (fail-closed visual
+ 403/404 del backend).

## 11 · Política de unidad de negocio

- Cuatro unidades canónicas: `grandparent` · `breeder` · `hatchery` · `broiler` (`OD-16.a`).
  Sin quinta unidad. Sin alias (`grandparents`, `incubator`… quedan prohibidos).
- **Company BU OFF es absoluto** para navegación productiva, incluido el actor global (`D-1`
  no puede regresar): la visibilidad productiva global exige la unidad en
  `company_business_units` del `/me`.
- **Encender no concede** (`OD-16.d`): la habilitación no altera `effective_business_units` de
  nadie; la navegación no finge lo contrario.
- **Apagar prevalece sobre la concesión** (`OD-16.e`): con la unidad OFF la entrada productiva
  desaparece aunque exista concesión viva (la concesión no se borra — `BU-D10`
  `PENDING_RATIFICATION`).
- El productivo multi-unidad (`poultry` raíz, `review`, `approvals`, `reports`) exige que el
  conjunto efectivo (o habilitado, para el global) **no sea vacío**.

## 12 · Política del actor global

- Sin contexto (`effective_company_id == null`): el **selector de empresa permanece visible**
  (Header); las entradas de inquilino (`INQUILINO`) **fallan cerradas** (productivo, review,
  approvals, reports ocultos); el plano de control sigue visible según permiso (`OD-14.d`).
- Situado: la navegación se recalcula desde el nuevo contexto (sin entradas accionables
  heredadas de la empresa anterior).
- El productivo global **nunca** cruza Company BU OFF (regla B del §9) ni se vuelve unión de
  inquilinos (`OD-14`). El fix `D-1` no regresa.

## 13 · Política del plano de control

- Las superficies de control (`users`, `roles`, `masters`, `audit`, `unit-access`, selector)
  **no dependen** de concesiones productivas ni de BU habilitadas (`OD-09.b`).
- Access Admin (rol 35) descubre **solo** su plano (`Acceso por unidad`); **cero** navegación
  productiva por su rol (`OD-15`). La auto-concesión sigue denegada por el backend y el propio
  administrador sigue excluido de candidatos (GA-FE-02, sin cambio).
- Company-BU Admin descubre **solo** su superficie (`Acceso por unidad` + CORE); sin productivo
  propio y sin `users` salvo permiso real.
- La pantalla administrativa de unidades **sigue mostrando** las unidades apagadas a quien
  puede encenderlas: eso es administración, no navegación productiva (§37).

## 14 · Política móvil (390×844)

La misma semántica que desktop (una sola fuente + un solo evaluador). `view_type=mobile`
conserva su recorte de presentación (drawer = área operativa; barra inferior = Inicio / KPI /
área operativa). Con cero unidades, la entrada productiva desaparece **también** en móvil; sin
overflow, sin controles inalcanzables, sin menú duplicado. Breakpoint 390×844 certificado.

## 15 · i18n

Todas las etiquetas nuevas o conservadas: ES + EN en `public/locales/{es,en}/translation.json`.
Sin claves crudas, sin literales hardcodeados en componentes de GA-FE-03, sin etiquetas por
nombre de rol. La entrada nueva `nav.roles` («Roles»/«Roles») se añade a ambos idiomas.

## 16 · Invariantes de seguridad

```
NAV NO ES AUTORIZACIÓN · ROUTE GUARDS INDEPENDIENTES DEL MENÚ · BACKEND AUTORIDAD FINAL
COMPANY BU OFF = BLOQUEO ABSOLUTO PRODUCTIVO (global incluido)
SIN CONTEXTO ≠ UNIÓN DE INQUILINOS · SIN CONCESIÓN = CONJUNTO VACÍO
ENCENDER ≠ CONCEDE · RBAC ≠ BU · BU ≠ MÓDULO RBAC
SIN GATING POR NOMBRE DE ROL NI POR USERNAME · SIN AUTORIDAD SOLO-UI
SIN GRUPOS VACÍOS · SIN PARIDAD ROTA DESKTOP/MÓVIL · SIN CLAVES CRUDAS
SIN CERTIFICACIÓN SIN EVIDENCIA RUNTIME AUTENTICADA
```

## 17 · Criterios de aceptación

**Núcleo**: `NAV-AC01` modelo canónico único sin duplicación · `NAV-AC02` sin gating por nombre
de rol · `NAV-AC03` sin gating por username · `NAV-AC04` capacidad sin permiso no
accionable/descubrible · `NAV-AC05` grupo vacío oculto · `NAV-AC06` paridad semántica
desktop/móvil · `NAV-AC07` MenuHub obedece la misma política · `NAV-AC08` atajos accionables del
Dashboard obedecen la misma política · `NAV-AC09` guardas de ruta independientes ·
`NAV-AC10` deep link no autorizado denegado.

**BU**: `NAV-AC11` BU OFF ⇒ sin exposición productiva · `NAV-AC12` BU ON sola no expone sin
concesión/regla global · `NAV-AC13` concesión sin BU ON no expone · `NAV-AC14` RBAC solo no
expone sin elegibilidad BU · `NAV-AC15` ON + concesión + RBAC expone · `NAV-AC16` zero-BU
conserva CORE y pierde productivo · `NAV-AC17` el global respeta BU ON · `NAV-AC18` el global
usa el plano de control (selector) como gobernado.

**Contexto**: `NAV-AC19` switch de empresa recalcula · `NAV-AC20` hard refresh
reconstruye lo mismo · `NAV-AC21` grant actualiza según propagación canónica (refresh) ·
`NAV-AC22` revoke retira · `NAV-AC23` sin enlaces accionables de la empresa anterior ·
`NAV-AC24` sin enlaces accionables tras revoke/relogin.

**Admin**: `NAV-AC25` CBU Admin descubre su superficie · `NAV-AC26` Access Admin descubre la
suya · `NAV-AC27` Access Admin no gana productivo · `NAV-AC28` no autorizado no descubre
superficies GA-FE-02 · `NAV-AC29` global sin contexto descubre el selector · `NAV-AC30`
superficie de inquilino falla cerrada sin contexto.

**Calidad**: `NAV-AC31` ES completo · `NAV-AC32` EN completo · `NAV-AC33` sin claves crudas ·
`NAV-AC34` 390×844 usable · `NAV-AC35` sin overflow bloqueante · `NAV-AC36` sin entradas
duplicadas · `NAV-AC37` sin enlaces muertos introducidos · `NAV-AC38` sin errores fatales de
consola · `NAV-AC39` sin navegación falsa tras mutación fallida · `NAV-AC40` sin regresión
GA-FE-02.

**Extras de certificación**: `NAV-AC41` matriz 3D de navegación 4/4 + seguridad de ruta directa ·
`NAV-AC42` sin flash de permisos (nada accionable antes de hidratar la sesión) · `NAV-AC43` sin
tormenta de fetches ni bucles de render · `NAV-AC44` `D-2` (hub para D) cerrado como
consecuencia.

## 18 · No regresión

`GA-FE-02` completa (sesión hidratada, selector, unidades de empresa, concesiones, Access
Admin, D-1, F1–F4) debe seguir verde **antes** de desplegar. Los tests existentes (205/205)
siguen pasando sin debilitar aserciones. `BU-D10`, `R-181`, `R-182`, Wave B/C, SAP: sin
cambios.

## 19 · Certificación en runtime

Contra la generación desplegada **final**: actores A–E + Z + P autenticados; matriz 3D de
navegación; deep links representativos; refresh/relogin; desktop 1440×900 y móvil 390×844; ES/EN;
consola/red saneadas; 0 secretos capturados. Sin esta evidencia no hay certificación (no por
transitividad con GA-FE-02).

## 20 · Despliegue

Pipeline normal: commit → push a `main` → GitHub Actions → Docker Hub `:latest` → Watchtower →
bundle nuevo servido por Nginx. Sin cambios de política de despliegue, tagging, Nginx ni CI.
Sin parche manual en vivo.

## 21 · Evidencia

`audit/ga-fe-03/`: spec, clarificaciones, plan, checklist, tareas, matrices (ruta, fuentes de
navegación, contrato, actores, visibilidad), evidencia RED, reconciliaciones R-98/R-119,
evidencia runtime autenticada, red, índice de capturas, ledger de datos de prueba,
reconciliación de certificación y UAT del propietario. Addendum (no reescritura) al Master
Frontend Runtime Audit y al catálogo de capacidades.

## 22 · Cierre

`R-119` y `R-98` se cierran **individualmente** por su propia evidencia (`§94`). `GA-FE-03` =
`FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING` solo si **toda** la certificación runtime
autenticada pasa. `GA-FE-02` permanece `FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING`
hasta UAT explícita del propietario. No se inicia la tranche siguiente.
