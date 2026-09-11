# GA-UAT-08 · R-188 — ÍNDICE DE CAPTURAS

Walkthrough de referencia con actores sintéticos (`uat188op` / `uat188adm`), lote `L-R187-DET` (54), unidad **Engorde**. Sin secretos; sin solapas de depuración.

| ID | Archivo | Contenido | Evidencia de |
|---|---|---|---|
| C01 | `evidence/C01-BUON-con-acceso.png` | BU ON + concesión válida: menú productivo visible y tarjeta IPE **333.3** | UAT-01 |
| C02 | `evidence/C02-BUOFF-sin-acceso.png` | BU apagada (sin cerrar sesión): menú productivo **ausente** | UAT-02 |
| C03 | `evidence/C03-reenable-historico-sin-acceso.png` | BU **re-encendida sin regrant**: el acceso **no** vuelve | **UAT-03 (central)** |
| C04 | `evidence/C04-adm-concesion-nueva.png` | Access Admin · «Acceso por unidad» → Engorde: fila del operador en **«No concedida · Conceder»** | UAT-04 |
| C04b | `evidence/C04b-adm-concesion-hecha.png` | Tras pulsar **Conceder**: fila en **«Concedida»** | UAT-04 |
| C05 | `evidence/C05-regrant-acceso-restaurado.png` | Operador tras el regrant: menú **restaurado** + IPE 333.3 | UAT-04 |
| C06 | `evidence/C06-superficie-productiva.png` | Reporte productivo accesible de nuevo (333.3) | UAT-04 |
| C07 | `evidence/C07-movil-con-acceso.png` | Móvil 390×844 con acceso válido (legible, overflow 0) | UAT-05 |
| C08 | `evidence/C08-movil-sin-acceso.png` | Móvil en estado sin acceso (menú productivo ausente) | UAT-02/05 |
