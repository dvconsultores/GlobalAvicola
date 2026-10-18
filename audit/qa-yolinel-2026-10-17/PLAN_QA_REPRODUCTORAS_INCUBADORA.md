# Plan de pruebas — Reproductoras e Incubadora (ronda QA siguiente)

Ambiente: QA/UAT compartido · Ronda posterior a la revisión QA 2026-10-17

Referencias: `docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md` (usuarios y guía integral), `frontend/src/data/processCatalog.ts` (catálogo real de etapas y eventos), `audit/qa-yolinel-2026-10-17/OPERATION_STATE_MACHINE.md` (máquina de estados del evento operativo).

---

## 1 · Objetivo y alcance

Este plan profundiza las dos cadenas que la guía integral trata de forma resumida: **Reproductoras** (cría y producción) e **Incubadora** (recepción de huevo, incubación, nacimiento y despacho de pollito), más un bloque transversal de interfaz y ciclo de vida del registro.

**Qué se quiere demostrar**

1. Que las reglas de negocio que protegen los datos se cumplen en pantalla y no se pueden saltar (fechas, órdenes de compra, cadena del lote, desglose de la recepción, saldos de población y de huevo).
2. Que la secuencia real de la operación avícola se recorre de punta a punta con los eventos que el sistema ofrece: en Reproductoras desde la llegada de las pollitas hasta el despacho del huevo fértil a la incubadora; en Incubadora desde la recepción del huevo hasta el despacho del pollito a la granja de engorde.
3. Que el flujo de revisión y aprobación (segregación de funciones, devolución, corrección y reverso) se comporta como describe la máquina de estados.
4. Que los listados identifican claramente **de qué granja** es cada registro, **quién lo registró** y **cuándo**, y permiten filtrar por granja.

**Fuera de alcance de esta ronda**

- Integración real con SAP: solo se valida que «Enviado a SAP» y «Confirmado SAP» **no** aparezcan en este ambiente (manual, §1.5).
- Progenitoras y Pollo de Engorde (ya cubiertos en la guía integral, §4.4).
- Pruebas de carga o rendimiento.

---

## 2 · Precondiciones

### 2.1 · Usuarios (manual, §1.2)

| Usuario | Rol | Unidad | Uso en este plan |
|---|---|---|---|
| `qa.operator.breeder` | Operador de Granja | Reproductoras | registra y envía a revisión los casos RP |
| `qa.operator.hatchery` | Operador de Granja | Incubadora | registra y envía a revisión los casos IN |
| `qa.supervisor` | Supervisor Avícola | las 4 | revisa, devuelve, corrige, solicita reversos |
| `qa.approver` | Aprobador | las 4 | aprueba, rechaza, aprueba el reverso |
| `qa.admin` | Super Administrador | las 4 | maestros (desactivar/reactivar) y desbloqueo de segregación |
| `qa.auditor` | Auditor | las 4 | verificación de solo lectura en listados |

Las contraseñas se entregan por separado (manual, §1.1).

### 2.2 · Lotes y granjas

| Cadena | Lote | Uso principal | Granja / galpón |
|---|---|---|---|
| Reproductoras (cría) | `QA-BR-CRIA-001` | cría: alimento, agua, pesaje, vacunación, mortalidad, descarte | `QA-BR-01` / `QA-BR-01-G1` |
| Reproductoras (cría) | `QA-BR-NUEVO-<iniciales>` | recepción de pollitas con orden de compra (crear según manual §4.2) | `QA-BR-01` / `QA-BR-01-G3` |
| Reproductoras (producción) | `QA-BR-PROD-001` | huevo fértil, despacho a incubadora, mortalidad | `QA-BR-01` / `QA-BR-01-G2` |
| Reproductoras (producción) | `QA-BR-PROD-002` | descarte y correcciones | `QA-BR-02` |
| Reproductoras (cría, Cargas Iniciales) | `QA-CUT-BR-001` | solo lectura: datos desconocidos, no usar para escritura | `QA-BR-02` |
| Incubadora | `QA-HAT-REC-001` | recepción y clasificación de huevo | planta `QA-INC-F1` |
| Incubadora | `QA-HAT-INC-001` | carga / transferencia a nacedora | `QA-INC-F1` |
| Incubadora | `QA-HAT-OVO-001` | ovoscopía | `QA-INC-F1` |
| Incubadora | `QA-HAT-NAC-001` | nacimiento | `QA-INC-F1` |
| Incubadora | `QA-HAT-BIRTH-001` | pollitos por despachar | `QA-INC-F1` |
| Incubadora | `QA-HAT-CHICK-001` | ciclo ya despachado (solo lectura / referencia) | `QA-INC-F1` |
| Pollo de Engorde | `QA-BRO-001` | destino del despacho de pollito | `QA-EN-01` |

Máquinas de incubación: **QA Incubadora A1** (activa), **QA Nacedora N1** (activa) y **QA Incubadora A4 (inactiva)** para el caso negativo.

### 2.3 · Órdenes de compra sintéticas necesarias

Si no existen en el ambiente, créelas antes de la ronda (con `qa.supervisor` o `qa.admin`, según permiso de maestros) y anote el código exacto en la evidencia:

| Código de OC | Contenido | Uso |
|---|---|---|
| `QA-OC-BR-AVES-001` | aves, cadena **Reproductoras**, límite 12 000 | RP-01 |
| `QA-OC-BR18-BR-TEST` | aves, cadena **Reproductoras**, límite **10 000** | RP-03 |
| `QA-OC-BR-CROSS-001` | aves con centros SAP de la cadena **Incubadora** | RP-02 |
| `QA-OC-BR-SINC-001` | aves **sin cadena** (sin centros SAP asociados) | RP-02 (control, debe permitirse) |

### 2.4 · Aviso sobre el juego de datos

El juego de datos **QA-DEMO-V1** (25 lotes, más de 360 registros y los usuarios de la tabla 2.1) **puede no estar cargado** en el ambiente al momento de la ronda. QA debe confirmarlo con el equipo del proyecto antes de empezar:

- **Si está cargado**: ejecutar el plan tal cual, con los lotes de la tabla 2.2.
- **Si no está cargado**: crear manualmente, antes de la ronda y con `qa.supervisor` / `qa.admin`, (a) las granjas y galpones de la tabla 2.2, (b) los lotes de Reproductoras e Incubadora en la fase indicada, (c) las máquinas de incubación activas y la inactiva, y (d) las OC de la tabla 2.3. En este escenario los casos se ejecutan **en el orden del plan**, porque cada uno genera el saldo que consume el siguiente (el despacho de huevo de RP-13 alimenta el huevo que recibe IN-01). Anote en cada resultado si el lote fue preexistente o creado en la ronda.

---

## 3 · Convenciones

### 3.1 · Identificador de caso

`<CADENA>-<NN>`: `RP` = Reproductoras, `IN` = Incubadora, `TR` = transversal (por ejemplo `RP-05`, `IN-03`, `TR-02`). Cada caso se reporta individualmente; si un caso tiene variantes negativas, se indica cuál falló («RP-03 variante b»).

### 3.2 · Prioridad

| Prioridad | Significado | Efecto si falla |
|---|---|---|
| **Alta** | regla de negocio que impide datos incorrectos, o bloqueo del flujo | detiene la ronda; se reporta de inmediato |
| **Media** | funcionalidad principal sin riesgo de dato incorrecto | se reporta y se continúa |
| **Baja** | cosmético, textos, orden de columnas | se acumula para el informe |

### 3.3 · Resultado esperado y registro

Un «Resultado esperado» que no se cumple **es un hallazgo**, aunque la pantalla «parezca funcionar». Registre usuario, pantalla, lote, datos usados, fecha y hora, y captura de pantalla (plantilla en la sección 8).

### 3.4 · Estados del registro y reglas verificadas

`draft` (Borrador) → `registered` (Registrado) → `pending_review` (Pendiente de revisión) → `in_review` (En revisión) → `returned` (Devuelto) → `corrected` (Corregido/Validado) → `approved` (Aprobado) o `rejected` (Rechazado) → `consolidated` (Consolidado). Además: `cancelled` (Cancelado) y `reversed` (Revertido).

