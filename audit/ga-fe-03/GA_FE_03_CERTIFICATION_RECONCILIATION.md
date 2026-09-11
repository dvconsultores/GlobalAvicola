# GA-FE-03 · RECONCILIACIÓN DE CERTIFICACIÓN

**Generación**: `index-CElqNz3R.js` · HEAD `5608465` · desktop 45/45 · móvil 13/13 ·
regresión+restauración 29/29 · RED→GREEN completo · sin transitividad.

## Criterios de aceptación → evidencia

| AC | Evidencia | Estado |
|---|---|---|
| NAV-AC01 modelo único | `auth/navigation.ts` único evaluador; grep: 0 listas duplicadas de rutas, 0 `filterNavItemsByPermissions` | ✅ |
| NAV-AC02/03 sin rol/usuario | grep navegación: **0** `role.name`/`roleName`/`username ===` | ✅ |
| NAV-AC04 sin permiso no accionable | D: 10/10 deep links + nav mínimo; unit tests | ✅ |
| NAV-AC05 grupos vacíos | Z: OPERATIVO/REVISIÓN/REPORTES/INTEGRACIÓN ausentes; contenedor vacío dropea | ✅ |
| NAV-AC06 paridad desktop/móvil | Misma fuente/evaluador; móvil Cm/Zm/Dm/Bm | ✅ |
| NAV-AC07 MenuHub | Hub solo hijos visibles (E5/C3/B2/D2) | ✅ |
| NAV-AC08 atajos Dashboard | `stageVisibleForSession` + tests; hub proyectos filtrado | ✅ |
| NAV-AC09/10 guardas/deep-link | `CapabilityRoute` + backend 403/404 (familia) | ✅ |
| NAV-AC11/12/13/14/15 (matriz 3D) | OFF/YES/YES HIDDEN · ON/NO/YES HIDDEN · ON/YES/NO HIDDEN · ON/YES/YES VISIBLE + rutas directas | **4/4** ✅ |
| NAV-AC16 zero-BU | Z: CORE sí, productivo no, sin error genérico | ✅ |
| NAV-AC17/18 global | E: BU OFF absoluto; selector/situarse por UI | ✅ |
| NAV-AC19/20 contexto | E7 switch immediate; E6 refresh idéntico | ✅ |
| NAV-AC21/22 grant/revoke | C2/C7 (refresh/relogin del objetivo); C1-SIN-GRANT tras revoke | ✅ |
| NAV-AC23/24 sin estancamiento | Sin entradas heredadas (E7, C8); semántica de propagación documentada | ✅ |
| NAV-AC25→28 admin | A/B descubren su superficie por UI; D sin superficies | ✅ |
| NAV-AC29/30 global no-contexto | E1: selector visible; inquilino fail-closed | ✅ |
| NAV-AC31→33 i18n | ES/EN completos; 0 claves crudas; `nav.roles` nueva | ✅ |
| NAV-AC34→36 móvil | 390×844; overflow 0; sin duplicados | ✅ |
| NAV-AC37→39 calidad | Sin enlaces muertos nuevos; consola sin fatales; sin mutación falsa | ✅ |
| NAV-AC40 regresión GA-FE-02 | 241/241 vitest (0 debilitado) + spots runtime D-1/F1–F3 + E2E F4/D1 previo vigente | ✅ |
| NAV-AC41 3D + ruta directa | Tabla §2 de la evidencia runtime | ✅ |
| NAV-AC42 sin flash | `isLoading` protege el layout hasta hidratar `/me` | ✅ |
| NAV-AC43 sin fetch storm | Red: sin bucles; 1 mutación/acción | ✅ |
| NAV-AC44 `D-2` | `D_hub_settings.png`: solo Perfil | ✅ |

## Findings

- **R-119 → `CLOSED`**: sus AC (menú estático → derivado; sin permiso oculto; móvil; grupos
  vacíos; el backend sigue denegando; módulos por unidad) tienen implementación + tests +
  evidencia runtime autenticada. Cierre individual (ver `GA_FE_03_R119_RECONCILIATION.md`).
- **R-98 → `PARTIAL`** (honesto): la parte de **acciones de navegación** (menú, hubs, atajos,
  rutas accionables) queda implementada y certificada; la parte de **acciones de escritura
  intra-pantalla** (botones de página para roles de solo lectura) excede GA-FE-03 y permanece
  como residuo transversal (`P-13`), sin reabrirse aquí. No se cierra por asociación.
- `H360-F01`: subsumido en R-98/R-119; su parte de navegación cerrada con R-119.
- `R-181`/`R-182`: UNCHANGED (`OUT_OF_SCOPE_OPEN_FINDING` si aparecen en inventario — no
  implementados).
- `BU-D10`: `PENDING_RATIFICATION` intacto; la navegación representó el acceso efectivo actual.
- `D-3` (`/audit?module=`) y `D-4` (home sin `dashboard:read`): documentados, sin cambio.

## Estado de certificación

```
GA-FE-03 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING
OWNER_UAT_READY = YES · OWNER_ACCEPTANCE = PENDING (decisión exclusiva del propietario)
GA-FE-02 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTANCE_PENDING (sin cambio)
Nueva tranche: NO INICIADA
```
