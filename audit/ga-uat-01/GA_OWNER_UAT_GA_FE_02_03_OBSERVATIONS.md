# GA-UAT-01 · REGISTRO DE OBSERVACIONES DEL PROPIETARIO

**Estado**: esperando la sesión del propietario. Las columnas de resultado se completan
**solo** con lo que el propietario responda — el agente no rellena decisiones por él.

Instrucciones: para cada caso, anote resultado (PASS · PASS_WITH_OBSERVATION · FAIL), la
observación en lenguaje natural, severidad percibida, si bloquea su aceptación, y cualquier
comentario. Al final de la sesión, la decisión global (A/B/C) se registra en la última fila.

| UAT ID | Resultado del propietario | Observación | Severidad | Captura de referencia | ¿Hallazgo existente? | ¿Candidato a hallazgo nuevo? | ¿Bloquea aceptación? | Comentario del propietario |
|---|---|---|---|---|---|---|---|---|
| UAT-01 login/contexto | PENDIENTE | — | — | `UAT01_contexto_empresa.png` · `UAT01_selector_abierto.png` | R-127 (cerrado) · F4 (cerrado) | — | — | — |
| UAT-02 cuatro unidades | PENDIENTE | — | — | `UAT02_cuatro_unidades.png` | F1 (cerrado) | — | — | — |
| UAT-03 activar/desactivar | PENDIENTE | — | — | `UAT03_dialogo_activar.png` | GA-FE-02 (certificado) | — | — | — |
| UAT-04 empresa vs. usuario | PENDIENTE | — | — | `UAT04_empresa_vs_usuario.png` | OD-16.d (normativo) | — | — | — |
| UAT-05 conceder | PENDIENTE | — | — | `UAT05_tras_conceder.png` | GA-FE-02 (certificado) | — | — | — |
| UAT-06 revocar | PENDIENTE | — | — | (misma pantalla del 05) | GA-FE-02 (certificado) | — | — | — |
| UAT-07 límite Access Admin | PENDIENTE | — | — | `UAT07_menu_access_admin.png` | OD-15 §6 · NAV-AC27 | — | — | — |
| UAT-08 CBU Admin | PENDIENTE | — | — | `UAT08_menu_cbu_admin.png` | NAV-AC25 | — | — | — |
| UAT-09 nav productiva | PENDIENTE | — | — | `UAT09_nav_productivo.png` · `UAT09_hub_productivo.png` | NAV-AC15 | — | — | — |
| UAT-10 zero-BU | PENDIENTE | — | — | `UAT10_zero_bu_home.png` | NAV-AC16 · CAP-ADM-07 (referencia) | — | — | — |
| UAT-11 navegación dinámica | PENDIENTE | — | — | (dinámica: concesión/revocación) | NAV-AC21/22 | — | — | — |
| UAT-12 cambio de empresa | PENDIENTE | — | — | `UAT01_selector_abierto.png` | NAV-AC19 | — | — | — |
| UAT-13 móvil | PENDIENTE | — | — | `UAT13_*` | NAV-AC34/35 | — | — | — |
| UAT-14 ES/EN | PENDIENTE | — | — | `UAT14_nav_ES.png` · `UAT14_nav_EN.png` | NAV-AC31/32/33 | — | — | — |
| UAT-15 visual/UX | PENDIENTE | — | — | (todas) | UAT subjetivo | — | — | — |

## Decisión global del propietario

| Campo | Valor |
|---|---|
| Respuesta (A / B / C) | **A) ACEPTO GA-FE-02 Y GA-FE-03** |
| Texto libre | — (ninguna observación) |
| Fecha | 2026-09-11 |
| Efecto | GA-FE-02 = ACCEPTED · GA-FE-03 = ACCEPTED · OWNER_ACCEPTANCE = PASS |

**Regla**: este archivo no se completa hasta que el propietario responda. No se infiere
aceptación del silencio (`§37`). Las observaciones subjetivas **no** se clasifican como defecto
de producto hasta después de la sesión (`§25`) — en esta sesión no hubo observaciones.
