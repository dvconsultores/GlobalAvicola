# GA-FE-04 · MATRIZ DE ACTORES

Mecanismos oficiales; credenciales efímeras fuera del repo; baja y roles desactivados al cierre;
rol canónico 35 intacto. Reutilización de patrones GA-FE-02/03.

| Actor | Usuario | Rol (fixture) | Autoridad | Concesiones | Uso en GA-FE-04 |
|---|---|---|---|---|---|
| `E` Global | `admin` (bootstrap) | Super Administrador (comodín) | todo | — | 3D global · BU OFF absoluto · control-plane · D-1/R-163 |
| `A` CBU Admin | `ga-fe04-a` (id 99) | **44** nueva (`business_units:read`+`update`, `dashboard:read`) | unidades de empresa | — | P13-AC17/18: opera CBU, **sin** User-BU ni productivo |
| `B` Access Admin | `ga-fe04-b` (id 100) | **canónico 35** | acceso por unidad | — | P13-AC15/16/20: conceder/revocar; sin productivo; self-grant 403 |
| `C` Productivo | `ga-fe04-c` (id 101) | **43** nueva (`lots:read`+`create`, `operations:read`+`create`, `dashboard:read`) | productivo con escritura | `broiler` (otorgada en runtime) | 3D caso 4 (ALLOW) · CTAs visibles · flujo grant/revoke |
| `D` Sin autoridad | `ga-fe04-d` (id 102) | **45** nueva (`dashboard:read`) | CORE | — | P13-AC19/74: controles privilegiados ocultos; API 403 |
| `Z` Cero unidades | `ga-fe04-z` (id 103) | 45 | CORE | — | P13-AC14/73: sin acciones productivas; sin CTA vacío |
| `P` RBAC-negativo productivo | `ga-fe04-p` (id 104) | 45 | CORE | `broiler` (otorgada) | 3D caso 3: concesión+BU ON sin RBAC → sin acciones |
| `R` Solo lectura administrativa | `ga-fe04-r` (id 98) | **41** nueva (`users:read`+`masters:read`+`dashboard:read`) | lectura de administración | — | **P13 núcleo**: ve páginas de usuarios/maestros, **sin** controles de escritura; API de escritura 403 |

**Solo se crean los fixtures mínimos nuevos** (§47): roles 41 (R lectura), 43 (C con escritura),
44 (A CBU admin), 45 (D/Z/P core-only), reutilizando el canónico 35 para B. Los roles 36/39/40
de GA-FE-02/03 ya no existen en el catálogo tras la limpieza de GA-UAT-01 — se sustituyen por
los nuevos anteriores. El borrador preveía «41=C / 42=R»; la asignación real de ids fue
«41=R / 42=duplicado desactivado», reconciliada aquí (42 quedó desactivado en la sesión de
provisión; 43/44/45 se asignaron a C/A/DZP).

**Verificación de /me por actor** (runtime): E `is_super_admin` · A/B/R permisos de control ·
C permisos productivos + `effective_business_units` tras grant · P efectivas con RBAC no ·
D/Z solo dashboard.
