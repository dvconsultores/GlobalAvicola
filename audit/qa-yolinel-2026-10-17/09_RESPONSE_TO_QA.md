# 09 · Respuesta a la revisión QA — Yolinel Cortez (2026-10-17)

**Para**: Yolinel Cortez — Revisión QA
**De**: Equipo de producto y desarrollo — Global Avícola
**Fecha**: 2026-10-18
**Asunto**: Respuesta a los 18 hallazgos de la revisión del 17-10-2026
**Referencia interna**: SPEC 008 · `dbd6122` (IMPL) + `9390afc` (IMPL-2) · estado `LOCALLY_CERTIFYING`

---

## Antes de empezar

Muchas gracias por la revisión. Dieciocho observaciones en una sola pasada sobre Maestros, Operativo, Revisión y
SAP es un trabajo serio, y varias encontraron cosas que no habíamos visto: los dos defectos reales (la columna
«Editar» de los maestros y la búsqueda continua del Centro de Revisión) y la posibilidad de recibir aves con una
orden de compra de otra cadena productiva. Eso último habría llegado a producción si no lo señalas.

Tres aclaraciones de método para que puedas leer esta respuesta con precisión:

1. **El PDF original de tu revisión no estaba disponible en nuestra estación de trabajo.** Trabajamos desde la
   transcripción que hizo el propietario de tus observaciones. Si alguna de nuestras interpretaciones no coincide
   con lo que escribiste, **la palabra válida es la tuya**: dínoslo y lo corregimos. Cada hallazgo queda, por
   ahora, «pendiente de contraste con el PDF».
2. **Ninguna observación se descartó.** No hay ningún «falso positivo» en esta respuesta: los 18 puntos son
   legítimos. Donde el sistema ya hacía lo correcto, lo que fallaba era la explicación, y es lo que documentamos.
3. **Todavía no lo hemos visto funcionar en el servidor de pruebas.** La base de UAT no es alcanzable desde
   nuestra estación. Todo lo que decimos aquí está respaldado por pruebas automáticas y por revisión del sistema,
   y por eso cada punto incluye **cómo verificarlo tú misma en pantalla**. La sesión de verificación en UAT es el
   último paso y está pendiente.

Estados usados: **CORREGIDO** (hay un cambio y una prueba que lo cubre) · **YA CUMPLÍA** (el sistema ya lo hacía
bien) · **ACLARADO** (lo que faltaba era la explicación) · **PENDIENTE DE DECISIÓN** (necesita una decisión del
propietario) · **BRECHA DECLARADA** (falta una capacidad del sistema; la reconocemos y no la maquillamos).

---

## QA-001 · ¿Granjas e Incubadoras están relacionadas con su Unidad de Negocio?

**Qué observaste**: preguntaste si los maestros de Granjas e Incubadoras están ligados a la unidad de negocio que
les corresponde.

**Qué encontramos**: es una pregunta muy pertinente y la respuesta es contraintuitiva: **no existe —ni debe
existir— una relación directa entre una granja y una unidad de negocio**. El motivo es operativo: una misma granja
aloja galpones de varias unidades a la vez (por ejemplo, galpones de reproductoras y galpones de engorde en el
mismo terreno). Si la granja se ligara a una sola unidad, el sistema estaría obligado a mentir en cuanto la
realidad cambie. La cadena productiva se determina en el **lote** (por el tipo de ave) y de ahí se propaga a todo
lo que ese lote produce. Las plantas de incubación, en cambio, se clasifican como una cadena propia: incubadora.

**Qué aclaramos**: quedó documentado en la guía «Lotes: origen y maestros» que entregamos con esta respuesta, con
el ejemplo de la granja con galpones de dos unidades y la forma en que el sistema deduce la cadena.

**Cómo verificarlo**:
1. En **Maestros → Granjas**, abre cualquier granja: no verás un campo «unidad de negocio», y eso es correcto.
2. En **Lotes**, mira el tipo de ave de dos lotes de la misma granja: si son de distinto tipo, pertenecen a cadenas
   distintas y ambos conviven en la misma granja.
3. En **Maestros → Plantas de Incubación** verás que se administran aparte, como cadena propia.

**Estado**: **YA CUMPLÍA** · con aclaración documentada.

---

## QA-002 · ¿Se puede eliminar un maestro en uso? Si viene de SAP no debería eliminarse