- Reenviar a revisión solo es posible desde `registered`, `returned` o `rejected`.
- Corregir deja el registro en `corrected`, pendiente de aprobación (valor original, valor corregido, motivo y autor).
- Iniciar revisión solo desde `pending_review`; devolver con observaciones solo desde `in_review`.
- Con **un nivel** de aprobación, «completar revisión» aprueba; con **dos o más niveles**, deja el registro en `corrected` a la espera del aprobador.
- **Rechazo** solo desde `corrected` (o `in_review` en configuración de un nivel), con motivo obligatorio y notificación al operador que registró.
- **Cancelación** no es posible en `approved`, `consolidated`, `reversed` ni en estados posteriores a SAP.
- **Reverso** solo de un registro `approved`, mediante contrapartida que también debe aprobarse; un segundo reverso del mismo registro se rechaza; los registros de huevo e incubación **no admiten reverso** (manual, §5.3).
- Los estados `sent_to_sap` / confirmado SAP no se ejercitan en este ambiente.
## 4 · Casos — Reproductoras

Todos los casos se ejecutan en **Gestión Avícola → Reproductoras**, seleccionando el lote y pulsando
**Registrar operación**. Usuarios (definidos en §2): `qa.operator.breeder` (registra), `qa.supervisor`
(revisa/devuelve/corrige), `qa.approver` (aprueba/rechaza), `qa.admin`, `qa.auditor`.
Lotes (definidos en §2): `QA-BR-CRIA-001` (cría, granja `QA-BR-01`, galpón `QA-BR-01-G1`),
`QA-BR-NUEVO-<iniciales>` (cría, lote nuevo, galpón `QA-BR-01-G3`, para recepciones), `QA-BR-PROD-001`
(producción, granja `QA-BR-01`, galpón `QA-BR-01-G2`), `QA-BR-PROD-002` (producción, granja `QA-BR-02`).
Órdenes de compra sintéticas (definidas en §2): `QA-OC-BR-AVES-001` (Reproductoras, límite 12 000),
`QA-OC-BR18-BR-TEST` (Reproductoras, límite 10 000), `QA-OC-BR-CROSS-001` (centros SAP de la cadena
Incubadora), `QA-OC-BR-SINC-001` (sin cadena).

Eventos válidos (los únicos nombres que deben aparecer en la UI):

- **Reproductoras–Cría** (`breeder_rearing`): «Inspección de granja», «Recepción de aves», «Distribución a
  galpones», «Alimento», «Agua», «Pesaje», «Vacunación», «Medicación», «Mortalidad», «Descarte»,
  «Salida/traslado a producción».
- **Reproductoras–Producción** (`breeder_production`): los diarios y sanitarios anteriores más «Recolección de
  huevo» (tipo, cantidad, peso), «Despacho de huevo a incubadora», «Traslado de aves», «Inspección de
  transporte», «Salida/traslado a producción».
- «Recepción de aves» y «Distribución a galpones» **solo** existen en Cría; «Recolección de huevo» y «Despacho
  de huevo a incubadora» **solo** en Producción.

Reglas ejercitadas: **BR-06** (el evento no puede ser anterior a la activación del lote), **BR-18** (acumulado
recibido ≤ límite de la OC), **BR-19** (período abierto: no más de 90 días atrás y fecha del evento no futura;
el selector de fecha limita con `max = hoy`), **BR-20** (la recepción de reproductoras exige total recibido,
muertas a la llegada y rechazadas a la llegada; viable = total − muertas − rechazadas), **BR-23 (nueva)** (una
OC cuya cadena no coincide con la del lote se rechaza con mensaje claro; el selector solo ofrece OC de la
cadena del lote o sin cadena) y **BR-14/RR-03** (segregación de funciones: quien registró no puede revisar ni
aprobar su propio registro).
Ciclo de estados de referencia: **Registrado → Pendiente de revisión → Revisado → Aprobado**; el revisor puede
**Devolver**; el **rechazo solo procede desde Corregido**; **no se puede cancelar** desde Aprobado en adelante.

En todos los casos la comprobación final en **Historial** se hace sobre las columnas
**Lote · Granja · Fecha del evento · Registrado por · Fecha de registro**.

---

### RP-01 · Recepción de aves con OC válida (desglose completo)

- **Precondición:** lote `QA-BR-NUEVO-<iniciales>` activo hoy en granja `QA-BR-01`, galpón `QA-BR-01-G3`,
  etapa Cría; OC `QA-OC-BR-AVES-001` (Reproductoras, límite 12 000) con 0 aves recibidas acumuladas; sesión
  con `qa.operator.breeder`.
- **Pasos:**
  1. Gestión Avícola → Reproductoras → lote `QA-BR-NUEVO-<iniciales>` → **Registrar operación**.
  2. Elegir evento **«Recepción de aves»**.
  3. Fecha del evento = hoy (valor por defecto).
  4. OC = `QA-OC-BR-AVES-001`; comprobar que el selector solo ofrece OC de la cadena del lote o sin cadena.
  5. Total recibido = `6000`; Muertas a la llegada = `40`; Rechazadas a la llegada = `60`.
  6. Comprobar el viable calculado por la UI (debe mostrar `5900`).
  7. Guardar y confirmar.
  8. Ir a **Historial** del lote y localizar la fila.
- **Datos:** OC `QA-OC-BR-AVES-001`; total `6000`; muertas `40`; rechazadas `60`; viable esperado `5900`;
  fecha del evento = hoy.
- **Resultado esperado:** el registro se guarda en estado **Registrado** con la etiqueta «Recepción de aves»;
  el viable mostrado y persistido es **5 900**; el acumulado recibido de `QA-OC-BR-AVES-001` queda en `6000`
  (≤ 12 000); no aparecen errores de validación. En **Historial**: Lote `QA-BR-NUEVO-<iniciales>`,
  Granja `QA-BR-01`, Fecha del evento = hoy, Registrado por `qa.operator.breeder`, Fecha de registro = hoy con
  la hora del sistema.
- **Regla:** BR-20 (desglose obligatorio y cálculo del viable) + BR-18 (acumulado dentro del límite) + BR-06
  (fecha ≥ activación).
- **Prioridad:** Alta.

---

### RP-02 · OC de otra cadena ⇒ rechazo BR-23 (con control de OC sin cadena)

- **Precondición:** lote `QA-BR-NUEVO-<iniciales>` de la cadena **Reproductoras**; `QA-OC-BR-CROSS-001`
  pertenece a centros SAP de la cadena **Incubadora**; `QA-OC-BR-SINC-001` no tiene cadena; sesión con
  `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → `QA-BR-NUEVO-<iniciales>` → **Registrar operación** → «Recepción de aves».
  2. Abrir el selector de OC y anotar qué OC se ofrecen: **no** debe aparecer `QA-OC-BR-CROSS-001`; sí deben
     aparecer las de la cadena del lote y `QA-OC-BR-SINC-001`.
  3. Forzar el caso negativo: enviar la petición con OC `QA-OC-BR-CROSS-001` (reutilizando una petición válida
     editada desde las herramientas del navegador) y guardar.
  4. Leer el mensaje de error devuelto.
  5. Repetir el alta con OC `QA-OC-BR-SINC-001` (total `1000`, muertas `0`, rechazadas `0`) y guardar.
  6. Ir a **Historial** del lote.
- **Datos:** OC cruzada `QA-OC-BR-CROSS-001` (cadena Incubadora) frente a lote de Reproductoras; OC de control
  `QA-OC-BR-SINC-001`; total `1000`, muertas `0`, rechazadas `0`.
- **Resultado esperado:** el intento con `QA-OC-BR-CROSS-001` se **rechaza** (HTTP 4xx) con un mensaje claro
  que indica que la cadena de la OC no coincide con la del lote; no se crea registro. El selector solo ofrece
  OC de la cadena del lote o sin cadena. El intento con `QA-OC-BR-SINC-001` **sí se permite** y queda en estado
  **Registrado**. En **Historial** aparece **una sola** fila de recepción: Lote `QA-BR-NUEVO-<iniciales>`,
  Granja `QA-BR-01`, Fecha del evento = hoy, Registrado por `qa.operator.breeder`, Fecha de registro = hoy.
- **Regla:** BR-23 (nueva) — validación de cadena OC ↔ lote, con selector filtrado y mensaje explícito.
- **Prioridad:** Alta.

---

### RP-03 · Recepción que excede el límite de la OC (acumulado BR-18)

- **Precondición:** OC `QA-OC-BR18-BR-TEST` (Reproductoras, límite `10 000`) con `0` aves recibidas; lote
  `QA-BR-NUEVO-<iniciales>` activo; sesión con `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → `QA-BR-NUEVO-<iniciales>` → **Registrar operación** → «Recepción de aves».
  2. OC = `QA-OC-BR18-BR-TEST`; total `8000`, muertas `10`, rechazadas `10`; guardar.
  3. Verificar que el registro se crea (acumulado `8000` ≤ `10 000`).
  4. Registrar una **segunda** recepción con la misma OC: total `3000`, muertas `0`, rechazadas `0`; guardar.
  5. Leer el mensaje de error.
  6. Consultar el acumulado de la OC (vista de OC o resumen de recepciones).
  7. Ir a **Historial** del lote.
