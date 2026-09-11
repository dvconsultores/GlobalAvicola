# GA-UAT-03 · GUÍA DEL PROPIETARIO — GA-FE-05 (envío/reenvío a revisión)

**Cómo usar esta guía**: sesión guiada y corta (10 puntos). Usted solo interactúa con la
aplicación como un operador real: **sin consola, sin programas técnicos, sin escribir
direcciones**. Cada caso se responde con una de tres opciones: **PASS** · **PASS CON
OBSERVACIÓN** · **FALLA** (con comentario libre si lo desea).

**Ya preparado por el equipo**: cuenta de operador, operaciones de prueba en cada estado y
capturas de referencia. **Credenciales** (archivo local de este equipo, fuera del repositorio;
se destruye al terminar): `~/ga_uat_03_credentials.txt`
**Cómo llegar a una operación**: menú → **Operaciones** → abra la operación por su número
(la guía indica cuál en cada caso).

**Qué cambió, en una frase**: antes, un operador no podía **enviar a revisión** ni
**reenviar** una operación desde la aplicación (solo existía por dentro); ahora puede hacerlo
desde la propia pantalla de la operación, viendo siempre el estado claro.

---

## UAT-01 · Operación registrada — *Operador*
- **Dónde**: abra la operación **#53** (aparece como «Registrado»).
- **Observe**: ¿el estado se entiende a primera vista? ¿el botón **«Enviar a revisión»** se
  encuentra fácil, cerca del estado? ¿hay botones confusos o duplicados?
- **Pregunta**: *¿Encontrar la acción «Enviar a revisión» fue fácil y claro?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-02 · Enviar a revisión — *Operador*
- **Haga**: pulse **«Enviar a revisión»** una vez. Luego **recargue la página (F5)**.
- **Observe**: ¿la respuesta es clara (aviso de confirmación + cambio de estado a
  «Enviado a Revisión»)? ¿el botón desaparece después? ¿el estado se mantiene tras recargar?
- **Pregunta**: *¿El envío da confianza y el resultado es evidente?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-03 · Ya enviada — *Operador*
- **Dónde**: abra la operación **#54** (aparece como «Enviado a Revisión»).
- **Observe**: ¿se entiende que ya salió de sus manos? ¿NO aparece ningún botón de
  enviar/reenviar? ¿nada sugiere que pueda volver a enviarla?
- **Pregunta**: *¿Queda claro que esta operación ya está en revisión y no requiere acción?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-04 · Operación devuelta — *Operador*
- **Dónde**: abra la operación **#55** (aparece como «Devuelto»).
- **Observe**: ¿la situación se entiende? ¿ve el **motivo de la devolución** en la pantalla?
  ¿entiende que debe corregir/reenviar?
- **Pregunta**: *¿Un operador entiende por qué le devolvieron la operación y qué hacer?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-05 · Reenviar a revisión — *Operador*
- **Haga**: en la misma operación **#55**, pulse **«Reenviar a revisión»**. Recargue (F5).
- **Observe**: ¿el botón es fácil de encontrar y distinto de «editar»? ¿la respuesta es
  clara? ¿el estado vuelve a «Enviado a Revisión» y el botón desaparece? ¿persiste al recargar?
- **Pregunta**: *¿Reenviar se siente natural y el resultado es evidente?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-06 · Operación aprobada / final — *Operador*
- **Dónde**: abra la operación **#56** (aparece como «Aprobado»).
- **Observe**: ¿se entiende que el flujo terminó? ¿NO hay botón de enviar/reenviar ni de
  corrección? ¿nada sugiere que pueda volver a enviarse?
- **Pregunta**: *¿La inmutabilidad de lo aprobado se comprende desde la pantalla?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-07 · Cuando algo sale mal — *Operador* (demostración preparada)
- **Contexto**: preparamos una situación real y segura: la operación **#57** fue enviada en
  segundo plano **mientras el operador decidía**; al pulsar «Enviar» la aplicación responde
  con un aviso de error y se actualiza sola al estado correcto. No hay riesgo alguno.
- **Observe en la captura** `c08_failure_race_error_and_reconcile.png`: ¿aparece un aviso de
  error claro y **ningún** mensaje de éxito? ¿la operación se muestra luego como «Enviado a
  Revisión» (sin perder el trabajo hecho)?
- **Pregunta**: *¿Un fallo se comunica con honestidad (sin falsos éxitos) y la pantalla queda
  coherente?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-08 · En el teléfono (390×844) — *Operador*
- **Haga**: abra la aplicación en un teléfono (o estreche la ventana del navegador):
  - operación **#58** → debe verse **«Enviar a revisión»**;
  - operación **#59** → debe verse **«Reenviar a revisión»**.
- **Observe**: ¿el estado se ve? ¿los botones se alcanzan y no quedan cortados? ¿no hay
  desbordes horizontales? ¿la experiencia se siente el mismo producto que en escritorio?
- **Pregunta**: *En el teléfono, ¿enviar y reenviar se sienten tan claros como en escritorio?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-09 · Español / Inglés — *Operador*
- **Haga**: cambie el idioma (ES → EN) y mire la operación **#60** (Registrada).
- **Observe**: ¿el botón dice «Submit for review»? ¿el estado «Registered» se entiende en
  inglés? ¿el aviso de confirmación está traducido? ¿no hay textos a medio traducir?
- **Pregunta**: *¿La experiencia en inglés es completa y comprensible?*
- **Resultado**: [ ] PASS  [ ] PASS CON OBSERVACIÓN  [ ] FALLA · Comentario: ______

## UAT-10 · Comprensión del flujo — *pregunta directa*
**Pregunta**: ¿Queda claro el flujo completo **Registrar → Enviar a revisión →
Devuelto/Rechazado → Reenviar a revisión → Aprobado/Final**?
- **Resultado**: [ ] SÍ (PASS)  [ ] SÍ CON OBSERVACIÓN  [ ] NO · Comentario: ______

---

## NOTAS (transparencia)

- Los casos de permisos y unidades («quién puede enviar») ya están certificados por ingeniería;
  esta sesión juzga la **experiencia**, no la seguridad.
- Si aparece un problema de fechas de cierre de lote o áreas (R-182), se registrará como
  **existente y fuera del alcance de GA-FE-05**.
- No se pedirá ninguna decisión sobre BU-D10 en esta sesión.

## SU DECISIÓN (una sola)

```
A) ACEPTO GA-FE-05
B) ACEPTO GA-FE-05 CON OBSERVACIONES: <texto>
C) RECHAZO GA-FE-05 — CORREGIR: <texto>
```