**Qué observaste**: preguntaste si un maestro puede eliminarse cuando ya existen registros que lo usan, y
señalaste que lo que viene de SAP no debería eliminarse en Global Avícola.

**Qué encontramos**: tenías razón en la preocupación y te damos una buena noticia: **el sistema nunca borra nada de
forma física**. Al «eliminar» un maestro, este se marca como inactivo y deja de ofrecerse en los selectores, pero
el histórico se conserva intacto. No hay registros huérfanos ni errores. Lo que sí estaba mal era **la
experiencia**: la pantalla decía «Eliminar», avisaba «esta acción no se puede deshacer» —lo cual es falso—, el
listado no distinguía los registros inactivos y, si la baja fallaba, no se avisaba de nada.

**Qué cambió**:
- La acción ahora se llama **Desactivar**, y en un registro inactivo aparece **Reactivar**.
- El aviso dice la verdad: «Dejará de poder seleccionarse; podrá reactivarlo después».
- El listado tiene una columna **Estado** (Activo / Inactivo) y atenúa la fila del registro inactivo.
- Si la baja falla, aparece un aviso de error visible en pantalla.

**Cómo verificarlo**:
1. **Maestros → Granjas**: desactiva una granja que no estés usando y confirma el mensaje del diálogo.
2. Vuelve a la lista: la granja aparece atenuada, con Estado «Inactivo», y su acción dice Reactivar.
3. Entra en un formulario que use granjas: la granja desactivada **no** aparece en el selector.
4. Reactívala desde la lista y comprueba que vuelve a estar disponible.

**Estado**: **CORREGIDO** (el comportamiento ya era seguro; la pantalla ahora lo explica).

---

## QA-003 · ¿Existe un campo único que identifique vacunas, medicamentos, causas de mortalidad y de descarte?

**Qué observaste**: preguntaste si hay un campo único que permita identificar sin ambigüedad vacunas,
medicamentos, causas de mortalidad y causas de descarte.

**Qué encontramos**: hoy el identificador es el **nombre**, que es obligatorio pero **no único por empresa**: se
pueden crear dos vacunas con el mismo nombre. Ninguna norma del proyecto ha exigido hasta ahora un código único.
Y había un problema real de presentación: las columnas de esos maestros mostraban datos bajo rótulos incorrectos
(exactamente el hallazgo QA-013), de modo que no se veía el laboratorio, el tipo, la vía, el principio activo ni la
descripción.

**Qué cambió**:
- Las columnas ya muestran el nombre real del dato: **Laboratorio**, **Tipo de vacuna**, **Vía de aplicación**,
  **Principio activo**, **Categoría**, **Descripción**.
- La decisión de exigir unicidad de nombre y/o un código pasa a **decisión del propietario** (OD-QA2-01). No la
  tomamos por nuestra cuenta porque cambia la forma de cargar los maestros.

**Cómo verificarlo**:
1. **Maestros → Vacunas**: verás las columnas Nombre / Laboratorio / Tipo de vacuna / Vía de aplicación.
2. **Maestros → Medicamentos**: Nombre / Laboratorio / Principio activo.
3. **Maestros → Causas de Mortalidad** y **Causas de Descarte**: Nombre / Categoría / Descripción.

**Estado**: **CORREGIDO** en la presentación · **PENDIENTE DE DECISIÓN** en la unicidad (OD-QA2-01).

---

## QA-004 · ¿Las plantas/incubadoras manejan ZONA igual que las granjas?

**Qué observaste**: preguntaste si las plantas de incubación manejan el concepto de zona de la misma forma que las
granjas.

**Qué encontramos**: las granjas tienen **zona física**; las plantas de incubación no, solo una **ubicación**
descrita como texto. Y no es un olvido: el diseño define «Área» como estructura **organizativa** (quién responde
por qué), no como zona física. Copiar el modelo de granja en la planta sin decidirlo antes crearía un campo que
nadie va a llenar con criterio.

**Qué aclaramos**: la diferencia está documentada. Si el negocio necesita clasificar las plantas por zona física,
es una decisión del propietario (OD-QA2-02) y se implementa después; hoy la planta se describe por su ubicación.

**Cómo verificarlo**:
1. **Maestros → Granjas**: el formulario de una granja tiene zona/área.
2. **Maestros → Plantas de Incubación**: el formulario tiene ubicación (texto) y no zona. Es el comportamiento
   declarado, no un defecto de la pantalla.

**Estado**: **PENDIENTE DE DECISIÓN** (OD-QA2-02) · diferencia aclarada en la documentación.