- **Datos:** 1.ª recepción `8000/10/10`; 2.ª recepción `3000/0/0`; acumulado pretendido `11 000` > límite
  `10 000`.
- **Resultado esperado:** la 1.ª recepción se guarda (**Registrado**) y el acumulado queda en `8000`. La 2.ª
  recepción se **rechaza** con error de límite de OC (BR-18) que muestra el acumulado (`8000`) frente al límite
  (`10 000`), sin crear registro ni alterar el acumulado, que permanece en `8000`. En **Historial** hay
  exactamente una fila de recepción con OC `QA-OC-BR18-BR-TEST`: Lote `QA-BR-NUEVO-<iniciales>`,
  Granja `QA-BR-01`, Fecha del evento = hoy, Registrado por `qa.operator.breeder`, Fecha de registro = hoy.
- **Regla:** BR-18 (acumulado recibido ≤ límite de la OC, validado sobre la suma histórica y no solo sobre el
  envío actual).
- **Prioridad:** Alta.

---

### RP-04 · Recepción sin desglose de muertas/rechazadas ⇒ error BR-20

- **Precondición:** lote `QA-BR-NUEVO-<iniciales>`; OC `QA-OC-BR-AVES-001`; sesión con `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → `QA-BR-NUEVO-<iniciales>` → **Registrar operación** → «Recepción de aves».
  2. OC = `QA-OC-BR-AVES-001`; total recibido `2000`.
  3. Dejar **vacíos** Muertas a la llegada y Rechazadas a la llegada; guardar.
  4. Repetir dejando muertas y rechazadas en `0` pero vaciando el total recibido; guardar.
  5. Repetir con total `1000`, muertas `700`, rechazadas `400` (viable negativo); guardar.
  6. Leer los mensajes de error de cada intento.
  7. Ir a **Historial** del lote.
- **Datos:** intento A `2000 / vacío / vacío`; intento B `vacío / 0 / 0`; intento C `1000 / 700 / 400`.
- **Resultado esperado:** los tres intentos se **rechazan** con error de validación BR-20: el desglose (total,
  muertas, rechazadas) es obligatorio y el viable no puede ser negativo; los campos faltantes se marcan en el
  formulario. No se crea ningún registro. En **Historial** no aparece ninguna fila nueva para el lote (Lote,
  Granja, Fecha del evento, Registrado por, Fecha de registro sin cambios respecto al estado previo).
- **Regla:** BR-20 (desglose obligatorio; viable = total − muertas − rechazadas ≥ 0).
- **Prioridad:** Alta.

---



### RP-05 · Fecha futura bloqueada

- **Precondición:** sesión iniciada como `qa.operator.breeder`; lote `QA-BR-CRIA-001` con período abierto; pantalla Reproductoras → lote → **Registrar operación** disponible.
- **Pasos:**
  1. Abrir el formulario con tipo de evento `bird_reception` («Recepción de aves»).
  2. Desplegar el selector de **fecha del evento** y comprobar el día de mañana.
  3. Intentar seleccionar la fecha de mañana desde el selector.
  4. Escribir a mano la fecha de mañana en el campo (si admite tecleo) y confirmar con **Registrar**.
  5. Repetir los pasos 1–4 con el tipo de evento `feed_registration` («Alimento»).
- **Datos:** fecha del evento = `hoy + 1 día` (p. ej. si se ejecuta el 2026-10-17, usar 2026-10-18); resto de campos con valores válidos (aves viables 5 900 / alimento 3 800 kg, 95 sacos).
- **Resultado esperado:** el selector no ofrece el día de mañana (máximo = hoy); si la fecha se teclea, al guardar aparece un mensaje de error de validación claro y no se crea ningún registro. **Historial** permanece sin fila nueva: no debe aparecer ninguna fila con **Fecha del evento** posterior a hoy para el lote `QA-BR-CRIA-001`; la última fila visible sigue siendo la existente con su **Lote**, **Granja** `QA-BR-01`, **Fecha del evento**, **Registrado por** y **Fecha de registro** sin cambios.
- **Regla:** BR-19 — la fecha del evento no puede ser futura (selector con máximo hoy) y el período abierto debe ser ≤90 días.
- **Prioridad:** Alta.

### RP-06 · Fecha anterior a la activación del lote

- **Precondición:** lote `QA-BR-NUEVO-<iniciales>` creado y recibido hoy en RP-01 (cría, granja `QA-BR-01`, galpón `QA-BR-01-G3`), con fecha de activación = hoy; período abierto. Sesión como `qa.operator.breeder`.
- **Pasos:**
  1. Entrar a Reproductoras → lote `QA-BR-NUEVO-<iniciales>` → **Registrar operación**.
  2. Elegir tipo de evento `feed_registration` («Alimento»).
  3. Ingresar cantidad de alimento válida (p. ej. 500 kg / 13 sacos), tipo de alimento «QA Iniciador» y **fecha del evento = ayer**.
  4. Confirmar con **Registrar**.
  5. Control: repetir los pasos 2–4 con **fecha del evento = hoy**.
- **Datos:** fecha del evento del intento negativo = `hoy - 1 día` (p. ej. 2026-10-16 si se ejecuta el 2026-10-17); fecha del control = hoy.
- **Resultado esperado:** en el paso 4 el sistema muestra un error claro que referencia **BR-06** (evento no anterior a la activación del lote) y no se crea el registro. En el paso 5 el registro se confirma con estado **Registrado**. **Historial:** tras el intento negativo no debe aparecer fila con **Fecha del evento** = ayer; tras el control aparece exactamente una fila nueva con **Lote** `QA-BR-NUEVO-<iniciales>`, **Granja** `QA-BR-01`, **Fecha del evento** = hoy, **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual.
- **Regla:** BR-06 — el evento no puede ser anterior a la activación del lote (en combinación con BR-19: fecha no futura y período ≤90 días).
- **Prioridad:** Alta.

### RP-07 · Distribución a galpones

- **Precondición:** lote `QA-BR-NUEVO-<iniciales>` recibido en RP-01 con **5 900 aves viables**; galpón destino `QA-BR-01-G3` dado de alta en granja `QA-BR-01`. Sesión como `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → lote `QA-BR-NUEVO-<iniciales>` → **Registrar operación**.
  2. Elegir tipo de evento `bird_distribution` («Distribución a galpones»), fecha del evento = hoy.
  3. Distribuir cantidades entre galpones cuya suma sea exactamente **5 900** (una sola línea a `QA-BR-01-G3` con 5 900, o varias líneas que sumen 5 900) y confirmar con **Registrar**.
  4. Abrir un nuevo formulario `bird_distribution` e ingresar **6 000** en `QA-BR-01-G3`; confirmar con **Registrar**.
- **Datos:** distribución válida = 5 900 aves a `QA-BR-01-G3`; intento inválido = 6 000 aves (excede en 100 los viables del lote).
- **Resultado esperado:** el paso 3 se confirma como registrado y en **Historial** aparece una fila con **Lote** `QA-BR-NUEVO-<iniciales>`, **Granja** `QA-BR-01`, **Fecha del evento** = hoy, evento «Distribución a galpones», **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual. En el paso 4 el sistema rechaza el exceso (error de validación o aviso bloqueante de cantidad mayor a las aves viables) y no crea registro; si el sistema acepta 6 000 y lo registra, **se reporta como hallazgo** con severidad Alta y el ID/URL del registro creado.
- **Regla:** BR-19 (fecha no futura, período ≤90 días) y control de consistencia de cantidades distribuidas frente a aves viables del lote.
- **Prioridad:** Media.

