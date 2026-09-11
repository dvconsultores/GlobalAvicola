# GA-UAT-05 · ÍNDICE DE CAPTURAS — GA-FE-07

Referencia de ingeniería (walkthrough previo a la sesión del propietario). Ruta base: `audit/ga-uat-05/evidence/`.

| Captura | Archivo | Qué muestra | Caso guía |
|---|---|---|---|
| C01 | `C01-selector-activa.png` | Formulario «Crear lote» (operador) con el selector de Área abierto: **solo** «Nave Disponible (UAT GA-FE-07)» (la activa); sin retiradas; sin IDs | UAT-01 |
| C02 | `C02-previa-creacion.png` | Formulario completo antes de crear: área activa elegida, fecha prevista de cierre, granja y tipo | UAT-01/02 |
| C03 | `C03-creado-detalle.png` | Tras «Crear Lote» (201): pantalla del lote `UAT7-NUEVO-01` creado con el área activa | UAT-02 |
| C04 | `C04-historico-usable.png` | Lote histórico `UAT7-HIST-01` abierto con normalidad **después** de retirar su Área («Nave Histórica») | UAT-03 |
| C05 | `C05-masters-admin.png` | Administración de Áreas (cuenta de consulta): «Nave Retirada» y «Nave Histórica» siguen listadas (presencia; sin marca visual de estado) | UAT-04 |
| C06 | `C06-form-movil.png` | Móvil 390×844: formulario de creación, operador | UAT-05 |
| C07 | `C07-selector-movil.png` | Móvil: selector de Área abierto con la activa seleccionada | UAT-05 |

Datos estructurados: `evidence/reference-walkthrough.json` (opciones del selector desktop/móvil, resultado de creación, accesibilidad del histórico, visibilidad en administración, conteo de consola) y `evidence/reference-walkthrough-notes.md` (interpretación honesta de los campos).

Durante la sesión del propietario, sus propias capturas/pantallas son la evidencia primaria; estas capturas de referencia documentan el comportamiento verificado de antemano. Las capturas del propietario no se versionan (se conservan como registro de sesión si él las aporta).
