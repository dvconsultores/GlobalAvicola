# GA-FE-08 · TRAZA DE LA SUPERFICIE DE LOTES

Fecha: 2026-09-11 · Baseline: `30fe3dc`.

## 1 · Mapa de rutas (`frontend/src/App.tsx`)

Comentario l.258: «Operations, Lots, Reports — accessible by both web and mobile». Rutas l.263-265:

```tsx
<Route path="/lots" element={<CapabilityRoute permission="lots:read"><LotListPage /></CapabilityRoute>} />
<Route path="/lots/new" element={<WebOnlyRoute><CapabilityRoute permission="lots:create"><LotFormPage /></CapabilityRoute></WebOnlyRoute>} />
<Route path="/lots/:id" element={<CapabilityRoute permission="lots:read"><LotDetailPage /></CapabilityRoute>} />
```

- Componentes: `frontend/src/pages/lots/LotListPage.tsx` · `LotDetailPage.tsx` · `LotFormPage.tsx` (imports estáticos, l.34-36; sin lazy loading).
- Guard: `CapabilityRoute` (App.tsx:88-97) — **el mismo evaluador** `canAccessCapability` que la navegación; fail-closed visual (`common.noPermission`). `/lots/new` añade `WebOnlyRoute` (l.68-72; móvil → `/`).
- Acciones intra-pantalla: CTA «Nuevo Lote» por `useCan()` (LotListPage:53); transiciones de detalle idem (GA-FE-04).

## 2 · Autoridad backend

- `backend/app/lots/router.py:30-31` — `require_permission("lots", "read"|"create"|"update")` en todos los endpoints (403 sin permiso; wildcard global).
- Row-scope por **unidades efectivas** (`service.py:59-73,108-121` → `unidades_de_alcance_productivo`): para actor de empresa = unidades habilitadas ∩ concedidas ∩ activas; para autoridad global = unidades **habilitadas** de la empresa de contexto (fail-closed sin contexto).
- Escrituras: `_exigir_unidad_operativa` → 403 si la unidad de la empresa está OFF (R-163).
- **Unidad del lote = `bird_type`** ∈ `{grandparent, breeder, broiler}` (LotListPage BIRD_TYPE_KEYS; service «unidad es el código canónico del lote…»). La incubadora no produce lotes.
- Tenant: **sí** — todo acotado por `company_id` + unidades.

## 3 · Respuestas §9

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| ¿Existe página de listado de Lotes? | **YES** | `LotListPage.tsx` (título `lots.title` = «Lotes») |
| ¿El ruteo directo funciona? | **YES** | Pre-fix autenticado: `/lots` carga (82 enlaces de fila; API 41 lotes en alcance broiler; consola 0) — `evidence/P02-direct-lots-prefix.png` |
| ¿Requiere BU existente? | **Ruta: NO** (guarda = permiso `lots:read`, contrato certificado GA-FE-03) · **Datos: SÍ** (unidades efectivas; sin unidades ⇒ lista vacía; escritura exige unidad operativa) | App.tsx:263; service.py:59-99 |
| ¿Qué unidad(es)? | Dominio del lote: `{grandparent, breeder, broiler}`; datos acotados a las unidades **efectivas** | LotListPage:9; service.py |
| ¿Qué permiso(s)? | `lots:read` (lista/detalle) · `lots:create` (alta) · `lots:update` (acciones) | router.py |
| ¿Tenant-scoped? | **YES** | service.py + security.py |
| Direct route pre-fix (autorizado) | **PASS** | `P02` + JSON `pre-fix-repro.json` |

## 4 · Reproducción pre-fix (runtime `30fe3dc`)

- **Desktop `fe08op`** (empresa 1, `effective=[broiler]`, permisos dashboard/operations/lots read): sidebar **sin** «Lotes»; hub `/menu/poultry` **sin** tarjeta «Lotes» (solo «Pollo de Engorde»); `/lots` directo **OK** (41 lotes). `P01`, `P02`.
- **Móvil `fe08mob`** (`view_type=mobile`): barra inferior «Gestión Avícola|Inicio|KPI»; hub móvil **sin** «Lotes». `P03`.
- Consola: **0** errores. ⇒ **OBS-UAT-01 STILL PRESENT: YES**.
