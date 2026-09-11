# GA-UAT-02 · GUÍA DEL PROPIETARIO — GA-FE-04 (R-98 / P-13 · «quien solo lee no ve botones de escritura»)

**Cómo usar esta guía**: es una sesión guiada y corta (6 casos). Usted solo interactúa con la
aplicación como lo haría una persona real: **sin URLs escritas a mano, sin consola, sin
conocimientos técnicos**. Cada caso termina en una sola pregunta con tres respuestas posibles:
**PASS** · **PASS CON OBSERVACIÓN** · **FALLA** (puede añadir comentario en lenguaje natural).

**Preparado ya por el equipo** (usted no hace nada de esto): cuenta de solo lectura, permisos,
datos y capturas de referencia.

- **Credenciales** (archivo local de este equipo, fuera del repositorio; se destruye al
  terminar): `~/ga_uat_02_credentials.txt`
  - Cuenta de **solo lectura**: para los casos 1, 2, 3, 5 y 6.
  - Cuenta **autorizada** (caso 4): use **su cuenta habitual de Super Administrador**.
- **Empresa de pruebas**: «Avícola Global C.A.» (si aparece otra empresa u otra pantalla, arriba
  a la derecha puede cambiarla o volver al inicio).
- **Qué cambió en esta entrega, en una frase**: antes, un usuario que solo podía **leer**
  igual veía botones de escritura (Nuevo, Editar, Eliminar, Crear…) que al pulsarlos fallaban;
  ahora **la interfaz solo muestra lo que su permiso permite de verdad**, y el servidor sigue
  rechazando lo que no está permitido (eso no cambió).

---

## CASO 01 · Un usuario de solo lectura en Maestros — *Solo lectura*
- **Dónde**: entre con la cuenta de solo lectura → menú lateral → **Administración → Maestros →
  Granjas** (se llega por el menú; nada de URLs).
- **Haga**: mire la pantalla con calma. Verá el listado de granjas y, debajo del título, una
  nota en gris.
- **Observe**: ¿Aparece **algún** botón de **Nuevo**, **Editar** o **Eliminar**? ¿La lista se
  ve normal y completa? ¿La nota «Vista de solo lectura…» explica la situación?
- **Pregunta**: *¿Un usuario que solo puede leer ve la información pero SIN botones de
  escritura, de forma clara?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 02 · El mismo usuario en Usuarios — *Solo lectura*
- **Dónde**: mismo menú → **Configuración → Usuarios** (o Administración → Usuarios).
- **Haga**: observe la lista de personas.
- **Observe**: ¿Hay botón **Crear**? ¿Hay lápiz de editar o papelera en las filas? ¿El estado
  de cada persona se muestra como información (sin parecer un botón que cambia cosas)?
- **Pregunta**: *En una pantalla de administración, ¿el usuario de solo lectura queda
  efectivamente en modo consulta?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 03 · El menú del usuario de solo lectura — *Solo lectura*
- **Dónde**: recorra el menú lateral y, si está en escritorio, también la página **Configuración**
  dentro del menú.
- **Haga**: mire qué áreas ve: ¿aparecen Gestión Avícola (lotes, operaciones), Revisión,
  Aprobaciones o «Acceso por unidad»?
- **Observe**: ¿El menú muestra solo lo que esta persona necesita (Maestros y Usuarios en
  consulta)? ¿No hay enlaces que lleven a pantallas donde no puede hacer nada?
- **Pregunta**: *¿El menú acompañó al permiso, sin ofrecer áreas fuera de su alcance?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 04 · Un usuario autorizado (control) — *Super Administrador*
- **Dónde**: cierre sesión, entre con **su cuenta habitual**. Arriba a la derecha, elija la
  empresa **«Avícola Global C.A.»**. Vaya a **Maestros → Granjas**.
- **Haga**: compare con el caso 01.
- **Observe**: ¿Aquí SÍ aparecen **Nuevo**, **Editar** y **Eliminar**? ¿No aparece la nota de
  solo lectura? ¿La diferencia entre ambos perfiles es evidente?
- **Pregunta (crítica)**: *¿Se ocultó lo que sobra, sin esconder de más lo que sí corresponde?*
  (se espera **SÍ**)
- **Resultado**: [ ] SÍ (PASS)  [ ] SÍ CON OBSERVACIÓN  [ ] NO — Comentario: ______

## CASO 05 · En el teléfono (390×844) — *Solo lectura*
- **Haga**: abra la aplicación en un teléfono (o estreche la ventana del navegador al ancho de
  un teléfono) y entre con la cuenta de solo lectura → **Maestros → Granjas**.
- **Observe**: ¿La lista se lee bien en tarjetas? ¿Sigue sin haber botones de escritura? ¿Se
  ve la nota de solo lectura? ¿Nada se desborda ni queda cortado?
- **Pregunta**: *La misma garantía se mantiene en el teléfono. ¿Se siente usable y seguro?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 06 · Español / Inglés — *Solo lectura*
- **Haga**: cambie el idioma arriba (ES → EN) y vuelva a mirar la pantalla de Granjas del caso
  anterior.
- **Observe**: ¿La nota se traduce (inglés correcto) y desaparecen los botones igual? ¿No hay
  texto a medio traducir?
- **Pregunta**: *La garantía se comunica bien en ambos idiomas. ¿Correcto?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

---

## NOTAS (transparencia, sin acción pedida)

- **Aprobar ≠ rechazar**: la separación entre permiso de aprobar y permiso de rechazar también
  se implementó, pero en la empresa de pruebas **no hay registros pendientes de aprobación**,
  así que no se convierte en un caso visible de esta sesión; queda certificado en la evidencia
  técnica (capturas y pruebas automáticas).
- **Observación OBS-01** (ya documentada, **no bloqueante**): con una cuenta que no puede ver
  el panel de inicio, la entrada «menú» a secas redirige al panel y muestra «Permiso requerido».
  Es un comportamiento anterior y ajeno a esta entrega; **no se reclasifica ni se oculta**.
  Su superficie propia (Administración/Maestros) funciona con normalidad.

## AL TERMINAR — su decisión

Responda **una sola** de estas tres opciones:

```
A) ACEPTO GA-FE-04
B) ACEPTO CON OBSERVACIONES: <escriba sus observaciones>
C) RECHAZO — CORREGIR: <escriba qué debe corregirse>
```
