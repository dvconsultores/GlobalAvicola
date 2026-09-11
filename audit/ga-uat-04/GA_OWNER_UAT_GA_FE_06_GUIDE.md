# GA-UAT-04 · GUÍA DEL PROPIETARIO — GA-FE-06 (R-182)

Sesión guiada de aceptación del **alta de lote con Fecha prevista de cierre y Área**.
No se necesitan conocimientos técnicos: todo se hace en la aplicación, como un usuario normal.

**Acceso**: se le han entregado usuario y contraseña en el mensaje de la sesión (no están escritos en este documento).
**Punto de partida**: https://avicola.globaldv.net — puede iniciar sesión en la ventana que ya tiene abierta.

> Nota de preparación (transparencia): la aplicación todavía **no tiene una entrada de menú para «Lotes»** (limitación detectada al preparar su sesión; quedará registrada como observación en UAT-01). Para que pueda completar el recorrido, use este acceso directo en el navegador: **https://avicola.globaldv.net/lots**

---

## Qué va a validar (12 casos breves)

| # | Caso | Pregunta de aceptación |
|---|---|---|
| 01 | Encontrar dónde se crea un lote | ¿Le resultó natural llegar? |
| 02 | Claridad del formulario | ¿Se entiende sin conocimientos técnicos? |
| 03 | Fecha prevista de cierre | ¿Queda claro qué significa? |
| 04 | Selector de Área | ¿La selección es clara y natural? |
| 05 | Crear el lote | ¿El botón y la confirmación son claros? |
| 06 | Ver lo guardado | ¿Lo que guardó es lo que ve? |
| 07 | Recargar y volver a entrar | ¿Los datos siguen ahí? |
| 08 | Campos opcionales | ¿Entiende qué puede dejarse vacío? |
| 09 | Móvil | ¿Funciona igual de bien en el teléfono? |
| 10 | Español / Inglés | ¿Los textos son claros en ambos idiomas? |
| 11 | Aviso de cierre próximo | (N/A en esta sesión — ver abajo) |
| 12 | Comprensión global del flujo | ¿Queda claro el ciclo completo? |

---

## Recorrido sugerido (paso a paso)

### UAT-01 · Encontrar la creación de lote
1. Inicie sesión.
2. Intente encontrar «Lotes» **por el menú** (sin usar el acceso directo). Anote si lo encontró.
3. Use el acceso directo indicado arriba y pulse **«Nuevo Lote»**.

**Pregunta**: ¿Encontró de manera natural dónde crear un lote?

### UAT-02 · Claridad del formulario
1. Observe el formulario completo sin rellenar nada.

**Observe**: ¿Se entiende cada campo? ¿El orden es lógico? ¿Algún texto técnico?
**Pregunta**: ¿El formulario es comprensible para alguien de negocio?

### UAT-03 · Fecha prevista de cierre
1. En «Fecha prevista de cierre» elija una fecha (por ejemplo, unos días después de hoy).

**Observe**: el texto del campo, el formato de fecha, lo fácil que resulta elegir y verificar.
**Pregunta**: ¿Queda claro qué significa «Fecha prevista de cierre»?

### UAT-04 · Selector de Área
1. Abra el selector «Área».
2. Si hay más de una opción, cambie de una a otra antes de guardar.

**Observe**: ¿ve **nombres** claros (ningún número/código técnico)? ¿La lista es corta y entendible?
**Pregunta**: ¿La selección de Área resulta clara y natural?

### UAT-05 · Crear el lote
1. Complete: **Código** (por ejemplo `UAT-LOTE-03`), **Tipo de producción** = Engorde, **Granja**, **Fecha prevista de cierre** (la del paso 3) y un **Área**.
2. Pulse **«Crear Lote»** una sola vez.

**Observe**: ¿el botón es fácil de encontrar? ¿hay mensaje de éxito? ¿pasa a la pantalla del lote creado?

### UAT-06 · Ver lo guardado
1. En la pantalla del lote, revise la tarjeta **«Información»**.
2. Compruebe que **«Fecha prevista de cierre»** muestra exactamente la fecha que eligió.

**Pregunta**: ¿Lo que acaba de guardar es exactamente lo que la aplicación le muestra?
*Nota honesta*: el Área elegida **no se muestra** en esta pantalla (decisión de diseño registrada). El Área se confirma en el formulario al crearla; su persistencia está verificada técnicamente. Si le parece que debería verse, coméntelo.

### UAT-07 · Recargar y volver a entrar
1. Recargue la página (F5): la fecha debe seguir ahí.
2. Cierre la sesión y vuelva a entrar con la misma cuenta.
3. Abra de nuevo su lote (búsquelo en la lista, está por la parte superior).

**Pregunta**: ¿Los datos son los mismos después de recargar y de volver a entrar?

### UAT-08 · Campos opcionales (regla actual)
**En lenguaje sencillo**: en esta versión, «Fecha prevista de cierre» y «Área» son **opcionales** — se puede crear un lote sin ellas; no dan error.
1. (Opcional) Pruebe a crear un lote **sin** fecha ni área para comprobarlo.
2. (Opcional) Pruebe a guardar **sin Código** para ver el mensaje de validación («Mínimo 2 caracteres»).

**Pregunta**: ¿Le queda claro qué puede dejar vacío y qué no?

### UAT-09 · Móvil
1. Repita lo esencial en el teléfono (o cambie la ventana a tamaño móvil): abra el formulario, elija fecha y área, guarde.

**Observe**: sin desbordes, el selector de área usable, el botón de guardar accesible.
**Pregunta**: ¿El formulario es usable en móvil?

### UAT-10 · Español / Inglés
1. Cambie el idioma a **EN** (botón del encabezado) y abra el formulario y un lote.
2. Vuelva a **ES**.

**Pregunta**: ¿Los textos son claros en ambos idiomas? (sin claves crudas ni mezclas)

### UAT-11 · Aviso de cierre próximo — N/A en esta sesión
El aviso automático «lote próximo a cierre» depende de un proceso interno que corre **una vez por hora** y no tiene pantalla de disparo manual. Para no fabricar avisos artificiales ni hacerle esperar, **este caso no se prueba en su sesión**: su corrección técnica ya está certificada. (Si en algún momento ve una campana con avisos, sepa que ahí aparecerían.)

### UAT-12 · Comprensión global
**Pregunta final**: ¿Queda claro el flujo completo?
### Crear lote → seleccionar Área → indicar Fecha prevista de cierre → guardar → consultar de nuevo sin perder esos datos.

---

## Decisión final (se le pedirá al terminar)

- **A) ACEPTO GA-FE-06**
- **B) ACEPTO GA-FE-06 CON OBSERVACIONES**: <texto>
- **C) RECHAZO GA-FE-06 — CORREGIR**: <texto>

Si algo no es aceptable, menciónelo en el momento: se registra como observación y **no se corrige durante la misma sesión** (para que la aceptación no se mueva bajo sus pies).
