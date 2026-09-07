# QUÉ PASA CON LO QUE YA ESTÁ GUARDADO

Análisis de decisión · 2026-09-07 · **sin código** · deriva de
`audit/remediation/LEGACY_DATA_MODULE_MAPPING_MATRIX.md` y de `specs/remediation/ENV-01`

---

## 1. Un hecho que cambia el peso de este bloqueante

La auditoría del 2026-09-07 clasificó la migración del legado como **bloqueante**, con el
argumento de que dejaría «la operación parada el lunes por la mañana».

Al preparar este análisis se contrastó contra `ENV-01`, aclaración normativa del propietario del
2026-09-04, **`VIGENTE`**, cuyo alcance declarado es «todo el proyecto: informes, gates,
políticas de push, estrategia de datos»:

```
CURRENT DEPLOYED ENVIRONMENT   =  SHARED DEVELOPMENT / TEST / CERTIFICATION
REAL PRODUCTION                =  NOT DEPLOYED YET
CURRENT DATABASE BUSINESS DATA =  TEST / CERTIFICATION DATA
CURRENT USERS                  =  DEVELOPMENT / TEST / CERTIFICATION USERS
REAL PRODUCTION RELEASE        =  FUTURE SEPARATE GATE
```

**No hay operación que parar.** Los «usuarios existentes» y los «datos existentes» de este
bloqueante son datos de prueba y certificación. Ninguna empresa real depende de ellos, ningún
cliente perdería acceso el lunes, y ninguna fila de negocio real se filtraría el día de la
migración.

Esto **no** anula el bloqueante: lo **traslada de gate**.

```
ANTES   bloquea la spec GA-REM-040
AHORA   bloquea el primer alta de cliente real  (READY_FOR_REAL_PRODUCTION)
```

Y hay una parte que **sigue bloqueando la spec**, por una razón distinta de la que la auditoría
dio. Es la sección siguiente.

---

## 2. Lo que no es un problema de legado, aunque lo parezca

La auditoría listó tres bloqueantes de datos. Al releerlos, **dos de los tres no son del pasado:
son permanentes.**

### 2.1 Los eventos sin lote seguirán existiendo mañana

`operational_events.lot_id` es nulable, y lo es **a propósito**: desde `i9j0k1l2m3n4` las
inspecciones de granja se registran sin lote, porque una inspección es de la granja, no de una
parvada. `GA-REM-039 §5` ya lo dejó escrito para las notificaciones, y la solución que adoptó
fue no avisar a gerente ni supervisor, sin que nada fallara.

De modo que la pregunta «¿de qué unidad es una inspección sin lote?» **no se responde migrando
datos viejos**. Se seguirá haciendo la pregunta con cada inspección nueva, indefinidamente.

**Es una regla de producto, no una tarea de migración**, y por eso sí bloquea la spec.

### 2.2 Los lotes de huevo y de pollito no son ambiguos: son bilaterales

La auditoría los marcó `BLOQUEANTE` por «pertenecer a dos unidades a la vez por diseño».
Verificado contra el modelo, la descripción más exacta es otra: llevan **una columna por cada
lado** (`source_lot_id` / `hatchery_lot_id`, y `hatchery_lot_id` / `destination_lot_id`).

No hay que decidir de quién son. La fila **es el traspaso**, y cada columna dice a quién alcanza.
Se desarrolla en `BUSINESS_UNIT_CROSS_FLOW_DECISION_MATRIX.md §2.1`.

**Corrección registrada.** De los tres bloqueantes de datos que declaró la auditoría, **queda
uno y medio**: los eventos sin lote y las inspecciones —que son el mismo— y ninguno de ellos por
ser legado.

### 2.3 Y hay una vía de recuperación que la auditoría no vio

`Lot.bird_type` es nulable, y la auditoría concluyó de ahí que un lote sin ese campo es
inclasificable. Pero **`Breed` también lleva `bird_type`**, y `Lot.breed_id` apunta a `Breed`.

```
Lot.bird_type            si está, manda
  └─ si es nulo →  Lot.breed_id → Breed.bird_type      candidato
       └─ si tampoco →  sin clasificar
```

Esto **reduce** el volumen de lo inclasificable, y es derivación de dato persistido, no
adivinación. Aun así **requiere ratificación del propietario**, porque afirmar «la raza dice la
unidad» es una inferencia de negocio: hay razas que se usan en más de una. Se propone, no se
aplica.

---

## 3. Las preguntas del propietario, una por una

### 3.1 ¿Qué pasa con las empresas existentes?

