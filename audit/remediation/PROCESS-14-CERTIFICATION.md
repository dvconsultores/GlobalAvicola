# `P-14` · NOTIFICACIONES Y ALERTAS — INFORME DE CERTIFICACIÓN

`docs/02 §3.14` · `docs/10 §6.2` · `GA-REM-038` · `OD-07`

```
P-14  = CERTIFIED        6 de los 6 tipos normativos — ver ADDENDUM B
OD-07 = RESOLVED         canal interno / in-app
OD-08 = RESOLVED         destinatarios · modelo de área · próximo a cierre
```

> **`ADDENDUM A`.** Este informe se escribió con **dos** de seis tipos cubiertos. `OD-08`
> resolvió los destinatarios y releer los nombres literales desbloqueó el aviso de las 24 horas:
> ahora son **cinco**. El veredicto no cambia — cinco de seis sigue sin ser seis.

---

## 1. El veredicto, por delante

`P-14` **no queda certificado**, y no es por un defecto: es porque `docs/02 §3.14` enumera seis
tipos de aviso y solo dos dicen a quién avisar.

```
6 tipos normativos · 2 implementados · 4 sin destinatario definido
```

`GA-REM-016 AC05` no admite certificar por muestra. Dos de seis es una muestra, por buena que
sea. Declararlo `CERTIFIED` porque la campana funciona sería el mismo salto que costó revertir
`P-03` hace un día: de «el mecanismo hace lo que la decisión describe» a «el proceso está
completo».

## 2. Qué decidió el propietario, y qué no

```
OD-07 = RESOLVED

P-14 utilizará como canal obligatorio inicial
NOTIFICACIONES INTERNAS DENTRO DE GLOBAL AVÍCOLA.

Fuera: correo · WhatsApp · SMS · push móvil · web push · Telegram
```

Concuerda con `spec.md §9`, que ya listaba «Notificaciones push (v2)» entre lo que el proyecto
no hace. La decisión no contradice la spec: la confirma.

**Resolvió el canal, y solo el canal.** No autorizó decidir qué eventos notifican, a quién, con
qué prioridad ni cuánto se conservan. Al derivar eso de las fuentes apareció el hueco.

## 3. Los dos que sí, y por qué solo esos

| Tipo | Disparador | Destinatario | Fuente |
|---|---|---|---|
| `record_rejected` | `review/service.py:409`, único punto que asigna `REJECTED` | `event.registered_by_id` | `docs/02 §3.14`: «Registro rechazado (**notificar al operador**)» |
| `sap_send_failed` | `sap/service.py:367,451`, `PayloadStatus.FAILED` | rol `Analista SAP` | `docs/10 §6.2`: «**Notificar al rol "Analista SAP"**» |

Los dos citan una fuente **con sus palabras**. No se dedujeron.

El rol `Analista SAP` existe de verdad: lo crea la migración `l2m3n4o5p6q7` y
`review/service.py:549` ya lo resolvía por nombre para armar el tercer paso de aprobación. La
regla de `docs/10` era aplicable tal como estaba escrita.

## 4. Los cuatro que no, y qué se descartó

```
mortalidad > umbral     disparador SÍ · destinatario NO
peso fuera de estándar  disparador SÍ · destinatario NO
pendiente > 24 h        disparador NO (temporal, sin planificador) · destinatario NO
lote próximo a cierre   disparador NO · «próximo» sin definir · destinatario NO
```

Para los dos primeros el dato tampoco ayuda: se enumeraron los campos de `Lot` uno a uno y
**ninguno apunta a una persona**. No hay responsable, ni supervisor, ni usuario asignado.

Se consideraron tres candidatos y se descartaron por escrito:

| Candidato | Por qué no |
|---|---|
| `registered_by_id` del evento | es quien acaba de registrar la mortalidad: ya lo sabe |
| rol `Supervisor Avícola` | `docs/02 §6.1` le da «revisar, corregir, devolver registros» — el flujo de revisión, no las alertas |
| todos los administradores | inventar un destinatario y llamarlo requisito |

