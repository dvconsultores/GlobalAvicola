# GA-FE-04 · MATRIZ DE ACTORES

Mecanismos oficiales; credenciales efímeras fuera del repo; baja y roles desactivados al cierre;
rol canónico 35 intacto. Reutilización de patrones GA-FE-02/03.

| Actor | Usuario | Rol (fixture) | Autoridad | Concesiones | Uso en GA-FE-04 |
|---|---|---|---|---|---|
| `E` Global | `admin` (bootstrap) | Super Administrador (comodín) | todo | — | 3D global · BU OFF absoluto · control-plane · D-1/R-163 |
| `A` CBU Admin | `ga-fe04-a` | 36 reactivado (`business_units:read`+`update`, `dashboard:read`) | unidades de empresa | — | P13-AC17/18: opera CBU, **sin** User-BU ni productivo |
| `B` Access Admin | `ga-fe04-b` | **canónico 35** | acceso por unidad | — | P13-AC15/16/20: conceder/revocar; sin productivo; self-grant 403 |
| `C` Productivo | `ga-fe04-c` | **41** nueva (`lots:read`+`create`, `operations:read`+`create`, `dashboard:read`) | productivo con escritura | `broiler` (otorgada en runtime) | 3D caso 4 (ALLOW) · CTAs visibles · flujo grant/revoke |
| `D` Sin autoridad | `ga-fe04-d` | 40 reactivado (`dashboard:read`) | CORE | — | P13-AC19/74: controles privilegiados ocultos; API 403 |
| `Z` Cero unidades | `ga-fe04-z` | 40 | CORE | — | P13-AC14/73: sin acciones productivas; sin CTA vacío |
| `P` RBAC-negativo productivo | `ga-fe04-p` | 40 | CORE | `broiler` (otorgada) | 3D caso 3: concesión+BU ON sin RBAC → sin acciones |
| `R` Solo lectura administrativa | `ga-fe04-r` | **42** nueva (`users:read`+`masters:read`+`dashboard:read`) | lectura de administración | — | **P13 núcleo**: ve páginas de usuarios/maestros, **sin** controles de escritura; API de escritura 403 |

**Solo se crean los fixtures mínimos nuevos** (§47): rol 41 (C con escritura), rol 42 (R
lectura), y los usuarios GA-FE-04. Los roles 36/39/40 se reactivan/desactivan; 39 queda como
variante «productivo solo lectura» reutilizable si algún caso lo pide (no obligatorio).

**Verificación de /me por actor** (runtime): E `is_super_admin` · A/B/R permisos de control ·
C permisos productivos + `effective_business_units` tras grant · P efectivas con RBAC no ·
D/Z solo dashboard.
