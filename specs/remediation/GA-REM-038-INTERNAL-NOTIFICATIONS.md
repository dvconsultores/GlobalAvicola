# `GA-REM-038` · NOTIFICACIONES INTERNAS

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-038` · `CAPABILITY SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` — enmienda A abierta (`OD-08`) |
| **Requisito** | `docs/02 §3.14` · `docs/10 §6.2` |
| **Decisión** | **`OD-07` `RESOLVED`** · **`OD-08` destinatarios `RESOLVED`, semántica temporal `OPEN`** |
| **Proceso** | `P-14` · Notificaciones y alertas |
| **Dependencias** | `GA-REM-002` `CERTIFIED` (RBAC) · `GA-REM-026` `CERTIFIED` (frontera transaccional) |
| **Antecedentes** | `P14_NOTIFICATION_CAPABILITY_MATRIX.md` · `P14_NOTIFICATION_EVENT_MATRIX.md` · `P14_NOTIFICATION_RECIPIENT_MATRIX.md` |

---

## 1. La decisión del propietario

```
OD-07 = RESOLVED  ·  2026-09-07

P-14 utilizará como canal obligatorio inicial
NOTIFICACIONES INTERNAS DENTRO DE GLOBAL AVÍCOLA.
```

Quedan **fuera del alcance inicial**, por decisión expresa:

```
EMAIL · WHATSAPP · SMS · PUSH MÓVIL · WEB PUSH · TELEGRAM · cualquier canal externo
```

Concuerda con `spec.md §9`, que ya listaba «Notificaciones push (v2)» entre lo que el proyecto
**no** hace. La decisión no contradice la spec: la confirma y fija qué sí se hace.

**Lo que `OD-07` NO decide.** Resolvió el canal, y solo el canal. No autoriza a inventar qué
eventos notifican, a quién, con qué prioridad, ni cuánto se conservan. Todo eso debe salir de
requisitos existentes, y lo que no esté escrito se declara hueco.

## 2. Las tres cosas que no son lo mismo

```
ALERT         pertenece al LOTE        OperationalAlert        ya existe
NOTIFICATION  pertenece a UNA PERSONA  bandeja con lectura     es esto
AUDIT         pertenece al SISTEMA     AuditLog · P-09         ni una ni otra
```

Una operación puede generar las tres, dos, una o ninguna. Que exista una alerta **no** implica
notificación: hace falta que una fuente normativa lo exija *y* que diga a quién.

`AuditLog` **no** se reutiliza como bandeja. Es historia inmutable del sistema y `P-09` lo
gobierna; convertirlo en buzón mezclaría dos procesos certificados por separado.

## 3. Qué se implementa, y qué no

`docs/02 §3.14` enumera seis tipos. Dos tienen disparador **y** destinatario escritos; cuatro
no. Se implementan los dos y se declaran los cuatro.

| Tipo | Disparador | Destinatario | Veredicto |
|---|---|---|:--:|
| Registro rechazado | `review/service.py:409` | `event.registered_by_id` — `§3.14` literal | **SE IMPLEMENTA** |
| Error de envío SAP | `sap/service.py:367,451` | rol `Analista SAP` — `docs/10 §6.2` literal | **SE IMPLEMENTA** |
| Mortalidad > umbral | existe | **sin definir** | hueco → `OD-08` |
| Peso fuera de estándar | existe | **sin definir** | hueco → `OD-08` |
| Pendiente de revisión > 24 h | **no existe** (temporal, sin planificador) | sin definir | hueco → `OD-08` |
| Lote próximo a cierre | **no existe**; «próximo» sin definir | sin definir | hueco → `OD-08` |

Consecuencia, dicha por delante: **`P-14` quedará `PARTIAL`**, no `CERTIFIED`. El canal
existirá y funcionará de extremo a extremo, y seguirán faltando cuatro de los seis tipos por
falta de requisito. Certificar con dos de seis sería certificar por muestra.

## 4. El modelo

```
Notification
    id
    company_id            FK companies          tenencia
    recipient_user_id     FK users              la bandeja es de una persona
    notification_type     str                   record_rejected | sap_send_failed
    payload               JSON                  datos para componer el texto
    related_entity_type   str?                  operational_event | sap_payload
    related_entity_id     int?
    created_at            timestamptz
    read_at               timestamptz?          NULL = no leída