Notificar a la persona equivocada es **peor** que no notificar, porque parece que el sistema
avisa. De ahí `OD-08`.

## 5. Alerta, notificación y auditoría no son lo mismo

Merece constar porque es lo que evita convertir el producto en una máquina de ruido:

```
ALERT         pertenece al LOTE        OperationalAlert     ya existía
NOTIFICATION  pertenece a UNA PERSONA  bandeja con lectura  esto
AUDIT         pertenece al SISTEMA     AuditLog · P-09      ninguna de las dos
```

`AuditLog` **no** se reutilizó como bandeja. Es historia inmutable y `P-09` lo gobierna;
convertirlo en buzón habría mezclado dos procesos certificados por separado. Y ninguna alerta
existente se convirtió automáticamente en notificación: `high_mortality` y `weight_deviation`
figuran en `§3.14` y esperan destinatario; `temperature_out_of_range` y
`humidity_out_of_range` ni siquiera figuran ahí.

## 6. Tres decisiones de modelo

**`read_at` y nada más.** `NULL` es sin leer. No hay `SENT`, `DELIVERED` ni `OPENED`: son de
correo y de push, y los dos están fuera de alcance. El canal es interno y la entrega es la fila.

**Tipo y `payload`, no texto redactado.** Guardar la frase la congelaría en el idioma que
tuviera el servidor ese día, y quien cambia a inglés seguiría leyendo español.

**Entidad relacionada sin clave foránea.** Deliberado: el aviso debe sobrevivir a la
desaparición de aquello de lo que informaba. Con `FK` y `CASCADE`, borrar un evento borraría la
historia de que fue rechazado.

## 7. Dos guardas del proyecto obligaron a modelar mejor

**`test_ac08b`** limita a seis las rutas públicas, y ya estaban las seis. Añadir cuatro
exenciones la habría convertido en el colador que su propio docstring teme.

El problema era de modelado: la lista mezclaba rutas **sin sesión** con rutas que exigen sesión
y autorizan por **titularidad**. `/me` figuraba como «pública» cuando exige token, y las de
titularidad gastaban el cupo de superficie anónima. Se separaron en dos listas con su motivo
por entrada. Las públicas de `/api` bajan de seis a **dos**, y el límite baja con ellas: la
guarda quedó más estricta, no menos.

**`GA-REM-037 AC22`** prohibía cualquier tabla llamada «notification», porque cuando se escribió
eso solo podía significar que `P-14` se había colado por la puerta de atrás. Desde `OD-07`,
`P-14` entra por la principal. La guarda pasa a comprobar lo que quería decir —ningún canal
externo— y además que la alerta de peso no se haya convertido en notificación, que es
justamente lo que `OD-08` aún no autoriza.

## 8. Evidencia

| Nivel | Archivo | Resultado |
|---|---|:--:|
| Creación, destinatario, lectura, aislamiento | `backend/tests/test_notifications.py` | **11/11** |
| Experiencia | `e2e/proceso-p14-notificaciones.spec.ts` | **5/5** `UI_E2E` |
| Campana y estados | `frontend/src/components/notifications/__tests__` | **8/8** |
| `tsc --noEmit` | — | **limpio** |
| Paridad `i18n` | `es` / `en` | **931 = 931** |
| Regresión backend | suite completa | **460 passed · 49 skipped** (antes 449) |
| Regresión `E2E` | 17 suites | **129 passed** (antes 124) |
| Regresión `vitest` | suite completa | **82 passed** (antes 74) |
| Alembic | `n4o5p6q7r8s9` | **cabeza única** |

**Sobre la modalidad.** `OD-07` exige que el usuario **reciba y consulte** el aviso dentro del
producto. Eso es capacidad operativa y no se demuestra por API: `AC16`…`AC19` son `UI_E2E`.

