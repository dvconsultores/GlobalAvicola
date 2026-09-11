# GA-FE-03 · ÍNDICE DE CAPTURAS — `audit/ga-fe-03/evidence/` (25)

**Generación**: `index-CElqNz3R.js` · capturadas por Playwright (contextos aislados por actor).
Sin secretos en ninguna captura (0 passwords/tokens/cookies visibles).

## Desktop 1440×900 (19)

| Archivo | Escenario | Qué muestra |
|---|---|---|
| `E1_noctx.png` | E sin contexto | Plano de control + selector; producto fail-closed |
| `E2_ctx_alloff.png` | E @c1 · 4×OFF | Producto oculto con CBU OFF |
| `E3_unit_access_broiler_on.png` | E habilita por UI | «Engorde» **Activa** en la superficie de unidades |
| `E4_sidebar_broiler_on.png` | E con BU ON | Sidebar: Gestión Avícola + Review + Reports |
| `E5_hub_poultry.png` | Hub proyectos | Solo la unidad habilitada |
| `E7_switch_c3.png` | Switch a empresa 3 | Producto oculto (c3 todo OFF) |
| `E9_broiler_off.png` | E deshabilita por UI | «Engorde» **Inactiva** |
| `A_hub_settings.png` | A · hub Configuración | Acceso por unidad + Perfil (mínimo) |
| `A_unit_access.png` | A · descubribilidad | Llega por UI sin URL manual |
| `B_hub_settings.png` | B · hub Configuración | Mínimo; sin Usuarios/Roles |
| `B_grant_C.png` | B · concesión | C «Concedida»; B ausente de candidatos |
| `C_hub_broiler.png` | C · hub proyectos | Solo «Pollo de Engorde» |
| `C_stage_broiler.png` | C · etapa permitida | Etapa de su unidad |
| `C_buoff.png` | C · BU OFF (grant viva) | Operativo oculto; sin acción posible |
| `P_denied.png` | P · RBAC negativo | Denegación (tercera dimensión) |
| `D_hub_settings.png` | D · hub Configuración | **Solo Perfil** (`D-2` cerrado) |
| `D_denied.png` | D · deep links | Denegación fail-closed |
| `Z_sidebar.png` | Z · sidebar | CORE sí; sin grupos vacíos |
| `Z_home.png` | Z · home | Sin error genérico al entrar |

## Móvil 390×844 (6)

| Archivo | Escenario | Qué muestra |
|---|---|---|
| `MOB_Cm_home.png` | Cm con concesión | Barra Operativo+Home+KPI |
| `MOB_Cm_hub.png` | Cm hub proyectos | Solo su unidad |
| `MOB_Cm_stage.png` | Cm etapa | Permitida, sin overflow |
| `MOB_Zm_home.png` | Zm cero-BU | Home+KPI; sin Operativo |
| `MOB_Bm_home.png` | Bm control | Sin ítems accionables (fail-closed) |
| `MOB_Dm_denied.png` | Dm | Admin denegado/redirigido |

```
Capturas ........... 25 (19 desktop + 6 móvil)
Con secretos ....... 0
```
