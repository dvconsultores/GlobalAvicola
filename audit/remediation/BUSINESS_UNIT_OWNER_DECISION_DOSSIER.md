# UNIDADES DE NEGOCIO · LO QUE HAY QUE DECIDIR ANTES DE CONSTRUIR

Dosier de decisión · 2026-09-07

```
MODO                     ANÁLISIS DE DECISIÓN
CÓDIGO MODIFICADO        NINGUNO
TABLAS CREADAS           NINGUNA
CERTIFICACIONES TOCADAS  NINGUNA
SPEC CREADA              NINGUNA
```

---

## 1. Dos palabras que hasta ahora eran una

El proyecto llama «módulo» a dos cosas distintas, y eso ha hecho que la conversación fuera
confusa. Aquí se separan y no se vuelven a mezclar:

```
MÓDULO RBAC          un permiso dentro del sistema
                     operations · lots · masters · reports · users · sap …
                     EXISTE · está certificado · no se toca

UNIDAD DE NEGOCIO    una línea de producción de la empresa
                     Progenitoras · Reproductora · Incubadora · Engorde
                     NO EXISTE en ninguna forma
```

Son dos ejes independientes. Una persona podrá tener permiso de `operations` y aun así no ver la
operación de Incubadora, porque tiene el permiso pero no la unidad.

Lo único que hoy se parece a una unidad es `BirdTypeEnum` —`grandparent`, `breeder`, `hatchery`,
`broiler`—, que es un **campo descriptivo de un lote**, no un control de acceso. Este dosier lo
usa para razonar sobre la correspondencia con el negocio y **no propone convertirlo en permiso**.

| Unidad de negocio | Valor descriptivo actual | ¿Es correspondencia exacta? |
|---|---|---|
| Progenitoras | `grandparent` | sí |
| Reproductora | `breeder` | sí |
| Incubadora | `hatchery` | sí, y además tiene `hatchery_purpose` |
| Engorde | `broiler` | sí |

Las cuatro se corresponden. Pero el campo **es nulable en `lots`**, de modo que la
correspondencia existe donde el dato está, y hay filas donde no está.

---

## 2. La pregunta de fondo, en lenguaje de negocio

> Una empresa contrata Incubadora y Engorde, pero no Progenitoras. Otra contrata las cuatro.
> Dentro de la primera, Ana lleva la incubadora y Luis el engorde.
>
> **¿Qué ve cada uno, y qué no debería ver nunca?**

Hoy la respuesta es que todos ven todo. No porque se haya decidido así, sino porque la pregunta
no se había hecho todavía.

---

## 3. Cuántas decisiones hay, de verdad

La auditoría del 2026-09-07 enumeró **8**. Al releer las veintiuna matrices para este dosier,
el número real es **12**.

**Ninguna de las ocho desaparece.** Se añaden cuatro que la auditoría no había formulado:

```
+ Un usuario nuevo sin ninguna unidad asignada          régimen permanente, no migración
+ La empresa deja de tener una unidad que sí tenía      nadie lo había preguntado
+ ¿Contraloría y administración son transversales?      COLISIONA con OD-08 y con P-14 certificado
+ ¿Qué permisos RBAC quedan fuera del filtro?           afecta a todos los usuarios, no solo a los nuevos
```

Las cuatro tienen algo en común, y explica por qué se escaparon: la auditoría miró **el pasado**
—qué datos hay guardados y cómo clasificarlos— y estas cuatro son del **régimen permanente**, de
cómo funcionará el producto todos los días después.

Y hay un movimiento en sentido contrario, que también hay que decir:

```
− «Registros de doble unidad»    NO era una decisión. El modelo ya lo resuelve.
                                 Las filas de traspaso llevan una columna por cada lado.
```

**Cambia además cuáles bloquean.** La auditoría dijo que bloqueaban dos: los flujos entre
unidades y la migración de usuarios. Con `ENV-01` a la vista —no hay producción real
desplegada—, la migración **deja de bloquear la spec** y pasa a bloquear el alta del primer
cliente real. En su lugar bloquean tres decisiones nuevas y una que la auditoría no había
considerado bloqueante.