```
A) todas las unidades habilitadas          nadie pierde nada, el aislamiento nace apagado
B) ninguna habilitada                       correcto por defecto, todo el mundo fuera
C) transición controlada                    se habilita lo que la empresa demuestre usar
D) periodo de gracia                        A durante N días, luego B
```

Con `ENV-01` sobre la mesa, esta pregunta **casi se disuelve para hoy**: las empresas actuales
son de prueba. Se vuelve importante el día del primer cliente real, y ese día la respuesta
natural es que **el alta declare sus unidades**, porque es un dato comercial que alguien conoce.

**Recomendación · `C` para el alta real, `A` para el entorno compartido actual**, y decirlo así
en la spec: el entorno de certificación no debe quedar inutilizable por una capacidad que aún se
está construyendo.

### 3.2 ¿Qué pasa con los usuarios existentes?

Es la decisión 5 de la auditoría, la que declaró bloqueante. Con `ENV-01`, los usuarios
existentes son de desarrollo y certificación.

**Recomendación · `A` para los usuarios actuales** —de prueba, sin consecuencia real— y **`C`
para los usuarios de un cliente real**: el alta los concede. Lo que **no** debe hacerse es `C)
derivarlos de su historial de actividad`, que la auditoría ya descartó y `§64` prohíbe.

### 3.3 ¿Y un usuario **nuevo** sin ninguna unidad asignada?

Esta pregunta **no estaba en la auditoría**, y no es de migración: es de régimen permanente.
Mañana alguien creará un usuario y no le pondrá unidad.

```
A) no puede entrar                    seguro, y desconcertante: la contraseña es correcta
B) entra, y ve solo lo transversal    puede administrarse, no ve operación de ninguna unidad
```

**Recomendación · `B`.** Denegar el acceso confunde un problema de configuración con uno de
credenciales, y deja al usuario sin forma de entender qué le falta. Entrar y encontrar la
operación vacía, con un aviso claro, es diagnosticable.

Requiere decidir **qué es «transversal»** —§3.7—.

> **`RESUELTA` · 2026-09-07 · `OD-09.c`.** El propietario eligió esta opción. El usuario sin
> unidades **entra**, usa lo transversal que su rol permita y no ve ni opera dato productivo.
> Nunca se retrocede a «toda la empresa» como valor por defecto.

### 3.4 ¿Qué pasa con los registros clasificables?

Los que tienen `bird_type`, directo o vía raza (§2.3). Se clasifican y no hay decisión que tomar,
salvo ratificar la vía de la raza.

### 3.5 ¿Qué pasa con los registros ambiguos?

Los eventos sin lote, sobre todo inspecciones. **La decisión permanente del producto.**

```
A) FAIL OPEN        sin unidad → lo ve todo el mundo
                    la capacidad no aísla: basta una inspección para ver la granja

B) FAIL CLOSED      sin unidad → no lo ve nadie
                    seguro, y hace desaparecer todas las inspecciones de todas las pantallas
                    incluidas las de quien acaba de registrarlas

C) CUARENTENA       sin unidad → estado explícito «pendiente de clasificar»
                    visible para quien lo registró y para administración
                    con una bandeja de trabajo para resolverlo
```

`A` vacía la capacidad de sentido. `B` es la recomendación general de la auditoría (`§66`) y,
aplicada aquí, borra de la vista datos que alguien acaba de escribir —el peor mensaje posible.

**Recomendación · `C`.** Es la única que no obliga a elegir entre seguridad y operación: nada se
filtra, nada desaparece, y lo indeterminado queda **nombrado** en vez de silenciado. Cuesta un
estado más y una pantalla; a cambio, hace visible un problema que las otras dos ocultan en
direcciones opuestas.

Y encaja con el precedente del propio proyecto: `GA-REM-039` ya resolvió el evento sin área **no
inventándole una** y dejando que el resolutor devolviera un conjunto vacío sin fallar.

### 3.6 ¿Qué pasa con los registros de doble unidad?

No los hay. Son bilaterales (§2.2). **Sin decisión pendiente.**

### 3.7 ¿Qué capacidades quedan sin ninguna unidad?

Candidatas, del catálogo RBAC ya existente:

```
transversal        auth · users · roles · companies · areas · audit · notifications
                   y los maestros no específicos de una línea
por unidad         lots · operations · reports · dashboards · traceability · sap
```

**Recomendación:** ratificar esta frontera como parte de la decisión, no derivarla en la
implementación. Es lo que define qué puede hacer el usuario de §3.3.

