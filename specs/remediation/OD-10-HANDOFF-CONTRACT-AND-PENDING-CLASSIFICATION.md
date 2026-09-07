# OD-10 — CONTRATO DE TRASPASO Y CLASIFICACIÓN PENDIENTE

## Metadata
| Campo | Valor |
|---|---|
| ID | `OD-10` |
| Tipo | **Decisión normativa** (no es una remediación) |
| Fecha | 2026-09-07 |
| Origen | Resolución explícita del propietario del producto |
| Estado | **VIGENTE** |
| Alcance | Acceso por unidad de negocio: `GA-REM-040` y sus derivados |
| Antecedente | `audit/remediation/BU_DECISION_BRIEF_D01_D02.md` |
| Resuelve | `BU-D01 = B` · destino del despacho `= A` · `BU-D02 = C` |
| Complementa | `OD-09` · `ENV-01` |
| Preserva | `P-10` `CERTIFIED` · `P-14` `CERTIFIED` · `OD-08` |

---

## 0. Por qué es un `OD` aparte y no una enmienda de `OD-09`

`OD-09` declara una cosa concreta:

```
VISIBILIDAD DE CONTROL  y  ACCESO OPERATIVO  SON CAPACIDADES DISTINTAS
```

De ahí salen sus tres partes, y las tres tratan de **quién** atraviesa el eje: contraloría,
administración, el usuario sin unidades.

Esta resolución declara otra cosa, y no se deduce de la anterior:

```
ENTRE UNIDADES SOLO PASA EL CONTRATO
Y LO QUE NO SE PUEDE CLASIFICAR QUEDA NOMBRADO
```

Trata del **plano operativo** entre unidades: qué ve un usuario de producción normal, que en
`OD-09` no se tocó. Meterla dentro de `OD-09` diluiría una declaración que es precisa, y
sugeriría que se puede cambiar una sin revisar la otra.

Las dos van juntas en un solo `OD` porque **`BU-D02` es anterior a `BU-D01`**: un registro que no
se sabe de quién es no puede entrar en ningún contrato de traspaso.

---

## 1. Declaración

```
LA UNIDAD PROPIA        operación completa, según RBAC y reglas de negocio
LA UNIDAD AJENA         sin acceso general
EL TRASPASO             solo el contrato explícito, y solo en su contexto
LO NO CLASIFICABLE      pendiente de clasificar; ni se adivina ni se pierde
```

---

## 2. `OD-10.a` — El contrato de traspaso · resuelve `BU-D01` con la opción `B`

```
CROSS-BUSINESS-UNIT VISIBILITY  =  LIMITED HANDOFF CONTRACT
```

Cada unidad conserva **visibilidad autorizada completa sobre su propio dato**. Entre unidades se
comparte únicamente la información estrictamente necesaria para:

```
crear · ejecutar · recibir · confirmar · auditar · revertir o anular
```

el traspaso. **Participar en un traspaso no concede acceso a la unidad de enfrente.**

### 2.1 Lo que NO se recibe por participar en un traspaso

```
dato completo del lote ajeno          registros operativos ajenos
mortalidad ajena                      detalle de producción ajeno
flujo de trabajo interno ajeno        paneles ajenos
KPI ajenos                            agregados ajenos
exportaciones ajenas                  registros ajenos no relacionados
```

Solo se recibe lo que el **contrato de ese flujo** declare como compartido.

### 2.2 Las cuatro categorías

Toda la política se expresa con cuatro cajas, y se eligen así porque son comprobables: una prueba
puede afirmar «esto se ve» y «esto no» para cada una.

```
A · PROPIO           dato de las unidades concedidas. Operación completa según RBAC.
B · TRASPASO         la fila puente, y del lote de enfrente solo lo mínimo para actuar.
                     Solo lectura, ambos lados, y solo en el contexto del traspaso.
C · INTERNO AJENO    todo lo demás del otro lado. DENEGADO.
D · AGREGADO         totales, contadores, promedios, ratios, KPI, paneles, reportes.
                     Se calculan sobre A ∪ B. NUNCA sobre C.
```

La clasificación campo por campo de `B` frente a `C`, para cada flujo, es trabajo de
`GA-REM-040`. Esta decisión fija la regla, no el detalle.

### 2.3 Los agregados no son un detalle posterior

```
PROHIBIDA LA FUGA POR AGREGADO
```

Un usuario restringido **no puede deducir** dato ajeno mediante contador, suma, promedio, ratio,
KPI, panel, reporte o exportación. Un número calculado sobre filas que no puede ver no le enseña
la fila: le enseña que existe y cuánto pesa. Y es la única fuga que **no deja rastro y que nadie
reporta**, de modo que no puede quedar para una fase final.

### 2.4 Las entidades de traspaso conservan sus dos lados

`egg_batches` y `chick_batches` llevan origen y destino en **columnas separadas**:

```
egg_batches      source_lot_id   →  hatchery_lot_id
chick_batches    hatchery_lot_id →  destination_lot_id
```

**La fila es el traspaso.** No se les impone propiedad única, y **no se les añade una columna de
unidad** para forzarla: sus dos lados ya dicen a quién alcanza cada una.

### 2.5 Anulación y reversión

El producto ya distingue `RETURNED`, `CORRECTED`, `REJECTED` y permite anular. Un traspaso
anulado o rechazado **sigue el contrato**: el lado que lo veía lo ve desaparecer **con su motivo**,
no evaporarse sin explicación. Un camión que no llega tiene que poder entenderse.

### 2.6 `P-10` se conserva

La trazabilidad generacional está certificada sobre la cadena completa. La **cadena** —qué lote
vino de qué lote, con fechas y cantidades— es categoría `B` y se ve entera. El **interior** de
cada eslabón sigue en `C`.

