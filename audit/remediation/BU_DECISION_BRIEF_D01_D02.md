# LAS DOS ÚLTIMAS DECISIONES ANTES DE CONSTRUIR

`BU-D01` · `BU-D02` · 2026-09-07

```
QUÉ ES ESTO       un documento para decidir
QUÉ NO ES         no es spec · no contiene tareas de implementación
                  no crea tablas · no cambia código · no cambia certificaciones
ESTADO            las dos PENDING_OWNER
BLOQUEANTES       2 de 2 — son las únicas que quedan para GA-REM-040
```

## Lo que ya está decidido, y sirve de suelo a estas dos

```
OD-09.a    visibilidad de control de toda la empresa · operación por unidad
OD-09.b    administrar el acceso ≠ acceder al dato
OD-09.c    sin unidades: entra, usa lo transversal, no ve dato productivo
```

Las dos que siguen tratan del **plano operativo**: qué ve un usuario de producción normal. El
contralor y el administrador ya están resueltos por `OD-09` y **no vuelven a discutirse aquí**.

---

# `BU-D01`

```
TÍTULO LITERAL    Qué sigue viendo cada línea cuando el producto cambia de manos

PREGUNTA DE       Cuando un lote de huevo sale de Reproductora y entra en
NEGOCIO           Incubadora, ¿qué sigue viendo la gente de Reproductora, y qué
                  empieza a ver la gente de Incubadora?

POR QUÉ DECIDE    Porque define si esta capacidad sirve para algo. Si cada línea
EL PROPIETARIO    sigue viendo todo, no se ha aislado nada; si deja de ver el
                  traspaso, se rompe la trazabilidad ya certificada. No hay
                  respuesta técnica: es cómo trabaja el negocio.

EVIDENCIA         `CROSS_MODULE_FLOW_MATRIX.md §3` — siete flujos cruzan unidades
NORMATIVA         los siete: «Fully specified: 0 · Owner decision required: 7»
                  `P-10` CERTIFIED sobre la cadena generacional completa

EVIDENCIA         `egg_batches`   source_lot_id  →  hatchery_lot_id
DE AUDITORÍA      `chick_batches` hatchery_lot_id → destination_lot_id
                  el lado destino es NULABLE: se rellena al recibir
                  `operational_events.destination_farm_id` existe, es una GRANJA
                  y es opcional

UNIDADES          las cuatro
AFECTADAS         Progenitoras · Reproductora · Incubadora · Engorde

PROCESOS          `P-02` `P-04` `P-05` `P-06` cruzan por diseño
AFECTADOS         `P-10` trazabilidad generacional — CERTIFICADO
                  `P-11` activación de lotes · `P-15` reportes y KPI
                  `P-07` y `P-08` quedan cubiertos por OD-09.a y BU-D04

ENTIDADES         `egg_batches` · `chick_batches` · `bird_movements`
AFECTADAS         `operational_events` · `lots` · `consolidated_movements`

FLUJOS            los siete, sin excepción
```

## SI NO SE DECIDE

No se puede construir. No hay valor por omisión inocente: dejarlo abierto es la opción de
visibilidad total —la capacidad no aísla nada— y cerrarlo sin decidir rompe `P-10`, que está
certificado sobre la cadena completa.

## SITUACIÓN ACTUAL

Todas las líneas ven todo dentro de su empresa. No porque se decidiera, sino porque el eje no
existe.

---

## Los siete flujos, con lo que cada uno necesita

Antes del traspaso, durante y después no son lo mismo, y la diferencia es donde está el trabajo.

| # | Origen → Destino | Entidad puente | Antes del traspaso | Durante | Después |
|:--:|---|---|---|---|---|
| 1 | Progenitoras → *(Incub.)* → Reproductora | `egg_batches` gen. `grandparent` + `chick_batches` | origen prepara postura | despacho y recepción | **origen quiere ver el lote resultante** |
| 2 | Reproductora → Incubadora | `egg_batches` gen. `breeder` | **destino no sabe que le viene** | despacho → recepción | origen ve la merma |
| 3 | Incubadora → Engorde | `chick_batches` | destino no sabe que le viene | despacho → recepción | **origen quiere la 1.ª semana del destino** |
| 4 | Granja → Granja | `bird_movements` | según el caso | movimiento | cada lado su parte |
| 5 | las cuatro → SAP | `consolidated_movements` | — | consolidación | resuelto por `BU-D04` |
| 6 | las cuatro → control | `operational_events` | — | revisión | **resuelto por `OD-09.a`** |
| 7 | las cuatro ↔ las cuatro | `egg_batches` + `chick_batches` | — | — | cadena completa · `P-10` |

