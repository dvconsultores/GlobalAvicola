# QUÉ VE CADA UNIDAD DE NEGOCIO CUANDO EL PRODUCTO CAMBIA DE MANOS

Análisis de decisión · 2026-09-07 · **sin código** · deriva de
`audit/remediation/CROSS_MODULE_FLOW_MATRIX.md §3` y del modelo verificado

---

## 0. Vocabulario, para que la decisión sea sobre lo correcto

Este documento usa dos palabras que **no son la misma** y que hasta ahora el proyecto llamaba
igual:

```
MÓDULO RBAC        un permiso:   operations · lots · masters · reports · users …
                   ya existe, ya está certificado, no se toca aquí

UNIDAD DE NEGOCIO  una línea:    Progenitoras · Reproductora · Incubadora · Engorde
                   no existe todavía en ninguna forma
```

Un usuario podrá tener el módulo `operations` **y** aun así no poder ver las operaciones de
Incubadora, porque son dos ejes distintos. Todo lo que sigue trata del segundo.

---

## 1. La pregunta del propietario, en una frase

> Cuando un lote de huevo sale de Reproductora y entra en Incubadora, **¿qué sigue viendo la
> gente de Reproductora, y qué empieza a ver la gente de Incubadora?**

Hoy la respuesta es «todo, los dos, siempre». No porque se haya decidido, sino porque nunca se
preguntó.

---

## 2. Lo que el modelo ya resuelve, y conviene saber antes de decidir

Al releer el código para este análisis aparecieron **dos hechos que la auditoría anterior no
había registrado**, y los dos aligeran el problema.

### 2.1 Las entidades de traspaso nombran los dos lados, por separado

`egg_batches` y `chick_batches` no son filas «de dos unidades a la vez». Son filas **con dos
columnas**, una por cada lado:

```
egg_batches      source_lot_id  ──►  hatchery_lot_id
chick_batches    hatchery_lot_id ──►  destination_lot_id
```

Esto cambia el planteamiento. No hay que decidir «de quién es la fila»: la fila **es el
contrato**, y cada columna dice a quién alcanza. Un usuario de Reproductora ve las filas cuyo
`source_lot` es suyo; uno de Incubadora, aquellas cuyo `hatchery_lot` lo es. No hace falta
inventar una columna de unidad para estas dos tablas.

La auditoría las había clasificado como **`BLOQUEANTE` — «pertenecen a dos unidades a la vez por
diseño»**. Es más exacto decir que son **bilaterales**, y que la bilateralidad es justo la forma
que un contrato de traspaso necesita. **Corrección registrada** frente a
`LEGACY_DATA_MODULE_MAPPING_MATRIX.md §3`.

### 2.2 Hay un hueco real, y es anterior a la recepción

El lado destino solo queda escrito **cuando recibe**: `hatchery_lot_id` y `destination_lot_id`
son nulables y se rellenan en el evento de recepción. Entre el despacho y la recepción, la fila
sabe de dónde sale pero no adónde va.

Existe `operational_events.destination_farm_id`, que apunta a una **granja**, no a una unidad, y
también es nulable. Sirve como pista, no como clave.

Esto importa porque el destino necesita ver **lo que viene en camino** —es la mitad del sentido
de la funcionalidad— y hoy no hay dato que se lo garantice. Es el único punto de estos siete
flujos donde la decisión del propietario obliga además a **añadir información**, no solo a
repartir la que ya existe.

---

## 3. Las cuatro categorías de visibilidad

Toda la decisión se puede expresar con cuatro cajas. Se proponen así porque son comprobables:
una prueba puede afirmar «esto se ve» y «esto no».

```
A · PROPIO             lotes y eventos de las unidades que el usuario tiene.
                       Acceso completo, según su módulo RBAC. Sin cambios.

B · TRASPASO           la fila puente, y del lote de enfrente solo lo mínimo para actuar:
                       identificador, cantidad, fecha, estado sanitario.
                       Solo lectura, para los dos lados.

C · INTERNO AJENO      todo lo demás del lote de enfrente: mortalidad diaria, consumo,
                       pesajes, inspecciones, costos, incidencias.
                       Denegado.

D · AGREGADO           totales, KPI, paneles y reportes.
                       Se calculan sobre A ∪ B, nunca sobre C.
```

La caja `D` no es decorativa. Un total que incluye lo que el usuario no puede ver **filtra por
diferencia**: no enseña la fila, pero enseña que existe y cuánto pesa. Y una fuga por diferencia
no deja rastro y nadie la reporta.