---

## QA-005 · Cómo se relacionan los maestros importados de SAP

**Qué observaste**: preguntaste cómo se relacionan con el sistema los maestros que se importan de SAP.

**Qué encontramos**: no hay importación directa. Global Avícola **lee** SAP en modo **solo lectura** y el recorrido
es por etapas: se recibe el dato crudo, se valida, se traduce al lenguaje del sistema, se guarda en un área de
preparación y solo entonces se **promueve de forma controlada** a las referencias que usan las pantallas. Se
trabajan 14 tipos de objeto. Nada se escribe en SAP y nada entra en producción sin pasar por la promoción.

**Qué aclaramos**: se entregó la guía **«SAP para QA»**, que explica el recorrido completo con un ejemplo de orden
de compra, qué se guarda y qué se queda en preparación. La conexión real con SAP está pendiente para el
20-10-2026; hasta entonces, todo lo que se ve en SAP Manager es dato de prueba cargado manualmente.

**Cómo verificarlo**:
1. **SAP**: en la lista de referencias verás las órdenes de compra y los objetos importados.
2. Observa que las pantallas operativas (por ejemplo, Recepción de Aves) solo ofrecen las órdenes ya promovidas,
   no cualquier cosa que esté en preparación.
3. Lee la guía «SAP para QA», sección «Cómo Global Avícola recibe información de SAP».

**Estado**: **ACLARADO**.

---

## QA-006 · ¿Los lotes vienen de SAP? ¿En qué casos se crean directamente?

**Qué observaste**: preguntaste si los lotes provienen de SAP y en qué casos se crean directamente en Global
Avícola.

**Qué encontramos**: **SAP nunca crea lotes**. Un lote nace de dos maneras y solo dos: por **alta manual** en el
sistema (incluida la importación de abuelas) o por **carga inicial** durante la migración de arranque. El sistema
guarda ese origen y lo distingue. Lo que sí llega de SAP son **referencias** (órdenes de compra, de traslado,
proveedores, centros), que se usan como documento de respaldo de una operación, nunca para crear el lote.

**Cómo verificarlo**:
1. **Lotes**: abre un lote y observa su origen.
2. Compara un lote creado a mano con uno que venga de una carga inicial: los dos existen, con origen distinto.
3. En **SAP**, comprueba que no hay ninguna pantalla que genere lotes.

**Estado**: **ACLARADO** (documentado en «Lotes: origen y maestros»).

---

## QA-007 · No debería poder seleccionarse una OC de Engorde dentro de Reproductoras

**Qué observaste**: en Recepción de Aves de Reproductoras se podía seleccionar una orden de compra de Engorde.
Fue la observación más importante de la revisión y tenías razón.

**Qué encontramos**: el sistema validaba que la orden fuera de la empresa y que no se recibiera más cantidad de la
declarada, pero **nunca comparaba la cadena productiva**. El selector, además, ofrecía todas las órdenes. Un lote
de reproductoras podía recibir aves respaldadas por una compra de engorde.

**Qué cambió**:
- Se creó una **regla nueva (BR-23)**: si la cadena de la orden es conocida y no coincide con la cadena del lote,
  la recepción se **rechaza** con un mensaje que nombra la cadena de la orden y el código del lote.
- Si la cadena de la orden **no se puede determinar** (sin desglose de centros o sin centro configurado), la
  recepción se **permite**: bloquearla dejaría fuera operaciones legítimas. La orden se rotula «sin cadena» para
  que se sepa que esa comprobación no aplicó.
- Si el desglose mezcla centros de cadenas distintas, la cadena no se considera determinable.
- En pantalla, el selector de órdenes de compra **solo ofrece las de la cadena del lote** (más las de cadena
  desconocida), cada una con su cadena visible, y no se deja elegir hasta que haya lote.
- La validación anterior de cantidad **no se tocó** y sigue funcionando.

**Cómo verificarlo**:
1. **Operativo → Recepción de Aves**, selecciona un lote de **reproductoras**.
2. Abre el selector de orden de compra: la orden de Engorde **no** debe aparecer; las que aparezcan deben mostrar
   su cadena o «sin cadena».
3. Intenta forzarla (por ejemplo, desde una pestaña abierta antes del cambio): el sistema responde con un error y
   la operación **no** se guarda.
4. Repite con una orden de la **misma** cadena: la recepción se registra con normalidad.

