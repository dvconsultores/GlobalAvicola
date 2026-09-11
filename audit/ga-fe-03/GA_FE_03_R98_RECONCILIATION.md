# GA-FE-03 · RECONCILIACIÓN `R-98` (individual)

**Definición canónica** (`REMEDIATION_BACKLOG.md`): «Ninguna pantalla oculta acciones de
escritura por permiso: no hay modelo de permisos en el frontend» (P2, transversal, pertenece a
`P-13`). Residuo verificado en `AC-FE16`: `/me` no exponía la lista de permisos ⇒ ninguna
pantalla podía ocultar nada. **Hoy `/me` sí expone `permissions`** (fase 8), de modo que la
precondición técnica está resuelta; lo que resta es decidir hasta dónde llega esta tranche.

**Alcance real de `R-98`**: ocultar **acciones accionables** (escritura) según permiso en
**cualquier pantalla** — p. ej. botones de crear/editar/eliminar dentro de páginas.

**Intersección con GA-FE-03**: las **acciones de navegación** (entradas de menú, hubs, atajos
accionables de dashboard) son acciones accionables y quedan gobernadas por el modelo canónico
de GA-FE-03. La **acción intra-pantalla** (p. ej., botones dentro de `UsersPage`,
`OperationForm`, `MasterListPage`) es un universo más amplio (decenas de superficies,
`R-120`/`CAP-ERR-01` ya en vuelo por otras tranches) que **excede el alcance autorizado** de
GA-FE-03 (encargo §2: no implementar flujos nuevos; §37: no crear clutter).

| AC original (reconstruido) | Cobertura GA-FE-03 | Prueba | Evidencia |
|---|---|---|---|
| AC1 · Existe un modelo de permisos utilizable por pantallas | ✅ `auth/permissions.ts` (espejo exacto de `tiene_permiso`, `R-121`) + `auth/navigation.ts` como evaluación de capacidades | `gaFe02.permissions.test.ts` + `gaFe03.navigation.test.ts` | runtime GA-FE-02/03 |
| AC2 · Ninguna pantalla oculta acciones de escritura por permiso | ⚠️ PARCIAL — las **acciones de navegación** (menú/hub/atajos) quedan ocultas por permiso; las **acciones intra-pantalla** no se abordan en esta tranche (fuera de alcance) | matriz de navegación | matrices por actor |
| AC3 · La ocultación no sustituye al backend | ✅ backend autoridad final; guardas independientes | deep links | 403/404 |

**Clasificación provisional** (`§94` al cierre): previsible **`PARTIAL`** — GA-FE-03 cierra la
parte de navegación (acciones accionables de descubribilidad) con evidencia; la parte
intra-pantalla permanece como trabajo del frente `P-13` (sin re-ID, sin cierre por asociación).

## Clasificación FINAL (post-certificación runtime, 2026-09-11)

```
R-98 = PARTIAL
```

- **Cerrado por GA-FE-03** (runtime autenticado): las **acciones de navegación** sin autoridad
  real quedan ocultas — menú, hubs, barra móvil, atajos de procesos del Dashboard y del hub;
  deep links fail-closed; backend autoridad (familia D-1 re-verificada 0/404/403). Desktop
  45/45 · móvil 13/13.
- **Residuo declarado** (sin reabrir): ocultado de acciones de **escritura intra-pantalla** en
  superficies fuera de la frontera de navegación (`P-13`/`H360-F01` residual). No se cierra
  por asociación con `R-119`.

Evidencia: `GA_FE_03_CERTIFICATION_RECONCILIATION.md` ·
`GA_FE_03_AUTHENTICATED_RUNTIME_EVIDENCE.md`.
