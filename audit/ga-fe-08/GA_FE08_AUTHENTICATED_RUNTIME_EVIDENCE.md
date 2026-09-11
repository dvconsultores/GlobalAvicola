# GA-FE-08 · EVIDENCIA RUNTIME AUTENTICADA (E2E-01…10)

Fecha: 2026-09-11 · Generación: **`index-DtzHNDMG.js`** (health 200) · Raw: `evidence/e2e-uat.json`, `evidence/probe-uat.json`, `evidence/cleanup-uat.json`.

## Resultados

| E2E | Escenario | Resultado | Datos |
|---|---|---|---|
| 01 | Autorizado desktop (A) | **PASS** | Hub «Gestión Avícola» con tarjeta **Lotes (1)**; clic → `/lots`; **82** filas; sin URL directa (C01/C02) |
| 02 | Estado activo | **PASS** | `aria-current="page"` en «Gestión Avícola» estando en `/lots` |
| 03 | Móvil (F) | **PASS** | Barra inferior → hub → tarjeta **Lotes (1)** → `/lots` (82 filas); overflow **0** (C03/C04) |
| 04 | BU OFF | **PASS** | Sidebar sin «Gestión Avícola»; `/lots` directo **sin datos (0 filas)**; **actor global tampoco** (hub 0, sidebar 0) (C05) |
| 05 | OD-23 histórico | **PASS** | Re-encendida **sin regrant**: tarjeta **ausente (0)** (C06) |
| 05b | Regrant por UI (E) | **PASS** | Fila del operador pasó a **«Concedida / Revocar»** (C06b) |
| 05c | Tras concesión nueva | **PASS** | Tarjeta **restaurada (1)**; `/lots` 82 filas (C07) |
| 06 | Sin concesión (B) | **PASS** | Raíz oculta (redirige a Home); `/lots` directo **0 filas** (sin datos; fail-closed de datos) |
| 07 | Sin RBAC de lotes (C) | **PASS** | Hub con su unidad visible pero **sin «Lotes» (0)**; `/lots` → **«No tiene permiso»** (denegación visual) (C08) |
| 08 | Zero-BU (D) | **PASS** | Sin superficies productivas; `/lots` → **«No tiene permiso»** |
| 09 | Access Admin (E) | **PASS** | Administración de accesos disponible; **sin «Lotes»** en su navegación; `/lots` → denegado (C09) |
| 10 | Tenant | **PASS** | Lista del operador = **41 lotes** de su alcance (todos broiler); deep-link `/lots/999999` → **404**; sin datos ajenos |

## Calidad transversal

- **Errores/overflow**: consola total **1** (pre-existente: `GET /dashboard/admin → 403` en el home del actor de control sin `dashboard:read` — nota N-1 ya documentada en GA-UAT-08; **ajeno a GA-FE-08**, no aparece en actores autorizados). Overflow horizontal: **0** en todas las páginas medidas.
- **ES/EN** (probe): tarjeta «Lotes» (ES) → «Lots» (EN) → «Lotes» (restauración) — clave `nav.lots` reusada, **sin claves nuevas**.
- **Etiqueta deep-link**: `/lots` y `/lots/:id` cubiertos por `isPathActive`; contenedor resaltado (`isAnyChildActive`).
- **Regresión funcional de Lotes**: lista (82 filas), detalle y acciones intactos (misma generación; sin cambios de producto fuera de la entrada de navegación).

## Semántica declarada honestamente

- **E2E-06/04 (sin unidades)**: el contrato **certificado** de la ruta `/lots` es por permiso (`lots:read`); sin unidades el backend devuelve **lista vacía** (fail-closed de datos, sin 403/404 de ruta). GA-FE-08 **no cambia** ese contrato (solo la representación en el menú): la entrada desaparece y no hay dato productivo alguno.
- **E2E-07/08/09 (sin permiso)**: denegación visual «No tiene permiso» (CapabilityRoute) + backend 403 si se llamara directo.
