# FINAL FRONTEND AUDIT · ÍNDICE DE CAPTURAS

Fecha: 2026-09-11 · Runtime `index-DtzHNDMG.js` · Actores sintéticos (154-159). Sin secretos. Una captura puede evidenciar varias filas.

| ID | Archivo | Pantalla | Actor | Filas FVA soportadas |
|---|---|---|---|---|
| S01 | `S01-home-operador.png` | Home operador (contexto empresa + sidebar) | fdaop | 01, 04, 11, 31 |
| S02 | `S02-hub-poultry.png` | Hub Gestión Avícola (5 tarjetas: Lotes + 4 unidades) | fdaop | 11, 16, 29 |
| S03 | `S03-stage-broiler.png` | Etapa Pollo de Engorde | fdaop | 16 |
| S04 | `S04-stage-gp-rearing.png` | Etapa Progenitoras · Cría | fdaop | 16, 17 |
| S05 | `S05-lots-via-nav.png` | Lotes alcanzado por navegación | fdaop | 29 |
| S06 | `S06-form-agua.png` | Formulario consumo de agua (`water_liters`) | fdaop | 24 |
| S07 | `S07-form-recepcion.png` | Recepción reproductoras (cuadre B01: dead_on_arrival/received_total) | fdaop | 21 |
| S08 | `S08-form-import.png` | Importación de abuelas (plan tipado) | fdaop | 17 |
| S09 | `S09-lote-detalle.png` | Detalle de lote (IPE) | fdaop | 29, 31 |
| S10 | `S10-reportes.png` | Reportes | fdaop | 31 |
| S11 | `S11-campana-notificaciones.png` | Campana/bandeja de notificaciones | fdaop | 37 |
| S12 | `S12-centro-revision.png` | Centro de Revisión | fdarev | 26 |
| S13 | `S13-maestros-areas.png` | Maestros · Áreas | fdaadm | 06, 33, 34 |
| S14 | `S14-auditoria.png` | Auditoría | fdaadm | 36 |
| S15 | `S15-usuarios.png` | Usuarios (administración) | fdaadm | 13, 15 |
| S16 | `S16-acceso-por-unidad.png` | Acceso por unidad (control-plane) | fdaacc | 08, 09 |
| S17 | `S17-zero-bu.png` | Usuario zero-BU (sin producto; denegado ≠ vacío) | fdazbu | 12, 38 |
| S18 | `S18-movil-lotes.png` | Móvil 390×844: Lotes desde hub | fdamob | 16, 29 |
| S19 | `S19-perfil.png` | Perfil | fdaop | 02, 03 |
| S20 | `S20-sap.png` | Integración SAP (UI) | fdaadm | 32 |
| S21 | `S21-curvas-peso.png` | Curvas de peso | fdaadm | 35 |

Capturas históricas referenciadas (paquetes UAT/tranches): C01-C09 (GA-FE-08), walkthrough C01-C10 (GA-UAT-01), etc. Los JSON probatorios: `runtime-uat.json`, `probe-403-urls.json`, `probe-b01-wizard.json`, `probe-bell-pending-curves.json`, `cleanup-uat.json`.