> **`RESUELTA` · 2026-09-07 · `OD-09.b`.** Frontera por planos, con los veintidós maestros
> clasificados **una vez en el catálogo** y no pantalla por pantalla. Administrar el acceso no
> concede acceso al dato: un administrador puede asignar Incubadora a otro usuario sin poder
> consultar sus lotes.

### 3.8 ¿Quién administra la transición?

Hoy conviven un **Super Administrador global** —sembrado con `company_id = None`, verificado en
`recipients.py`— y el **Administrador de Empresa**.

```
habilitar unidades A UNA EMPRESA          decisión comercial   → Super Administrador
conceder unidades A UN USUARIO            decisión operativa   → Administrador de Empresa
                                                                  dentro de lo habilitado
```

La segunda mitad toca `OD-05` —escalada de privilegios, **todavía abierta**—: un administrador de
empresa no debe poder concederse a sí mismo lo que su empresa no tiene. **No se resuelve aquí**;
se señala la dependencia.

### 3.9 ¿Cómo evitamos el `fail open`?

No con una regla global, sino con tres concretas:

1. **Nada de `fail open` global.** El valor por defecto de una consulta sin unidad resuelta es
   negar, no permitir.
2. **La cuarentena no es `fail open`.** Un registro en cuarentena lo ven **dos** partes
   nombradas —quien lo registró y administración—, no «todos».
3. **Los agregados cuentan.** Un total calculado sobre filas que el usuario no puede ver filtra
   por diferencia. Es la fuga que no deja rastro, y la única forma de impedirla es que el
   agregado se calcule sobre el mismo conjunto filtrado que el listado.

### 3.10 ¿Cómo evitamos parar toda la operación?

Con el orden, no con excepciones:

```
1  catálogo y modelo, sin efecto             nada cambia para nadie
2  clasificación de lo existente             se puede ver y corregir antes de que filtre
3  bandeja de cuarentena                     lo indeterminado tiene dónde resolverse
4  filtro en modo informe                    se registra a quién se le habría negado qué
5  filtro efectivo                           solo cuando 4 esté en silencio
```

El paso 4 es el que hace que esto no sea un salto a ciegas: **medir la denegación antes de
aplicarla**. Si al activarlo aparecen mil denegaciones diarias, la clasificación está incompleta
y se corrige sin que nadie se haya quedado fuera.

---

## 4. Resumen

| # | Pregunta | Opciones | Recomendación | ¿Bloquea la spec? |
|:--:|---|---|---|:--:|
| 1 | Empresas existentes | A · B · C · D | **C** real · **A** entorno compartido | no |
| 2 | Usuarios existentes | A · B · C | **A** actuales · **C** cliente real | no |
| 3 | Usuario sin unidad *(nueva)* | denegar · transversal | **`RESUELTA` · transversal → `OD-09.c`** | ~~SÍ~~ |
| 4 | Registros clasificables | — | clasificar; ratificar vía raza | no |
| 5 | Registros ambiguos | fail open · fail closed · cuarentena | **cuarentena** | **SÍ** |
| 6 | Registros de doble unidad | — | **no existen**: son bilaterales | no |
| 7 | Capacidades transversales | — | **`RESUELTA` · frontera por planos → `OD-09.b`** | ~~SÍ~~ |
| 8 | Quién administra | — | comercial vs operativo; depende de `OD-05` | no |
| 9 | Evitar `fail open` | — | denegar por defecto · agregados incluidos | no |
| 10 | No parar la operación | — | modo informe antes del filtro | no |

```
BLOQUEANTES DE LA SPEC       1   (registros ambiguos)   — eran 3
RESUELTOS POR OD-09          2   usuario sin unidad · frontera transversal   (2026-09-07)
BLOQUEANTES DEL ALTA REAL    2   (empresas y usuarios de un cliente real)
DESAPARECIDOS POR ENV-01     0   ninguno desaparece; dos cambian de gate
FALSOS BLOQUEANTES           1   «registros de doble unidad»
```

Lo que cambia respecto de la auditoría no es cuántos hay, sino **cuáles son y cuándo hacen
falta**: lo que se creía urgente por el legado resultó ser urgente por el régimen permanente, y
lo que se creía ambiguo por diseño resultó estar ya resuelto en el modelo.

---

## 5. Lo que este documento NO hace

- No migra nada, no crea tablas y no borra ninguna fila. **`§65` · sin migración destructiva.**
- No propone eliminar dato de negocio que no se pueda clasificar. La cuarentena lo conserva.
- No resuelve `OD-05`.
- No decide. **Las diez preguntas quedan `PENDIENTE DE PROPIETARIO`.**