Es la diferencia entre *saber de dónde viene* y *saber cómo le fue*.

### 2.7 La excepción de control

`OD-09.a` sigue en pie: los roles de control expresamente autorizados conservan visibilidad
transversal **dentro de su misma empresa**, incluidos los agregados. Un usuario operativo normal,
no.

```
VISIBILIDAD DE CONTROL  ≠  AUTORIDAD OPERATIVA TRANSVERSAL
```

---

## 3. `OD-10.b` — El destino del despacho · opción `A`

```
EL DESTINO DE UN DESPACHO SE DECLARA AL CREARLO
```

Así la unidad receptora identifica **qué traspasos pendientes son suyos**, sin que se le expongan
todos los despachos pendientes de la empresa.

### 3.1 Lo que sigue y lo que no

```
LA UNIDAD DESTINO PUEDE VER    los traspasos dirigidos explícitamente a ella,
                               antes de recibirlos

NO PUEDE VER                   todos los despachos pendientes de la empresa
```

### 3.2 La columna no se decide aquí

Esto es un **contrato de negocio**, no un esquema. `GA-REM-040` debe auditar el modelo real
—`destination_farm_id`, `destination_plant_id`, la granja, la incubadora, el lote destino— y
determinar qué combinación existente satisface el contrato.

```
PROHIBIDO   crear `destination_business_unit_id` por defecto, sin esa auditoría
```

Puede que el dato necesario ya exista y solo falte hacerlo obligatorio para este flujo.

### 3.3 Cambiar el destino después

Ninguna fuente normativa dice si el destino puede cambiarse una vez creado el despacho.

```
SPEC DECISION REQUIRED   antes de implementar ese comportamiento
```

No se inventa edición libre. Si no aparece norma al escribir la spec, queda registrado como hueco
y se resuelve antes de construirlo.

---

## 4. `OD-10.c` — Clasificación pendiente · resuelve `BU-D02` con la opción `C`

```
DATO DE NEGOCIO NO CLASIFICABLE  =  PENDIENTE DE CLASIFICAR
```

Cuando un registro no pueda asociarse **con seguridad** a una unidad:

```
NO ADIVINAR        NO ABRIR         NO BORRAR        NO OCULTAR PARA SIEMPRE
```

### 4.1 Quién lo ve mientras está pendiente

```
PUEDE VERLO    1. quien lo creó o lo registró
               2. la administración o el control de la empresa expresamente autorizados

NO PUEDE       todos los usuarios de la empresa
               todos los usuarios de una unidad
```

No es `fail open`: los que ven son **dos partes nombradas**, no «todos».

### 4.2 El recorrido

```
SIN CLASIFICAR
    ↓
PENDIENTE DE CLASIFICAR
    ↓
clasificación por quien esté autorizado
    ↓
asignación de unidad, o clasificación como contrato
    ↓
reglas normales de visibilidad
```

La interfaz final no se diseña aquí.

### 4.3 No es una quinta unidad

```
PROHIBIDO   crear una unidad falsa «SIN ASIGNAR» como si fuera una línea productiva
```

Es un **estado de clasificación**, o el mecanismo equivalente que determine la arquitectura. Las
unidades productivas son cuatro y no cambian por esto.

### 4.4 La clasificación es explícita, y se audita

No se auto-asigna por rol, por quien lo creó, por el nombre de la granja, por la URL ni por
ninguna conjetura, salvo reglas deterministas ya certificadas.

Y deja rastro en **`P-09`**, no en una auditoría paralela:

```
quién clasificó · cuándo · estado anterior · nueva clasificación · motivo u origen si aplica
```

### 4.5 Nada se pierde en silencio

Los registros pendientes deben poder **contarse, revisarse, clasificarse y auditarse**. Hoy nadie
sabe cuánto dato quedaría sin clasificar, porque no hay dónde mirarlo; el estado lo hace medible.

### 4.6 El precedente del proyecto

`GA-REM-039 §5` ya se encontró con el evento sin área y **no le inventó una**: devolvió un
conjunto vacío de destinatarios, sin fallar y sin fingir. `OD-10.c` es esa misma respuesta, con
una bandeja para resolverla.

---

## 5. Lo que esta decisión NO autoriza

- **No crea** `GA-REM-040`, ni tablas, ni migraciones, ni guardas, ni columnas.
- **No impone** `business_unit_id` a las entidades que representan el cruce.
- **No convierte** `BirdTypeEnum` en control de acceso: sigue siendo enum de dominio.
- **No modifica** el `RBAC` ni ninguna de las 198 rutas.
- **No reabre** ninguna certificación. `FUNCIONAL 14/15` sin cambios.
- **No toca** `P-08`, `GA-TD-014`, `R-98`, `R-99` ni el despliegue automático.
- **No resuelve** `BU-D05`, que `ENV-01` sitúa en el alta del primer cliente real.
- **No resuelve** `OD-05`.
- **No mezcla** unidad de negocio con `Area`: son dos ejes distintos.

## 6. Trazabilidad

| Dosier | Pregunta | Respuesta | Parte |
|---|---|:--:|---|
| `BU-D01` | Qué sigue viendo cada línea cuando el producto cambia de manos | **B** | `OD-10.a` |
| `BU-D01` acompañante | ¿El despacho declara su destino al crearse? | **A** | `OD-10.b` |
| `BU-D02` | Los registros que no se puede saber a qué línea pertenecen | **C** | `OD-10.c` |

## 7. Consecuencia sobre la preparación de la spec

```
BLOQUEANTES DE LA SPEC GA-REM-040     2  →  0
```

`GA-REM-040` queda autorizada a escribirse. **Autorizada a escribirse, no a construirse.**
