# `P-14` · NOTIFICACIONES INTERNAS — QUÉ EXISTE Y QUÉ FALTA

`docs/02 §3.14` · `OD-07` · 2026-09-07 · **antes de tocar código**

Auditoría de lo que el producto ya tiene, hecha con búsqueda sobre `backend/app`, `frontend/src`,
modelos, rutas, servicios, migraciones y suites. Nada aquí se supone: cada fila se comprobó.

---

## 1. Lo primero, porque decide el resto

```
NO existe ninguna infraestructura de notificaciones.
```

La única coincidencia de la palabra en todo `backend/app` es un comentario que dice que `P-14`
no está implementado. En `frontend/src`, ninguna. No hay tabla, ni modelo, ni endpoint, ni
campana, ni bandeja.

Lo que **sí** existe y conviene no confundir con esto:

| Cosa existente | Qué es | Por qué **no** es una notificación |
|---|---|---|
| `Toast` (`frontend/src/components/Toast.tsx`) | aviso efímero en pantalla | vive en la sesión de quien acaba de actuar; no se persiste, no tiene destinatario, no sobrevive a una recarga |
| `OperationalAlert` | alerta operativa del lote | pertenece al **lote**, no a una persona; no tiene destinatario ni estado de lectura |
| `AuditLog` | registro inmutable de qué pasó | es historia del sistema, no bandeja de nadie. `P-09` lo gobierna y reutilizarlo como bandeja mezclaría dos procesos |

## 2. Matriz de capacidades

| Capability | Exists | Correct | Normative | Gap |
|---|:--:|:--:|:--:|---|
| Notification model | **NO** | — | sí · `§3.14` | falta entero |
| Recipient | **NO** | — | sí · `§3.14` («notificar al operador») | falta |
| Tenant scope | parcial | sí | sí · `spec.md §8.14` | el patrón `company_id` existe y se reutiliza; falta aplicarlo |
| Event source | parcial | sí | sí | los disparadores existen (§3 de esta matriz); falta enganchar |
| Unread count | **NO** | — | implícito en «notificaciones» | falta |
| List endpoint | **NO** | — | sí | falta |
| Mark read | **NO** | — | implícito | falta |
| Frontend bell | **NO** | — | sí, para que exista canal interno | falta |
| Notification panel/page | **NO** | — | sí | falta |
| Deep link | parcial | sí | condicional | las rutas destino existen (`/operations/:id`); falta el enlace |
| Realtime/polling | **NO** | — | **no exigido** | no hay WebSocket, SSE ni `react-query`. Ver §5 |
| RBAC | parcial | sí | sí | la propiedad del destinatario es la puerta; **no** hace falta módulo de permiso nuevo |
| E2E | **NO** | — | sí | falta |

## 3. Los disparadores que ya existen

Ninguno hay que construirlo; lo que falta es el enganche.

| Tipo de `§3.14` | Punto exacto del código | ¿Disparador disponible? |
|---|---|:--:|
| Registro rechazado | `app/review/service.py:409` · `reject()`, único sitio que asigna `REJECTED` | **SÍ** |
| Error de envío SAP | `app/integrations/sap/service.py:367,451` · `PayloadStatus.FAILED` | **SÍ** |
| Mortalidad > umbral | `app/operations/service.py:397` · alerta `high_mortality`, umbral en `settings` | **SÍ** |
| Peso fuera de estándar | `app/operations/service.py` · alerta `weight_deviation` (`GA-REM-037`) | **SÍ** |
| Pendiente de revisión > 24 h | — | **NO** · disparador temporal, y no hay planificador |
| Lote próximo a cierre | — | **NO** · disparador temporal, y «próximo» no está definido |

Se buscó explícitamente `apscheduler`, `celery`, `cron`, `schedule` y `BackgroundTasks` en
`backend/` y en las dependencias declaradas. **No hay ninguno.** Los dos tipos temporales no
tienen momento de creación posible sin introducir infraestructura que ninguna fuente pide.

## 4. Destinatarios: dónde está escrito y dónde no

`§14` del encargo es explícito —no vale «todos los administradores»—, así que se separa lo
declarado de lo que habría que inventar. Detalle en `P14_NOTIFICATION_RECIPIENT_MATRIX.md`.

```
DECLARADO   Registro rechazado  →  «notificar al operador»          docs/02 §3.14, literal
DECLARADO   Error de envío SAP  →  «Notificar al rol Analista SAP»  docs/10 §6.2, literal
SIN DEFINIR Mortalidad > umbral →  ninguna fuente dice a quién
SIN DEFINIR Peso fuera de estándar → ninguna fuente dice a quién
SIN DEFINIR Pendiente > 24 h    →  ninguna fuente dice a quién
SIN DEFINIR Lote próximo a cierre → ni destinatario ni qué es «próximo»
```

El rol **`Analista SAP` existe de verdad**: lo crea la migración `l2m3n4o5p6q7` y
`review/service.py:549` ya lo resuelve por nombre. La regla de `docs/10 §6.2` es aplicable tal
como está escrita, sin inventar nada.

`Lot` **no tiene responsable ni supervisor asignado** —sus campos se enumeraron uno a uno—, de
modo que para las alertas operativas no hay persona derivable del dato. Esa es la razón exacta
por la que dos de los seis tipos quedan sin destinatario.

## 5. Realtime: por qué no

`§50`…`§52` del encargo piden auditar antes de introducir nada. El resultado:

```
WebSocket / SSE / Supabase Realtime ......... no existe
react-query / SWR / invalidación de caché ... no existe (axios directo + useState)
```

Y la decisión del propietario exige que la notificación **exista dentro del sistema**, no que
llegue al instante. Introducir un canal en tiempo real sería infraestructura nueva sin
requisito, que es lo que `§27` y `§51` prohíben. El contador se refresca al navegar y con un
sondeo del propio componente, que es lo que la arquitectura vigente permite sin inventarse una.

## 6. Permisos: por qué no hace falta un módulo nuevo

Los módulos del catálogo son `approvals`, `audit`, `corrections`, `dashboard`, `lots`,
`masters`, `operations`, `reports`, `review`, `sap` y `users`. Ninguno cubre notificaciones.

Pero una notificación es **de una persona**, no de un módulo: la puerta es que
`recipient_user_id` coincida con quien pregunta, igual que `/me` o el cambio de contraseña, que
usan `get_current_user` sin permiso de módulo. Añadir un permiso `notifications` obligaría a
tocar la matriz `RBAC` de la migración y a reconciliar los seis roles, con el riesgo que `R-44`
ya costó, para no proteger nada que la propiedad no proteja mejor.

## 7. Superficie de interfaz que se reutiliza

| Pieza | Dónde | Uso |
|---|---|---|
| Cabecera de escritorio | `frontend/src/components/layout/Header.tsx` | alberga la campana |
| Cabecera móvil | mismo archivo, bloque `lg:hidden` | ídem, `§127` |
| `Modal`, `Button`, `EmptyState` | `components/ui` | panel, vacío y error |
| Rutas destino | `/operations/:id`, `/lots/:id` | enlace profundo |
| `i18n` | `public/locales/{es,en}` | paridad obligatoria |
