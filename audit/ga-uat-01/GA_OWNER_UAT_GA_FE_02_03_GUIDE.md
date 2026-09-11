# GA-UAT-01 · GUÍA DEL PROPIETARIO — GA-FE-02 + GA-FE-03

**Cómo usar esta guía**: es una sesión guiada. Usted solo interactúa con la aplicación como lo
haría un administrador real: **sin URLs escritas a mano, sin consola, sin terminal, sin
conocimientos técnicos**. Cada caso termina en una sola pregunta de aceptación con tres
respuestas posibles: **PASS** · **PASSA CON OBSERVACIÓN** · **FALLA** (puede añadir comentario
en lenguaje natural).

**Preparado ya por el equipo** (usted no hace nada de esto): cuentas de prueba, estado de la
empresa de pruebas, datos, permisos y capturas.
**Credenciales**: están en el archivo local `~/ga_uat_credentials.txt` de este equipo (fuera
del repositorio; se destruye al terminar). El Super Administrador usa **su cuenta habitual**.
**Empresa de pruebas**: «Avícola Global C.A.» (segunda empresa: «Avícola Del Sur C.A.»).
**Estado inicial preparado**: en la empresa de pruebas, **Engorde está Activa** y
**Progenitoras, Reproductoras e Incubadora están Inactivas**; el usuario productivo **no**
tiene ninguna concesión (usted la dará en el caso 05).

---

## CASO 01 · Entrar y elegir empresa — *Super Administrador*
- **Dónde**: pantalla de inicio de sesión; luego el selector de empresa en la barra superior.
- **Haga**: entre con su cuenta de Super Administrador. Observe cómo se ve la empresa activa
  arriba a la derecha. Abra el selector y elija «Avícola Global C.A.». Recargue la página
  (F5) y observe si el contexto se mantiene claro.
- **Observe**: ¿Se entiende en qué empresa está trabajando en todo momento? ¿Elegir empresa es
  intuitivo? ¿Al recargar no se pierde ni confunde?
- **Pregunta**: *¿Entrar y situarse en una empresa es claro e intuitivo?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 02 · Las cuatro unidades — *Super Administrador*
- **Dónde**: menú lateral → **Configuración → Acceso por unidad** (se llega por el menú; nada
  de URLs).
- **Haga**: observe la pantalla con las cuatro unidades y revise estados y botones.
- **Observe**: ¿Los nombres (Progenitoras, Reproductoras, Incubadora, Engorde) se entienden?
  ¿Se distingue de un vistazo cuál está **Activa** y cuál **Inactiva**? ¿La pantalla se siente
  ordenada y sin tecnicismos?
- **Pregunta**: *¿La pantalla de unidades es comprensible sin conocimientos técnicos?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 03 · Activar y desactivar una unidad — *Super Administrador*
- **Haga**: en la misma pantalla, active **Incubadora** (confirme el diálogo) y observe el
  mensaje y el cambio de estado. Después desactívela.
- **Observe**: ¿Se entiende qué cambió? ¿Las otras tres permanecen igual? ¿La aplicación deja
  claro que **activar una unidad NO concede acceso a ninguna persona**?
- **Pregunta**: *¿Queda claro que activar una unidad para la empresa no da acceso automático a
  los usuarios?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 04 · Unidad de la empresa vs. unidad del usuario — *Administrador de Accesos*
- **Haga**: cierre sesión y entre como **Administrador de Accesos**, vaya a
  **Configuración → Acceso por unidad**, elija «Engorde» en el selector de unidad y mire la
  lista de personas.
- **Observe**: ¿Se distingue visualmente lo que está **activado para la empresa** de lo que
  está **concedido a una persona**? ¿Se entiende que son dos decisiones distintas?
- **Pregunta (crítica)**: *¿Queda claro que activar Engorde para la empresa NO significa
  darle Engorde automáticamente a todos los usuarios?* (se espera **SÍ**)
- **Resultado**: [ ] SÍ (PASS)  [ ] SÍ CON OBSERVACIÓN  [ ] NO — Comentario: ______

## CASO 05 · Conceder acceso a una persona — *Administrador de Accesos*
- **Haga**: en la misma pantalla, con «Engorde» seleccionado, conceda la unidad a
  **la persona de pruebas «Usuario Productivo»** y observe el resultado.
- **Observe**: ¿Está claro a quién le está dando acceso? ¿El diálogo y el mensaje de éxito son
  claros? ¿El estado final de esa persona se entiende?
- **Pregunta**: *¿Conceder acceso es claro y el resultado queda evidente?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 06 · Revocar ese mismo acceso — *Administrador de Accesos*
- **Haga**: revoque la misma concesión y observe.
- **Observe**: ¿La acción se descubre fácil? ¿Queda claro que se le quitó **a la persona** y
  que **la empresa sigue con Engorde activa**? ¿No hay ambigüedad sobre qué se acaba de
  cambiar?