**Estado**: **CORREGIDO**.

---

## QA-008 · Al elegir una OC SAP todavía debe seleccionar granja, lote, etc.

**Qué observaste**: al seleccionar una orden de compra en Recepción de Aves de Reproductoras, el sistema todavía
te obliga a elegir granja, lote y demás datos.

**Qué encontramos**: hoy la orden de compra **sí** completa automáticamente la referencia del documento, la
cantidad declarada y el proveedor. Lo que no completa —granja, galpón, lote, transporte, fecha— es información
que **SAP no guarda de forma que podamos usar con seguridad**: para saber a qué galpón corresponde un renglón de
la orden hace falta una tabla de equivalencias (código de almacén de SAP ↔ galpón) que todavía **no está
aprobada**; lo mismo ocurre con la clasificación de centros (centro de SAP ↔ granja). Completar esos campos sin
esa tabla sería **adivinar**, y un dato adivinado en trazabilidad es peor que un campo vacío.

**Qué aclaramos**: entregamos una **matriz de autocompletado** campo por campo, indicando cuáles se completan
solos y se pueden editar, cuáles exige el usuario y cuáles quedan a la espera de la tabla de equivalencias. La
decisión de avanzar (OD-QA2-03) es del propietario.

**Cómo verificarlo**:
1. **Operativo → Recepción de Aves** de reproductoras, elige una orden de compra.
2. Verás que la referencia, la cantidad declarada y el proveedor se completan; granja, galpón, lote, transporte y
   fecha siguen siendo tuyos.
3. Revisa la matriz de autocompletado que acompaña a esta respuesta para el detalle campo por campo.

**Estado**: **PENDIENTE DE DECISIÓN** (OD-QA2-03) · comportamiento actual aclarado con matriz.

---

## QA-009 · ¿Se valida que los procesos se registren en orden?

**Qué observaste**: preguntaste si el sistema valida el orden de los procesos, y señalaste que en
Reproductoras/Cría no debería poder registrarse alimento si todavía no existe la Recepción de Aves.

**Qué encontramos**: tienes razón: **el sistema no impone el orden en el servidor**. Solo comprueba saldos, que el
lote esté activo y que la fecha sea válida. La secuencia correcta existe únicamente como guía en la pantalla, de
modo que un registro fuera de orden se acepta si los números cuadran. Es un hueco funcional real, y cerrarlo
implica una decisión de negocio: qué procesos son obligatorios, en qué orden y qué pasa con los datos históricos
cargados sin ese orden.

**Qué aclaramos**: entregamos una **matriz de predecesores** con la propuesta: para cada proceso, qué debería
existir antes y qué severidad tendría la falta (impedir el registro o solo avisar). No se implementó en esta ronda
porque cambia las reglas de operación y necesita la decisión del propietario (OD-QA2-04).

**Cómo verificarlo**:
1. En un lote sin recepción de aves, intenta registrar alimento: hoy el sistema lo acepta (el aviso es solo de la
   pantalla). Esto **no** está corregido todavía y no lo presentamos como corregido.
2. Revisa la matriz de predecesores para ver la propuesta y las opciones de severidad.

**Estado**: **PENDIENTE DE DECISIÓN** (OD-QA2-04) · hueco reconocido y documentado.

---

## QA-010 · ¿Desde qué estado pueden ocurrir rechazado, cancelado y reversado?

**Qué observaste**: preguntaste desde qué estados puede rechazarse, cancelarse o reversarse un registro.

**Qué encontramos**: la máquina de estados es más rica de lo que la pantalla deja ver y la documentamos completa,
con las guardas de cada acción. En resumen: un registro nace como borrador, pasa a registrado y de ahí a la bandeja
de revisión; el revisor puede devolverlo (para corrección), corregirlo o aprobarlo según los niveles configurados;
el rechazo ocurre sobre un registro corregido; la **cancelación** se permite en todos los estados salvo los ya
cerrados o enviados a SAP; y el **reverso** solo aplica a un registro **aprobado** y genera una contrapartida que
también debe aprobarse, quedando ambos marcados como reversados.

**Cómo verificarlo**:
1. Toma un registro **aprobado**: la acción Cancelar no debe estar disponible; sobre uno en revisión, sí.
2. Toma un registro aprobado y revierte: aparecerá la contrapartida pendiente de aprobación.
3. Consulta el documento «Máquina de estados de la operación» para el detalle estado por estado.