### Qué necesita ver cada lado, y qué no

| # | El origen necesita | El destino necesita | Prohibido al otro lado |
|:--:|---|---|---|
| 1 | el lote de reproductora que nació de sus huevos, y cómo rinde | de qué lote de progenitoras viene, línea genética, fecha | mortalidad diaria · consumo · costos · inspecciones |
| 2 | qué despachó, cuánto llegó, **la merma** | **lo que viene en camino**, edad de la madre, genética, fecha de postura | la operación diaria de la granja de reproductoras |
| 3 | cuántos entregó, cuántos llegaron, **la mortalidad de 1.ª semana** | procedencia, nacimiento, sexaje, cantidad, genética | `hatchery_params` · temperaturas · volteos · costos y facturación del engorde |
| 4 | su lado del movimiento | su lado del movimiento | el interior del lote ajeno |
| 7 | la cadena entera: qué vino de qué, con fechas y cantidades | ídem | el interior de cada eslabón |

Los flujos 3 y 1 tienen una particularidad que conviene ver: **el dato que mide al origen vive en
el destino.** La calidad de una incubadora se lee en la mortalidad de primera semana del engorde;
la calidad de una progenitora, en el rendimiento del lote de reproductora. Sin ese retorno, quien
produce no puede corregirse.

### Anulaciones y correcciones

El producto ya tiene `RETURNED`, `CORRECTED`, `REJECTED` y un endpoint de anulación. De ahí sale
una pregunta que la matriz de flujos no cubría:

> Si la incubadora ya vio «vienen 40.000 huevos» y después el despacho se anula o se rechaza,
> ¿qué ve entonces?

La respuesta que se recomienda: **lo ve desaparecer con su motivo, no evaporarse sin más.** Un
traspaso anulado que simplemente deja de existir para el destino hace imposible entender qué pasó
con un camión que no llegó.

### Los agregados

No es un detalle de implementación: es parte de esta decisión.

```
Un usuario de Reproductora NO debe poder deducir el dato de Incubadora
a través de un total, un promedio, un ratio, un contador o un panel de la empresa.
```

Un número calculado sobre filas que el usuario no puede ver **filtra por diferencia**: no enseña
la fila, enseña que existe y cuánto pesa. Y es la única fuga que no deja rastro y que nadie
reporta.

La excepción es la que `OD-09.a` ya concedió: los roles de control ven agregados de toda la
empresa. **Un usuario operativo normal, no.**

---

## OPCIÓN A · Aislamiento estricto

Cada línea ve lo suyo. La fila de traspaso se corta por la mitad: cada lado ve solo su columna.

```
Seguridad        la máxima. Una sola regla, sin excepciones que recordar.
Operación        rota. Quien recibe huevo no sabe de qué lote viene; quien lo
                 despachó no sabe si llegó. La merma deja de ser medible.
Uso              cada línea trabaja a ciegas respecto de la anterior.
Trazabilidad     ROMPE `P-10`, que está certificado sobre la cadena completa.
                 Un proceso certificado dejaría de cumplir su spec.
Implementación   la más sencilla: un filtro y ninguna excepción.
Extensibilidad   añadir una línea nueva no cuesta nada, porque nada se comparte.
```

## OPCIÓN B · Contrato de traspaso

Cada línea ve lo suyo, más la fila puente, más lo mínimo del lote de enfrente para poder
trabajar. Cuatro categorías:

```
A · PROPIO            lo de las unidades concedidas. Acceso completo según RBAC.
B · TRASPASO          la fila puente + del lote de enfrente: identificador,
                      cantidad, fecha, estado sanitario. Solo lectura, ambos lados.
C · INTERNO AJENO     mortalidad diaria, consumo, pesajes, inspecciones, costos.
                      Denegado.
D · AGREGADO          se calcula sobre A ∪ B. Nunca sobre C.
```