El identificador compartido ya existe y es `lots.lot_code` —único e indexado—, de modo que la
caja `B` no necesita inventar clave.

---

## 4. Las tres opciones, y por qué solo dos están sobre la mesa

```
A · AISLAMIENTO ESTRICTO
    Cada unidad ve lo suyo. La fila puente se corta por la mitad.
    Seguro. Rompe la trazabilidad generacional que P-10 certifica.

B · CONTRATO DE TRASPASO           ← recomendada
    Cada unidad ve lo suyo, más la fila puente, más el mínimo del lote de enfrente.
    Es lo que el negocio hace de verdad: quien recibe huevo necesita saber de qué
    lote viene, y quien lo despachó necesita saber si llegó.

C · VISIBILIDAD TOTAL
    Todos ven todo. Es el estado actual.
    No se recomienda en ningún flujo: haría que la capacidad no sirviera para nada.
```

`A` se descarta con evidencia, no por gusto: `P-10` está certificado sobre la cadena
`egg_batches` + `chick_batches`, y cortar la fila puente rompería un proceso certificado.

---

## 5. Los siete flujos

Se listan tal como los registró `CROSS_MODULE_FLOW_MATRIX.md`. Al reconstruirlos aparece una
**asimetría en cómo estaban anotados** que conviene decir: el flujo 1 describe una cadena de
**dos saltos** (Progenitoras → Incubadora → Reproductora), mientras que los flujos 2 y 3
describen los dos saltos de la otra cadena por separado. No es un error de la matriz —los tres
existen— pero el flujo 1 exige una decisión extra que los otros no: si el origen alcanza al
**destino final** o solo al **siguiente eslabón**.

---

### Flujo 1 · El huevo de progenitoras acaba siendo un lote de reproductora

| | |
|---|---|
| **Unidades** | Progenitoras → *(Incubadora)* → Reproductora |
| **Entidad puente** | `egg_batches` con `generation = 'grandparent'`, y después `chick_batches` |
| **Identificador compartido** | `lots.lot_code` de origen y de destino |
| **Saltos** | **dos**: el huevo pasa por Incubadora antes de volverse lote de reproductora |

**Qué necesita ver el origen (Progenitoras).** Cuántos huevos despachó, cuándo, a qué
incubadora, cuántos se recibieron, y —esto es lo que decide el propietario— si el lote de
reproductora que nació de sus huevos existe y cómo rinde. Lo segundo es *evaluación genética de
su propio trabajo*, y es la razón por la que la trazabilidad generacional se construyó.

**Qué necesita ver el destino (Reproductora).** De qué lote de progenitoras viene su parvada,
con qué línea genética y en qué fecha. Es su antecedente sanitario y genético.

**Qué debe quedar oculto.** El día a día del otro: mortalidad diaria de progenitoras, su
consumo, sus inspecciones, sus costos.

**Qué falta decidir.** Si el origen ve el **resultado final** —el lote de reproductora— o se
detiene en el traspaso a Incubadora. Es la única pregunta de este flujo, y no es técnica.

**Recomendación · `B` con alcance de dos saltos.** El origen ve el lote resultante en categoría
`B` —identificador, fechas, estado, y los indicadores de rendimiento que ya publica `P-10`— y no
su interior. Motivo: sin eso, el productor de progenitoras no puede evaluar su propia genética,
que es exactamente lo que `GA-REM-037` acaba de certificar que el producto sabe medir.

---

### Flujo 2 · Despacho de huevo fértil a incubadora

| | |
|---|---|
| **Unidades** | Reproductora → Incubadora |
| **Entidad puente** | `egg_batches` (`generation = 'breeder'`) · eventos `egg_dispatch` / `egg_reception_hatchery` |
| **Identificador compartido** | `lot_code` · `egg_batches.id` |

**Qué necesita ver el origen.** Qué despachó, cuándo, cuánto se recibió y con qué merma. La
merma es suya: mide su calidad de postura y manejo.

**Qué necesita ver el destino.** Lo que viene en camino **antes** de que llegue, y de qué lote
viene: edad de la madre, línea genética y fecha de postura condicionan la incubación.

**Qué debe quedar oculto.** La operación diaria de la granja de reproductoras.