```
Bloqueaban antes   2      flujos · migración de usuarios
Bloquean ahora     5      flujos · registros sin clasificar · usuario sin unidad
                          contraloría transversal · frontera del catálogo
```

---

## 4. Las doce decisiones

Los identificadores `BU-Dnn` son **provisionales de este documento**. No son `OD-` definitivos:
esos los asigna el propietario al decidir.

---

### `BU-D01` · Qué sigue viendo cada línea cuando el producto cambia de manos

> Cuando un lote de huevo sale de Reproductora y entra en Incubadora, ¿qué sigue viendo la gente
> de Reproductora, y qué empieza a ver la gente de Incubadora?

**Por qué importa.** Es la decisión que define si esta capacidad sirve para algo. Si cada línea
sigue viendo todo, no hemos aislado nada; si deja de ver el traspaso, rompemos la trazabilidad
que ya está certificada.

**Evidencia.** Siete flujos atraviesan unidades. Los siete están hoy sin especificar y los siete
muestran todo a todos. `CROSS_MODULE_FLOW_MATRIX.md §3`.

**Opciones.** Aislamiento estricto · **contrato de traspaso** · visibilidad total.

**Recomendación · contrato de traspaso**, con el detalle flujo por flujo en
`BUSINESS_UNIT_CROSS_FLOW_DECISION_MATRIX.md`. Cada línea ve lo suyo, más el papel de entrega, más
lo mínimo del lote de enfrente para poder trabajar: identificador, cantidad, fecha, estado
sanitario. El interior del otro —su mortalidad diaria, su consumo, sus costos— no.

**Si no se decide.** No se puede construir. Cualquier elección por omisión rompe un proceso
certificado o vacía la capacidad de contenido.

**Estado · `PENDIENTE DE PROPIETARIO` · BLOQUEANTE**

---

### `BU-D02` · Los registros que no se puede saber a qué línea pertenecen

> Una inspección de granja no es de ninguna parvada concreta. ¿Quién debe verla?

**Por qué importa.** No es un problema de datos viejos. Las inspecciones se registran sin lote
**a propósito**, y se seguirán registrando así mañana y el año que viene. Sea cual sea la
respuesta, será la respuesta para siempre.

**Evidencia.** La inspección de granja admite no tener lote desde `i9j0k1l2m3n4`. `GA-REM-039`
ya se topó con esto para las notificaciones y resolvió no inventarle un área.

**Opciones.**

```
lo ve todo el mundo      basta una inspección para ver la granja entera: no aísla
no lo ve nadie           seguro, y borra de la pantalla lo que uno acaba de escribir
pendiente de clasificar  lo ve quien lo registró y administración, con bandeja para resolverlo
```

**Recomendación · pendiente de clasificar.** Es la única que no obliga a elegir entre seguridad y
operación. Nada se filtra, nada desaparece, y lo indeterminado queda **nombrado** en lugar de
silenciado en una de las dos direcciones.

**Si no se decide.** Se elegirá una de las dos malas sin querer: o una puerta abierta, o
inspecciones que se evaporan.

**Estado · `PENDIENTE DE PROPIETARIO` · BLOQUEANTE**

---

### `BU-D03` · La auditoría

> ¿Puede alguien de Engorde leer en el historial que se aprobó un movimiento de Incubadora?

**Por qué importa.** La auditoría cuenta lo que pasó. Filtrarla protege; no filtrarla convierte
el historial en la puerta trasera por la que se ve lo que la pantalla principal oculta.

**Evidencia.** `audit_logs` es hoy visible por empresa, sin más eje.

**Opciones.** Filtrar igual que el resto · dejarla completa para quien tenga permiso de auditoría
· dejarla completa para todos.

**Recomendación · completa para quien tenga el permiso de auditoría, filtrada para el resto.**
Auditar es, por oficio, mirar lo que uno no opera; pero eso vale para el auditor, no para todos.

**Si no se decide.** Queda como está, y es una fuga silenciosa: nadie mira el historial buscando
un agujero hasta que lo encuentra.

