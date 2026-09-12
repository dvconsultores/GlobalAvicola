# GA-UAT-09 · GUÍA DEL PROPIETARIO — R-153 / OD-25 (lote de abuelas al aprobar)

Fecha: 2026-09-12 · Para: Propietario · Estado: **sesión recomendada: POSPUESTA hasta corregir el hallazgo F-01**.

> **Aviso de preparación.** La verificación interna previa (los mismos pasos que usted hará) encontró un **bloqueo**: al guardar la importación, el sistema la rechaza y la pantalla queda **en blanco** (hallazgo F-01, detalle en `GA_OWNER_UAT_R153_OBSERVATIONS.md`). Por eso los casos 2 a 7 **no pueden completarse todavía**. Cuando el bloqueo se corrija, esta guía se usa tal cual.

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
