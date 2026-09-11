# GA-FE-04 · EVIDENCIA RUNTIME AUTENTICADA (post-implementación)

Generación certificada: bundle **`index-B66tpdeW.js`** (GA-FE-04 C2, `de40d36`) · Last-Modified 2026-09-11 04:31:36 GMT
Entorno: https://avicola.globaldv.net · navegador Chromium (Playwright) · desktop 1440×900 / móvil 390×844.

## 1 · Actors y autoridad

| Actor | Usuario (id) | Rol (fixture) | Permisos /me verificados |
|---|---|---|---|
| `R` | ga-fe04-r (98) | 41 «GA-FE04 TEST READ-ONLY ADMIN» | dashboard:read · masters:read · users:read |
| `C` | ga-fe04-c (101) | 43 «GA-FE04 TEST PRODUCTIVE CREATE» | dashboard:read · lots:read+create · operations:read+create |
| `A` | ga-fe04-a (99) | 44 «GA-FE04 TEST CBU ADMIN» | dashboard:read · business_units:read+update |
| `B` | ga-fe04-b (100) | **35 canónico** | business_units:read+update+create+delete |
| `D`/`Z` | ga-fe04-d/z (102/103) | 45 «GA-FE04 TEST CORE ONLY» | dashboard:read |
| `P` | ga-fe04-p (104) | 45 + concesión broiler | dashboard:read + effBU broiler |
| `E` | bootstrap global | Super Administrador | comodín |

## 2 · Matriz P13 ejecutada (evidencia dura)

| Caso | Pantalla / acción | Esperado | Medido | Captura |
|---|---|---|---|---|
| R · lectura maestros | `/masters/farms` desktop | sin Nuevo/Editar/Eliminar | **0/0/0** (pre-fix 1/7/7) + aviso solo lectura | `R_masters_farms_readonly.png` |
| R · lectura usuarios | `/users` desktop | sin Crear/editar/borrar | **Crear=0 · pencil=0 · trash=0** (pre-fix Crear=1) + aviso | `R_users_readonly.png` |
| R · deep links | `/lots/new`, `/operations/new`, `/review/1/correct` | negativa visual | **3/3** «No tiene permiso» | `R_deeplink_operations_new_denied.png` |
| D · sin autoridad | `/masters/farms`, `/users` | negativa visual | 2/2 | `D_masters_denied.png` |
| P · RBAC-negativo 3D (caso 3) | `/poultry`, `/lots`, `/operations/new` | denegado pese a concesión+BU ON | **3/3** denegadas | `P3D_case3_poultry_denied.png` |
| C · 3D (caso 4) | `/poultry`, `/operations/new`, CTA lote | permitido con permiso ∧ unidad | nav=1 · denied=0 · denied=0 · CTA=1 | `C3D_case4_lots_cta_allowed.png` |
| C · propagación revoke | tras revocar broiler | productivo oculto | `/poultry` denegado + nav=0 + effBU=[] | `C_revoked_poultry_denied.png` |
| A/B · CBU | `/admin/unit-access` | página operativa; toggles de unidad por `business_units:update` | 4 toggles por actor (ventana broiler ON); sin Conceder/Revocar sin candidatos cargados | `A_unit_access.png` `B_unit_access.png` |
| E · control | `/masters/farms`, `/users` | CTAs de alta visibles (comodín) | Nuevo=1 · Crear=1 | `E_users_controls_positive.png` |

Notas de honestidad:
- **E sin empresa efectiva en la sesión de navegador**: las listas (maestros/usuarios) llegan vacías por alcance de empresa; por eso la fila «Editar/Eliminar» de E no es observable en runtime y el control positivo de fila queda cubierto por (a) los controles unitarios verdes (`masters:*` ⇒ botones visibles) y (b) el control positivo de C (CTA) y de A/B (operación de unidades).
- **Z ≡ D**: misma autoridad efectiva (rol 45, sin CBU, sin concesiones). La corrida de D cubre el caso «cero unidades / sin autoridad»; no se repitió usuario Z para no duplicar evidencia idéntica.

## 3 · Backend sigue siendo la autoridad (AC-FE16, mitad «ocultar no es autorizar»)

Token de R sobre la generación congelada:

| Llamada | Resultado |
|---|---|
| `GET /users?limit=5` | 200 |
| `PUT /masters/farms/1` | **403** `Permiso requerido: masters:update` |
| `POST /masters/farms` | **403** `Permiso requerido: masters:create` |
| `DELETE /masters/farms/1` | **403** `Permiso requerido: masters:delete` |
| `POST /users` | **403** `Permiso requerido: users:create` |

## 4 · Móvil 390×844

| Caso | Medido | Captura |
|---|---|---|
| R `/masters/farms` (tarjetas) | Nuevo/Editar/Eliminar = 0/0/0 + aviso | `Rm_masters_farms_readonly_390.png` |
| R `/users` (tarjetas) | Crear=0 · editar usuario=0 · eliminar usuario=0 | `Rm_users_readonly_390.png` |
| C `/lots` | CTA «Nuevo lote» = 1 | `Cm_lots_cta_390.png` |

## 5 · i18n EN

| Caso | Medido | Captura |
|---|---|---|
| R `/masters/farms` EN | «Read-only view…» visible · New/Nuevo = 0 | `R_masters_farms_readonly_EN.png` |

## 6 · Consola

0 errores de consola en R (masters, users, deep links). Sin bucles de fetch (ver `GA_FE_04_NETWORK_EVIDENCE.md`).

## 7 · Limpieza post-certificación (§100)

| Acción | Resultado |
|---|---|
| Revocar concesiones (C, P) | 200 · `is_effective=false` |
| `broiler` OFF (restauración) | 200 · **4 unidades × OFF** (breeder/grandparent/hatchery/broiler) |
| Bajas de usuarios fixture (7: r,a,b,c,d,z,p) | 204 ×7 · ninguna `ga-`/`ga_` visible en `/users` |
| Roles fixture OFF (41, 42, 43, 44, 45) | 405 DELETE → `is_active=false` ×5 |
| Rol canónico 35 | **intacto y activo** (sin cambios en toda la tranche) |
| Credenciales efímeras | destruidas (`/tmp/ga4*.json` eliminados) |

Estado final de empresa: 4×OFF como estaba al inicio de GA-FE-04.
