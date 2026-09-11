# GA-BU-D10 · EVIDENCIA FRONTEND (R-188 · OD-23 B)

Fecha: 2026-09-11 · Frontend: **sin cambios (0 archivos)** · Bundle: `index-BUthrUt9.js` (sin rebuild esperado).

## 1 · Gates

| Gate | Resultado |
|---|---|
| `npx tsc -b --noEmit` | **PASS** |
| `npm run build` | **PASS** |
| `npx vitest run` | **280/280** (37 files) |
| `git diff -- frontend/` | **0 archivos** |

## 2 · Por qué el frontend no cambia

Todas las superficies relevantes ya derivan del **acceso efectivo** servido por `/me` (navegación `requiresUnits`, guards por ruta, ActionGate por permisos) y la administración muestra la concesión con `is_effective` (misma proyección que el resolutor). B se implementa íntegro en backend: al apagar, la concesión queda terminada y `/me` deja de listarla como efectiva **ni como concedida**; al re-encender, sigue sin aparecer hasta concesión nueva. No hay copy nuevo ⇒ ES/EN: **N/A**.

Superficies verificadas en runtime (UI, ver evidencia runtime):

- `/lots/54` (detalle productivo del operador): tarjeta IPE visible con acceso; ausente sin acceso (OFF y post-re-encendido hasta regrant).
- Navegación lateral: ítem `/lots` presente/ausente según acceso efectivo.
- `/admin/unit-access` (Access Administrator): superficie de control operativa; muestra el estado de la unidad; sin acceso productivo propio.
- Móvil 390×844: sin recorte/overflow, sin error crudo.