```
Seguridad        buena, y comprobable: una prueba puede afirmar «esto se ve» y
                 «esto no» para cada categoría. Concede exactamente lo que el
                 traspaso necesita y nada más.
Operación        es lo que el negocio hace de verdad. Quien recibe sabe de dónde
                 viene; quien despachó sabe si llegó y con qué merma.
Uso              natural: se ve el papel de entrega, no la contabilidad del otro.
Trazabilidad     `P-10` se conserva. La cadena se ve entera; el interior de cada
                 eslabón no.
Implementación   la más cara de las tres: hay que clasificar campo por campo qué
                 entra en `B` y qué se queda en `C`, en seis entidades.
Extensibilidad   buena: una línea nueva se incorpora declarando sus contratos.
                 El modelo ya lo soporta — las entidades puente llevan los dos
                 lados en columnas separadas y no necesitan columna de unidad.
```

## OPCIÓN C · Visibilidad total

Todos ven todo dentro de su empresa. Es el estado actual.

```
Seguridad        ninguna en este eje. La capacidad no serviría para nada.
Operación        perfecta, como hoy.
Uso              el de hoy.
Trazabilidad     intacta.
Implementación   nula: no hacer nada.
Extensibilidad   nula: no habría qué extender.
```

**No se recomienda.** Sería construir el modelo de unidades y no usarlo.

---

## RECOMENDADA · **OPCIÓN B**

**POR QUÉ.** `A` rompe un proceso certificado —`P-10`— y deja el negocio trabajando a ciegas
entre eslabones. `C` hace que todo el esfuerzo no sirva de nada. `B` es la única que aísla de
verdad **y** deja pasar lo que la cadena avícola necesita para funcionar, que es poco y está
bien delimitado: quién me lo mandó, cuánto, cuándo y en qué estado.

Y hay un argumento de evidencia, no de gusto: **el modelo ya está construido para `B`.** Las
entidades de traspaso llevan origen y destino en columnas separadas, y `lot_code` es único. No
hay que inventar clave ni añadir columna de unidad a las filas de cruce.

### Con dos condiciones

**Primera — los agregados van dentro de la decisión, no después.** Si se implementan las filas
ahora y los totales en otra fase, existirá un periodo con fuga por diferencia. Y una fuga por
diferencia no deja rastro.

**Segunda — la clasificación `B` frente a `C` se hace campo por campo y una sola vez.** Es el
trabajo real de esta opción. Dejarlo a cada pantalla reintroduce `C` por la puerta de atrás.

---

## La pregunta acompañante · el destino del despacho

**Gobernada por `BU-D01`**, flujo 2 — verificado en `BUSINESS_UNIT_OWNER_DECISION_MATRIX.md §5`.
Es la única de las doce decisiones que obliga a capturar información que hoy no se guarda, y
conviene contestarla en el mismo acto.

> **¿Un despacho de huevo debe decir a qué destino va desde el momento en que se crea?**

Hoy no lo garantiza. El lado destino de la fila puente se rellena **al recibir**, y
`destination_farm_id` apunta a una granja y es opcional. Entre el despacho y la recepción, nada
dice a quién va dirigido.

**Por qué importa.** Sin destino declarado, la incubadora **no puede saber que un despacho es
para ella antes de recibirlo**. Y la alternativa —que vea todos los despachos pendientes de la
empresa— anularía el aislamiento justo en el punto que se quería proteger.

```
A · El destino se declara al crear el despacho
    El destino ve lo que viene en camino desde el primer momento.
    Coste: un campo obligatorio más en el despacho, y quien despacha tiene que
    saber adónde manda — que normalmente lo sabe, porque el camión sale hacia
    algún sitio.

B · El destino se declara antes del traspaso, no necesariamente al crear
    Permite registrar el despacho y asignar destino después.
    El destino ve lo suyo en cuanto se le asigna. Más flexible; deja una ventana
    en la que el despacho no es de nadie.

C · Todas las incubadoras de la empresa ven todos los despachos pendientes
    No requiere dato nuevo.
    Anula el aislamiento entre unidades para este flujo. NO se recomienda.
```

**Recomendada · `A`**, por mínimo privilegio: es la única que da la información al destino sin
enseñársela a nadie más. `B` es aceptable si el negocio despacha antes de saber adónde — el
propietario sabrá si eso ocurre—; `C` no.