**Qué falta decidir.** Si la incubadora ve el despacho **antes de recibirlo**. Y, si la respuesta
es sí, el propietario está pidiendo implícitamente que el despacho registre su destino, porque
hoy no lo garantiza (**§2.2**).

**Recomendación · `B`, con destino declarado en el despacho.** Es el único flujo cuya decisión
arrastra un requisito de dato nuevo, y conviene que el propietario lo sepa al decidir: decir
«sí» aquí cuesta un campo obligatorio en el despacho, no solo una regla de lectura.

---

### Flujo 3 · Nacimiento y despacho de pollito

| | |
|---|---|
| **Unidades** | Incubadora → Engorde *(o → Reproductora, en cría)* |
| **Entidad puente** | `chick_batches` · eventos `chick_dispatch` / `bird_reception` |
| **Identificador compartido** | `lot_code` · `chick_batches.id` · `egg_batch_id` hacia atrás |

**Qué necesita ver el origen (Incubadora).** Cuántos pollitos entregó y cuántos se recibieron, y
—decisión— cómo se comportan después: la mortalidad de primera semana en destino es **el
indicador de calidad de la incubadora**, y sin él la incubadora no puede corregirse.

**Qué necesita ver el destino (Engorde).** Procedencia, fecha de nacimiento, sexaje, cantidad y
antecedente genético del lote que recibe.

**Qué debe quedar oculto.** Parámetros internos de incubación —`hatchery_params`, temperaturas,
volteos— y, del lado del engorde, su costo y su facturación.

**Qué falta decidir.** Si Incubadora ve la mortalidad de primera semana del lote de engorde. Es
un dato *del destino* que mide *al origen*.

**Recomendación · `B` con una excepción nombrada.** El indicador de primera semana entra en
categoría `B` como **agregado acotado** —un número y una ventana de días—, no como acceso a los
eventos diarios del lote de engorde. Así el origen se mide sin abrir el interior del destino.

---

### Flujo 4 · Transferencia de aves entre granjas

| | |
|---|---|
| **Unidades** | cualquiera → cualquiera |
| **Entidad puente** | `bird_movements`, colgado de un `operational_event` |
| **Identificador compartido** | `lot_code` de origen y destino |

Es el flujo más abierto: nada en el modelo restringe qué unidad transfiere a cuál. Una
transferencia dentro de la misma unidad —de una granja de engorde a otra— es un movimiento
interno y no plantea problema. Una transferencia **entre unidades distintas** es un traspaso, y
debería tratarse como los tres anteriores.

**Qué falta decidir.** Si el producto debe **restringir qué transferencias son legítimas** entre
unidades, o solo controlar quién las ve. Son dos cosas distintas y conviene no mezclarlas.

**Recomendación · `B` para la visibilidad; y *no* legislar todavía qué transferencias son
válidas.** Prohibir combinaciones exigiría un catálogo de transiciones permitidas que ninguna
fuente normativa contiene, y `§64` prohíbe inventarlo.

---

### Flujo 5 · Consolidación a SAP

| | |
|---|---|
| **Unidades** | las cuatro → *(sistema externo)* |
| **Entidad puente** | `consolidated_movements` |
| **Rol implicado** | `Analista SAP` |

La consolidación **es** transversal por definición: agrupa el movimiento de toda la empresa para
enviarlo a SAP. Filtrarla por unidad la rompería, y con ella `P-08`.

**Qué falta decidir.** Si `Analista SAP` es una **excepción normativa declarada** al filtro por
unidad —ve las cuatro siempre— o si se le conceden unidades como a cualquiera.

**Recomendación · excepción declarada y escrita.** No como efecto lateral de que su consulta no
filtre, sino como regla explícita, con prueba que la demuestre. Una excepción que solo existe
porque nadie puso el filtro es indistinguible de un fallo.

`P-08` está `PARTIAL` y bloqueado por contrato externo; esta decisión **no lo desbloquea ni lo
toca**, solo evita que la nueva capacidad lo empeore.

---

### Flujo 6 · Revisión y aprobación

| | |
|---|---|
| **Unidades** | las cuatro → *(control)* |
| **Entidad puente** | `operational_events` |
| **Roles implicados** | contraloría · administración de empresa |

Aquí hay una **colisión con una decisión ya tomada y certificada**, y es el hallazgo más
delicado de este análisis.

`OD-08` decidió —y `P-14` está certificado sobre ello— que administración y contraloría reciben
avisos **de toda la empresa, sin filtro de área**. En el código esto es literal:
`FUNCIONES_DE_EMPRESA` no aplica ningún filtro de alcance, frente a `FUNCIONES_DE_AREA` que sí.