**Estado**: **ACLARADO** (documentado con las guardas exactas).

---

## QA-011 · ¿Cómo se configura y funciona la segregación de funciones?

**Qué observaste**: preguntaste cómo se configura y cómo funciona la segregación de funciones.

**Qué encontramos**: ya está implementada y activa, y es configurable **por paso de aprobación** y por empresa. Por
defecto impide que quien **registró** un evento lo apruebe, y también excluye a quien lo **corrigió** y a quien lo
**rechazó**. El supervisor que revisó el evento **sí** puede aprobarlo, que es el flujo normal. Lo que faltaba era
la explicación.

**Qué aclaramos**: quedó documentado, incluida una nota de advertencia: si se desactiva la segregación en un paso,
se desactivan también las exclusiones de corrector y de quien rechazó (es una lectura del comportamiento
configurado que el propietario debe confirmar como deseada).

**Cómo verificarlo**:
1. Registra una operación con un usuario y trata de aprobarla con el mismo: el sistema lo impide.
2. Registra con uno, revisa con el supervisor y aprueba con otro usuario autorizado: se permite.
3. Revisa la configuración del paso de aprobación: verás la opción de segregación por empresa.

**Estado**: **YA CUMPLÍA** · **ACLARADO** en la documentación.

---

## QA-012 · Galpones, incubadoras (equipo) y nacedoras no identifican claramente el padre

**Qué observaste**: en los listados de Galpones, Equipos de Incubadora y Nacedoras no se identifica con claridad a
qué granja o planta pertenecen.

**Qué encontramos**: el sistema sí sabe a qué padre pertenece cada hijo, pero los listados mostraban solo el
identificador interno. Exactamente lo que describiste.

**Qué cambió**:
- **Galpones**: nueva columna **Granja** con el nombre.
- **Equipos de Incubadora** y **Nacedoras**: nueva columna **Planta de incubación** con el nombre.
- El nombre del padre se muestra incluso si ese padre está **inactivo** (antes se habría quedado en blanco).

**Cómo verificarlo**:
1. **Maestros → Galpones**: columna Granja con nombres.
2. **Maestros → Equipos de Incubadora**: columna Planta de incubación.
3. **Maestros → Nacedoras**: ídem.
4. Desactiva una granja y mira sus galpones: siguen mostrando el nombre.

**Estado**: **CORREGIDO**.

---

## QA-013 · Algunos maestros muestran una columna EDITAR cuyo contenido es otro atributo

**Qué observaste**: en algunos maestros, la columna titulada «EDITAR» contenía otro atributo.

**Qué encontramos**: era un defecto real y más amplio de lo que parecía: **20 de 42 columnas** de los maestros
usaban por error las etiquetas de los botones («Editar», «Guardar») como título del dato. Por eso se veía «Editar»
encima de un RIF, una placa o una capacidad, y el dato quedaba sin nombre.

**Qué cambió**:
- Cada columna tiene ahora su propio título: RIF/ID fiscal, País, Código, Ubicación, Capacidad, Placa, Laboratorio,
  Categoría, Orden, Descripción, Código SAP, entre otros, en español e inglés.
- Añadimos una prueba automática que impide volver a usar una etiqueta de acción como título de dato: si alguien
  lo hace, la prueba falla antes de publicar.

**Cómo verificarlo**:
1. Recorre **Maestros** de arriba abajo: ninguna cabecera dice «Editar» ni «Guardar».
2. **Empresas**: Nombre / RIF-ID fiscal / País. **Transportes**: Nombre / Placa. **Equipos** y **Nacedoras**:
   Nombre / Capacidad. **Tipos de Corrección**: Nombre / Descripción.
3. Cambia el idioma a inglés: los títulos siguen siendo nombres de dato, no de acción.

**Estado**: **CORREGIDO**.

---

## QA-014 · Incluir Granja/Incubadora en Lotes, Historial, Mis Pendientes y las bandejas

**Qué observaste**: propusiste incluir Granja/Incubadora en Lotes, Historial, Mis Pendientes, Centro de Revisión y
Aprobaciones.

**Qué encontramos**: las pantallas recibían solo los identificadores internos de granja y de lote, así que no
podían mostrar nombres. El dato existía, pero no llegaba a la pantalla.