## 9. Sensibilidad · `GA-REM-016 AC13`

Ocho mutaciones, todas revertidas:

| # | Mutación | Rompe | Fallos |
|:--:|---|---|:--:|
| 1 | Se retira la creación del aviso de rechazo | `AC03` | 7 |
| 2 | El aviso va a quien rechaza, no a quien registró | `AC09` | 7 |
| 3 | Se retira el filtro de destinatario | `AC14` | 2 |
| 4 | El contador ignora el predicado de no leídas | `AC12` | 1 |
| 5 | Marcar leída deja de fijar `read_at` | `AC13` | 2 |
| 6 | Se retira la campana de la cabecera | `AC16` | 5 (`UI_E2E`) |
| 7 | El contador se calcula contando lo cargado | `AC12` | 2 (`vitest`) |
| 8 | Un fallo de carga se presenta como bandeja vacía | `AC19` | 1 (`vitest`) |

### Sobre el protocolo de reversión

El checkpoint anterior perdió un endpoint al revertir una mutación con `git checkout` sobre un
archivo que contenía implementación sin confirmar, y **la comprobación de residuo lo dio por
limpio** porque el código sospechoso ya no existía.

Aquí no se repitió, y no por cuidado sino por método:

```
1. la implementación se confirmó y publicó ANTES de mutar        07e7410 · a2e21da
2. se copió además una salvaguarda explícita de cada archivo
3. cada reversión se hizo desde esa copia, nunca desde el índice
4. tras revertir se comprobó que la capacidad SIGUE EXISTIENDO,
   patrón por patrón — no solo que `git diff` estuviera limpio
```

Las ocho comprobaciones del punto 4 pasaron: `crear_notificacion`, `event.registered_by_id`,
`_avisar_fallo_sap`, el filtro de destinatario, el predicado de no leídas, `NotificationBell`
en la cabecera, `getUnreadCount()` y el estado de error.

## 10. Lo que queda fuera, dicho

- **Los cuatro tipos sin destinatario.** `OD-08`. No se adivinan.
- **Planificador.** `P-14` no introduce ejecución periódica: `OD-07` decidió canal, no
  arquitectura. Los dos tipos temporales lo necesitarían.
- **Tiempo real.** No hay `WebSocket`, `SSE` ni caché de consultas en el proyecto, y ninguna
  fuente lo pide. El contador se refresca al montar, al abrir el panel y con un sondeo de un
  minuto.
- **`read-all`, borrado, retención.** Ninguna fuente los define. Si la retención llega a ser
  requisito, será deuda registrada y no una cifra inventada.
- **`R-98`.** El frontend sigue sin modelo de permisos y `P-14` no se hizo la excepción: el
  backend manda y la interfaz maneja el rechazo. No se cierra incidentalmente.
- **`R-99`.** El frontend del entorno compartido sigue por detrás de `main`. No se declara
  resuelto.
- **`P-08`, `RC-07`, `GA-TD-014`.** Intactos. La regla de la orden de compra sigue siendo
  `recibido_acumulado <= cantidad_ordenada`, sin tolerancia, y SAP sigue siendo la autoridad
  sobre el estado de la OC.

---

# ADDENDUM A · `OD-08` resuelve los destinatarios · cinco de seis

`OD-08` · `GA-REM-038` enmienda A

```
P-14  = PARTIAL          5 de los 6 tipos normativos cubiertos
OD-08 · destinatarios ......... RESOLVED
OD-08 · semántica temporal .... OWNER_DECISION_REQUIRED
```

## A.1 Qué cambió

El informe anterior dejó `P-14` en `PARTIAL` con **dos** de seis tipos, porque cuatro no decían
a quién avisar. `OD-08` lo resolvió:

```
DESTINATARIOS = explícitos de fuentes anteriores
              ∪ quien cargó el dato ∪ administradores ∪ contraloría ∪ supervisor
              filtrado por empresa del evento · DISTINCT por user_id
```

Y al releer los **nombres literales** de `docs/02 §3.14` apareció algo que el informe anterior
había agrupado mal:

```
«Registro pendiente de revisión > 24h»   el umbral ESTÁ en el nombre  → accionable
«Lote próximo a cierre»                  «próximo» no está en ninguna parte → bloqueado
```

Los dos se habían clasificado juntos como «temporales sin definir». Solo uno lo era.

```
2 de 6  →  5 de 6
```

## A.2 Los términos del propietario contra los roles reales

`OD-08` nombra funciones, no roles. La correspondencia se hizo contra el catálogo antes de
escribir código (`P14_OD08_ROLE_MAPPING_MATRIX.md`):

| Término | Rol real | Estado |
|---|---|:--:|
| persona que cargó el dato | `OperationalEvent.registered_by_id` | **resuelto** |
| administradores | `Administrador de Empresa` · `Super Administrador` **con empresa** | **resuelto** |
| contraloría | `Contralor Avícola` | **resuelto** |
| supervisor | `Supervisor Avícola` | **resuelto** |
| **gerente del área** | **ninguno** | **`BLOCKED_BY_MODEL_GAP`** |

No hay tabla de área, departamento ni unidad organizativa. El usuario se asocia a una empresa y
a un rol, y a nada más. Ni los roles identifican el área ni el usuario la tiene asignada.

**`Super Administrador` no entra por serlo.** Se siembra con `company_id = None`, luego no
pertenece a ninguna empresa, y su nombre de rol contiene «administrador». Sin la condición de
pertenencia recibiría el detalle operativo de todas — la fuga exacta que había que evitar.

De paso quedó anotado un desfase anterior: `docs/02 §6.1` enumera **once** roles y hay **seis**
sembrados. No se corrige aquí; `GA-REM-034` permite crearlos y el resolutor funciona con los que
existan.

## A.3 El aviso de las 24 horas

Su umbral es normativo, así que no había nada que decidir. Lo que sí hubo que resolver es desde
cuándo se cuenta:

```
updated_at   NO — cambia con cualquier edición; un evento tocado a las 23 h reiniciaría la cuenta
AuditLog     SÍ — guarda la transición a `pending_review` con su instante exacto
```

Leer la auditoría para computar una condición no es convertirla en bandeja: es consultar
historia, que es para lo que existe. `P-09` sigue gobernándola y nadie escribe avisos en ella.

**La recurrencia no está definida en ninguna fuente**, de modo que se emite **una vez** por
evento y destinatario, con idempotencia. Inventar una repetición diaria habría añadido ruido que
nadie pidió; el hueco queda registrado.

**El mecanismo no es del propietario.** `§30` del encargo lo dice y es correcto: elegir entre
`cron`, `Celery` o una tarea del proceso es decisión técnica. Se eligió la mínima que cumple —una
tarea sobre el `lifespan` que ya existía—, sin `Redis`, ni colas, ni dependencias nuevas.

## A.4 Una guarda obligó a poner la lógica donde va

`R-26` prohíbe `except Exception` en `app/main.py`, porque el contrato de error no puede
apoyarse en una captura genérica. La tarea de fondo sí necesita una —un fallo al evaluar no
puede tumbar la aplicación—, y esa contradicción fue la señal de que estaba en el archivo
equivocado.

Vive en `notifications/sla.py`; `main.py` solo la arranca. La guarda no se tocó, y el resultado
es mejor código: el arranque de la aplicación no contiene lógica de notificaciones.

## A.5 Lo que sigue sin convertirse en notificación

Las alertas de **temperatura** y **humedad** fuera de rango no figuran en `docs/02 §3.14`, de
modo que siguen siendo alertas del lote. Convertirlas habría sido inventar requisito.