```

**`read_at` y nada más.** `§19`: `NULL` es no leída, con valor es leída. No se inventa un enum
de estados. Y no hay `SENT`, `DELIVERED`, `BOUNCED` ni `OPENED` (`§20`): son de correo y de
push, que están fuera de alcance — el canal es interno y la entrega es la fila misma.

**Tipo y `payload`, no texto.** Se persiste `notification_type` con los datos que el mensaje
necesita, y el texto se compone con `i18n` al mostrarlo. Guardar la frase ya redactada la
congelaría en el idioma que tuviera el servidor el día que ocurrió, y un usuario que cambia a
inglés seguiría leyendo español. El `payload` no lleva secretos, credenciales ni trazas
internas.

**Entidad relacionada genérica.** `related_entity_type` + `related_entity_id` en lugar de una
clave foránea por tipo: los dos tipos apuntan a tablas distintas, y añadir una columna por cada
uno haría que el modelo creciera con cada evento nuevo. A cambio, **borrar la entidad no borra
la notificación** (`§79`): sin clave foránea no hay `CASCADE`, y el historial sobrevive. Si el
destino ya no existe, la interfaz lo maneja (`AC17`).

## 5. Cuándo se crea

**Dentro de la misma transacción del negocio.** Si el rechazo se persiste, la notificación
también; si el rechazo revierte, la notificación revierte con él. `GA-REM-026` fijó que la
transacción se confirma en la capa de ruta, de modo que ambas cosas salen o no salen juntas.

**No se traslada aquí la excepción de `LOGIN_FAILED`.** `P-09` necesita que un intento fallido
persista aunque la operación falle, porque el registro *es* el hecho de seguridad. En `P-14` no:
una notificación de algo que no llegó a ocurrir es una mentira, y `§84` lo prohíbe.

**Una operación rechazada no genera notificaciones.** Si la llamada falla por regla de negocio,
permiso o tenencia, el número esperado de notificaciones es cero.

**Consultar la bandeja no crea nada.** Solo los eventos del negocio crean notificaciones.

**Sin duplicados por reintento.** El envío SAP reintenta hasta tres veces; si el mismo
`SapPayload` vuelve a fallar mientras su aviso sigue **sin leer**, no se crea otro: el problema
es el mismo y la bandeja no debe convertirse en un contador de reintentos. La clave natural es
`(recipient_user_id, notification_type, related_entity_type, related_entity_id)` entre las no
leídas.

## 6. Quién puede leerlas

La puerta es **la propiedad**, no un permiso de módulo:

```
notification.recipient_user_id == usuario autenticado
```

Es el mismo patrón que `/me` o el cambio de contraseña, que usan `get_current_user` sin permiso
de módulo. Añadir un módulo `notifications` al catálogo obligaría a reconciliar la matriz `RBAC`
de la migración `l2m3n4o5p6q7` con sus seis roles —el trabajo que `R-44` costó— para no proteger
nada que la propiedad no proteja mejor.

Filtrar **solo** por `company_id` sería inseguro: devolvería las notificaciones de los demás
compañeros de empresa. El alcance de destinatario es obligatorio y el de empresa se suma.

## 7. Contrato

| Método | Ruta | Devuelve |
|---|---|---|
| `GET` | `/notifications` | página de notificaciones propias, `created_at` descendente, con `X-Total-Count` |
| `GET` | `/notifications/unread-count` | `{ "unread": n }` — cuenta en el servidor, no en el cliente |
| `PATCH` | `/notifications/{id}/read` | la notificación con `read_at` fijado |

**No hay `read-all`** (`§47`) ni borrado (`§48`): ninguna fuente los pide y las notificaciones
son historial operativo. **No hay endpoint de creación**: las crea el backend al ocurrir el
evento, nunca el cliente.

## 8. Interfaz

Campana en la cabecera existente —escritorio y móvil—, con el número de no leídas. Al pulsarla,
un panel con las recientes; cada una dice qué pasó, cuándo, y si está leída, **con texto y no
solo con color**. Abrir una la marca leída y lleva a la entidad relacionada cuando existe.

No se introduce ningún canal externo, ningún módulo de primer nivel nuevo y ningún sistema de
tiempo real: no hay `WebSocket`, ni `SSE`, ni `react-query` en el proyecto, y `OD-07` exige que
la notificación **exista dentro del sistema**, no que llegue al instante.

## 9. Criterios de aceptación

### Grupo A · canal

**`AC01`** · El canal de `P-14` es interno. Existe bandeja dentro de Global Avícola.

**`AC02`** · No se introduce ningún canal externo: ni correo, ni WhatsApp, ni SMS, ni push. Se
comprueba sobre el esquema y las dependencias, no sobre la intención.

### Grupo B · creación

**`AC03`** · Rechazar un registro crea una notificación `record_rejected`.

**`AC04`** · Un fallo de envío SAP crea una notificación `sap_send_failed` por cada usuario con
rol `Analista SAP` de esa empresa.

**`AC05`** · La notificación lleva su empresa, su destinatario y la entidad relacionada.

**`AC06`** · Una operación que **no** llega a ocurrir no crea notificación.

**`AC07`** · Consultar la bandeja no crea notificaciones.

**`AC08`** · Un reintento que vuelve a fallar no duplica un aviso que sigue sin leer.

### Grupo C · destinatario

**`AC09`** · `record_rejected` llega a **quien registró**, no a quien rechazó.

**`AC10`** · `sap_send_failed` llega al rol `Analista SAP`. Si la empresa no tiene ninguno, no
se crea ninguna y el envío no falla por ello.

### Grupo D · lectura

**`AC11`** · Un usuario lista **sus** notificaciones, con paginación y total real.

**`AC12`** · El contador de no leídas lo calcula el servidor y es exacto.

**`AC13`** · Marcar una como leída fija `read_at` y baja el contador. Hacerlo dos veces deja el
mismo estado final.

### Grupo E · aislamiento

**`AC14`** · Un usuario **no** accede a la notificación de otro usuario de su misma empresa.

**`AC15`** · Un usuario de otra empresa no accede a ninguna. Cero filtración.

### Grupo F · interfaz

**`AC16`** · La cabecera muestra campana y número de no leídas, en escritorio y en móvil.

**`AC17`** · La lista distingue leída de no leída **por texto**, muestra qué pasó y cuándo, y
navega a la entidad relacionada; si el destino ya no existe, no rompe la aplicación.

**`AC18`** · Abrir una notificación la marca leída y el contador baja sin recargar.

**`AC19`** · Hay estado vacío, de carga y de error, y son distinguibles entre sí: un fallo de
API no se presenta como bandeja vacía.

**`AC20`** · Todo texto nuevo pasa por `i18n`, con paridad `es`/`en`.

### Grupo G · validez

**`AC21`** · Las pruebas satisfacen `GA-REM-016 AC13`. Aserciones no vacuas.

**`AC22`** · La sensibilidad demuestra que las pruebas detectan la retirada de la creación, del
destinatario, del filtro de propiedad, del predicado de no leídas y del marcado.

## 10. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC03`…`AC10` | `backend/tests/test_notifications.py` | integración HTTP |
| `AC11`…`AC15` | `backend/tests/test_notifications.py` | integración HTTP |
| `AC02` | `backend/tests/test_notifications.py` | esquema + dependencias |
| `AC16`…`AC19` | `e2e/proceso-p14-notificaciones.spec.ts` | **`UI_E2E`** |
| `AC17`, `AC19` | `frontend/src/**/__tests__` | `vitest` |
| `AC20` | paridad de `translation.json` | conteo |
| `AC21`, `AC22` | informe de certificación | mutación |

