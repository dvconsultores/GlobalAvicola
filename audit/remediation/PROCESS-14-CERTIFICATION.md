# `P-14` · NOTIFICACIONES Y ALERTAS — INFORME DE CERTIFICACIÓN

`docs/02 §3.14` · `docs/10 §6.2` · `GA-REM-038` · `OD-07`

```
P-14  = PARTIAL          el canal existe y funciona; faltan 4 de los 6 tipos normativos
OD-07 = RESOLVED         canal interno / in-app
OD-08 = OWNER_DECISION_REQUIRED
```

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
