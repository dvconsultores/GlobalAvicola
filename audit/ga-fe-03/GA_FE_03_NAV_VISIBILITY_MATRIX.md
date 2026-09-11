# GA-FE-03 · MATRIZ DE VISIBILIDAD DE NAVEGACIÓN

Fuente de las expectativas E2E. `VISIBLE` / `HIDDEN` / `N/A`. Escenarios (empresa 1):

```
S1  E sin contexto            S7  C: BU ON · grant SÍ · RBAC SÍ
S2  E @c1 · 4 unidades OFF    S8  C: BU OFF · grant viva · RBAC SÍ
S3  E @c1 · broiler ON        S9  D (dashboard:read)
S4  A (CBU Admin)             S10 Z (dashboard:read, cero concesiones)
S5  B (Access Admin, rol 35)  S11 P: BU ON · grant SÍ · RBAC NO (dashboard:read)
S6  C: BU ON · grant NO · RBAC SÍ
```

| Entrada de menú | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 | S10 | S11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dashboard `/` | V | V | V | V | H | V | V | V | V | V | V |
| Poultry raíz | H | H | **V** | H | H | H | **V** | H | H | H | H |
| · broiler | H | H | **V** | H | H | H | **V** | H | H | H | H |
| · grandparent | H | H | H | H | H | H | H | H | H | H | H |
| · breeder | H | H | H | H | H | H | H | H | H | H | H |
| · hatchery | H | H | H | H | H | H | H | H | H | H | H |
| Review | H | H | **V** | H | H | H | H | H | H | H | H |
| Approvals | H | H | **V** | H | H | H | H | H | H | H | H |
| Reports | H | H | **V** | H | H | H | H | H | H | H | H |
| · SAP vs App | H | H | **V** | H | H | H | H | H | H | H | H |
| SAP | V | V | V | H | H | H | H | H | H | H | H |
| Auditoría | V | V | V | H | H | H | H | H | H | H | H |
| Maestros | V | V | V | H | H | H | H | H | H | H | H |
| Usuarios | V | V | V | H | H | H | H | H | H | H | H |
| Roles | V | V | V | H | H | H | H | H | H | H | H |
| Acceso por unidad | V | V | V | **V** | **V** | H | H | H | H | H | H |
| Mi Perfil | V | V | V | V | V | V | V | V | V | V | V |
| Grupo «Configuración» | V | V | V | V | V | V | V | V | V | V | V |
| Grupo «Operativo» | H | H | **V** | H | H | H | **V** | H | H | H | H |
| Grupo «Revisión» | H | H | **V** | H | H | H | H | H | H | H | H |
| Grupo «Reportes» | H | H | **V** | H | H | H | H | H | H | H | H |
| Grupo «Integración» | V | V | V | H | H | H | H | H | H | H | H |
| Selector de empresa (Header) | **V** | V | V | H | H | H | H | H | H | H | H |
| Barra inferior móvil: Home/KPI | V | V | V | V | H | V | V | V | V | V | V |
| Barra inferior móvil: Operativo | H | H | **V** | H | H | H | **V** | H | H | H | H |

**Notas de cálculo** (política §9 de la SPEC):

- S2/S3: B está en «Usuario y Roles»? No — B (rol 35) **no** tiene `users:read` (OD-15 §6):
  Usuarios/Roles/Auditoría/Maestros/SAP ocultos para él en todos los escenarios (columnas S5
  ya lo reflejan; no se repiten).
- S5 B: Dashboard oculto (sin `dashboard:read`) — comportamiento D-4 documentado (la home
  muestra el fail-closed existente; **no** se cambia en esta tranche).
- S7: C ve Únicamente `broiler` en Operativo; las otras tres unidades no (sin concesión).
- S3: E ve `broiler` (único habilitado) + review/approvals/reports (anyBU ≥1) + control total.
- S1: E sin contexto ve control plane + selector; **cero** inquilino (falla cerrada `OD-14.d`).
- S8: con BU OFF la concesión viva NO muestra nada (apagar prevalece `OD-16.e`; `BU-D10`
  `PENDING_RATIFICATION` intacto — la fila se conserva, la navegación no la expone).
- S11: P tiene BU ON + concesión pero **sin permiso productivo**: todo productivo oculto
  (tercera dimensión RBAC).
- S10: Z no ve productivo, no ve grupos vacíos, ve CORE y perfil; **ningún** error genérico.

**Reconciliación con el encargo (§74)**: la matriz 3D de navegación se ejecuta como
`S2→HIDDEN` · `S6→HIDDEN` · `S11→HIDDEN` · `S7→VISIBLE`, más seguridad de ruta directa por
backend (los cuatro casos con la misma autoridad, no con la UI).