**Estado · `PENDIENTE DE PROPIETARIO`**

---

### `BU-D04` · El analista de SAP

> Para enviar a SAP hay que sumar el movimiento de las cuatro líneas. ¿El analista las ve todas?

**Por qué importa.** La consolidación es transversal por definición. Filtrarla la rompe.

**Recomendación · sí, y escrito como excepción.** No como efecto lateral de que su consulta no
filtre, sino como regla declarada y con prueba. Una excepción que solo existe porque nadie puso
el filtro es indistinguible de un fallo.

**Si no se decide.** O se rompe la consolidación, o el analista ve todo sin que conste por qué.

**Estado · `PENDIENTE DE PROPIETARIO`** · no toca `P-08`, que sigue bloqueado por contrato externo.

---

### `BU-D05` · Las empresas y los usuarios que ya existen

> El día que esto se encienda, ¿qué líneas tiene cada empresa y cada persona?

**Por qué importa —y por qué menos de lo que parecía.** `ENV-01`, aclaración vigente del
propietario, dice que **no hay producción real desplegada**: lo que hay en la base son datos de
prueba y certificación. No hay operación que se detenga ni cliente que pierda acceso.

**Esto no anula la decisión: la traslada.** Deja de bloquear la construcción y pasa a bloquear el
alta del primer cliente real, donde la respuesta natural es que el contrato declare sus líneas.

**Recomendación · todo habilitado en el entorno compartido actual; declarado en el alta del
cliente real.** Y en ningún caso deducirlo del historial de actividad: eso es adivinar.

**Estado · `PENDIENTE DE PROPIETARIO` · bloquea el alta real, no la spec**

---

### `BU-D06` · Los lotes sin tipo de ave

> Hay lotes guardados sin decir si son de engorde, de incubadora o de reproductora.

**Evidencia, y una vía que la auditoría no vio.** El tipo de ave está también en la **raza**, y
el lote apunta a una raza. Donde el lote no lo diga, la raza suele decirlo. Eso reduce el
problema, pero **es una inferencia de negocio** —hay razas usadas en más de una línea— y
necesita que el propietario la ratifique.

**Recomendación · usar la raza como segunda fuente, si el propietario la ratifica; y lo que
siga sin clasificar, a la misma bandeja que `BU-D02`.**

**Estado · `PENDIENTE DE PROPIETARIO`**

---

### `BU-D07` · Quién concede qué

> ¿Quién decide las líneas que tiene una empresa, y quién las de cada persona?

**Recomendación.** Habilitar líneas **a una empresa** es comercial y corresponde a la
administración global. Concederlas **a una persona** es operativo y corresponde al administrador
de la empresa, **siempre dentro de lo que su empresa tenga**.

**Dependencia.** La segunda mitad toca `OD-05` —escalada de privilegios, todavía abierta—: un
administrador no debe poder concederse lo que su empresa no tiene. **No se resuelve aquí.**

**Estado · `PENDIENTE DE PROPIETARIO`**

---

### `BU-D08` · Contratado y habilitado

> ¿Conviene distinguir lo que una empresa **contrató** de lo que tiene **encendido** hoy?

**Por qué importa ahora.** Hoy no existe ninguno de los dos. Separarlos mientras se diseña es
casi gratis; separarlos después obliga a migrar lo ya concedido.

**Recomendación · sí, separarlos.** Permite suspender por impago sin borrar el contrato, y
encender por fases sin renegociar.

**Estado · `PENDIENTE DE PROPIETARIO`**

---

### `BU-D09` · Alguien sin ninguna línea asignada · **decisión nueva**

> Se crea un usuario y nadie le asigna línea. Entra. ¿Qué pasa?

**Por qué la auditoría no la vio.** Miró la migración, y esto no es migración: pasará todos los
meses, con cada alta que alguien deje a medias.

**Opciones.** No puede entrar · entra y ve solo lo transversal.

**Recomendación · entra, y encuentra la operación vacía con un aviso claro.** Denegar el acceso
confunde un problema de configuración con uno de credenciales: la contraseña es correcta y el
usuario no tiene forma de saber qué le falta.