**Qué cambió**:
- **Lotes**: columnas **Granja** y **Lote** con nombres y códigos legibles.
- **Historial**: columnas **Lote**, **Granja**, **Fecha del evento**, **Registrado por** y **Fecha de registro**.
- **Mis pendientes**: cada tarjeta muestra el código de lote y la granja.
- **Centro de Revisión** y **Aprobaciones**: las mismas columnas de contexto, también en la versión móvil.
- Todo es **informativo y adicional**: no se guardó nada nuevo ni se cambió ningún dato existente.

**Qué queda pendiente**: la parte de **incubadora** (mostrar la planta) depende de la brecha que explicamos en
QA-015. Preferimos decirlo antes que enseñar una columna vacía.

**Cómo verificarlo**:
1. **Lotes**: mira la columna Granja y comprueba que coincide con la granja del lote.
2. **Historial**: verifica que «Fecha del evento» y «Fecha de registro» muestran fechas distintas cuando el
   registro se hizo en otro día.
3. **Mis pendientes**: abre una tarjeta y contrasta el código de lote con el de Lotes.
4. **Centro de Revisión** y **Aprobaciones**: mismas columnas; y en pantalla pequeña, la información aparece
   debajo del título de cada tarjeta.

**Estado**: **CORREGIDO** para granja, lote y registrador · incubadora pendiente (ver QA-015).

---

## QA-015 · Agregar filtro por Granja / Incubadora

**Qué observaste**: propusiste poder filtrar por Granja y por Incubadora.

**Qué encontramos**: dos situaciones distintas que conviene no confundir. El **filtro por granja ya existía en el
servidor** (Lotes e Historial lo aceptaban) pero **no estaba expuesto en la pantalla**: nadie podía usarlo. El
**filtro por planta de incubación no existe**: ningún listado del sistema tiene hoy ese criterio, porque las
pantallas de operaciones no guardan la planta como campo consultable.

**Qué cambió**:
- **Granja** ya se puede filtrar en **Lotes**, **Historial** y **Aprobaciones** (el Centro de Revisión ya lo tenía).
  El filtro se aplica en el servidor, no solo a la página visible, y se puede limpiar.
- El panel de filtros se corrigió de paso: abrir y cerrar, y el botón «Limpiar», funcionan con un solo clic.

**Qué queda pendiente**: el filtro por **planta de incubación** es una **brecha declarada**. Requiere añadir la
planta como criterio en los listados (cambio de modelo de datos), no es un botón olvidado. No lo simulamos con un
filtro en memoria, porque daría resultados incompletos sin avisar.

**Cómo verificarlo**:
1. **Lotes**: elige una granja en el filtro y comprueba que la lista se reduce y que, al limpiar, vuelven todos.
2. **Historial**: mismo filtro; verifica que el total cambia con el filtro aplicado.
3. **Aprobaciones**: filtra por granja y confirma que solo quedan los registros de esa granja.
4. Comprueba que **no** hay filtro por planta: es la brecha declarada de este punto.

**Estado**: **CORREGIDO** (granja) · **BRECHA DECLARADA** (planta de incubación).

---

## QA-016 · En campos sin fechas futuras permitidas el calendario aún las ofrece

**Qué observaste**: en los campos donde no se admiten fechas futuras, el calendario permite elegirlas y luego el
sistema rechaza el registro.

**Qué encontramos**: la validación del servidor ya rechazaba la fecha futura del evento (no había riesgo de datos
inválidos), pero el calendario no la bloqueaba: se podía elegir y el problema aparecía al guardar. Y había un
detalle fino: el valor por defecto se calculaba en hora universal, lo que en determinadas horas del día ofrecía el
día anterior o el siguiente.

**Qué cambió**:
- El calendario de la **fecha del evento** ya no permite elegir fechas posteriores a **hoy**.
- Lo mismo en las fechas de **salida** y **llegada** de la importación de abuelas.
- «Hoy» se calcula en la **hora local** de la planta, no en hora universal: el día que ves es el que estás viviendo.

**Qué queda pendiente**: las demás fechas (inspecciones, parámetros de incubación, fechas planificadas, cutover)
**no** se limitaron, porque algunas describen planes a futuro y bloquearlas rompería su significado. Cuáles se
limitan es decisión del propietario (OD-QA2-05).

**Cómo verificarlo**:
1. **Operativo**: abre un formulario y toca el campo **Fecha del evento**: los días posteriores a hoy no se pueden
   seleccionar.
2. Prueba pasada la medianoche o con el equipo en otra zona horaria: «hoy» debe ser el día real.
3. En la **importación de abuelas**, las fechas de salida y llegada tampoco aceptan futuro.
4. En las fechas **planificadas**, el futuro **sí** se puede elegir: es lo esperado por ahora.

