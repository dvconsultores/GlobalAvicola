# GA-UAT-06 · GUÍA DEL PROPIETARIO — R-184 (KPI / IPE)

Sesión guiada corta para aceptar el **indicador IPE del lote**: que se muestre, se entienda y ya no falle.

No se necesitan conocimientos técnicos: todo se hace en la aplicación, como un usuario normal.

**Acceso**: se le ha entregado usuario y contraseña en el mensaje de la sesión (no están escritos en este documento).
**Punto de partida**: https://avicola.globaldv.net

> Nota de preparación (transparencia): sigue sin existir una entrada de menú para «Lotes» (mejora de navegación ya registrada como pendiente; no forma parte de esta aceptación). Use estos accesos directos:
> - **Lote de prueba: https://avicola.globaldv.net/lots/11** (lote **L-BO-2026-05**)
> - **Reporte del lote: https://avicola.globaldv.net/reports/lot/11**

**Contexto en lenguaje sencillo**: hasta la corrección de esta semana, la tarjeta del **IPE** (Índice Productivo Europeo) **desaparecía** en todos los lotes reales: la pantalla pedía el cálculo, el servidor fallaba y la tarjeta se ocultaba. Ese problema está resuelto y verificado técnicamente; lo que usted validará hoy es la **experiencia visible**: que el indicador carga, se entiende y se mantiene.

---

## Qué va a validar (6 casos, ~5 minutos)

| # | Caso | Pregunta de aceptación |
|---|---|---|
| 01 | Abrir el lote y ver la tarjeta IPE | ¿La tarjeta carga correctamente y muestra un resultado sin errores? |
| 02 | Claridad de la presentación | ¿La información del IPE se entiende como indicador productivo del lote? |
| 03 | Recargar y volver a entrar | ¿El IPE permanece estable al recargar y volver a entrar? |
| 04 | Reporte del lote | ¿El IPE se presenta de forma consistente entre el detalle del lote y el reporte? |
| 05 | Móvil | ¿La tarjeta se ve bien en el teléfono? |
| 06 | Comprensión global | ¿Queda claro que el IPE ahora puede consultarse con normalidad? |

---

## Recorrido paso a paso

### UAT-01 · Abrir el lote y ver la tarjeta IPE
1. Inicie sesión con la cuenta entregada.
2. Abra el **lote de prueba** con el acceso directo de arriba.
3. Busque la tarjeta con el símbolo de tendencia y la etiqueta **«IPE»**.

**Debe ver**: un número grande (**556.6**), un punto verde con la palabra **«Excelente»**, y debajo: Viabilidad 100 %, FCR 24.5, Peso prom. 1500g, Edad (días) 110.
**Pregunta**: ¿La tarjeta IPE carga correctamente y muestra un resultado sin errores?

### UAT-02 · Claridad de la presentación
1. Observe la tarjeta con calma, sin prisa.

**Observe**: ¿la etiqueta «IPE» y su icono se entienden? ¿el valor se lee bien? ¿«Excelente» es claro como clasificación? ¿ve algún texto técnico raro, un error, o símbolos extraños (NaN, ∞, códigos)?
**Pregunta**: ¿La información del IPE se entiende como indicador productivo dentro del lote?
*(No necesita comprobar la fórmula ni los cálculos: eso ya está certificado por ingeniería.)*

### UAT-03 · Recargar y volver a entrar
1. Recargue la página (F5). Compruebe que el IPE sigue ahí con el mismo valor.
2. **Cierre la sesión** (menú de su usuario → Cerrar Sesión) y **vuelva a entrar**.
3. Navegue de nuevo al mismo lote (acceso directo).

**Pregunta**: ¿El IPE permanece estable al recargar y volver a entrar? (mismo valor, misma clasificación, sin errores)

### UAT-04 · Reporte del lote
1. Abra el **reporte del lote** (acceso directo de arriba).
2. Localice el mismo indicador IPE dentro del reporte.

**Observe**: ¿el reporte carga con normalidad? ¿aparece el IPE? ¿coincide con lo que vio en el detalle del lote (556.6)? ¿alguna sección rota o error?
**Pregunta**: ¿El IPE se presenta de forma consistente entre el detalle del lote y el reporte?

### UAT-05 · Móvil
1. Abra el lote de prueba en el **teléfono** (o en una ventana estrecha).

**Observe**: ¿la tarjeta IPE se ve completa? ¿el valor y «Excelente» se leen sin cortarse? ¿la página se desliza con normalidad, sin desbordes?
**Pregunta**: ¿La tarjeta se ve bien en el móvil?

### UAT-06 · Comprensión global
**Pregunta final**: ¿Queda claro que el **IPE es un indicador productivo del lote** y que ahora puede consultarlo con normalidad, sin que la pantalla falle?

---

## Decisión final (se le pedirá al terminar)

- **A) ACEPTO R-184**
- **B) ACEPTO R-184 CON OBSERVACIONES**: <texto>
- **C) RECHAZO R-184 — CORREGIR**: <texto>

Si algo no es aceptable, menciónelo en el momento: se registra como observación y **no se corrige durante la misma sesión** (para que la aceptación no se mueva bajo sus pies).
