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

**Clasificación provisional** (`§94` al cierre): PENDIENTE — se decide con la certificación
runtime. Criterio previsto: `CLOSED` si AC1–AC6 pasan con evidencia autenticada; `PARTIAL` si
alguna capa móvil/plano no alcanza evidencia. Prohibido cerrar por asociación con `R-98`.
