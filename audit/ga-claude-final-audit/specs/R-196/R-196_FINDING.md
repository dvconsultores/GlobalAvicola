# R-196 · FINDING — MAESTROS ESTRUCTURALES NO CREABLES/EDITABLES POR UI Y 20/21 SOLO POR URL

| Campo | Valor |
|---|---|
| **ID canónico** | **R-196** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | El formulario genérico de maestros no captura claves padre ni resuelve numéricos vacíos: crear `farms`, `houses`, `hatcheries`, `incubators`, `hatchers` desde la UI envía `{}` ⇒ 422 y **React #31** (sin `ErrorBoundary`); además 20 de 21 maestros solo son alcanzables por URL escrita |
| **Severidad** | **P1** (§49: alta de maestros estructurales imposible por UI; `{}`⇒422 + pantalla en blanco; P-12) |
| **Clase** | `REQUEST_CONTRACT` / `MISSING_UI` / `ERROR_HANDLING` |
| **Proceso** | P-12 (gestión de datos maestros; prerequisito de todas las cadenas) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **Familia** | B-08/B-14/B-36/B-15 (informe B); C#6/#7 (informe C); F G-01 (navegación); `C-17` (cubrió solo `PUT` faltantes) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-196/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (maestros base; OD-24 en juego para empresas/granjas) |
| **UAT del propietario** | sí (flujo visible; agrupable con R-215 para errores) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `frontend/src/pages/masters/MasterListPage.tsx:40,80,87-103,193-203` — la pantalla genérica renderiza solo columnas configuradas como `<Input>` de texto y envía `formValues: Record<string,string>` tal cual; en edición rellena `item[key] ?? ''`; `company_id` solo lo inyecta el servicio cuando el esquema es opcional y llega `None` (`masters/service.py:227-235`).
- Esquemas con claves padre **requeridas**: `FarmCreate.company_id` (`masters/schemas.py:64-73`), `HouseCreate.farm_id` (`:95-103`), `HatcheryCreate.company_id` (`:124-132`), `IncubatorCreate.hatchery_id` (`:149-157`), `HatcherCreate.hatchery_id` (`:166-173`); numéricos opcionales que viajan `''` ⇒ 422 (`capacity`, `order`; `:98,108,152,169,227,525,531,538`).
- `is_active` nunca se renderiza (`:193-200`) ⇒ no hay reactivación desde la UI (B-36).
- Error de guardado: `setFormError(detail)` crudo ⇒ React #31 con `detail` lista (`:99,201-205`).
- Navegación: `App.tsx:220` redirige `/masters` → `/masters/farms`; `MasterListPage` no ofrece selector de entidad; el único ítem de menú es `masters` (`navigationConfig.ts:238-247`); grep de `/masters/` solo en `App.tsx:244` y `WeightCurvesPage.tsx:151`.

### 1.2 Evidencia runtime local (2026-09-13)

- `MAS-hatchery-create-ui` / `MAS2-hatchery-create-ui`: `POST /masters/hatcheries {}` ⇒ **422** (`company_id`, `name`) + `pageerror` React #31 (`E99-adm-exception.png`).
- `H4-masters-house-create-ui`: `POST /masters/houses {}` ⇒ 422 (`farm_id`, `name`) (`H04-masters-house-create.png`).
- Pasa 1: `fatal_react: 2`.

### 1.3 Alcance real

16 maestros planos **sí** funcionan (sus Create tienen claves opcionales inyectables); **6 superficies** fallan (farms, houses, hatcheries, incubators, hatchers, productive-phases por `order` vacío).

## 2 · Causa raíz

Formulario único genérico para 21 entidades con columnas-texto: sin campos por entidad (padres, numéricos, booleanos), sin resolución de `company_id` en servidor para los Create que lo exigen, sin reactivación, sin render seguro de errores; la navegación quedó en un único enlace a `farms`.

## 3 · Impacto

Sin maestros estructurales no hay lotes/granjas/galpones/incubadoras nuevos: bloquea la implantación real (P-12 es prerequisito). La pantalla en blanco agrava cada intento (R-215 comparte el fix de render).

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `C-17`/`FE_BE_CONTRACT_MATRIX.md:71` cerró los `PUT` faltantes, no la creación; `R-50` (company_id del cliente) es seguridad, no UX; `GA-REM-040` clasificación. |
| Informes B/C/F | B-08/B-14/B-36 + C#6/#7 + F G-01: sin hallazgo conjunto previo. |

Conclusión: **nuevo**; ID asignado **R-196**. Incluye la parte de navegación de maestros (selector de entidad), documentada en `GA_CLAUDE_NAVIGATION_ACTION_AUDIT.md`.

## 5 · Propietario sugerido

Frontend (maestros) + backend (resolución de `company_id` en Create — coordinado con R-50). Sin migración.

## 6 · Bloquea SAP y por qué

**SÍ**: los maestros son la base de toda operación y de los datos que P-08 mapeará; su gestión por UI es requisito de implantación (docs/02 §3.2).

## 7 · Interdependencias

- **R-50** (`company_id` fijable): el fix ideal resuelve `company_id` en servidor para Create (como `create_user`); R-50 es el paquete de seguridad; aquí se consume su patrón.
- **R-215** (render seguro + `ErrorBoundary`): el 422 de maestros es su caso demostrador; fixes coordinados (R-196 usa `getErrorMessage`; R-215 añade el boundary global).
- **R-212** (UI consciente del permiso): gates de maestros.
- **OD-24** (empresas/granjas SAP no editables): régimen provisional documentado; no bloquea.
