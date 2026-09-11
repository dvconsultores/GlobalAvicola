# GA-FE-04-A · EVIDENCIA RUNTIME — SELF-ACTION + CROSS-COMPANY (P13-AC20 / P13-AC21)

Fecha: 2026-09-11 · Generación: bundle **`index-B66tpdeW.js`** (producto `de40d36`, sin cambios de producto en esta tranche)
Entorno: https://avicola.globaldv.net · activos: Chromium/Playwright desktop 1440×900 y móvil 390×844 (isMobile).
Tranche: cierre de las dos brechas de evidencia declaradas «NO EJECUTADO» por el informe GA-FE-04. **Sin desarrollo nuevo.**

## 1 · Actores y fixtures (sintéticos, vía mecanismos oficiales)

| Alias | Usuario (id) | Rol | Empresa | Autoridad observada (`/me`) | Baja al cierre |
|---|---|---|---|---|---|
| `B` Access Admin | `ga-fe04a-b` (105) | **35 canónico** «Administrador de Accesos» | A = 1 «Avícola Global C.A.» | `business_units:read+update+create+delete` · `effBU=[]` · sin `dashboard:read` | 204 |
| `T` mismo tenant | `ga-fe04a-t` (106) | 3 «Operador de Granja» | A = 1 | usuario elegible de la empresa efectiva | 204 |
| `X` foráneo | `ga-fe04a-x` (107) | 3 «Operador de Granja» | B = 3 «Avícola Del Sur C.A.» | objetivo sintético en otra empresa | 204 |

Ventana controlada: `broiler` ON en Empresa A solo para que la superficie de candidatos cargue (restaurado a OFF; estado final 4×OFF). Roles de fixture: ninguno nuevo (se reutilizó el canónico 35). Credenciales efímeras en `/tmp`, destruidas al cierre; nunca impresas.

## 2 · P13-AC20 · SELF-GRANT

### 2.1 UI (desktop 1440×900, navegación dinámica normal)

- Login B → shell → (sidebar) **Acceso por unidad** (`/admin/unit-access`) → selector de unidad **broiler**.
- Candidatos cargados: **24** filas de la empresa A. Medición específica:
  - fila del propio actor (`ga-fe04a-b`): **0** → *self target EXCLUDED* (resultado gobernado **A**),
  - fila de `T` presente **con botón «Conceder»** (control diferencial: **1**) → la lista funciona y la exclusión es específica del actor,
  - cualquier botón sobre la fila del actor: **0**.
- Captura: `evidence/runtime/SELF_CROSS_candidates_desktop.png`.

Defensa en profundidad documentada en código (sin cambio en esta tranche): el backend **no ofrece al actor a sí mismo** (`candidatos_de_concesion`, OD-15.a) y la UI además exige `c.user_id !== sessionUser?.id` para pintar «Conceder».

### 2.2 API (sesión real de B, ruta oficial)

| Petición | Esperado | Medido |
|---|---|---|
| `POST /api/v1/users/105/business-units` `{code:'broiler'}` | DENY | **403** `administrar el acceso no autoriza a concedérselo a uno mismo` |

Capturado: actor=B · empresa=A · objetivo=self(105) · ruta/método=POST `/users/105/business-units` · status=403 · semántica=SOD. Sin token/cabeceras/cookies en evidencia.

### 2.3 Persistencia / estado (fresh state, misma sesión B)

| Verificación | Medido |
|---|---|
| `GET /users/105/business-units` | **200 `[]`** (sin concesión creada) |
| `/me` `effective_business_units` / `granted_business_units` | **`[]` / `[]`** (sin cambio) |
| `GET /business-units` (Empresa A) | broiler sigue ON (ventana), breeder/grandparent/hatchery OFF → **sin cambio por el intento** |
| RBAC | `/me` permisos idénticos antes/después |
| Candidatos post-intento | self ausente, T presente, X ausente (sin mutación) |

### 2.4 Auditoría / UX

| Verificación | Medido |
|---|---|
| Filas de auditoría de éxito por actor B (`GET /audit?user_id=105`) | **total 0** |
| Filas `permission_change` recientes con 105/107 | **0** |
| Toast de éxito («Unidad concedida») | **0** |
| Estado optimista | ninguno; tras recarga dura los candidatos siguen sin fila self (0) |
| Refresco blando/duro | correcto (misma medición) |

### 2.5 Móvil 390×844

- Camino in-app: **Menú → Configuración (`/menu/settings`) → tarjeta «Acceso por unidad»** → `/admin/unit-access` → broiler → candidatos: filas 24 · self **0** · X **0** · T con «Conceder» **1**.
- Intentos directos desde la sesión móvil real: self **403**, cross **404**.
- Sin menú de desborde con mutaciones: el único selector de objetivo es la lista de candidatos; no hay ruta alterna que reexponga self o foráneo.
- Capturas: `SELF_CROSS_candidates_mobile_via_settings_390.png`, `SELF_CROSS_candidates_mobile_390.png`.

