# GA-FE-03 · RECONCILIACIÓN `R-119` (individual)

**Definición canónica** (`REMEDIATION_BACKLOG.md`): «el frontend no comprueba permisos en
ninguna pantalla. Cero `hasPermission`/`usePermission`; `navigationConfig.ts` estático; las
nueve entradas se dibujan para cualquiera; `docs/02 §3.1.3` pide módulos accesibles por rol. No
es agujero de seguridad — el backend deniega — sino producto que enseña puertas cerradas.
Depende de `GA-REM-040` fase 8 para el contrato de capacidades.»

**Relación con `R-98`** (`§18`): **misma familia raíz** (modelo de permisos del frontend),
**subsunción parcial** — `R-119` es la parte de **navegación/descubribilidad**; `R-98` es la de
**acciones de escritura dentro de pantalla** (más amplia que la navegación). No se cierra
ninguno por vecindad: cada uno con su AC y su evidencia.

| AC original (reconstruido de la fuente) | Implementación GA-FE-03 | Prueba | Evidencia runtime |
|---|---|---|---|
| AC1 · El menú no dibuja entradas sin permiso (`hasPermission` real) | `auth/navigation.ts` + metadatos de permiso en TODAS las entradas; Sidebar/Drawer/MobileNav/Hub | `gaFe03.navVisibility.test.ts` | matrices por actor (A–E, D, Z, P) |
| AC2 · Las entradas se derivan de un modelo declarativo (no listas estáticas por vista) | Única definición `navigationConfig.ts` con clase/permiso/BU/contexto; evaluador único | `gaFe03.navigation.test.ts` | grep cierre: 0 arrays duplicados de rutas |
| AC3 · Ocultar acción sin permiso también en móvil | Misma evaluación en `MobileDrawer`/`MobileNav` | casos `view_type=mobile` | móvil §77 |
| AC4 · Grupo de menú sin hijos visibles no se dibuja | Regla contenedor-vacío del evaluador | casos contenedor | capturas desktop/móvil |
| AC5 · El backend sigue denegando (la UI no es la frontera) | Sin cambios de backend; guardas independientes | deep links | 403/404 §79 |
| AC6 · «Módulos accesibles» también por UNIDAD (ampliación fase 9, `T-040-23`/`AC-H02/03`) | Dimensión BU completa (empresa ON ∩ concesión / regla global) | 3D de navegación | 3D 4/4 §74 |

**Precondición resuelta**: el contrato de la fase 8 (`AC-H11…H14`: `permissions`,
`company_business_units`, `granted_business_units`, `effective_business_units`,
`effective_company_id`) **existe y está desplegado** — verificado en GA-FE-02-E.

## Clasificación final (post-certificación runtime)

```
R-119 = CLOSED
```

- **AC1** ✅ menú derivado de `hasPermission` real + metadatos (todos los actores, runtime).
- **AC2** ✅ modelo declarativo único (`navigationConfig` + `auth/navigation`); 0 arrays
  duplicados.
- **AC3** ✅ móvil con la MISMA evaluación (`MobileNav`/drawer/hubs; Cm/Zm/Dm/Bm en 390×844).
- **AC4** ✅ grupos vacíos fuera (Z; secciones OPERATIVO/REVISIÓN/REPORTES/INTEGRACIÓN).
- **AC5** ✅ backend autoridad: familia D-1 re-verificada (OFF → 0/404/403) + negativas de la
  corrida (10/10 deep links D; C5; P1).
- **AC6** ✅ dimensión UNIDAD completa (`T-040-23`/`AC-H02/03`): matriz 3D 4/4 + hub por unidad
  + concesión/revocación + BU ON/OFF.

Evidencia: `GA_FE_03_AUTHENTICATED_RUNTIME_EVIDENCE.md` · RED→GREEN en
`GA_FE_03_RED_EVIDENCE.md` · reconciliación AC total en
`GA_FE_03_CERTIFICATION_RECONCILIATION.md`.