### RP-08 · Registro de alimento

- **Precondición:** lote `QA-BR-CRIA-001` (cría, granja `QA-BR-01`, galpón `QA-BR-01-G1`) con período abierto; catálogo de tipos de alimento con «QA Iniciador» disponible. Sesión como `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → lote `QA-BR-CRIA-001` → **Registrar operación**.
  2. Elegir tipo de evento `feed_registration` («Alimento»), fecha del evento = hoy.
  3. Ingresar 3 800 kg, 95 sacos y tipo de alimento «QA Iniciador»; confirmar con **Registrar**.
  4. Abrir un nuevo formulario `feed_registration` e ingresar **−100 kg** (kilogramos negativos) con el resto de campos válidos; confirmar con **Registrar**.
- **Datos:** registro válido = 3 800 kg / 95 sacos / «QA Iniciador»; registro inválido = −100 kg (mismo tipo de alimento, fecha hoy).
- **Resultado esperado:** el paso 3 se confirma como registrado y en **Historial** aparece una fila con **Lote** `QA-BR-CRIA-001`, **Granja** `QA-BR-01`, **Fecha del evento** = hoy, evento «Alimento», **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual; al abrir el detalle se muestran 3 800 kg, 95 sacos y «QA Iniciador» sin alteraciones. En el paso 4 el sistema muestra error de validación de cantidad (kg negativo) y no crea registro, por lo que **Historial** no gana ninguna fila adicional.
- **Regla:** BR-19 (fecha del evento no futura, período abierto ≤90 días) y validación de cantidades no negativas en el registro de alimento.
- **Prioridad:** Media.

### RP-09 · Registro de agua

- **Precondición:** lote `QA-BR-CRIA-001` (cría, granja `QA-BR-01`, galpón `QA-BR-01-G1`) con período abierto. Sesión como `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → lote `QA-BR-CRIA-001` → **Registrar operación**.
  2. Elegir tipo de evento `water_consumption` («Agua»), fecha del evento = hoy.
  3. Ingresar 12 000 litros y confirmar con **Registrar**.
  4. Abrir un nuevo formulario `water_consumption`, ingresar **0 litros** y confirmar con **Registrar**.
  5. Repetir el paso 4 con **−500 litros**.
- **Datos:** registro válido = 12 000 litros; registros inválidos = 0 litros y −500 litros (fecha del evento = hoy en los tres intentos).
- **Resultado esperado:** el paso 3 se confirma como registrado y en **Historial** aparece una fila con **Lote** `QA-BR-CRIA-001`, **Granja** `QA-BR-01`, **Fecha del evento** = hoy, evento «Agua», **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual, mostrando 12 000 litros en el detalle. En los pasos 4 y 5 el sistema muestra error de validación (el consumo debe ser mayor que cero) y no crea registro, de modo que **Historial** no gana filas con valor 0 o negativo.
- **Regla:** BR-19 (fecha del evento no futura, período abierto ≤90 días) y validación de volumen de agua mayor que cero.
- **Prioridad:** Baja.



### RP-10 · Mortalidad y descarte reducen la población y disparan alerta

- **Precondición:** lote `QA-BR-CRIA-001` (cría, granja `QA-BR-01`, galpón `QA-BR-01-G1`) con período abierto y población actual conocida (anotarla antes de empezar: **P0**). Sesión como `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → lote `QA-BR-CRIA-001` → **Registrar operación**; evento `mortality_recording` («Mortalidad»), fecha del evento = hoy.
  2. Registrar **25** aves muertas con causa «QA Ahogamiento» y confirmar.
  3. Nuevo formulario `cull_recording` («Descarte»): registrar **10** aves descartadas (motivo «QA Descarte sanitario»); confirmar.
  4. Consultar la población/cabezas del lote en la ficha del lote y anotarla (**P1**).
  5. Nuevo formulario `mortality_recording` con **600** aves muertas (causa «QA Ahogamiento»); confirmar.
- **Datos:** mortalidad 25 (causa «QA Ahogamiento»); descarte 10; segundo registro de mortalidad 600; fecha del evento = hoy en los tres casos.
- **Resultado esperado:** pasos 2 y 3 quedan en estado **Registrado** y la población pasa de **P0** a **P1 = P0 − 35** (verificar en la ficha del lote). El paso 5 registra el evento y muestra/expone una **alerta de mortalidad crítica** (banner, aviso o indicador de umbral) visible para el usuario y en el detalle del registro. **Historial:** tres filas nuevas con **Lote** `QA-BR-CRIA-001`, **Granja** `QA-BR-01`, **Fecha del evento** = hoy, eventos «Mortalidad» (25), «Descarte» (10) y «Mortalidad» (600), **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual; el contador de aves ya no coincide con la suma de eventos de población.
- **Regla:** mortalidad y descarte reducen la población del lote y disparan alerta al superar el umbral; estados Registrado → Pendiente de revisión.
- **Prioridad:** Alta.

### RP-11 · Pesaje semanal: registro válido y alerta por desvío de curva

- **Precondición:** lote `QA-BR-CRIA-001` (cría, granja `QA-BR-01`, galpón `QA-BR-01-G1`) con período abierto y curva genética de referencia cargada. Sesión como `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → lote `QA-BR-CRIA-001` → **Registrar operación**; evento `weight_recording` («Pesaje»), fecha del evento = hoy.
  2. Ingresar **30** aves muestreadas y peso promedio **760 g**; confirmar.
  3. Abrir un nuevo formulario `weight_recording`: **30** aves muestreadas y peso promedio **300 g**; confirmar.
  4. Revisar la alerta mostrada en el segundo registro y comprobar que el evento sí quedó guardado (abrir su detalle).
- **Datos:** pesaje válido = 30 aves / 760 g; pesaje desviado = 30 aves / 300 g; fecha del evento = hoy en ambos.
- **Resultado esperado:** el paso 2 queda en estado **Registrado** sin alerta. El paso 3 se guarda igualmente (la alerta **no bloquea** el registro) y muestra un aviso de **desvío respecto de la curva genética** (peso por debajo del rango esperado); el detalle conserva 30 aves y 300 g sin alteraciones. **Historial:** dos filas nuevas con **Lote** `QA-BR-CRIA-001`, **Granja** `QA-BR-01`, **Fecha del evento** = hoy, evento «Pesaje», **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual; los valores 760 g y 300 g se muestran tal cual en cada fila.
- **Regla:** el pesaje registra aves muestreadas y peso promedio (g) y alerta cuando se desvía de la curva genética, sin bloquear el guardado.
- **Prioridad:** Media.

### RP-12 · Vacunación y medicación (dosis por ave y días de tratamiento)