**P13-AC20 = PASS** (frontend PASS · backend PASS · persistencia PASS · auditoría PASS · desktop PASS · móvil PASS).

## 3 · P13-AC21 · CROSS-COMPANY

### 3.1 Aislamiento de candidatos (Empresa A ve solo su inquilino)

| Verificación | Medido |
|---|---|
| Candidatos broiler (24) contienen X(107) | **NO** |
| B lee concesiones de X (`GET /users/107/business-units`) | **404** `usuario 107` (indistinguible de inexistente; sin detalles del vecino) |
| Oráculo de búsqueda | el endpoint de candidatos no admite parámetros de búsqueda/identificador (contrato ya certificado) |

### 3.2 API directa (sesión real de B)

| Petición | Esperado | Medido |
|---|---|---|
| `POST /api/v1/users/107/business-units` `{code:'broiler'}` | DENY | **404** `usuario 107` |

Capturado: empresa origen=A · objetivo=X(107, empresa 3) · ruta/método=POST `/users/107/business-units` · status=404 · semántica=no-existe-en-mi-empresa (sin fuga de inquilino).

### 3.3 Persistencia / auditoría / fuga

| Verificación | Medido |
|---|---|
| Concesiones de X (admin en empresa 3) | **200 `[]`** — 0 concesiones cross-company |
| Auditoría de éxito por B | **0 filas** |
| Fuga de información foránea | ninguna observable: X no aparece en lista de candidatos, ni en estado de sesión, ni en mensaje de error (404 genérico, sin nombre/detalle del vecino) |
| Toast de éxito / estado optimista / objetivo obsoleto tras refresh | **0 / ninguno / ninguno** |

### 3.4 Móvil 390×844

Mismos invariantes por el camino in-app (lista de candidatos): X ausente; intento directo 404. Sin selección alterna móvil que exponga al foráneo.

**P13-AC21 = PASS** (frontend candidatos PASS · backend PASS · persistencia PASS · fuga PASS · desktop PASS · móvil PASS).

## 4 · Red (sanitizada)

Flujo desktop (por orden): `200 GET /business-units` → `200 GET /business-units/broiler/grant-candidates` → `403 POST /users/105/business-units` → `404 POST /users/107/business-units` → `200 GET /users/105/business-units` → `200 GET /business-units`.
Sin duplicación de mutaciones; sin petición con éxito falso; sin persistencia. (Detalle en `GA_FE_04_NETWORK_EVIDENCE.md` §GA-FE-04-A.)

## 5 · Observación (fuera del alcance AC20/AC21, sin acción)

- `OBS-01`: con B (rol 35, sin `dashboard:read`), la entrada desnuda `/menu` redirige a `/` (comportamiento fail-closed de GA-FE-03 para hub sin clave) y el home de dashboard muestra «Permiso requerido: dashboard:read» con `Reintentar`. Es preexistente a esta tranche (producto sin cambios), ajeno a self/cross y **no** bloquea la superficie de acceso por unidad (camino in-app móvil verificado: `/menu/settings → Acceso por unidad`). Evidencia: `hub_menu_mobile_B.png`, `hub_menu_desktop_B.png`, red `403 GET /dashboard/admin`. Se registra sin acción ni cambio de producto (§18: sin implementación cosmética).

## 6 · Smoke local (sin cambios de producto)

| Gate | Esperado | Medido |
|---|---|---|
| `tsc --noEmit` | 0 | **0** |
| Build | PASS | **PASS** |
| Vitest suite | 263/263 | **263/263 (34 archivos)** |
| GA-FE-04 dirigida | 22/22 | **22/22 (8 archivos)** |

## 7 · Limpieza

| Acción | Resultado |
|---|---|
| Baja B(105) y T(106) (empresa 1) | 204 ×2 |
| Baja X(107) (empresa 3) | 204 |
| Residuos `ga-fe04a-*` en empresas 1 y 3 | **0 / 0** |
| broiler restaurado | **OFF** → estado final **4×OFF** |
| Roles fixture | ninguno creado; **rol 35 intacto y activo** |
| Credenciales | `/tmp/ga4a_creds.json` destruido |
| Usuarios humanos | sin tocar |

## 8 · Veredicto

- **P13-AC20 = PASS** · **P13-AC21 = PASS**, ejecutados contra la generación GA-FE-04 final (`index-B66tpdeW.js`), sin cambios de producto.
- Los AC originales de R-98 permanecen **PASS** (sin regresión: suite 263/263; evidencia previa íntegra).
- **R-98 = CLOSED** (reconciliación actualizada con AC20/AC21).
- **GA-FE-04 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING** — OWNER_UAT_READY: YES.