> **Sobre la modalidad.** `OD-07` exige que el usuario **reciba y consulte** la notificación
> dentro del producto. Eso es una capacidad operativa y no se demuestra por API: `AC16`…`AC19`
> exigen `UI_E2E`. Es la misma lección que `R-96`.

## 11. Fuera de alcance

- **Canales externos.** Decisión de `OD-07`.
- **Los cuatro tipos sin requisito.** Registrados como `OD-08`; no se adivinan.
- **Planificador.** `P-14` no introduce ejecución periódica: `OD-07` decidió canal, no
  arquitectura. Los dos tipos temporales lo necesitarían.
- **Tiempo real.** No hay infraestructura y ninguna fuente lo pide.
- **`read-all`, borrado, retención.** Ninguna fuente los define. Si la retención llega a ser
  requisito, será deuda registrada, no una cifra inventada aquí.
- **`R-98`.** El frontend sigue sin modelo de permisos. `P-14` no será la excepción
  arquitectónica: el backend manda y la interfaz maneja el rechazo.
- **`P-08`, `RC-07`, `GA-TD-014`.** Intactos. La regla de la orden de compra sigue siendo
  `recibido_acumulado <= cantidad_ordenada`, sin tolerancia, y SAP sigue siendo la autoridad
  sobre el estado de la OC.