**Si no se decide.** Se resolverá en el código, probablemente denegando, y nadie sabrá que se
decidió.

**Estado · `PENDIENTE DE PROPIETARIO` · BLOQUEANTE**

---

### `BU-D10` · Cuando una empresa deja de tener una línea · **decisión nueva**

> Una empresa cierra su incubadora. ¿Qué pasa con lo que ya hay registrado, y con la gente que
> la llevaba?

**Por qué importa.** Es donde una capacidad de acceso puede destruir información. Quitar la
línea no debería borrar tres años de historia.

**Opciones.**

```
revocar y ocultar        el histórico desaparece de informes y trazabilidad
revocar y conservar      nadie registra nuevo; el histórico se sigue consultando
conservar todo           se deja de facturar y no cambia nada: no significa nada
```

**Recomendación · revocar la escritura y conservar la lectura del histórico.** Lo que pasó, pasó,
y `P-10` lo necesita para reconstruir la cadena hacia atrás.

**Estado · `PENDIENTE DE PROPIETARIO`**

---

### `BU-D11` · Contraloría y administración · **decisión nueva, y la más delicada**

> ¿El contralor sigue recibiendo los avisos de las cuatro líneas, aunque solo tenga dos?

**Por qué importa, y por qué es urgente.** `OD-08` —decisión ya tomada por el propietario, y
sobre la que `P-14` está **certificado**— dice que administración y contraloría reciben avisos de
**toda la empresa, sin filtro de alcance**. En el código es literal: las funciones de empresa no
aplican filtro, y las de área sí.

Si el filtro por línea se aplicara sin más a las notificaciones y a las colas de revisión, **un
contralor con dos líneas de cuatro dejaría de recibir en silencio los avisos de las otras dos**, y
`P-14` incumpliría `OD-08` sin que ninguna prueba actual lo detectara.

**Es el punto concreto donde esta capacidad puede romper algo ya certificado.**

**Recomendación · transversales por definición, y declarado.** Controlar es mirar lo que uno no
opera. Y debe decidirse **antes** de implementar, no después de romperlo.

**Estado · `PENDIENTE DE PROPIETARIO` · BLOQUEANTE**

---

### `BU-D12` · Qué queda fuera del filtro · **decisión nueva**

> Administrar usuarios, roles, áreas y maestros generales, ¿pertenece a alguna línea?

**Por qué importa.** Afecta a **todos** los usuarios, no solo a los que no tienen línea. Si
`users` fuera por línea, el administrador de una empresa con dos líneas administraría media
empresa.

**Recomendación · ratificar esta frontera como decisión, no dejar que la deduzca la
implementación:**

```
transversal   acceso · usuarios · roles · empresas · áreas · auditoría · notificaciones
              y los maestros que no son de una línea concreta
por línea     lotes · operación · reportes · paneles · trazabilidad · SAP
```

**Si no se decide.** Cada pantalla elegirá por su cuenta y acabarán discrepando.

**Estado · `PENDIENTE DE PROPIETARIO` · BLOQUEANTE**

---

## 5. Y una advertencia que no es una decisión

Los **totales** son la fuga que nadie ve. Si un panel suma toda la empresa mientras el listado
enseña solo dos líneas, el número **cuenta lo que la pantalla oculta**. No enseña la fila: enseña
que existe y cuánto pesa.

No es una decisión del propietario —nadie va a pedir que los totales filtren mal—, pero sí es la
que más fácil se olvida al construir, y la única cuya fuga **no deja rastro y nadie reporta**.

---

## 6. Lo que este dosier no hace

- No crea `BusinessUnit`, `CompanyBusinessUnit` ni `UserBusinessUnitAccess`.
- No convierte `BirdTypeEnum` en control de acceso.
- No crea `GA-REM-040`. Se recomienda; no se escribe.
- No modifica ninguna certificación. **`FUNCIONAL 14/15` sigue igual.**
- No asigna identificadores `OD-` definitivos.
- **No decide nada.** Las doce quedan `PENDIENTE DE PROPIETARIO`.