- **Pregunta**: *¿Revocar es claro y no se confunde con desactivar la unidad de la empresa?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 07 · El papel del Administrador de Accesos — *Administrador de Accesos*
- **Haga**: con esa cuenta, recorra el menú y navegue con normalidad.
- **Observe**: ¿Encuentra su pantalla de accesos **por el menú**? ¿El menú evita mostrarle
  áreas de producción (lotes, operaciones, revisión…) que no le corresponden? ¿Se entiende que
  esta persona **administra accesos, no produce**?
- **Pregunta**: *¿El Administrador de Accesos ve exactamente lo que necesita para su función,
  sin ruido de otras áreas?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 08 · El papel del Administrador de Unidades — *Administrador de Unidades*
- **Haga**: entre con la cuenta **Administrador de Unidades** y explore el menú y su pantalla
  de unidades de empresa.
- **Observe**: ¿Descubre su pantalla por el menú? ¿Puede activar/desactivar unidades según su
  autoridad? ¿La aplicación evita presentarlo como operador productivo?
- **Pregunta**: *¿La separación «administrar unidades ≠ operar producción» se percibe con
  claridad?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 09 · El día de un usuario productivo — *Usuario Productivo*
- **Preparación (usted mismo, 1 minuto)**: como **Administrador de Accesos**, vuelva a
  conceder «Engorde» a **Usuario Productivo** (igual que en el caso 05).
- **Haga**: entre ahora con **Usuario Productivo**. Recorra el menú; abra **Gestión Avícola**
  y vea el hub de unidades.
- **Observe**: ¿Aparece el área de trabajo de su unidad de forma natural? ¿Solo aparece **su**
  unidad (Engorde) y no las demás? ¿Se evita el ruido de opciones de administración?
- **Pregunta**: *¿El menú de un usuario productivo se entiende y le lleva directo a lo suyo?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 10 · Usuario sin unidades todavía — *Usuario Sin Unidades*
- **Haga**: entre con la cuenta **Usuario Sin Unidades** y recorra lo que ve.
- **Observe**: ¿La aplicación funciona con normalidad? ¿No aparecen menús productivos ni
  grupos de menú vacíos o rotos? ¿No salta un error genérico al entrar? ¿Se siente una
  aplicación intencional?
- **Pregunta**: *¿La aplicación se ve coherente para un usuario que todavía no tiene acceso a
  unidades productivas?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 11 · La navegación sigue la autoridad — *Administrador de Accesos + Usuario Productivo*
- **Haga**: como **Administrador de Accesos**, revoque la concesión de Engorde a **Usuario
  Productivo**; recargue la sesión del usuario productivo (o vuelva a entrar). Después vuelva
  a concederla. Finalmente, como **Super Administrador**, desactive temporalmente
  **Engorde** para la empresa y, al terminar el caso, **vuelva a activarla**.
- **Observe**: ¿El menú del usuario productivo aparece/desaparece siguiendo lo que realmente
  puede hacer? ¿Sin enlaces fantasma ni opciones obsoletas?
- **Pregunta**: *¿La navegación refleja fielmente los permisos reales del momento?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 12 · Cambiar de empresa — *Super Administrador*
- **Haga**: alterne entre «Avícola Global C.A.» y «Avícola Del Sur C.A.» y navegue después de
  cada cambio.
- **Observe**: ¿El cambio se nota? ¿El menú se actualiza sin arrastrar restos de la empresa
  anterior?
- **Pregunta**: *¿Cambiar de empresa es claro y el menú se recompone correctamente?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 13 · En el teléfono (390×844) — *móvil*
- **Haga**: abra la aplicación en un teléfono (o estreche la ventana del navegador al ancho de
  un teléfono). Entre con:
  - **Usuario Productivo Móvil** (ya tiene Engorde concedido) → recorra su menú inferior.
  - **Administrador de Accesos Móvil** → observe el menú.
- **Observe**: ¿El menú abre y cierra bien? ¿Los botones se alcanzan? ¿Se puede desplazar con
  naturalidad? ¿No hay desbordes horizontales ni controles cortados?
- **Nota**: en esta versión, las pantallas de administración son de escritorio por diseño; el
  recorrido móvil se centra en la experiencia operativa.
- **Pregunta**: *¿La experiencia móvil es usable para un usuario de producción?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 14 · Español / Inglés — *Super Administrador*
- **Haga**: cambie el idioma arriba (ES → EN → ES).
- **Observe**: ¿Todo se traduce completo? ¿Sin mezclas ni textos a medio traducir? ¿Los
  términos de administración se entienden?
- **Pregunta**: *¿La experiencia en ambos idiomas es completa y coherente?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## CASO 15 · Revisión visual y de experiencia — *libre*
- **Haga**: recorra las pantallas visitadas y mire con calma.
- **Observe**: jerarquía de la información · etiquetas y botones · espaciados · insignias de
  estado (Activa/Inactiva) · visibilidad de la empresa activa · legibilidad en móvil.
- **Pregunta**: *¿El conjunto se siente un producto aceptable para poner en manos de clientes
  reales?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

---

## AL TERMINAR — su decisión

Responda **una sola** de estas tres opciones:

```
A) ACEPTO GA-FE-02 Y GA-FE-03
B) ACEPTO CON OBSERVACIONES: <escriba sus observaciones>
C) RECHAZO — CORREGIR: <escriba qué debe corregirse>
```
