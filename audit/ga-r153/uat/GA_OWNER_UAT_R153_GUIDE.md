# GA-UAT-09 · GUÍA DEL PROPIETARIO — R-153 / OD-25 (lote de abuelas al aprobar)

Fecha: 2026-09-12 · Actualizada: 2026-09-13 · Para: Propietario · Estado: **sesión LISTA — bloqueos corregidos y verificados en el retry de referencia** (`GA_OWNER_UAT_R153_RETRY_REFERENCE.md`).

> **Actualización (2026-09-13).** El bloqueo F-01 (guardado rechazado + pantalla en blanco) y sus extensiones F-01d/F-01e quedaron **corregidos y certificados**: la verificación interna repitió este recorrido completo sobre la generación vigente (`index-DDCcWL76.js`) con **7/7 casos en verde** y **0 errores fatales** (evidencia: `audit/ga-f01/evidence/runtime-c2f/`). Esta guía se usa tal cual. El primer intento histórico (bloqueado) se conserva en `GA_OWNER_UAT_R153_OBSERVATIONS.md` (ATTEMPT 1 = iniciada-y-bloqueada-por-F-01).

## Antes de empezar

- Dirección: `https://avicola.globaldv.net`
- Cuentas de prueba (operador y aprobador de abuelas): en el archivo `~/ga_uat09_credentials.txt` de esta máquina (temporal, se destruye al cierre).
- Contexto ya preparado: empresa activa · unidad **Progenitoras** habilitada · ambos usuarios con acceso.
- Lo que valida esta sesión: la regla aprobada por usted — **el lote de abuelas nace al aprobar la importación, sin cargar aves; las aves entran con la recepción**.

## Casos (7)

| # | Caso | Qué hacer | Qué debe ver | Estado hoy |
|---|---|---|---|---|
| 1 | **Registrar sin crear lote** | Operaciones → Progenitoras – Cría → Importación. Complete el plan (país, cantidades, fechas, proveedor, transporte, orden de compra) y **deje el lote vacío**. Guardar. | Se guarda correctamente; junto al lote dice que **se creará al aprobar** | **FALLA** (F-01) |
| 2 | **Antes de aprobar** | Abra la importación guardada | «Lote: Se creará al aprobar» — no existe lote nuevo todavía | No alcanzable (depende del 1) |
| 3 | **Aprobar crea el lote** | Envíela a revisión y complete la aprobación como aprobador | Aparece «Lote: #N» con enlace al lote | No alcanzable |
| 4 | **Datos del lote** | Abra el lote enlazado | Código de abuelas, fecha = llegada del plan, sexo según lo declarado, granja de la importación | No alcanzable |
| 5 | **Sin aves al aprobar** | Observe el lote antes de recepcionar | El lote está creado pero **sin aves cargadas** | No alcanzable |
| 6 | **La recepción carga las aves** | Registre la recepción y apruébela | Desde ese momento el lote refleja la recepción (una sola vez) | No alcanzable |
| 7 | **La vía manual sigue** | Lotes → verifique que «Nuevo lote» sigue disponible | La creación manual de lotes sigue existiendo para los casos que correspondan | Parcial (visual) |

Preguntas guía (una por caso): las del guion original están incorporadas en la columna «Qué debe ver». Para cada caso responda **PASA / PASA CON OBSERVACIÓN / NO PASA** (+ comentario si aplica) en `GA_OWNER_UAT_R153_OBSERVATIONS.md` (dejar el comentario en la columna final).

## Qué NO se le pide

Ni contraseñas por escrito, ni pruebas técnicas (aprobaciones en paralelo, aislamientos, matemáticas de saldo): eso está certificado por ingeniería. Sólo el comportamiento visible.