Y `GA-REM-037` sigue vigente: **dentro de norma y sin referencia no hay alerta**, luego tampoco
notificación. Hay prueba de que un pesaje normal no avisa a nadie.

## A.6 Evidencia añadida

| Nivel | Archivo | Resultado |
|---|---|:--:|
| Destinatarios, deduplicación, tenencia, 24 h | `backend/tests/test_notification_recipients.py` | **9/9** |
| Regresión backend | suite completa | **469 passed · 49 skipped** (antes 460) |
| Regresión `E2E` | 17 suites | **129 passed** |
| Regresión `vitest` | suite completa | **82 passed** |
| `tsc --noEmit` | — | **limpio** |
| Paridad `i18n` | `es` / `en` | **934 = 934** |

## A.7 Sensibilidad · `GA-REM-016 AC13`

Siete mutaciones, todas revertidas desde salvaguarda previa:

| # | Mutación | Rompe | Fallos |
|:--:|---|---|:--:|
| 1 | Se excluye al originador | `AC-R01` | 3 |
| 2 | Se excluye a los administradores | `AC-R02` | 6 |
| 3 | Se excluye a la contraloría | `AC-R03` | 5 |
| 4 | Se retira la deduplicación | `AC-R07`, `AC-R09` | 1 |
| 5 | Se retira el filtro de empresa | `AC-R08` | 1 |
| 6 | Se pierde el destinatario explícito | `AC-R06` | 1 |
| 7 | El umbral de 24 h pasa a 0 | `AC-T03` | 1 |

**La mutación 6 merece un comentario.** Rompió el aviso de SAP y **no** el del rechazo, y es
correcto: en el rechazo el operador entra también como originador, de modo que quitarlo de los
explícitos no lo elimina. Quien distingue las dos vías es el evento de SAP, donde el
`Analista SAP` **no** es originador de nada. Una sola prueba no habría bastado.

### El protocolo de reversión

```
1. la implementación se confirmó y publicó ANTES de mutar        846b1bf
2. se copió además una salvaguarda explícita de cada archivo
3. cada reversión se hizo desde esa copia, nunca desde el índice
4. tras revertir se comprobó que la capacidad SIGUE EXISTIENDO,
   diez patrones uno a uno — no solo que `git diff` estuviera limpio
```

## A.8 El veredicto, y por qué no es otro

```
P-14 = PARTIAL
```

Cinco de seis no es seis. `docs/02 §3.14` enumera seis tipos y el sexto no tiene semántica:
«próximo» no está definido en ninguna fuente, `Lot.end_date` es la fecha **real** de cierre —para
cuando existe, el lote ya cerró— y no hay `planned_end_date`. Derivarla de
`ProductivePhase.duration_days` sería decidir el requisito en vez de leerlo.

Reducir el alcance para poder certificar —«cinco eventos certificados, luego `P-14` certificado»—
es exactamente lo que `§94` del encargo prohíbe, y lo que obligó a revertir `P-03` dos días
antes.

```
Falta para certificar P-14:
  · OD-08 · qué es «lote próximo a cierre»           decisión del propietario
  · modelo de área y rol de gerencia                  decisión de modelo, para AC-R04
```

---

# ADDENDUM B · `OD-08` completa · los seis eventos

`OD-08` · `GA-REM-038` enmienda B · `GA-REM-039`

```
P-14 = CERTIFIED
```

## B.1 Qué cerró el proceso

Faltaban dos cosas, y eran de clase distinta:

```
«lote próximo a cierre»   una DECISIÓN: qué significa «próximo»
gerente del área          un MODELO: el concepto no existía
```

`OD-08` resolvió la primera —tres días antes de la fecha prevista— y decidió la segunda: el
área es dato maestro configurable, el usuario pertenece a una, y gerente y supervisor se
resuelven por rol **dentro** de esa área.

```
2 de 6  →  5 de 6  →  6 de 6
```