## 12. Definición de terminado

- `AC01`…`AC22` pasan.
- Existe prueba que falla contra el código actual por la causa exacta.
- Sensibilidad demostrada sobre las cinco invariantes y revertida **desde una salvaguarda
  previa**, nunca con `git checkout` sobre implementación sin confirmar.
- Migración con cabeza única y sin deriva de esquema.
- Paridad `i18n`.
- Regresión completa sin fallos nuevos.
- `P-14` reevaluado con su matriz de cadena, sin certificar por muestra.

---

# ENMIENDA A · DESTINATARIOS Y EL AVISO DE LAS 24 HORAS

`2026-09-07` · decisión `OD-08` · estado de la spec: vuelve a `SPEC_READY`

## A.1 Lo que resolvió el propietario

```
OD-08 · destinatarios (RESUELTO)

  1. la persona que cargó/registró la data que originó el evento
  2. los usuarios administradores de la empresa correspondiente
  3. los usuarios con función de contraloría / contralor
  4. el gerente del área correspondiente
  5. el supervisor correspondiente

  ámbito: MISMA EMPRESA · y misma área cuando la arquitectura la tenga
```

Y lo que **no** resolvió: qué significa «lote próximo a cierre», ni si el aviso de las 24 horas
se repite. `OD-08` sigue abierta en esa mitad.

## A.2 La regla, entera

```
DESTINATARIOS = destinatarios explícitos de fuentes anteriores
              ∪ originador ∪ administradores ∪ contraloría ∪ supervisor
              filtrado por  user.company_id == evento.company_id  y  user.is_active
              DISTINCT por user_id
```

**La unión no resta.** «Notificar al operador» (`docs/02 §3.14`) y «Notificar al rol Analista
SAP» (`docs/10 §6.2`) siguen exigidos y se suman; `OD-08` amplía, no sustituye.

**Una persona, un aviso.** Quien cumpla varias condiciones a la vez recibe **una** fila, no una
por motivo. La deduplicación es del backend.

**`Super Administrador` no entra por serlo.** Se siembra con `company_id = None` y por tanto no
pertenece a ninguna empresa. La condición es la pertenencia, no el rol; sin ella, un usuario de
plataforma recibiría el detalle operativo de todas las empresas.

**El originador sale del dato persistido**, nunca de quien esté autenticado al generarse el
aviso: pueden ser personas distintas y momentos distintos.

## A.3 Los seis eventos, con sus nombres literales

| Nombre literal (`docs/02 §3.14`) | Estado |
|---|:--:|
| Registro pendiente de revisión > 24h | **se implementa** — umbral normativo |
| Registro rechazado (notificar al operador) | ya implementado · **se amplían destinatarios** |
| Mortalidad > umbral configurable | **se implementa** |
| Peso fuera de estándar | **se implementa** |
| Error de envío SAP | ya implementado · **se amplían destinatarios** |
| Lote próximo a cierre | **`BLOCKED_BY_OWNER_DECISION`** |

### El de las 24 horas deja de estar bloqueado

Su umbral **está en su propio nombre**, y la condición es computable con lo que existe:

```
evento.status == pending_review
  Y  ahora − (AuditLog más reciente del evento con new_state='pending_review').created_at > 24 h
```