- **Precondición:** lote `QA-BR-CRIA-001` (cría, granja `QA-BR-01`, galpón `QA-BR-01-G1`) con período abierto; catálogos con vacuna «QA Newcastle» y medicamento «QA Amoxicilina» disponibles. Sesión como `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → lote `QA-BR-CRIA-001` → **Registrar operación**; evento `vaccination` («Vacunación»), fecha del evento = hoy.
  2. Seleccionar vacuna «QA Newcastle», **5 900** aves vacunadas y confirmar.
  3. Nuevo formulario `medication` («Medicación»): medicamento «QA Amoxicilina», **dosis por ave 0.5**, **5 días** de tratamiento; confirmar.
  4. Nuevo formulario `medication` con «QA Amoxicilina», **dosis por ave 0**, 5 días de tratamiento; confirmar.
- **Datos:** vacunación = «QA Newcastle» / 5 900 aves; medicación válida = «QA Amoxicilina» / dosis por ave 0.5 / 5 días; medicación inválida = dosis por ave 0.
- **Resultado esperado:** pasos 2 y 3 quedan en estado **Registrado** y sus detalles muestran exactamente los valores ingresados (5 900 aves; dosis 0.5 y 5 días). El paso 4 muestra error de validación de dosis (valor mayor que 0 obligatorio) y no crea registro. **Historial:** dos filas nuevas (una «Vacunación» y una «Medicación») con **Lote** `QA-BR-CRIA-001`, **Granja** `QA-BR-01`, **Fecha del evento** = hoy, **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual; el intento con dosis 0 no agrega fila.
- **Regla:** la medicación exige dosis por ave y días de tratamiento válidos (> 0); estado inicial Registrado → Pendiente de revisión.
- **Prioridad:** Media.

### RP-13 · Recolección y despacho de huevo fértil a la incubadora

- **Precondición:** lote `QA-BR-PROD-001` (producción, granja `QA-BR-01`, galpón `QA-BR-01-G2`) con período abierto; planta de incubación destino `QA-INC-F1` dada de alta. Sesión como `qa.operator.breeder`.
- **Pasos:**
  1. Reproductoras → lote `QA-BR-PROD-001` → **Registrar operación**; evento `egg_collection` («Recolección de huevo»), fecha del evento = hoy.
  2. Registrar tipo «huevo fértil», cantidad **5 200** y peso promedio **62 g**; confirmar.
  3. Nuevo formulario `egg_dispatch` («Despacho de huevo a incubadora»): destino `QA-INC-F1`, cantidad **5 000**, fecha del evento = hoy; confirmar.
  4. Consultar el saldo de huevo disponible del lote y anotarlo.
  5. Nuevo formulario `egg_dispatch` con destino `QA-INC-F1`, cantidad **6 000** (excede el saldo); confirmar.
  6. Verificar el caso relacionado **IN-01** en la planta `QA-INC-F1`.
- **Datos:** recolección 5 200 huevos fértiles / 62 g; despacho válido 5 000 a `QA-INC-F1`; despacho inválido 6 000 (saldo disponible 200).
- **Resultado esperado:** pasos 2 y 3 en estado **Registrado**; el saldo del paso 4 es **200** huevos. El paso 5 se rechaza por **saldo insuficiente** con mensaje claro y sin crear registro; si el sistema lo acepta, **se reporta como hallazgo** de severidad Alta con ID/URL del registro creado. **Historial:** dos filas nuevas con **Lote** `QA-BR-PROD-001`, **Granja** `QA-BR-01`, **Fecha del evento** = hoy, eventos «Recolección de huevo» (5 200) y «Despacho de huevo a incubadora» (5 000), **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual; no aparece fila por el intento de 6 000. El despacho aprobado debe reflejarse como insumo del caso **IN-01**.
- **Regla:** `egg_collection` y `egg_dispatch` solo aplican en Producción; el despacho no puede exceder el saldo recolectado del lote.
- **Prioridad:** Alta.

### RP-14 · Envío a revisión, segregación de funciones y devolución

- **Precondición:** registro `egg_dispatch` de RP-13 creado por `qa.operator.breeder` en lote `QA-BR-PROD-001` (granja `QA-BR-01`) en estado **Registrado**; usuarios `qa.supervisor` y `qa.approver` disponibles.
- **Pasos:**
  1. Como `qa.operator.breeder`, enviar el registro de RP-13 a revisión desde el detalle (**Enviar a revisión**) y comprobar el estado **Pendiente de revisión**.
  2. Sin cerrar sesión, abrir **Centro de Revisión** e intentar abrir/revisar ese mismo registro; anotar el resultado.
  3. Iniciar sesión como `qa.supervisor`, abrir **Centro de Revisión** y aplicar el filtro **Granja = `QA-BR-01`**.
  4. Revisar el registro y usar **Devolver** con la observación «corregir peso».
  5. Como `qa.operator.breeder`, abrir el registro devuelto, corregir el peso, guardar y **reenviar** a revisión.
  6. Como `qa.supervisor`, revisar de nuevo y marcar **Revisado**.
  7. Como `qa.approver`, aprobar el registro (**Aprobado**).
  8. En **Centro de Revisión** y en **Aprobaciones**, verificar las columnas **Lote**, **Granja**, **Fecha del evento**, **Registrado por** y **Fecha de registro**, y el filtro Granja; dejar la pantalla abierta 60 s observando recargas.
- **Datos:** filtro Granja = `QA-BR-01`; observación de devolución «corregir peso»; peso corregido con un valor válido (p. ej. 63 g promedio).
- **Resultado esperado:** en el paso 2 el acceso queda **bloqueado por segregación** (error explícito; quien registró no puede revisar ni aprobar) y el registro permanece en **Pendiente de revisión**. El ciclo Devuelto → corregido → reenviado → **Revisado** → **Aprobado** se completa sin errores; el registro devuelto muestra la observación «corregir peso». En **Centro de Revisión** y **Aprobaciones** se ven las filas del lote `QA-BR-PROD-001` con **Granja** `QA-BR-01`, **Fecha del evento** = hoy, **Registrado por** `qa.operator.breeder` y **Fecha de registro** = hoy/hora actual, y el filtro Granja devuelve solo registros de `QA-BR-01`. Durante 60 s la pantalla **no recarga en bucle** (sin parpadeo ni peticiones repetidas continuas).
- **Regla:** BR-14 / RR-03 — segregación de funciones (quien registró no revisa ni aprueba); estados Registrado → Pendiente de revisión → Devuelto → Revisado → Aprobado.
- **Prioridad:** Alta.

## 5 · Casos — Incubadora

### IN-01 · Recepción en planta del huevo fértil despachado en RP-13

- **Precondición:** sesión con `qa.operator.hatchery`; planta `QA-INC-F1`; el lote `QA-HAT-REC-001` existe y está activo; el despacho de RP-13 (5 000 huevos fértiles desde `QA-BR-PROD-001`) figura como recibible.
- **Pasos:**
  1. Entrar a Gestión Avícola → Incubadora → `QA-HAT-REC-001` → Registrar operación.
  2. Registrar primero `transport_inspection` («Inspección de transporte») del vehículo que trasladó la carga de RP-13, con fecha de hoy.
  3. Registrar `egg_reception_hatchery` («Recepción de huevo en planta») con cantidad 5 000 y fecha del evento = hoy.
  4. Guardar y abrir el Historial del lote.
- **Datos:** lote `QA-HAT-REC-001`; planta `QA-INC-F1`; cantidad recibida 5 000; origen RP-13 (`QA-BR-PROD-001`); fecha del evento = hoy; usuario `qa.operator.hatchery`.
- **Resultado esperado:** ambas operaciones se guardan sin error; el saldo recibido del lote queda en 5 000, igual a lo despachado en RP-13 (cuadre de cantidades). El Historial muestra dos filas, una por evento, con las columnas Lote = `QA-HAT-REC-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento = hoy, Registrado por = `qa.operator.hatchery`, Fecha de registro = hoy.
- **Regla:** BR-19 (fecha no futura, ≤90 días), BR-06 (no anterior a la activación del lote), trazabilidad RP-13 → recepción en planta.
- **Prioridad:** Alta.

### IN-02 · Clasificación del huevo recibido: 4 700 incubables / 300 no incubables

- **Precondición:** IN-01 registrado; saldo recibido del lote `QA-HAT-REC-001` = 5 000.
- **Pasos:**
  1. Incubadora → `QA-HAT-REC-001` → Registrar operación → `egg_reception_classification` («Clasificación del huevo recibido»).
  2. Ingresar incubables 4 700 y no incubables 300, con fecha del evento = hoy.
  3. Guardar y revisar el saldo del lote.
  4. Intentar una segunda clasificación con incubables 4 700 y no incubables 400 (suma 5 100 > 5 000 recibidos).
  5. Guardar el segundo intento.