**No se diseña el campo aquí.** La pregunta es de negocio; cómo se guarde pertenece a la spec.

```
OWNER ANSWER REQUIRED    BU-D01:  A / B / C / OTRA
                         destino del despacho:  A / B / C / OTRA
```

---

# `BU-D02`

```
TÍTULO LITERAL    Los registros que no se puede saber a qué línea pertenecen

PREGUNTA DE       Una inspección de granja no es de ninguna parvada concreta.
NEGOCIO           ¿Quién debe verla?

POR QUÉ DECIDE    Porque no es un problema de datos viejos que se arregle una vez.
EL PROPIETARIO    Las inspecciones se registran sin lote a propósito, y se seguirán
                  registrando así. La respuesta será la respuesta para siempre.
                  Y las dos salidas obvias son malas en direcciones opuestas.

EVIDENCIA         `operational_events.lot_id` es NULABLE, y lo es a propósito:
NORMATIVA         `farm_inspection` se registra sin lote desde `i9j0k1l2m3n4`
                  `GA-REM-039 §5` ya se topó con esto para las notificaciones y
                  resolvió NO inventarle un área, devolviendo conjunto vacío sin
                  que nada fallara

EVIDENCIA         `LEGACY_DATA_MODULE_MAPPING_MATRIX.md`
DE AUDITORÍA      eventos sin lote      unidad derivable: NO · siempre ambiguo
                  `inspection_details`  a menudo NO · BLOQUEANTE
                  `Lot.bird_type` es nulable; `Breed.bird_type` da una segunda vía
                  `audit_logs` hereda la ambigüedad por la cadena

UNIDADES          ninguna — ése es exactamente el caso
AFECTADAS         y por tanto, potencialmente, las cuatro

PROCESOS          `P-01` … `P-06` (la inspección es el primer paso de casi todas
AFECTADOS         las cadenas) · `P-09` auditoría · `P-11` · `P-14` · `P-15`

ENTIDADES         `operational_events` sin `lot_id` · `inspection_details`
AFECTADAS         `lots` sin `bird_type` · `audit_logs` · `notifications`
                  `bird_movements` `egg_movements` `feed_movements` por cadena

FLUJOS            ninguno en concreto: es anterior a los flujos. Un registro que
                  no se sabe de quién es no puede entrar en ningún contrato.
```

## SI NO SE DECIDE

Se elegirá una de las dos malas sin querer, al escribir el filtro. Probablemente «no lo ve
nadie», porque parece lo prudente — y las inspecciones desaparecerán de la pantalla de quien
acaba de registrarlas.

## SITUACIÓN ACTUAL

Todo el mundo ve todas las inspecciones de su empresa. No hay eje que las clasifique.

---

## OPCIÓN A · Lo ve todo el mundo *(fail open)*

Un registro sin línea es visible para cualquiera de la empresa.

```
Seguridad        inaceptable. Basta una inspección para ver la granja entera, y
                 la inspección es el primer paso de casi todas las cadenas. La
                 capacidad quedaría vacía por su punto más frecuente.
Operación        perfecta: nada cambia.
Uso              perfecto.
Trazabilidad     intacta.
Implementación   trivial.
Extensibilidad   mala: cada entidad nueva sin clasificar amplía el agujero.
```

## OPCIÓN B · No lo ve nadie *(fail closed)*

Un registro sin línea no es visible para nadie.

```
Seguridad        la máxima, y coherente con «lo desconocido se deniega».
Operación        ROTA de una forma particularmente mala: el usuario registra una
                 inspección y desaparece de su pantalla al guardarla. No hay
                 forma de corregirla, porque no se puede ver.
Uso              el peor mensaje posible: el sistema se traga lo que acabas de
                 escribir.
Trazabilidad     las inspecciones dejan de aparecer en las cadenas.
Implementación   trivial.
Extensibilidad   segura, y cada vez más restrictiva.
```

## OPCIÓN C · Pendiente de clasificar *(cuarentena)*

El registro sin línea entra en un estado explícito. Lo ven **quien lo registró** y
**administración**, con una bandeja donde resolverlo.