`updated_at` no sirve: cambia con cualquier edición y reiniciaría la cuenta. La marca exacta es
la de la transición, que consta en la auditoría. Leerla no es convertir `AuditLog` en bandeja:
es consultar historia, para lo que existe.

`OD-08` decidió el destinatario; la **tecnología** del disparador no es del propietario y se
resuelve con la arquitectura vigente, sin `Celery`, `Redis` ni colas.

### El de «próximo a cierre» sigue bloqueado

Se buscó en toda la jerarquía y la única aparición de la frase es la línea que la enumera. El
modelo tampoco la deja derivar: `Lot.end_date` es la fecha **real** de cierre —para cuando
existe, el lote ya cerró— y no hay `planned_end_date`. Derivarla de
`ProductivePhase.duration_days` sería decidir el requisito, no leerlo.

## A.4 Criterios de aceptación añadidos

### Grupo H · resolución de destinatarios

**`AC-R01`** · En cada evento normativo se incluye a quien cargó el dato que lo originó, cuando
es identificable.

**`AC-R02`** · Se incluye a los administradores de la empresa, según los roles reales del
catálogo y no según nombres inventados.

**`AC-R03`** · Se incluye a los usuarios de contraloría, según el rol real.

**`AC-R04`** · Se incluye al gerente del área **cuando exista resolución de área**. Hoy no
existe: se declara, no se sustituye.

**`AC-R05`** · Se incluye al supervisor correspondiente.

**`AC-R06`** · Los destinatarios exigidos por fuentes anteriores —el operador en el rechazo, el
rol `Analista SAP` en el error de envío— **siguen incluidos**.

**`AC-R07`** · Un mismo usuario recibe **como mucho una** notificación por evento.

**`AC-R08`** · Ningún destinatario de otra empresa recibe nada.

**`AC-R09`** · Un usuario que cumple varias condiciones se deduplica.

**`AC-R10`** · La resolución es del backend. El frontend no decide destinatarios.

**`AC-R11`** · Lo que falta para resolver un destinatario se declara, no se adivina.

**`AC-R12`** · Las pruebas satisfacen `GA-REM-016 AC13`.

### Grupo I · el aviso de las 24 horas

**`AC-T01`** · La condición es objetivamente computable: 24 h desde la transición a
`pending_review`, tomada de la auditoría y no de `updated_at`.

**`AC-T02`** · La notificación se crea al cruzar el umbral normativo.

**`AC-T03`** · **Antes** del umbral no existe notificación.

**`AC-T04`** · Reevaluar no duplica: la recurrencia no está definida en ninguna fuente, de modo
que el aviso se emite **una sola vez** por evento y destinatario. Que se repita o no es un hueco
de requisito registrado, no una decisión nuestra.

## A.5 Trazabilidad añadida

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC-R01`…`AC-R11` | `backend/tests/test_notification_recipients.py` | integración HTTP |
| `AC-T01`…`AC-T04` | `backend/tests/test_notification_recipients.py` | integración |
| `AC-R12` | informe de certificación | mutación |

## A.6 Fuera de alcance de la enmienda

- **`Lote próximo a cierre`.** `OD-08` sigue abierta en esa mitad. Sin definición no se
  implementa, y `P-14` no puede certificarse.
- **Gerente del área.** No hay áreas ni rol de gerencia: `BLOCKED_BY_MODEL_GAP`.
- **Recurrencia del aviso de 24 h.** Sin fuente: se emite una vez.
- **Crear los roles que faltan del catálogo.** `docs/02 §6.1` enumera once y hay seis
  sembrados. Es un desfase anterior; `GA-REM-034` permite crearlos y el resolutor funciona con
  los que existan.
- **`P-08`, `RC-07`, `GA-TD-014`, `R-98`, `R-99`.** Intactos.

## A.7 Definición de terminado — ampliada

- `AC-R01`…`AC-R12` y `AC-T01`…`AC-T04` pasan, salvo `AC-R04`, declarado bloqueado.
- Sensibilidad sobre originador, administrador, contraloría, deduplicación, empresa y
  destinatario explícito, revertida desde salvaguarda previa.
- `P-14` reevaluado evento por evento. **Sigue `PARTIAL`** mientras el sexto no tenga
  semántica: cinco de seis no es seis.