- **Datos:** lote `QA-HAT-REC-001`; incubables 4 700; no incubables 300 (suma 5 000 = recibido); intento inválido incubables 4 700 + no incubables 400; fecha del evento = hoy; usuario `qa.operator.hatchery`.
- **Resultado esperado:** el paso 3 se guarda; el saldo incubable del lote queda en 4 700 y el no incubable en 300, con suma exacta 5 000 sin exceder lo recibido. El paso 5 se bloquea con mensaje de validación: la suma clasificada no puede exceder los 5 000 recibidos; no se crea ninguna fila nueva en el Historial para el intento inválido. El Historial muestra la fila de clasificación con Lote = `QA-HAT-REC-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento = hoy, Registrado por = `qa.operator.hatchery`, Fecha de registro = hoy.
- **Regla:** BR-19, BR-06, cuadre de cantidades (clasificado ≤ recibido); si el sistema acepta el paso 5 ⇒ hallazgo Alta.
- **Prioridad:** Alta.

### IN-03 · Inspección de incubadora previa en el lote de carga/transferencia

- **Precondición:** `QA-HAT-INC-001` activo; máquina «QA Incubadora A1» activa; sin carga registrada aún en el lote.
- **Pasos:**
  1. Incubadora → `QA-HAT-INC-001` → Registrar operación → `hatchery_inspection` («Inspección de incubadora»).
  2. Seleccionar la máquina «QA Incubadora A1» y registrar la inspección con fecha del evento = hoy.
  3. Guardar y verificar el Historial.
  4. Repetir el registro de una inspección para el mismo lote y máquina el mismo día (control de duplicado).
- **Datos:** lote `QA-HAT-INC-001`; máquina «QA Incubadora A1» (activa); planta `QA-INC-F1`; fecha del evento = hoy; usuario `qa.operator.hatchery`.
- **Resultado esperado:** el paso 2 se guarda y deja la inspección como antecedente del lote (habilita el paso previo a la carga de IN-04). El Historial muestra la fila con Lote = `QA-HAT-INC-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento = hoy, Registrado por = `qa.operator.hatchery`, Fecha de registro = hoy. En el paso 4 el sistema advierte del posible duplicado o registra la segunda inspección como evento independiente, sin sobreescribir la primera (cualquiera de los dos comportamientos se anota como observación, no bloquea).
- **Regla:** BR-19, BR-06; máquina inactiva no seleccionable (control positivo con máquina activa).
- **Prioridad:** Media.

### IN-04 · Carga de 4 700 huevos incubables en «QA Incubadora A1»

- **Precondición:** IN-02 registrado (4 700 incubables); IN-03 registrado; máquina «QA Incubadora A1» activa.
- **Pasos:**
  1. Incubadora → `QA-HAT-INC-001` → Registrar operación → `incubation_load` («Carga en incubadora»).
  2. Seleccionar máquina «QA Incubadora A1» e ingresar cantidad 4 700 con fecha del evento = hoy.
  3. Guardar y revisar el saldo del lote y la ocupación de la máquina.
  4. Intentar una segunda carga de 4 800 en la misma máquina y guardar.
- **Datos:** lote `QA-HAT-INC-001`; máquina «QA Incubadora A1» (activa); cantidad válida 4 700; intento inválido 4 800; incubables disponibles 4 700; fecha del evento = hoy; usuario `qa.operator.hatchery`.
- **Resultado esperado:** el paso 3 se guarda; el saldo cargado queda en 4 700 y la máquina refleja la carga. El paso 4 se rechaza con mensaje de validación: no se puede cargar más de lo incubable disponible (4 800 > 4 700); no se crea fila nueva en el Historial. El Historial muestra la fila de carga con Lote = `QA-HAT-INC-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento = hoy, Registrado por = `qa.operator.hatchery`, Fecha de registro = hoy.
- **Regla:** BR-19, BR-06, no cargar más que lo incubable; si el sistema acepta 4 800 ⇒ hallazgo Alta.
- **Prioridad:** Alta.

### IN-05 · Intento de carga en «QA Incubadora A4 (inactiva)»

- **Precondición:** máquina «QA Incubadora A4 (inactiva)» existe en el catálogo con estado inactivo; lote `QA-HAT-INC-001` con saldo incubable disponible.
- **Pasos:**
  1. Incubadora → `QA-HAT-INC-001` → Registrar operación → `incubation_load`.
  2. Abrir el selector de máquinas y revisar si «QA Incubadora A4 (inactiva)» aparece como opción.
  3. Si aparece, seleccionarla, ingresar cantidad 1 000 y guardar.
  4. Si no aparece, intentar forzar el envío del formulario usando el identificador de la máquina inactiva (manipulación del selector) y guardar.
- **Datos:** lote `QA-HAT-INC-001`; máquina «QA Incubadora A4 (inactiva)»; cantidad intentada 1 000; fecha del evento = hoy; usuario `qa.operator.hatchery`.
- **Resultado esperado:** «QA Incubadora A4 (inactiva)» no se ofrece en el selector (o, si se ofrece, la operación se rechaza con mensaje de validación por máquina inactiva). En ningún caso se crea una fila de carga en el Historial; el saldo del lote no cambia. Las máquinas activas («QA Incubadora A1», «QA Nacedora N1») sí permanecen seleccionables.
- **Regla:** máquina inactiva no seleccionable; BR-19, BR-06. Si la carga se acepta ⇒ hallazgo Alta.
- **Prioridad:** Alta.

### IN-06 · Ovoscopía de 250 claros: saldo 4 450

- **Precondición:** IN-04 registrado (4 700 cargados); lote `QA-HAT-OVO-001` asociado a la ovoscopía de la carga de `QA-HAT-INC-001`.
- **Pasos:**
  1. Incubadora → `QA-HAT-OVO-001` → Registrar operación → `ovoscopy` («Ovoscopía»).
  2. Registrar 250 huevos claros, referenciando la carga de 4 700, con fecha del evento = hoy.
  3. Guardar y verificar el saldo resultante.
  4. Abrir el Historial del lote.
- **Datos:** lote `QA-HAT-OVO-001`; claros 250; carga origen 4 700; saldo esperado 4 450; planta `QA-INC-F1`; fecha del evento = hoy; usuario `qa.operator.hatchery`.
- **Resultado esperado:** la operación se guarda; el saldo de huevos viables queda en 4 450 (4 700 − 250) y los 250 claros se registran como descarte de ovoscopía. El Historial muestra la fila con Lote = `QA-HAT-OVO-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento = hoy, Registrado por = `qa.operator.hatchery`, Fecha de registro = hoy.
- **Regla:** BR-19, BR-06; cuadre de cantidades (claros ≤ cargados; saldo = cargado − claros).
- **Prioridad:** Alta.

### IN-07 · Transferencia de 4 450 a «QA Nacedora N1»

- **Precondición:** IN-06 registrado (saldo 4 450 viables); máquina «QA Nacedora N1» activa.
- **Pasos:**
  1. Incubadora → `QA-HAT-INC-001` → Registrar operación → `transfer_to_hatcher` («Transferencia a nacedora»).
  2. Seleccionar «QA Nacedora N1» e ingresar 4 450 con fecha del evento = hoy.
  3. Guardar y verificar el saldo del lote y la ocupación de la nacedora.
  4. Intentar una segunda transferencia de 4 500 y guardar.
- **Datos:** lote `QA-HAT-INC-001`; máquina destino «QA Nacedora N1» (activa); cantidad válida 4 450; intento inválido 4 500; viables disponibles 4 450; fecha del evento = hoy; usuario `qa.operator.hatchery`.
- **Resultado esperado:** el paso 3 se guarda; el lote queda con 0 viables en incubadora y la nacedora recibe 4 450. El paso 4 se rechaza: no se puede transferir más que lo cargado menos los claros (4 500 > 4 450); no se crea fila nueva en el Historial. El Historial muestra la fila con Lote = `QA-HAT-INC-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento = hoy, Registrado por = `qa.operator.hatchery`, Fecha de registro = hoy.
- **Regla:** BR-19, BR-06, no transferir más que lo cargado menos claros; si acepta 4 500 ⇒ hallazgo Alta.
- **Prioridad:** Alta.

### IN-08 · Registro de nacimiento: 4 000 de primera + 100 de descarte

- **Precondición:** IN-07 registrado (4 450 transferidos a «QA Nacedora N1»).
- **Pasos:**
  1. Incubadora → `QA-HAT-NAC-001` → Registrar operación → `birth_registration` («Registro de nacimiento»).
  2. Ingresar pollitos de primera 4 000 y de descarte 100, con fecha del evento = hoy.
  3. Guardar y verificar el total nacido y la merma frente a los 4 450 transferidos.
  4. Intentar un segundo registro con 4 600 pollitos de primera y guardar.
- **Datos:** lote `QA-HAT-NAC-001`; primera 4 000; descarte 100; transferidos 4 450; intento inválido 4 600; planta `QA-INC-F1`; fecha del evento = hoy; usuario `qa.operator.hatchery`.
- **Resultado esperado:** el paso 3 se guarda; total nacido 4 100 y merma implícita 350 (4 450 − 4 100), con 4 000 aptos para despacho y 100 de descarte no despachables. El paso 4 se rechaza: no puede nacer más de lo transferido (4 600 > 4 450); no se crea fila nueva en el Historial. El Historial muestra la fila con Lote = `QA-HAT-NAC-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento = hoy, Registrado por = `qa.operator.hatchery`, Fecha de registro = hoy.
- **Regla:** BR-19, BR-06; cuadre de cantidades (nacidos ≤ transferidos); si acepta 4 600 ⇒ hallazgo Alta.
- **Prioridad:** Alta.

