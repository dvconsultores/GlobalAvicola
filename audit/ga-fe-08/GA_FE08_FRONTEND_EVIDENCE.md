# GA-FE-08 · EVIDENCIA FRONTEND (local)

Fecha: 2026-09-11 · Baseline: `30fe3dc` → C1 `4ba33f6` → C2 `a946cec`.

## 1 · RED → GREEN

| Paso | Comando | Resultado |
|---|---|---|
| RED pre-fix | `npx vitest run src/data/__tests__/gaFe08.lotsNav.test.ts` | **7 failed · 5 passed (12)** — detalle en `GA_FE08_RED_EVIDENCE.md` |
| GREEN dirigido | `npx vitest run gaFe08 + gaFe02.nav + gaFe03.navigation` | **34/34 (3 archivos)** |
| Vitest completo | `npx vitest run` | **292/292 (38 archivos)** — línea base 280/280 + 12 nuevas (sin saltos silenciosos) |
| TypeScript + build | `npm run build` (`tsc -b && vite build`) | **✓ built** (solo avisos pre-existentes `INEFFECTIVE_DYNAMIC_IMPORT`; 0 errores) |

## 2 · Diff de producto (C2)

```
frontend/src/data/navigationConfig.ts                  | 12 ++++++++++++
frontend/src/data/__tests__/gaFe02.nav.test.ts         |  9 ++++++++-
2 files changed, 20 insertions(+), 1 deletion(-)
```

- Backend: **0 archivos** · Migración: **0** · Permisos nuevos: **0** · Rutas nuevas: **0** · Endpoints: **0**.
- Motor de navegación: **no reescrito** (solo registro declarativo de una entrada + icono lucide `Layers`).
- Reusos probados: ruta `/lots` existente · permiso `lots:read` existente · clave `nav.lots` (ES/EN) existente · hub atenea existente.

## 3 · Cambio de expectativa heredada (único ajuste de suite existente)

`gaFe02.nav.test.ts` «el resto del menú también se evalúa»: la sesión fixture (`lots:read` + unidad efectiva) antes no veía `poultry`; ahora ve «Gestión Avícola» con la **única opción Lotes** — comportamiento objetivo de GA-FE-08. Actualización anotada; las fronteras (users/audit/sap ocultos, `settings_profile` visible, unidades ocultas) siguen verdes.

## 4 · Cobertura del test nuevo (12)

Contrato de la entrada (ruta única/permission/requiresUnits/PRODUCTIVE/sección) · posición (primera hija del hub, sin raíz nueva) · descubribilidad del autorizado · sin RBAC oculta · sin unidades oculta · BU OFF absoluta (global incluido) · OD-23 histórica≠fresca · zero-BU y Access Admin ocultos · global contexto · vistas web/móvil · estado activo (`isPathActive`/`isAnyChildActive`) · i18n por reuso.