**Estado**: **CORREGIDO** (fecha del evento, salida y llegada) · **PENDIENTE DE DECISIÓN** (resto de fechas,
OD-QA2-05).

---

## QA-017 · El Centro de Revisión busca constantemente

**Qué observaste**: el Centro de Revisión «busca constantemente»: se veía una ejecución continua de búsqueda.

**Qué encontramos**: era un defecto real, no una impresión. La pantalla dependía de una función que cambiaba de
identidad en cada repintado, de modo que cada repintado disparaba una nueva consulta, y esa consulta repintaba: un
círculo cerrado que se traducía en peticiones al servidor sin que el usuario hiciera nada. Además, cada una de esas
peticiones quedaba registrada en auditoría, con el ruido que eso genera.

**Qué cambió**:
- La comprobación de permisos devuelve ahora una referencia **estable**, y la pantalla depende de un **valor**
  (¿puede ver usuarios?) en lugar de una función que cambia.
- Las notificaciones y traducciones se leen por referencia, sin entrar en las condiciones de la consulta.
- La pantalla de Aprobaciones se alineó con el mismo criterio.
- Hay una prueba automática que fija el comportamiento: sin interacción, **una sola** consulta.

**Cómo verificarlo**:
1. Abre **Revisión → Centro de Revisión** y, sin tocar nada, deja la pantalla 60 segundos con la red del navegador
   a la vista: debe haber **una** petición, no una repetición continua.
2. Cambia de pestaña de estado: **una** petición por cambio.
3. Cambia de página: **una** petición por cambio.
4. Repite en **Aprobaciones**.

**Estado**: **CORREGIDO**.

---

## QA-018 · Mostrar Usuario y Fecha de creación en los listados

**Qué observaste**: propusiste mostrar el usuario y la fecha de creación en los listados de registros operativos,
de revisión y de aprobación.

**Qué encontramos**: los listados no mostraban ni quién registró el hecho ni cuándo se registró. Y había una
confusión de fondo que valía la pena resolver: **«fecha del evento» y «fecha de registro» no son lo mismo** —un
hecho puede haber ocurrido el lunes y registrarse el miércoles—, así que mostrarlas sin distinguirlas habría
empeorado la trazabilidad en lugar de mejorarla.

**Qué cambió**:
- Columnas **Registrado por** y **Fecha de registro** en **Historial**, **Mis pendientes**, **Centro de Revisión**
  y **Aprobaciones**.
- La **fecha del evento** sigue visible y **etiquetada aparte**, para que no se confundan.
- El usuario se muestra como nombre y apellidos; si la cuenta no tiene nombre declarado (cuentas técnicas), aparece
  el usuario.

**Cómo verificarlo**:
1. **Historial**: busca un registro cargado con fecha anterior a la del día en que se registró: las dos columnas
   deben mostrar fechas distintas.
2. Comprueba que «Registrado por» coincide con el usuario que hizo el registro.
3. Repite en **Centro de Revisión** y **Aprobaciones**.
4. Revisa una operación registrada por una cuenta técnica: aparece el usuario de la cuenta.

**Estado**: **CORREGIDO**.

---

## Resumen por estado

| Estado | Total | Hallazgos |
|---|---|---|
| **CORREGIDO** | **8** | QA-002, QA-007, QA-012, QA-013, QA-014 (granja/lote/registrador), QA-015 (granja), QA-017, QA-018 |
| **CORREGIDO parcial + pendiente de decisión** | **3** | QA-003 (presentación corregida), QA-016 (fecha del evento corregida), QA-015 (planta = brecha) |
| **YA CUMPLÍA** | **2** | QA-001, QA-011 |
| **ACLARADO** | **4** | QA-005, QA-006, QA-010 + las aclaraciones de QA-001/QA-004/QA-011 |
| **PENDIENTE DE DECISIÓN** | **4** | QA-003 (unicidad, OD-QA2-01), QA-004 (OD-QA2-02), QA-008 (OD-QA2-03), QA-009 (OD-QA2-04) |
| **BRECHA DECLARADA** | **1** | QA-015 — filtro por planta de incubación |

Ningún punto quedó sin respuesta y ninguno se declaró «no aplica»: de los 18, **11 tienen cambio visible en
pantalla**, **2 ya funcionaban correctamente**, **4 esperan una decisión de negocio** y **1 es una capacidad que el
sistema todavía no tiene** y que preferimos reconocer antes que disimular.