### IN-09 · Despacho de 4 000 pollitos a `QA-BRO-001`

- **Precondición:** IN-08 registrado (4 000 de primera despachables); lote `QA-HAT-BIRTH-001` con pollitos por despachar; lote de engorde `QA-BRO-001` de la granja `QA-EN-01` existente.
- **Pasos:**
  1. Incubadora → `QA-HAT-BIRTH-001` → Registrar operación → `chick_dispatch` («Despacho de pollito»).
  2. Seleccionar destino `QA-BRO-001` / granja `QA-EN-01` e ingresar 4 000 con fecha del evento = hoy.
  3. Guardar y verificar el saldo por despachar.
  4. Intentar un segundo despacho de 4 100 y guardar.
  5. Intentar un despacho con fecha del evento = mañana y guardar.
- **Datos:** lote `QA-HAT-BIRTH-001`; destino `QA-BRO-001` (`QA-EN-01`); cantidad válida 4 000; intento inválido 4 100; fecha inválida = mañana; primera disponible 4 000; usuario `qa.operator.hatchery`.
- **Resultado esperado:** el paso 3 se guarda y deja el saldo por despachar en 0, con 4 000 pollitos acreditados al lote `QA-BRO-001`. Los pasos 4 y 5 se rechazan: no se despacha más que los nacidos de primera (4 100 > 4 000) y la fecha no puede ser futura; el selector de fecha debe tener como máximo hoy. El Historial muestra la fila con Lote = `QA-HAT-BIRTH-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento = hoy, Registrado por = `qa.operator.hatchery`, Fecha de registro = hoy.
- **Regla:** BR-19 (no futura, ≤90 días), BR-06, no despachar más que los nacidos de primera; si acepta 4 100 o la fecha de mañana ⇒ hallazgo Alta.
- **Prioridad:** Alta.

### IN-10 · Ciclo de revisión y aprobación con segregación de funciones

- **Precondición:** IN-09 registrado; existen usuarios `qa.operator.hatchery`, `qa.supervisor` y `qa.approver`; el registro de despacho queda en estado enviado/pendiente; Centro de Revisión y Aprobaciones accesible.
- **Pasos:**
  1. Con `qa.operator.hatchery`, enviar a revisión el registro de `chick_dispatch` del lote `QA-HAT-BIRTH-001`.
  2. Sin cambiar de sesión, intentar que el mismo `qa.operator.hatchery` revise/revierta su propio registro (autoaprobación).
  3. Iniciar sesión como `qa.supervisor`, abrir Centro de Revisión y Aprobaciones, filtrar por Granja/Planta = `QA-INC-F1` y devolver el registro con observación.
  4. Volver como `qa.operator.hatchery`, corregir el dato observado (p. ej. observaciones del despacho) y reenviar a revisión.
  5. Entrar como `qa.approver`, filtrar por Granja/Planta = `QA-INC-F1`, revisar y aprobar.
- **Datos:** lote `QA-HAT-BIRTH-001`; planta `QA-INC-F1`; registros implicados: `chick_dispatch`; usuarios `qa.operator.hatchery` (registra), `qa.supervisor` (revisa/devuelve), `qa.approver` (aprueba); filtro Granja/Planta = `QA-INC-F1`.
- **Resultado esperado:** el paso 1 deja el registro en pendiente de revisión. El paso 2 es bloqueado: quien registró no puede revisar ni aprobar su propia operación (segregación de funciones). El paso 3 deja el registro devuelto con la observación del supervisor visible para el operador; el filtro `QA-INC-F1` devuelve únicamente registros de la planta `QA-INC-F1`. El paso 4 permite corregir y reenviar, generando nuevo estado pendiente sin perder la trazabilidad anterior. El paso 5 aprueba el registro y deja al aprobador como responsable de la aprobación. El Historial del lote mantiene todas las filas con Lote = `QA-HAT-BIRTH-001`, Granja/Planta = `QA-INC-F1`, Fecha del evento, Registrado por y Fecha de registro, y el estado final aprobado es coherente con los pasos ejecutados.
- **Regla:** BR-14 / RR-03 (segregación de funciones: registrar ≠ revisar ≠ aprobar), trazabilidad de estados y observaciones.
- **Prioridad:** Alta.

## 6 · Casos transversales

Se ejecutan sobre las pantallas de listado y sobre la máquina de estados, con independencia del evento registrado en cada caso RP/IN.

### TR-01 · Lotes: columna Granja y filtro por Granja
- **Precondición**: sesión con `qa.supervisor`; existen lotes registrados en `QA-BR-01`, `QA-BR-02` y `QA-EN-01`.
- **Pasos**: abrir Lotes; verificar la columna Granja en cada fila; aplicar el filtro Granja = `QA-BR-01`; limpiar el filtro; repetir con `QA-EN-01`.
- **Datos**: granjas `QA-BR-01`, `QA-BR-02`, `QA-EN-01`.
- **Resultado esperado**: cada fila muestra el nombre de su granja; con `QA-BR-01` solo quedan sus lotes; al limpiar el filtro se recupera la lista completa; con `QA-EN-01` no aparecen lotes de reproductoras.
- **Regla**: UX de listados — columna y filtro por granja.
- **Prioridad**: Alta.

### TR-02 · Historial: columnas de contexto y fecha de registro
- **Precondición**: TR-01 ejecutado; existen eventos registrados con fecha de evento distinta de la fecha de alta del registro.
- **Pasos**: abrir Historial; revisar las columnas Lote, Granja, Fecha del evento, Registrado por y Fecha de registro; filtrar por Granja = `QA-BR-01`; comparar, en un mismo registro, la fecha del evento con la fecha de registro.
- **Datos**: el registro de RP-01 en `QA-BR-01` (evento con fecha anterior a la del alta).
- **Resultado esperado**: la columna Lote muestra el código del lote (nunca el número interno); se ven Granja, Fecha del evento, Registrado por y Fecha de registro; el filtro por Granja acota la lista; la fecha de registro es la del alta y es distinta de la fecha del evento.
- **Regla**: UX de listados — trazabilidad fecha de evento vs. fecha de alta.
- **Prioridad**: Alta.
### TR-03 · Mis pendientes del usuario móvil
- **Precondición**: `qa.operator.hatchery` tiene al menos dos registros pendientes en la planta `QA-INC-F1`.
- **Pasos**: iniciar sesión como `qa.operator.hatchery` (usuario móvil); abrir Mis pendientes; revisar cada tarjeta y abrir una de ellas.
- **Datos**: registros pendientes de IN-01…IN-10 en `QA-INC-F1`.
- **Resultado esperado**: cada tarjeta identifica el código del lote y la granja o planta asociada (`QA-INC-F1`), sin ambigüedad; la lista es usable en pantalla móvil y al tocar la tarjeta se abre el registro correspondiente.
- **Regla**: UX de listados — contexto de origen en tareas pendientes.
- **Prioridad**: Alta.

### TR-04 · Centro de Revisión y Aprobaciones
- **Precondición**: existen registros en Pendiente de revisión y en Pendiente de aprobación; sesiones de `qa.supervisor` y `qa.approver`.
- **Pasos**: abrir Centro de Revisión y revisar las columnas Granja, Registrado por y Fecha de registro; filtrar por Granja = `QA-BR-01`; repetir en Aprobaciones; dejar ambas pantallas abiertas 60 s observando el indicador de carga y la pestaña Red del navegador.
- **Datos**: registros de `QA-BR-01` y `QA-BR-02`.
- **Resultado esperado**: ambas pantallas muestran Granja, Registrado por y Fecha de registro; el filtro Granja funciona en las dos; durante 60 s no hay recargas ni peticiones en bucle (sin indicador de carga permanente ni solicitudes repetidas en la pestaña Red).
- **Regla**: UX de listados — contexto de origen y ausencia de recarga en bucle.
- **Prioridad**: Alta.
### TR-05 · Maestros: desactivar/reactivar y columna del padre
- **Precondición**: sesión con `qa.admin`; existen maestros activos en Granjas, Galpones, Incubadoras (equipos) y Nacedoras.
- **Pasos**: abrir Maestros; revisar acciones de fila y cabeceras de cada pestaña; desactivar un maestro y volver a la lista; reactivarlo; abrir Galpones, Incubadoras y Nacedoras y revisar la columna con el nombre del padre.
- **Datos**: un galpón de `QA-BR-01`; una incubadora de la planta `QA-INC-F1`.
- **Resultado esperado**: la acción de fila es «Desactivar» (no «Eliminar»); al desactivar aparece la columna Estado = Inactivo y la fila se ve atenuada; «Reactivar» devuelve el maestro a Estado Activo; Galpones, Incubadoras (equipos) y Nacedoras muestran una columna con el nombre de la Granja/Planta padre; ninguna cabecera de tabla dice «Editar» ni «Guardar».
- **Regla**: UX de listados — baja lógica y jerarquía visible, sin borrado físico.
- **Prioridad**: Alta.
### TR-06 · Máquina de estados: acciones disponibles por estado
- **Precondición**: existen un registro en Pendiente de revisión, uno en Corregido y uno en Aprobado; sesiones de `qa.supervisor` y `qa.approver`.
- **Pasos**: sobre el Pendiente de revisión, comprobar si «Rechazar» está disponible; sobre el Corregido, comprobar que «Rechazar» sí está disponible y ejecutarlo; sobre el Aprobado, comprobar si «Cancelar» está disponible; ejecutar «Reversar» sobre el Aprobado y seguir el registro generado hasta su revisión y aprobación.
- **Datos**: un registro RP y uno IN en cada estado; lotes `QA-BR-01` y planta `QA-INC-F1`.
- **Resultado esperado**: en Pendiente de revisión no aparece «Rechazar» (solo desde Corregido); en Aprobado no aparece «Cancelar»; «Reversar» genera una contraparte que pasa por Centro de Revisión y por Aprobaciones y queda como registro vigente, con el original marcado como reversado.
- **Regla**: máquina de estados.
- **Prioridad**: Alta.

## 7 · Matriz caso ↔ pantalla ↔ regla

| ID | Pantalla | Evento/acción | Regla(s) | Prioridad |
|---|---|---|---|---|
| RP-01 | Recepción de aves | Recepción con OC válida | OC válida de la cadena BR | Alta |
| RP-02 | Recepción de aves | Recepción con OC de otra cadena (BR-23) | BR-23 | Alta |
| RP-03 | Recepción de aves | Recepción con exceso sobre la OC | BR-18 | Alta |
| RP-04 | Recepción de aves | Recepción sin desglose | BR-20 | Alta |
| RP-05 | Recepción de aves | Recepción con fecha futura | BR-19 | Alta |
| RP-06 | Recepción de aves | Recepción con fecha anterior a la activación | BR-06 | Alta |
| RP-07 | Registro de operación (lote) | Distribución | Cuadre de cantidades | Alta |
| RP-08 | Registro de operación (lote) | Alimento | Cuadre de cantidades | Media |
| RP-09 | Registro de operación (lote) | Agua | Cuadre de cantidades | Media |
| RP-10 | Registro de operación (lote) | Mortalidad / descarte | Cuadre de cantidades | Alta |
| RP-11 | Registro de operación (lote) | Pesaje | Alertas | Media |
| RP-12 | Registro de operación (lote) | Vacunación / medicación | Alertas | Media |
| RP-13 | Registro de operación (lote) | Recolección y despacho de huevo | Cuadre de cantidades | Alta |
| RP-14 | Centro de Revisión | Revisión y segregación | Máquina de estados | Alta |
| IN-01 | Recepción de aves | Recepción en planta `QA-INC-F1` | Cuadre de cantidades | Alta |
| IN-02 | Registro de operación (planta) | Clasificación de huevo | Cuadre de cantidades | Alta |
| IN-03 | Registro de operación (planta) | Inspección | Alertas | Media |
| IN-04 | Registro de operación (planta) | Carga A1 | Cuadre de cantidades | Alta |
| IN-05 | Registro de operación (planta) | Carga en máquina inactiva | Máquina de estados (equipo activo) | Alta |
| IN-06 | Registro de operación (planta) | Ovoscopía | Cuadre de cantidades | Media |
| IN-07 | Registro de operación (planta) | Transferencia N1 | Cuadre de cantidades, BR-14/RR-03 | Alta |
| IN-08 | Registro de operación (planta) | Nacimiento | Cuadre de cantidades | Alta |
| IN-09 | Registro de operación (planta) | Despacho de pollito | Cuadre de cantidades | Alta |
| IN-10 | Centro de Revisión y Aprobaciones | Ciclo de revisión | Máquina de estados | Alta |
| TR-01 | Lotes | Columna y filtro Granja | UX de listados | Alta |
| TR-02 | Historial | Columnas de contexto y fecha de registro | UX de listados | Alta |
| TR-03 | Mis pendientes | Tarjetas con lote y granja/planta | UX de listados | Alta |
| TR-04 | Centro de Revisión y Aprobaciones | Columnas, filtro Granja y no recarga | UX de listados | Alta |
| TR-05 | Maestros | Desactivar/reactivar y columna del padre | UX de listados | Media |
| TR-06 | Centro de Revisión y Aprobaciones | Acciones disponibles por estado | Máquina de estados | Alta |

## 8 · Plantilla de registro de resultados

| ID | Fecha | Ejecutor | Lote / dato usado | Resultado (PASA/FALLA/BLOQUEADO) | Evidencia | Observaciones |
|---|---|---|---|---|---|---|
| RP-01 |  |  |  |  |  |  |
| RP-02 |  |  |  |  |  |  |
| RP-03 |  |  |  |  |  |  |
| RP-04 |  |  |  |  |  |  |
| RP-05 |  |  |  |  |  |  |
| RP-06 |  |  |  |  |  |  |
| RP-07 |  |  |  |  |  |  |
| RP-08 |  |  |  |  |  |  |
| RP-09 |  |  |  |  |  |  |
| RP-10 |  |  |  |  |  |  |
| RP-11 |  |  |  |  |  |  |
| RP-12 |  |  |  |  |  |  |
| RP-13 |  |  |  |  |  |  |
| RP-14 |  |  |  |  |  |  |
| IN-01 |  |  |  |  |  |  |
| IN-02 |  |  |  |  |  |  |
| IN-03 |  |  |  |  |  |  |
| IN-04 |  |  |  |  |  |  |
| IN-05 |  |  |  |  |  |  |
| IN-06 |  |  |  |  |  |  |
| IN-07 |  |  |  |  |  |  |
| IN-08 |  |  |  |  |  |  |
| IN-09 |  |  |  |  |  |  |
| IN-10 |  |  |  |  |  |  |
| TR-01 |  |  |  |  |  |  |
| TR-02 |  |  |  |  |  |  |
| TR-03 |  |  |  |  |  |  |
| TR-04 |  |  |  |  |  |  |
| TR-05 |  |  |  |  |  |  |
| TR-06 |  |  |  |  |  |  |

## 9 · Criterios de salida de la ronda

La ronda no se cierra hasta que se cumplan todos los puntos:

- **Cobertura prioritaria**: el 100 % de los casos de prioridad Alta está en PASA — RP-01…RP-07, RP-10, RP-13, RP-14, IN-01, IN-02, IN-04, IN-05, IN-07…IN-10 y TR-01…TR-04, TR-06.
- **Defectos**: no queda ningún FALLA sin hallazgo registrado con ID, prioridad, pantalla, pasos de reproducción y evidencia.
- **Bloqueos**: cada BLOQUEADO tiene causa, responsable y fecha compromiso de resolución.
- **Evidencia por caso**: cada fila ejecutada de la plantilla de la sección 8 tiene evidencia asociada (captura, respuesta de API o identificador del registro generado).
- **Juego de datos y usuarios documentados**: quedan registrados los lotes `QA-BR-01`, `QA-BR-02`, `QA-EN-01`, la planta `QA-INC-F1`, las OC utilizadas y los usuarios `qa.operator.breeder`, `qa.operator.hatchery` (móvil), `qa.supervisor`, `qa.approver`, `qa.admin` y `qa.auditor` con su rol.
- **Hallazgos nuevos**: se entrega la lista de hallazgos nuevos de la ronda, cada uno con prioridad asignada y caso de origen.
- **Cierre formal**: fecha de cierre y firma de QA y del propietario del producto.