```
Seguridad        buena. No es fail open: los que ven son dos partes nombradas, no
                 «todos». Y lo indeterminado queda contado, de modo que se sabe
                 cuánto hay.
Operación        conservada. Nada desaparece; lo que falta se puede completar.
Uso              el único diagnosticable: el usuario ve su registro y ve que le
                 falta algo.
Trazabilidad     conservada, y además mejora: hoy nadie sabe cuántos registros
                 están sin clasificar porque no hay dónde mirarlo.
Implementación   la más cara: un estado más y una pantalla de resolución.
Extensibilidad   la mejor: cualquier entidad futura que no se pueda clasificar
                 tiene ya dónde caer, en vez de forzar una excepción nueva.
```

---

## RECOMENDADA · **OPCIÓN C**

**POR QUÉ.** Es la única que no obliga a elegir entre seguridad y operación. `A` vacía la
capacidad por su punto más frecuente; `B` hace que el sistema se coma lo que el usuario acaba de
escribir, que es la peor experiencia que un producto puede dar.

`C` **nombra** lo indeterminado en lugar de silenciarlo en una de las dos direcciones. Y tiene
un efecto que las otras dos no: hace **medible** cuánto dato hay sin clasificar. Hoy nadie lo
sabe.

Además, es lo que este proyecto ya hizo una vez. `GA-REM-039` se encontró con el evento sin área
y **no le inventó una**: devolvió un conjunto vacío de destinatarios, sin fallar y sin fingir.
`C` es esa misma respuesta con una bandeja para resolverla.

### Con dos precisiones

**El origen del dato importa.** Los lotes sin `bird_type` tienen una segunda vía: la raza
(`Breed.bird_type`). Es derivación de dato guardado, no adivinación — pero **es una inferencia de
negocio**, porque hay razas usadas en más de una línea. Si se ratifica, muchos registros salen de
la cuarentena solos; si no, entran en ella. Eso es `BU-D06`, y conviene contestarlo a la vez.

**La cuarentena no es un limbo permanente.** Si nadie resuelve la bandeja, crece. Conviene que
sea visible cuánto hay, para que resolverla sea una tarea y no un olvido.

```
OWNER ANSWER REQUIRED    BU-D02:  A / B / C / OTRA
```

---

# Cómo se relacionan

```
BU-D02   decide qué pasa con lo que NO se puede clasificar
   │
   └──►  BU-D01   decide qué se comparte de lo que SÍ está clasificado
```

`BU-D02` es anterior: un registro que no se sabe de quién es no puede entrar en ningún contrato
de traspaso. Por eso conviene contestar las dos, y en ese orden.

Si las dos recomendaciones se aceptan, la regla operativa completa cabe en cuatro líneas —y
junto con `OD-09`, cierra el diseño:

> Ves lo de tus líneas. Del traspaso ves el papel de entrega y lo mínimo del lote de enfrente
> para trabajar, nunca su interior. Los totales cuentan solo lo que puedes ver. Y lo que no se
> sabe de quién es queda pendiente de clasificar, a la vista de quien lo registró y de
> administración.

# Preguntas finales

```
BU-D01   Qué sigue viendo cada línea cuando el producto cambia de manos
         Recomendada:  B — contrato de traspaso
         Respuesta:    A / B / C / OTRA

         (acompañante) ¿el despacho declara su destino al crearse?
         Recomendada:  A — sí, al crearlo
         Respuesta:    A / B / C / OTRA

BU-D02   Los registros que no se puede saber a qué línea pertenecen
         Recomendada:  C — pendiente de clasificar
         Respuesta:    A / B / C / OTRA
```

# Lo que este documento no hace

- **No decide.** Las dos siguen `PENDING_OWNER`.
- **No crea** `GA-REM-040`, ni tablas, ni migraciones, ni guardas, ni columnas.
- **No propone** `business_unit_id` sobre las entidades que representan el cruce: llevan origen y
  destino en columnas separadas y no necesitan propiedad única.
- **No reabre** `P-14` ni ninguna certificación. `FUNCIONAL 14/15` sin cambios.
- **No toca** `P-08`, `R-98`, `R-99`, `GA-TD-014`, `BirdTypeEnum`, el `RBAC` ni el despliegue.
- **No revive** `BU-D05`: `ENV-01` lo sitúa en el alta del primer cliente real.
- **No mezcla** unidad de negocio con `Area`. Son dos ejes distintos.