## B.2 Los seis, con su disparador y su área

| Nombre literal (`docs/02 §3.14`) | Disparador | Área |
|---|---|---|
| Registro pendiente de revisión > 24h | 24 h desde la transición, tomada de la auditoría | `lot_id → Lot.area_id` |
| Registro rechazado (notificar al operador) | `review/service.py:409` | ídem |
| Mortalidad > umbral configurable | alerta `high_mortality`, umbral en `settings` | ídem |
| Peso fuera de estándar | alerta `weight_deviation` (`GA-REM-037`) | ídem |
| Error de envío SAP | `PayloadStatus.FAILED` | `ConsolidatedMovement.lot_id` |
| Lote próximo a cierre | `0 <= días hasta `planned_close_date` <= 3` | `Lot.area_id`, directo |

```
6 / 6 disparadores computables · 6 / 6 destinatarios resueltos · 6 / 6 probados
```

## B.3 El modelo de área, y la trampa que evita

```
Role   qué PUEDE hacer el usuario
Area   dónde PERTENECE
```

Se resolvió con `User.area_id` **más** el rol, y **sin** `Area.manager_user_id`. Guardar el
gerente en el área y además poder deducirlo del rol habría creado dos fuentes sin regla de
autoridad entre ellas: el día que discreparan, nadie sabría cuál manda.

Hacen falta las dos condiciones. Un usuario con rol de gerencia y **sin** área no es gerente de
nada, y hay prueba de ello: sin ese filtro, cualquiera con ese nombre de rol recibiría todo lo
de la empresa y el modelo de áreas no serviría para nada.

**El rol de gerencia no se creó.** `docs/02 §6.1` no lo tiene; `GA-REM-034` permite que la
empresa lo cree como dato. Si no existe, nadie entra por ese concepto y nada falla.

## B.4 La fecha prevista, y por qué no se derivó

```
planned_close_date   cuándo se PREVÉ cerrar     nulable, la pone quien planifica
end_date             cuándo se cerró DE VERDAD  intacto — `R-73`, `R-75`
```

No se derivó de la línea genética —`P-03` tiene Cobb, Ross y Hubbard, y ninguna fuente dice que
su curva implique una fecha de cierre—, ni de una edad fija, ni de `ProductivePhase.duration_days`.

Y la condición es una **ventana** `0..3`, no la igualdad `== 3`: con igualdad, el aviso solo
saldría si el evaluador corriera exactamente ese día. Con el sistema apagado no saldría nunca, y
un aviso que no sale es un aviso que no existe.

La idempotencia se ancla a `lot_id + planned_close_date + destinatario`. Una replanificación
real vuelve a avisar —es una situación nueva—; reevaluar la misma, no. Y **las notificaciones
ya emitidas no se borran**: eran evidencia de lo que se sabía entonces.

## B.5 Dos guardas del proyecto obligaron a hacerlo mejor

**`T-025-04`** avisó de que el `TRUNCATE ... CASCADE` de la herramienta de reset vacía toda
tabla que referencie a la truncada, **sin mirar el `ON DELETE`**: borrar las áreas se habría
llevado por delante a los usuarios. La respuesta no fue aflojar la guarda sino clasificar bien —
un organigrama es estructura, no historia operativa ficticia—.

**`R-26`**, en la tanda anterior, prohibió `except Exception` en `main.py`. La tarea de fondo
necesitaba una, y eso señaló que estaba en el archivo equivocado.

## B.6 Y un fallo propio que conviene registrar

`tsc --noEmit` dio **limpio** sobre un `UsersPage.tsx` con elementos JSX adyacentes sin
envolver. La aplicación no arrancaba: 46 pruebas de navegador en rojo, incluidas las de la
suite heredada que no tocan esa pantalla.

```
tsc --noEmit    comprueba tipos        →  pasó
vite build      compila de verdad      →  falló, y dijo el archivo y la posición
```

