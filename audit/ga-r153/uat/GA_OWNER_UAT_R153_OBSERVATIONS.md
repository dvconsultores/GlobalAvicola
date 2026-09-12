# GA-UAT-09 · REGISTRO DE OBSERVACIONES DEL PROPIETARIO — R-153 / OD-25

Fecha: 2026-09-12 · **No pre-llenar la aceptación.** El propietario completa «Resultado» y «Comentario» tras su sesión.

| UAT ID | Resultado | Observación | Severidad | Captura | ¿Hallazgo existente? | ¿Candidato nuevo? | ¿Bloquea aceptación? | Comentario del propietario |
|---|---|---|---|---|---|---|---|---|
| UAT-01 | **FAIL (verificado internamente)** | Al guardar la importación, el sistema la rechaza y la pantalla queda en blanco. La verificación interna reprodujo el fallo de forma determinista (2 veces) | **P1** | `evidence/F01-guardado-rechazado-422.png` · `evidence/referencia-walkthrough.json` | No (no estaba reportado) | **Sí — F-01** (dos causas encadenadas: el formulario envía un registro vacío de almacenamiento de huevos que el servidor exige completo; y la orden de compra elegida no llega al campo que la importación valida. El mensaje de error, además, **rompe la pantalla**) | **SÍ** | |
| UAT-02 | NO ALCANZABLE | Depende de UAT-01 | — | — | — | No | Sí (por dependencia) | |
| UAT-03 | NO ALCANZABLE | Depende de UAT-01 | — | — | — | No | Sí (por dependencia) | |
| UAT-04 | NO ALCANZABLE | Depende de UAT-01/03 | — | — | — | No | Sí (por dependencia) | |
| UAT-05 | NO ALCANZABLE | Depende de UAT-01/03 | — | — | — | No | Sí (por dependencia) | |
| UAT-06 | NO ALCANZABLE | Mismo bloqueo afecta también el alta de recepción por interfaz (misma causa) | **P1** | `referencia-walkthrough.json` | No | **Sí — F-01** | Sí (por dependencia) | |
| UAT-07 | PARCIAL | La entrada manual de lotes existe y es visible; no se completó el flujo por el bloqueo del resto | P3 | — | Parcial (FVA-17) | No | No (por sí solo) | |
| F-01 | **CANDIDATO NUEVO registrado** | Idem UAT-01/06. Clasificación propuesta: **BUG (P1)**, sin tratar como hotfix dentro de R-153 | P1 | F01 + journal | No | Sí | Sí | |
