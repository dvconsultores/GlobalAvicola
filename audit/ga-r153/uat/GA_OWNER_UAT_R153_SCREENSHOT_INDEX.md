# GA-UAT-09 · ÍNDICE DE CAPTURAS — R-153 / OD-25

Fecha: 2026-09-12 · Carpeta: `audit/ga-r153/uat/evidence/` · Escritorio 1440×900 salvo indicación.

| Ref | Archivo | Qué muestra | Estado |
|---|---|---|---|
| C01 | `C01-formulario-importacion.png` | Alta de Importación de Abuelas: lote **vacío y no obligatorio** + nota «Si no selecciona un lote, se creará automáticamente al aprobar la importación.» | ✅ |
| C02 | — | (Pre-aprobación «Se creará al aprobar») | ⛔ No disponible — bloqueada por F-01 |
| C03 | — | (Post-aprobación con lote enlazado) | ⛔ No disponible — bloqueada por F-01 |
| C04 | — | (Detalle del lote automático) | ⛔ No disponible — bloqueada por F-01 |
| C05 | — | (Sin aves antes de la recepción) | ⛔ No disponible — bloqueada por F-01 |
| C06 | — | (Población tras la recepción) | ⛔ No disponible — bloqueada por F-01 |
| C07 | — | (Vía manual de lote) | ⛔ No capturada — visual pendiente de sesión |
| C08 | `C08-movil-formulario.png` · `C08b-movil-nota-lote.png` | Móvil 390×844: alta de importación y nota del lote; sin desbordes horizontales | ✅ |
| F01 | `F01-guardado-rechazado-422.png` | **Fallo F-01**: pantalla en blanco tras guardar (el error del servidor rompe el render) | ✅ |
| — | `referencia-walkthrough.json` | Journal de la verificación: pasos, trazas de red (`POST 422`), error de render, payload exacto | ✅ |

Sin secretos en ninguna captura.