Si el filtro por unidad de negocio se aplicara sin más a las notificaciones y a las colas de
revisión, **un contralor con dos de las cuatro unidades dejaría de recibir en silencio los
avisos de las otras dos**, y `P-14` pasaría a incumplir `OD-08` sin que ninguna prueba actual lo
detecte.

**Qué falta decidir.** Si contraloría y administración son transversales por definición —como
`Analista SAP`— o si también se les conceden unidades.

**Recomendación · transversales por definición, declarado.** Controlar es, por oficio, mirar lo
que uno no opera. Y esta decisión debe tomarse **antes** de implementar, no después: es el punto
concreto donde la nueva capacidad puede romper un proceso ya certificado.

---

### Flujo 7 · Trazabilidad generacional

| | |
|---|---|
| **Unidades** | las cuatro ↔ las cuatro |
| **Entidad puente** | `egg_batches` + `chick_batches` encadenados por `egg_batch_id` |
| **Proceso** | `P-10`, **certificado** |

Es el flujo que más tensión produce, porque su valor **es** atravesar las cuatro unidades: seguir
un pollo de engorde hasta la abuela que puso el huevo.

**Qué falta decidir.** Si la cadena completa se ve siempre, o solo desde las unidades que el
usuario tiene.

**Recomendación · `B` sobre la cadena completa, con dos niveles.** La **cadena** —qué lote vino
de qué lote, con fechas y cantidades— se ve entera: es el objeto certificado de `P-10` y
recortarla la destruye. El **interior** de cada eslabón sigue en `C`: ver que un lote existe en
la cadena no es ver su mortalidad diaria.

Es la distinción entre *saber de dónde viene* y *saber cómo le fue*, y es la que permite
conservar `P-10` sin abrir el producto entero.

---

## 6. Resumen para decidir

| # | Flujo | Origen ve | Destino ve | Oculto | Opción recomendada | Coste añadido |
|:--:|---|---|---|---|:--:|---|
| 1 | Progenitoras → Reproductora | traspaso + lote resultante | antecedente genético | interior de ambos | **B**, dos saltos | ninguno |
| 2 | Reproductora → Incubadora | despacho y merma | lo que viene en camino | operación diaria | **B** | **destino en el despacho** |
| 3 | Incubadora → Engorde | entrega + 1.ª semana | procedencia y sexaje | `hatchery_params` · costos | **B** + agregado acotado | ninguno |
| 4 | Transferencia entre granjas | su lado | su lado | el ajeno | **B**, sin legislar transiciones | ninguno |
| 5 | Consolidación SAP | — | — | — | **excepción declarada** | prueba de la excepción |
| 6 | Revisión y aprobación | — | — | — | **transversal declarado** | **protege `P-14`** |
| 7 | Trazabilidad generacional | cadena entera | cadena entera | interior de cada eslabón | **B**, dos niveles | ninguno |

```
Opción A recomendada en   0 / 7
Opción B recomendada en   5 / 7
Excepción declarada en    2 / 7   (flujos 5 y 6)
Opción C recomendada en   0 / 7
```

## 6 bis. Resuelto · `OD-10.a` y `OD-10.b` (2026-09-07)

El propietario eligió la **opción B** para los siete flujos, y la **opción A** para el destino del
despacho:

```
CROSS-BUSINESS-UNIT VISIBILITY  =  LIMITED HANDOFF CONTRACT
EL DESTINO SE DECLARA AL CREAR EL DESPACHO
```

Las cuatro categorías de `§3` —`A` propio, `B` traspaso, `C` interno ajeno, `D` agregado— pasan a
ser normativas. La clasificación campo por campo de `B` frente a `C`, para cada flujo, es trabajo
de `GA-REM-040`.

Las excepciones de los flujos 5 y 6 quedan cubiertas: la del analista de SAP por el mecanismo de
`OD-09.a` —transversalidad concedida explícitamente—, y la de revisión y aprobación por
`OD-09.a` directamente.

## 7. Lo que este documento NO hace

- No crea `BusinessUnit`, ni ninguna tabla, ni ninguna migración.
- No convierte `BirdTypeEnum` en control de acceso.
- No modifica ninguna certificación: `P-10` y `P-14` siguen como están.
- No decide. **Las siete decisiones quedan `PENDIENTE DE PROPIETARIO`.**
