# GA-FE-05 · UAT DEL PROPIETARIO (R-181 — envío/reenvío a revisión)

**SESIÓN EJECUTADA (GA-UAT-03): decisión del propietario = A) ACEPTO GA-FE-05 — sin observaciones** (`audit/ga-uat-03/GA_OWNER_ACCEPTANCE_GA_FE_05_RECORD.md`). **GA-FE-05 = FUNCTIONALLY_CERTIFIED / OWNER_ACCEPTED · R-181 = CLOSED / OWNER_ACCEPTED.**

**OWNER_UAT_READY: YES** (2026-09-11 · GA-FE-05 FUNCTIONALLY_CERTIFIED · generación `index-WUv1-F9o.js`).
Sesión guiada corta (7 puntos). Las cuentas de prueba se preparan al abrir la sesión (no hay cuentas vivas entre sesiones).

## Qué cambió, en una frase

Un operador que registra una operación ahora puede **enviarla a revisión desde la propia pantalla** (y **reenviarla** si se la devuelven o la rechazan), viendo siempre el estado claro de la operación. Antes esto no existía en la interfaz.

## Qué observar (7 puntos)

1. **Descubrir la acción** — con un usuario operativo, abra una operación en estado «Registrado». Debe ver un botón **«Enviar a revisión»** cerca del estado, sin buscarlo en menús raros.
2. **Enviar** — púlselo una vez. Debe aparecer un aviso de confirmación («Enviado a revisión») y el estado debe cambiar a **«Enviado a Revisión»**; el botón desaparece (ya no aplica).
3. **Persistencia** — recargue la página (F5) y vuelva a entrar: el estado se mantiene, sin botón obsoleto.
4. **Devuelto** — si una operación fue devuelta, debe ver **«Devuelto»** y el motivo visible, con el botón **«Reenviar a revisión»**.
5. **Reenviar** — púlselo: mismo comportamiento que el envío; vuelve a «Enviado a Revisión».
6. **Sin acciones indebidas** — en una operación **aprobada/final** no debe existir ningún botón de envío/reenvío (ni de corrección nueva).
7. **Teléfono (390×844)** — repita el punto 1–2 en el móvil: botón alcanzable, mismo comportamiento, nada cortado.

**Transparencia**: la confirmación es por aviso + estado actualizado (no hay ventana modal, coherente con el resto del producto); los casos de seguridad (sin permiso, sin unidad, empresa apagada) ya están certificados por ingeniería y no se le piden al propietario.

## Su decisión

```
A) ACEPTO GA-FE-05
B) ACEPTO CON OBSERVACIONES: <observaciones>
C) RECHAZO — CORREGIR: <qué debe corregirse>
```
