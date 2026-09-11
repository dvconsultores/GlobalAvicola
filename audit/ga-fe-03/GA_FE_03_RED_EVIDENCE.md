# GA-FE-03 · EVIDENCIA RED (pre-implementación)

**Fecha**: 2026-09-11 · **HEAD**: `5a3acc9` · **Comando**:
`npx vitest run src/auth/__tests__/gaFe03.navigation.test.ts src/pages/operations/__tests__/gaFe03.menuHub.test.tsx src/components/layout/__tests__/gaFe03.sidebar.test.tsx src/components/layout/__tests__/gaFe03.mobileNav.test.tsx src/__tests__/gaFe03.routeGuards.test.tsx`

```
Test Files  5 failed (5)
     Tests  17 failed | 2 passed (19)
```

**Suite completa** (control de colateral):
`Test Files 5 failed | 21 passed (26)` · `Tests 17 failed | 207 passed (224)` — los 5 archivos
que fallan son EXCLUSIVAMENTE los nuevos; los 21 preexistentes (205 tests) quedan verdes ⇒
**cero colateral**.

## Fallos por archivo (contra el comportamiento actual)

| Archivo | Fallos | Qué prueba el RED (síntoma real, no fabricado) |
|---|---|---|
| `gaFe03.navigation.test.ts` | 1 (import) | El evaluador canónico no existe: `auth/navigation.ts` (`canAccessCapability`, `filterNavItemsBySession`, `stageVisibleForSession`). La semántica objetivo (RBAC ∩ BU ∩ contexto) no tiene implementación |
| `gaFe03.menuHub.test.tsx` | 4 | **`D-2` real**: con D, `/menu/settings` pinta «Usuarios y Roles» y «Acceso por unidad»; con Z, `/menu/poultry` pinta las 4 unidades; con C (solo broiler), el hub pinta Progenitoras/Incubadora. El hub consume `NAV_ITEMS` crudos |
| `gaFe03.sidebar.test.tsx` | 5 | Con D se ven Auditoría/Maestros/SAP/Reportes/Revisión/Aprobaciones/Usuarios y el grupo OPERATIVO con Gestión Avícola; con Z se ve el área operativa completa; con C aparece el hub aunque después las unidades no se filtran; B (rol 35) ve «Usuarios y Roles». El filtro actual solo afecta a entradas con `permission` |
| `gaFe03.mobileNav.test.tsx` | 2 | Con Z la barra inferior sigue ofreciendo «Gestión Avícola»; con B (sin `dashboard:read`) ofrece Home/KPI — la barra hardcodea 3 ítems sin evaluación |
| `gaFe03.routeGuards.test.tsx` | 5 (+1 control verde) | `/users`, `/roles`, `/audit`, `/masters/farms`, `/sap`, `/review`, `/approvals`, `/reports`, `/lots`, `/poultry/*` renderizan la página sin guarda de permiso; `/poultry/breeder` con concesión solo de broiler no falla cerrada; E sin contexto no falla cerrada en producto |

## Controles verdes conservados (no RED)

1. `/admin/unit-access` ya deniega a D (`PermissionRoute` GA-FE-02) — **PASS** representativo de
   la frontera ya existente que GA-FE-03 generaliza.
2. `MobileNav` con C muestra Operativo (comportamiento actual correcto para ese caso) — PASS.

## Validez del RED (§50)

- Los tests ejercitan **comportamiento actual** (render real de componentes + API pública
  existente) y fallan por aserción/importación concreta, no por entorno.
- No se fabricó RED probando algo que la spec vigente no prometiera: cada caso mapea a
  `R-98`/`R-119`, `D-2`, `T-040-23`, `CAP-ADM-06` o a la política del encargo §9/§17/§50.
- Los 2 casos no-RED son controles legítimos (frontera existente / comportamiento conservado).
