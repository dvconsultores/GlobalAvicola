# GA-UAT-05 · GUÍA DEL PROPIETARIO — GA-FE-07 (R-185 / OD-21)

Sesión guiada de aceptación de la regla: **un Área retirada (dada de baja) deja de poder elegirse para lotes nuevos, pero los lotes que ya la usaban siguen intactos**.

No se necesitan conocimientos técnicos: todo se hace en la aplicación, como un usuario normal.

**Acceso**: se le han entregado los usuarios y contraseñas en el mensaje de la sesión (no están escritos en este documento). Hay **dos cuentas**: una de trabajo (casos 1, 2, 3 y 5) y una de consulta (caso 4).
**Punto de partida**: https://avicola.globaldv.net

> Nota de preparación (transparencia): sigue sin existir una entrada de menú para «Lotes» (limitación ya conocida, registrada en UAT-01 como mejora de navegación). Para que pueda completar el recorrido, use estos accesos directos:
> - Lista de lotes: **https://avicola.globaldv.net/lots**
> - Crear lote: **https://avicola.globaldv.net/lots/new**
> - Lote histórico de esta prueba: **https://avicola.globaldv.net/lots/51**
> - Áreas (caso 4, cuenta de consulta): **https://avicola.globaldv.net/masters/areas**

---

## Qué va a validar (5 casos breves)

| # | Caso | Pregunta de aceptación |
|---|---|---|
| 01 | Selector de Área: la activa aparece, las retiradas no | ¿Le parece correcta y clara la lista? |
| 02 | Crear un lote eligiendo un Área activa | ¿Es claro y sin fricción? |
| 03 | El lote histórico sigue funcionando tras retirar su Área | ¿Queda claro que retirar un área no rompe lo ya existente? |
| 04 | Administración: el área retirada sigue visible | ¿Le tranquiliza que sigan visibles para consulta? |
| 05 | Móvil: mismo comportamiento | ¿Se comporta igual de bien en el teléfono? |

---

## Contexto en lenguaje sencillo

Al **retirar** (dar de baja) un Área, esta deja de poder elegirse al crear o cambiar lotes. Los lotes que **ya usaban** esa área no se tocan: siguen ahí y se pueden abrir con normalidad. Es la primera regla de este tipo en la aplicación (antes, un área retirada seguía siendo elegible — ese era el problema corregido).

---

## Recorrido sugerido (paso a paso)

### UAT-01 · Selector de Área: activa sí, retirada no
1. Entre con la **cuenta de trabajo** y abra **Crear lote** (acceso directo de arriba).
2. Abra el selector **«Área»**.

**Observe**: debe aparecer **«Nave Disponible (UAT GA-FE-07)»**. **No** deben aparecer **«Nave Retirada (UAT GA-FE-07)»** ni **«Nave Histórica (UAT GA-FE-07)»** (ambas fueron retiradas). Solo nombres claros, sin números ni códigos.
**Pregunta**: ¿Le parece correcta y clara la lista?

### UAT-02 · Crear un lote con un Área activa
1. Complete el formulario: **Código** `UAT7-OP-01` (o el que prefiera), **Tipo de producción** = Engorde, **Granja**, **Fecha prevista de cierre** (una fecha futura) y **Área** = «Nave Disponible (UAT GA-FE-07)».
2. Pulse **«Crear Lote»** una sola vez.

**Observe**: mensaje de éxito y paso a la pantalla del lote creado.
**Pregunta**: ¿Crear un lote con un área activa es claro y sin fricción?

*Nota honesta*: el detalle del lote **no muestra el Área** (decisión de diseño ya aceptada en GA-FE-06). El Área se confirma en el formulario al crearlo.

### UAT-03 · El lote histórico sigue funcionando
1. Abra **https://avicola.globaldv.net/lots/51** (lote «UAT7-HIST-01»).
2. Compruebe que se ve con normalidad: este lote se creó **usando** el Área «Nave Histórica (UAT GA-FE-07)», que fue **retirada después**.
3. (Opcional) Pulse **Editar** y guarde **sin tocar el Área**: debe guardar con normalidad.

> No modifique el Área de este lote: es el ejemplar histórico de la prueba.

**Pregunta**: ¿Queda claro que retirar un área **no rompe** los lotes que ya existían?

### UAT-04 · Administración: el área retirada sigue visible
1. Cierre la sesión y entre con la **cuenta de consulta**.
2. Abra **Áreas** (acceso directo de arriba).
3. Compruebe que **«Nave Retirada (UAT GA-FE-07)»** y **«Nave Histórica (UAT GA-FE-07)»** siguen en la lista (verá la pantalla en modo consulta, sin acciones).

**Observe**: el histórico administrativo se conserva.
*Nota honesta*: la lista **no marca visualmente** cuál está retirada (limitación actual de esa pantalla; la retirada se comprueba por su efecto: no aparecen en el selector).
**Pregunta**: ¿Le tranquiliza que las áreas retiradas sigan visibles para consulta y administración?

### UAT-05 · Móvil
1. Con la **cuenta de trabajo**, abra en el teléfono (o en una ventana estrecha) **Crear lote** y abra el selector **«Área»**.

**Observe**: la misma lista que en el ordenador (solo la activa), sin desbordes, botón accesible.
**Pregunta**: ¿Se comporta igual de bien en el móvil?

---

## Decisión final (se le pedirá al terminar)

- **A) ACEPTO GA-FE-07**
- **B) ACEPTO GA-FE-07 CON OBSERVACIONES**: <texto>
- **C) RECHAZO GA-FE-07 — CORREGIR**: <texto>

Si algo no es aceptable, menciónelo en el momento: se registra como observación y **no se corrige durante la misma sesión** (para que la aceptación no se mueva bajo sus pies).