Un typecheck limpio no es un build correcto. `vite build` pasa a formar parte de la
verificación de frontend, junto a `tsc` y `vitest`.

Merece decirse además que el diagnóstico llevó dos ejecuciones porque una espera activa mía
—un bucle `until` sin pausa— dejó la máquina sin CPU y los navegadores empezaron a caerse por
tiempo de espera. Los dos síntomas se parecían; solo uno era del producto. Se limpiaron los
procesos huérfanos y se repitió en limpio antes de concluir nada.

## B.7 Evidencia

| Nivel | Archivo | Resultado |
|---|---|:--:|
| Áreas como maestro | `backend/tests/test_areas.py` | **5/5** |
| Fecha prevista y ventana de cierre | `backend/tests/test_lot_planned_close.py` | **14/14** |
| Destinatarios, área, deduplicación, tenencia | `backend/tests/test_notification_recipients.py` | **14/14** |
| Bandeja, lectura, aislamiento | `backend/tests/test_notifications.py` | **11/11** |
| Experiencia | `e2e/proceso-p14-notificaciones.spec.ts` | **5/5** `UI_E2E` |
| Campana y estados | `frontend/src/components/notifications/__tests__` | **8/8** |
| Regresión backend | suite completa | **493 passed · 49 skipped** |
| Regresión `E2E` | 17 suites | **129 passed** |
| Regresión `vitest` | suite completa | **82 passed** |
| `tsc --noEmit` · `vite build` | — | **limpios** |
| Paridad `i18n` | `es` / `en` | **940 = 940** |
| Alembic | `o5p6q7r8s9t0` | **cabeza única** |

## B.8 Sensibilidad · `GA-REM-016 AC13`

Seis mutaciones en esta tanda, todas revertidas desde salvaguarda previa:

| # | Mutación | Rompe | Fallos |
|:--:|---|---|:--:|
| 1 | El filtro de área desaparece: cualquier gerente recibe | `AC-A04`, `AC-A10` | 2 |
| 2 | La ventana pasa de 3 a 4 días | `AC-C07` | 1 |
| 3 | Se retira la idempotencia por ocurrencia | `AC-C11`, `AC-C12` | 1 |
| 4 | Se retira la exclusión del lote cerrado | `AC-C09` | 1 |
| 5 | El filtro de empresa desaparece | `AC-A06`, `AC-R08` | 1 |
| 6 | La cuenta de 24 h vuelve a `updated_at` | `AC-T01`, `AC-C16` | 2 |

La sexta es la que más importa: `updated_at` **parece** servir y no sirve. Un evento editado a
las 23 horas reiniciaría la cuenta y no avisaría nunca mientras alguien lo tocara a diario. Hay
prueba dedicada de que editar no reinicia nada.

Tras cada reversión se comprobó, patrón por patrón, que la capacidad sigue existiendo — diez
comprobaciones, no solo `git diff` limpio.

## B.9 El veredicto

```
P-14 = CERTIFIED
```

Los seis eventos que `docs/02 §3.14` enumera tienen disparador computable, destinatarios
resueltos según `OD-08` e integración probada. El canal es interno, como `OD-07` decidió, y no
se introdujo ninguno externo.

## B.10 Lo que queda dicho, y no bloquea

- **Recurrencia del aviso de «> 24h».** Ninguna fuente dice si se repite. Se emite una vez, con
  idempotencia. Es un hueco de requisito registrado, no una decisión nuestra.
- **`R-98`.** El frontend sigue sin modelo de permisos y `P-14` no fue la excepción.
- **`R-99`.** El frontend del entorno compartido sigue por detrás de `main`. La certificación es
  del entorno de certificación aislado; el **runtime compartido** de la interfaz queda
  `NOT VERIFIED` mientras `R-99` siga abierto.
- **`P-08`, `RC-07`, `GA-TD-014`.** Intactos.
