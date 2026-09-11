# GA-FE-03 · LEDGER DE DATOS DE PRUEBA

**Mecanismos oficiales exclusivamente** (`POST /users`, `POST /roles`, `PUT /roles/{id}`,
`POST/DELETE /users/{id}/business-units`, `PATCH /business-units/{code}/enable|disable`).
Sin SQL directo, sin mutación de usuarios humanos, sin secretos en repo.

| Elemento | IDs | Creación | Restauración | Estado final |
|---|---|---|---|---|
| Usuarios desktop | `ga-fe03-a`=82 · `b`=83 · `c`=84 · `d`=85 · `z`=86 · `p`=87 | `POST /users` (roles 36/35/39/40/40/40) | `DELETE` → 204 ×6 | inactivos; login **403** |
| Usuarios móvil | `ga-fe03-cm`=88 · `zm`=89 · `bm`=90 · `dm`=91 | `POST /users` (39/40/35/40, view_type mobile) | `DELETE` → 204 ×4 | inactivos; login **403** |
| E-móvil | — | **DENEGADO por diseño**: `POST /users` rol 1 → **403** `_rol_asignable` (plantilla de sistema no asignable desde empresa, `OD-13`) | — | N/A documentado |
| Roles temporales | 39 «GA-FE03 TEST PRODUCTIVE» (lots:read+operations:read+dashboard:read) · 40 «GA-FE03 TEST CORE» (dashboard:read) | `POST /roles` → 201 ×2 | `PUT` is_active=false | inactivos |
| Rol reutilizado | 36 (GA-FE-02 CBU admin) | `PUT` is_active=true | `PUT` is_active=false | inactivo |
| Rol canónico | **35** | — | **no tocado** | activo, 4 permisos exactos |
| Concesiones | C(84)/P(87)/CM(88) → `broiler` | `POST` oficial (UI para C; API oficial para P/CM) | `DELETE` ×3 → vivas=0 | 0 concesiones vivas |
| Empresa | 4 CBU de empresa 1 | habilitación de `broiler` (UI/API; toggle ×N) | `PATCH disable` final | **4×OFF** |
| Auditoría | — | +13 `config_change` CBU +10 `permission_change` UBU | append-only | conservada |

```
Datos de negocio reales tocados .. 0 (empresa 1 de certificación)
Usuarios humanos modificados ...... 0
Eliminaciones físicas ............. 0 (baja lógica + historia conservada)
Credenciales en repo/docs ......... 0 (efímeras en /tmp 600; destruidas al cierre)
BU-D10 ............................ PENDING_RATIFICATION intacto — la navegación usó el
                                    acceso EFECTIVO vigente, sin decidir ciclo de vida
```
