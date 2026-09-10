# ADDENDUM · GA-FE-02 — ADMINISTRACIÓN MULTI-EMPRESA Y DE UNIDADES EN EL FRONTEND

**Fecha**: 2026-09-11 · **Autorización**: `OD-20` (fase 9, `AUTHORIZED`) · **Baseline**: `cb14523`
· **Implementación**: `48ffdbb` · **Despliegue**: verificado byte a byte
(`GA_FE_02_RUNTIME_EXIT_FINGERPRINT.md`).

> Addendum fechado a la auditoría del runtime (`2026-09-10`). **No** reescribe la foto original:
> la registra como histórica y declara el cambio de superficie sin elevarlo a certificación
> funcional.

## Capacidades afectadas — frontera actualizada (§147)

| Capacidad (auditoría original) | Estado auditoría (2026-09-10) | GA-FE-02 — implementación | Estado desplegado | Autenticado | UAT |
|---|---|---|---|---|---|
| Contexto de empresa visible (Super Admin / actor de empresa) | PARCIAL (indicador existente sólo desktop; nombre persistido) | **IMPLEMENTED** — sesión extendida `/me`; la empresa efectiva alimenta la tienda; resolución del nombre tras switch | **DEPLOYED** (en el bundle servido) | `BLOCKED_AUTH` | PENDING |
| Selección / cambio de empresa | PARCIAL (sólo super admin, sin refresco de datos de inquilino) | **IMPLEMENTED** — `switchCompany` + refetch `/me`; superficies GA-FE-02 refetchean y limpian selección al cambiar | **DEPLOYED** | `BLOCKED_AUTH` | PENDING |
| Administración de unidades por empresa (Company BU) | FRONTEND_MISSING (backend certificado fase 7) | **IMPLEMENTED** — `/admin/unit-access`: cuatro unidades, estado backend, habilitar/apagar con confirmación y reconciliación, cero concesiones creadas | **DEPLOYED** | `BLOCKED_AUTH` | PENDING |
| Concesiones de unidad por usuario (User BU) | FRONTEND_MISSING (fase 8) | **IMPLEMENTED** — candidatos por unidad (para el Administrador de Accesos sin `users:read`) + panel por usuario; conceder/revocar con gates por permiso; self sin concesión | **DEPLOYED** | `BLOCKED_AUTH` | PENDING |
| Descubribilidad administrativa de lo anterior | FRONTEND_MISSING (navegación estática) | **IMPLEMENTED (mínima)** — una entrada admin condicionada por `business_units:read` + ruta guardada; la navegación global sigue `GA-FE-03` | **DEPLOYED** | `BLOCKED_AUTH` | PENDING |

## Notas de frontera

- Las métricas de la matriz maestra (p. ej. «13 DEPLOYMENT_STALE», «7 FRONTEND_MISSING») **no se
  recalculan aquí**: GA-FE-02 cubre las capacidades administrativas de la fase 9; el resto del
  inventario permanece como estaba y se revisará en su tranche.
- `R-98` / `R-119` / `R-181` / `R-182` **sin cambio** (cero código en esos ámbitos; verificado por
  diff de la tranche).
- La certificación **funcional** de estas capacidades exige E2E autenticado — hoy
  `BLOCKED_AUTH` (`GA_FE_02_REQUIRED_TEST_ACCOUNTS.md`). `TECHNICALLY IMPLEMENTED` y
  `FUNCTIONALLY_CERTIFIED` no son lo mismo (regla del programa).