---

## Decisiones pendientes del propietario

Estos cinco puntos **no dependen de desarrollo**: dependen de una decisión de negocio. Mientras no se decidan, el
sistema se queda como está, y lo dejamos escrito para que no parezca un olvido.

| Código | Decisión | Qué pasa mientras no se decida |
|---|---|---|
| **OD-QA2-01** | ¿Se exige **nombre único por empresa** y/o un **código** en vacunas, medicamentos y causas? (QA-003) | Se mantiene la identidad por nombre; el riesgo de dos registros homónimos sigue existiendo |
| **OD-QA2-02** | ¿Las plantas de incubación manejan **zona física** como las granjas? (QA-004) | Las plantas se siguen describiendo por su ubicación (texto) |
| **OD-QA2-03** | **Autocompletado adicional** desde la orden de compra: ¿se aprueba la tabla de equivalencias almacén ↔ galpón y centro ↔ granja? (QA-008) | Granja, galpón, lote, transporte y fecha siguen siendo datos del usuario |
| **OD-QA2-04** | **Predecesores de proceso**: ¿bloqueante o solo aviso? ¿qué severidad? (QA-009) | La pantalla avisa, el servidor no impide registrar fuera de orden |
| **OD-QA2-05** | **Fechas distintas de la del evento**: ¿cuáles se limitan al presente? (QA-016) | Solo la fecha del evento (y salida/llegada de importación) rechazan el futuro |

Pendiente adicional, ya fuera de estas cinco: **filtro por planta de incubación** (QA-015), que exige añadir la
planta como criterio consultable en los listados.

---

## Próxima ronda de QA sugerida

El propietario ha marcado **Reproductoras e Incubadora** como prioridad para Líder Pollo. Sugerimos que la
próxima revisión se concentre ahí, porque es donde quedan las decisiones abiertas con mayor impacto operativo:

1. **Reproductoras — Recepción de Aves de punta a punta**: orden de compra (incluida una de otra cadena, para ver
   BR-23 en acción), granja, galpón, lote, transporte, fechas, y la posterior revisión y aprobación con
   segregación de funciones. Es el flujo donde se cruzan QA-007, QA-008, QA-011, QA-016 y QA-018.
2. **Ciclo de incubadora completo**: recepción y clasificación de huevos, carga de incubación, nacedoras, nacimiento
   y traslado. Aquí se verá con claridad la **brecha del filtro por planta** (QA-015) y la conveniencia o no de
   manejar zona física en la planta (QA-004).
3. **Orden de los procesos**: con un lote de reproductoras recién creado, intentar registrar alimento, vacunación y
   consumo de agua **antes** de la recepción de aves, para validar con nosotras la matriz de predecesores antes de
   implementarla (QA-009).
4. **Maestros de la cadena**: vacunas, medicamentos, causas de mortalidad y de descarte, para decidir la unicidad
   (QA-003) viendo los datos reales que usa la operación.
5. **SAP**: cuando la conexión real esté disponible (prevista para el 20-10-2026), revisar la promoción de
   referencias y la clasificación de centros, que es la que habilita todo el autocompletado de QA-008.

Sugerimos también, para esa ronda, contar con el **PDF de la revisión** y con el **dataset de demostración
cargado** en el entorno de pruebas: sin datos representativos, las pantallas de Lotes, Historial y las bandejas de
revisión no permiten comprobar de verdad los hallazgos de listados.

Quedamos a tu disposición para acompañar la sesión de verificación en pantalla y para corregir cualquier punto en
el que nuestra lectura de tus observaciones no coincida con lo que quisiste decir.

---

**Documentos de soporte que acompañan a esta respuesta**

| Documento | Para qué sirve |
|---|---|
| `OPERATION_STATE_MACHINE.md` | Estados y acciones (QA-010) |
| `SAP_PARA_QA.md` | Cómo llega la información de SAP (QA-005) |
| `LOT_ORIGIN_AND_MASTERS_FOR_QA.md` | Granjas, cadenas, origen de los lotes y segregación (QA-001, QA-006, QA-011) |
| `PROCESS_PREDECESSOR_MATRIX.md` | Propuesta de orden de procesos (QA-009) |
| `08_RUNTIME_VERIFICATION.md` | Checklist de verificación en pantalla para la sesión en UAT |

