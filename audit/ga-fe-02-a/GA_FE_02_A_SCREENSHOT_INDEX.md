# GA-FE-02-A · SCREENSHOT INDEX (§59–60) — corrida autenticada 2026-09-11 (GA-FE-02-C)

Capturas reales del runtime `https://avicola.globaldv.net` (bundle `index-B2-tZnkI.js`),
tomadas con Chromium local (Playwright 1.61) en viewports controlados:
**desktop 1440×900** y **móvil 390×844 (isMobile+hasTouch)**. Ninguna captura contiene
contraseñas ni tokens. Directorio: `audit/ga-fe-02-c/evidence/`.

| Archivo | Viewport | Paso | Qué evidencia |
|---|---|---|---|
| `E2E01_desktop_selector.png` | 1440×900 | E2E-01 (E) | Selector «Seleccionar empresa» **visible** para la autoridad global sin contexto (F4) |
| `E2E01b_dropdown_open.png` | 1440×900 | E2E-01 (E) | Dropdown «Empresa activa» con las 2 empresas |
| `E2E01_desktop_switched.png` | 1440×900 | E2E-01 (E) | Tras switch: «Avícola Global C.A.» como empresa activa en el header |
| `E2E01_desktop_hard_refresh.png` | 1440×900 | E2E-01 (E) | **Hard refresh**: sesión y contexto persisten (D1); sin forbidden |
| `E2E01b_desktop_back.png` | 1440×900 | E2E-01b | Round-trip c1 → c3 → c1 con contexto correcto |
| `E2E02_nav_discoverability.png` | 1440×900 | E2E-02 (A) | «Configuración → Acceso por unidad» alcanzable por navegación normal |
| `E2E02_four_units_all_off.png` | 1440×900 | E2E-02 (A) | Las 4 unidades (Progenitoras·Reproductoras·Incubadora·Engorde) con estado inicial «Inactiva» |
| `E2E02_enable_dialog.png` | 1440×900 | E2E-02 (A) | Diálogo «Activar unidad» (aviso: habilitar no concede a nadie) |
| `E2E02_enabled_broiler.png` | 1440×900 | E2E-02 (A) | Engorde «Activa»; las otras tres intactas |
| `E2E03_disabled.png` | 1440×900 | E2E-03 (A) | Engorde «Inactiva» tras desactivar (persistió tras refresh) |
| `E2E04_before_grant.png` | 1440×900 | E2E-04 (B) | Distinción visual: **empresa Activa** vs **C «No concedida»** |
| `E2E04_after_grant.png` | 1440×900 | E2E-04 (B) | C «Concedida» con acción «Revocar» disponible |
| `E2E05_revoked.png` | 1440×900 | E2E-05 (B) | C «No concedida» tras revocar |
| `E2E06_self_no_grant_button.png` | 1440×900 | E2E-06 (B) | Fila propia de B excluida de candidatos → sin ruta de auto-concesión |
| `E2E08_forbidden.png` | 1440×900 | E2E-08 (D) | Ruta `/admin/unit-access` protegida: alerta «No tiene permiso…», sin superficie |
| `E2E10_ui_unit_inactive_notice.png` | 1440×900 | E2E-10 (B) | Unidad inactiva: aviso «Actívela para conceder accesos» — la UI no implica acceso |
| `MOBILE_A_four_units.png` | 390×844 | §60 (A) | 4 unidades visibles en móvil, sin overflow (delta scrollWidth=0) |
| `MOBILE_A_disabled.png` | 390×844 | §60 (A) | Mutación segura en móvil: Engorde «Inactiva» |
| `MOBILE_A_enabled_again.png` | 390×844 | §60 (A) | Rehabilitación en móvil: Engorda «Activa» |
| `MOBILE_B_grant_state.png` | 390×844 | §60 (B) | Panel de concesiones en móvil: C «Concedida» + «Revocar» |
| `MOBILE_B_revoked.png` | 390×844 | §60 (B) | Revocación en móvil: C «No concedida» |

```
Capturas ............ 21
Desktop ............. 16 (1440×900)
Móvil ............... 5  (390×844)
Con secretos ........ 0
```
