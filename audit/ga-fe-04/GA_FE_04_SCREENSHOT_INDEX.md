# GA-FE-04 · ÍNDICE DE CAPTURAS

Directorio: `audit/ga-fe-04/evidence/`

## RED pre-fix (`evidence/red/`, generación `index-CElqNz3R.js`, antes de C2)

| Archivo | Qué demuestra | Resultado medido |
|---|---|---|
| `RED_masters_farms_R_write_controls_visible.png` | R ve controles de escritura en maestros (defecto) | Nuevo=1 · Editar=7 · Eliminar=7 |
| `RED_users_R_create_visible.png` | R ve «Crear» en usuarios (defecto) | Crear=1 |

## Certificación post-fix (`evidence/runtime/`, generación `index-B66tpdeW.js`)

| Archivo | Caso | Resultado |
|---|---|---|
| `R_masters_farms_readonly.png` | R · `/masters/farms` desktop | 0/0/0 + aviso solo lectura |
| `R_users_readonly.png` | R · `/users` desktop | Crear=0 · sin editar/borrar |
| `R_deeplink_operations_new_denied.png` | R · `/operations/new` directo | «No tiene permiso» |
| `D_masters_denied.png` | D · `/masters/farms` | negativa visual |
| `P3D_case3_poultry_denied.png` | P · concesión+BU ON sin RBAC | negativa visual |
| `C3D_case4_lots_cta_allowed.png` | C · con permiso ∧ unidad | CTA + páginas permitidas |
| `C_lots_cta.png` | C · `/lots` (pre-window) | CTA=1 |
| `C_revoked_poultry_denied.png` | C · post-revoke | denegado + nav oculto |
| `A_unit_access.png` | A · unidad de negocio (update) | toggles visibles |
| `B_unit_access.png` | B · unidad de negocio (canónico 35) | toggles visibles |
| `E_users_controls_positive.png` | E · control positivo | Crear=1 (comodín) |
| `E_masters_farms.png` | E · sin empresa efectiva | listas vacías (alcance) |
| `Rm_masters_farms_readonly_390.png` | R móvil | 0/0/0 + aviso |
| `Rm_users_readonly_390.png` | R móvil | sin acciones |
| `Cm_lots_cta_390.png` | C móvil | CTA=1 |
| `R_masters_farms_readonly_EN.png` | R · inglés | «Read-only view…» |
