# GA-R153 · UAT DEL PROPIETARIO (7 casos)

Puesta en escena: empresa con **Progenitoras (grandparent) habilitada**. Actores sugeridos: su operador de progenitoras y su aprobador habituales (el sistema exige concesión de la unidad, como siempre). Los datos de este paquete fueron verificados el 2026-09-12 en el runtime real.

| # | Caso | Qué hacer | Qué debe ver |
|---|---|---|---|
| 1 | **Registrar sin lote** | Operaciones → Progenitoras – Cría → Importación: llene plan, ♂/♀, OC/proveedor/transporte y **deje el lote vacío**; Guardar | Se guarda **sin error**; junto al selector aparece: «Si no selecciona un lote, se creará automáticamente al aprobar la importación.» |
| 2 | **Antes de aprobar** | Abra el evento | «Lote: **Se creará al aprobar**»; no existe ningún lote nuevo todavía |
| 3 | **Aprobar (P-07)** | Envíe a revisión y complete el flujo de aprobación de su empresa | Al final, el detalle muestra «Lote: **#N**» y el enlace abre el lote |
| 4 | **Datos del lote** | Abra el lote enlazado | Código `L-GP-{año}-{nn}`; tipo **abuela (grandparent)**; sexo mixto si declaró ♂ y ♀; fecha de inicio = **fecha de llegada**; granja/galpón del evento. Genética/área/curva quedan vacías (no aplican al nacimiento del lote) |
| 5 | **No puebla** | (Comprobación de saldo) intente registrar una mortalidad mayor al saldo | El sistema rechaza por saldo: la importación aprobada **no** metió aves |
| 6 | **Recepción sí puebla** | Registre la recepción del lote y apruébela | Desde ahí la mortalidad/pesaje operan con normalidad (una sola vez, sin duplicar) |
| 7 | **Manual y legado** | (a) Cree un lote a mano con lote elegido en una importación nueva; (b) repita una importación **eligiendo** un lote existente | (a) sigue funcionando; (b) **no** se crea un segundo lote: la importación conserva el suyo |

Criterio de aceptación: los 7 casos sin excepciones. Si algo difiere, anótelo sobre el evento/lote afectado para diagnóstico.
