# DOSSIER DE DECISIÓN · `RC-07` y `GA-TD-014`

**Gate B** · 2026-09-05 · para el propietario · escrito para decidirse sin leer código

---

## Resumen en una página

Se pedía preparar la decisión de negocio que mantiene bloqueado `GA-TD-014` —la referencia
de la orden de compra de SAP— y que, según los documentos de trabajo, dependía de `RC-07`.

**Al ir a las fuentes, esa dependencia no se sostiene.**

`RC-07` existe, es real y sigue siendo una decisión suya, pero trata de **otra cosa**: si la
mortalidad genera un movimiento de inventario en SAP o solo un indicador. No dice nada sobre
las órdenes de compra.

```
Lo que se creía        GA-TD-014  →  bloqueado por RC-07
Lo que dicen las fuentes  GA-TD-014  →  NO depende de RC-07
                          RC-07      →  sigue abierta, sobre mortalidad
```

Queda, eso sí, una decisión suya sobre `GA-TD-014`, pero es **más pequeña y más concreta**
de lo que se suponía. Está en §11 como `OD-04`.

---

## 1. Qué pide originalmente el cliente

Su documento **«Recomendación central»** fue auditado en `docs/16`. De ahí salen dos cosas
distintas que conviene no mezclar:

**a) Cinco decisiones que usted debe cerrar** (§25 de su documento, registradas como `G-R02`).
La cuarta es:

> «La mortalidad generará movimiento de inventario o solo indicador/costo.»

Eso es `RC-07`. Su documento **declara expresamente que la decisión no está tomada**.

**b) Cinco huecos técnicos críticos**, entre ellos:

> `G-R05` · **Sin validación cantidad ≤ OC** — «Puede recibir más de lo comprado».

Eso es `GA-TD-014`. **No aparece entre las cinco decisiones.**

La auditoría de su documento incluso las separa en fases distintas del plan:

| Fase | Contenido |
|---|---|
| **10A · Decisiones de negocio** | taller para resolver las cinco definiciones del §25 ← `RC-07` |
| **10B · Validaciones críticas** | `G-R04` capacidad de galpón · **`G-R05` cantidad ≤ OC** · `G-R03` |

Su documento trata `G-R05` como una validación a implementar, no como algo a decidir. Y su
hermana `G-R04` —capacidad de galpón— **ya está implementada y funcionando**.

## 2. Qué hace hoy Global Avícola

Cuando se recibe un lote de aves, el formulario pide la orden de compra de SAP. El operador
la escribe. **Se guarda, pero en un campo libre**, no en el campo con nombre propio que el
sistema usa para razonar.

Es como anotar el número de factura en el margen de la hoja en vez de en la casilla
«factura»: queda escrito, pero ningún control lo mira.

## 3. Qué está inerte hoy

Dos reglas que el sistema tiene escritas, probadas y listas, y que **nunca se ejecutan**
porque miran una casilla que siempre está vacía:

| Regla | Qué haría | Qué pasa hoy |
|---|---|---|
| «documentos SAP no se duplican» | impedir registrar dos veces la misma orden en el mismo lote | nada |
| «no recibir más de lo comprado» | impedir recibir 5.500 aves contra una orden de 5.000 | nada |

En este momento **se puede recibir cualquier cantidad contra cualquier orden**, y nadie
avisa.

## 4. Qué es `GA-TD-014`

Un cambio pequeño: que el formulario guarde la orden de compra **en la casilla que
corresponde** en lugar de al margen.

Técnicamente es una línea. Su efecto es que las dos reglas dormidas despiertan.

## 5. Qué cambiaría si se implementa

| Hoy | Después |
|---|---|
| se recibe cualquier cantidad contra la orden | se rechaza recibir más de lo comprado |
| la misma orden puede registrarse dos veces en un lote | la segunda se rechaza |
| el informe de comparación con SAP sale vacío | el informe compara de verdad |
| ningún control avisa a nadie | un operador puede ver su registro rechazado |

## 6. Qué hace la regla de «no duplicar documentos SAP»

Impide registrar **dos veces la misma orden de compra para el mismo lote y el mismo tipo de
operación**. La misma orden sí puede usarse en lotes distintos.

**Aquí está la pregunta real de negocio:** si una orden de compra se recibe en **dos
entregas parciales** al mismo lote, la segunda quedaría rechazada. ¿Ocurre eso en su
operación?

## 7. Qué hace la regla de «no recibir más de lo comprado»

Compara la cantidad recibida con la cantidad de la orden y rechaza el exceso.

Dos precisiones importantes:

- **Solo actúa si la orden existe cargada en el sistema.** Si el operador escribe una orden
  que el sistema no conoce, hoy no se valida nada y el registro pasa. Decidir qué debe pasar
  en ese caso es parte de la decisión (§11).
- **No admite tolerancia.** Rechaza cualquier exceso, aunque sea de una unidad. Un documento
  interno menciona un margen del ±10 % contra la orden, pero **no he encontrado esa
  tolerancia en ninguna fuente normativa suya**, así que no la doy por buena: si la quiere,
  hay que decidirla.

## 8. Qué procesos desbloquea

| Proceso | Situación |
|---|---|
| `P-01` Progenitoras — Cría | el paso de recepción quedaría completo |
| `P-03` Reproductoras — Cría | ídem |
| `P-06` Pollo de engorde | ídem, **pero le falta además otra cosa** (§10) |

Es el único asunto pendiente que afecta a **tres** procesos a la vez. Todos los demás
afectan a uno.

## 9. Qué consecuencias tendría activarlo

**A favor**

- Se cumple un hueco que su propio documento marca en rojo.
- Deja de ser posible recibir más aves de las compradas sin que nadie lo note.
- El informe de comparación con SAP empieza a servir para algo.

**En contra**

- Un operador que hoy registra sin problema puede encontrarse con un rechazo.
- Si su operación usa entregas parciales contra una misma orden, la regla de no duplicar
  las bloquearía.
- Los registros ya hechos tienen la orden en el campo libre. Si se decidiera trasladarlos al
  campo con nombre, podrían aflorar duplicados históricos.

## 10. Qué ocurre si se mantiene diferida

```
GA-TD-014 diferido
   ↓
P-01 sigue PARCIAL
P-03 sigue PARCIAL
P-06 sigue PARCIAL
```

Es cierto y seguirá siéndolo. Pero **cerrarlo no certifica automáticamente `P-06`**: a ese
proceso le falta además la alerta de peso fuera de curva (`GA-REQ-037`), y acaba de
aparecer un tercer asunto (`R-76`, §14).

También seguiría siendo posible recibir más aves de las compradas sin aviso.

## 11. Opciones de decisión

Las opciones salen de las fuentes, no de mi criterio. La única pregunta genuinamente abierta
es **cómo debe comportarse el control**, no si debe existir —su documento dice que sí—.

Queda registrada como **`OD-04`** (`OD-01`…`OD-03` ya están ocupadas).

### Opción A · Activar el control completo

El campo se guarda donde corresponde y las dos reglas actúan. Recibir de más se rechaza, y
repetir una orden en el mismo lote también.

### Opción B · Activar solo el límite de cantidad

El campo se guarda donde corresponde y se rechaza recibir de más, pero **se permite** usar la
misma orden dos veces en el mismo lote, para admitir entregas parciales.

### Opción C · Activar con tolerancia

Como A o B, pero admitiendo un margen sobre la cantidad de la orden. **Requiere que usted
diga cuál es el margen**: no consta en ninguna fuente suya.

### Opción D · Mantenerlo diferido

Todo sigue igual. Los tres procesos siguen parciales y se puede seguir recibiendo de más.

## 12. Recomendación técnica

> Esto es una recomendación de ingeniería. **No sustituye su decisión.**

**Opción B**, y después revisar.

Por qué: el límite de cantidad es el control que su documento marca en rojo y su ausencia
tiene consecuencia económica directa —recibir más de lo comprado—. La regla de no duplicar,
en cambio, choca con un patrón operativo perfectamente normal (entregas parciales) sobre el
que no tengo evidencia de su operación.

Activar primero lo que claramente aporta, y dejar lo dudoso para cuando se sepa si las
entregas parciales existen, evita bloquear a los operadores por una regla que quizá no
corresponda.

**Si me confirma que nunca hay entregas parciales contra una misma orden**, entonces la
Opción A es mejor que la B, sin matices.

## 13. Riesgos por opción

| Dimensión | Opción A | Opción B | Opción C | Opción D |
|---|---|---|---|---|
| Comportamiento del negocio | dos controles nuevos | un control nuevo | control con margen | sin cambio |
| `P-01` | paso completo | paso completo | paso completo | sigue parcial |
| `P-03` | paso completo | paso completo | paso completo | sigue parcial |
| `P-06` | paso completo, faltan otros | ídem | ídem | sigue parcial |
| No duplicar documentos | activa | **inactiva** | según variante | inactiva |
| No recibir de más | activa | activa | activa con margen | inactiva |
| Dependencia de SAP | **ninguna** — las órdenes se cargan a mano | ninguna | ninguna | ninguna |
| Modelo de datos | sin cambios | sin cambios | **cambia**: hay que guardar el margen | sin cambios |
| Interfaz | sin cambios visibles | sin cambios visibles | mostrar el margen aplicado | sin cambios |
| Pruebas | recepción, duplicado, exceso | recepción, exceso, parcial admitida | + casos de margen | ninguna |
| Riesgo operativo | **alto** si hay entregas parciales | bajo | medio | riesgo económico persistente |

## 14. Specs que habría que modificar

| Documento | Cambio |
|---|---|
| `FE_BE_CONTRACT_MATRIX.md` `C-15` | corregir la justificación: no depende de `RC-07` |
| spec nueva `GA-REM-030` | contrato de la referencia de orden de compra, con sus criterios |
| `spec.md` reglas `BR-11` / `BR-18` | precisar alcance —y corregir la numeración, ver abajo— |
| `PROCESS_CERTIFICATION_MATRIX.md` | reevaluar `P-01`, `P-03`, `P-06` al cerrarse |

### Dos hallazgos aparecidos al reconstruir esto

```
R-77 · la regla de «no duplicar documentos SAP» es BR-11 en la spec, pero el código la
       identifica como BR-10 —que en la spec es «eliminación lógica»—. El contrato de error
       devuelve por tanto una regla equivocada. P2, documental pero visible al cliente.

R-76 · docs/12 R7 —«un lote no puede cerrarse si tiene registros sin aprobar»— no está
       implementado. P1. Detallado en E2E_EVIDENCE_MODALITY_MATRIX §6.
```

Ninguno se corrige en este checkpoint, que es documental.

## 15. Pruebas que se requerirían

Sea cual sea la opción, no se daría por hecha sin:

- recepción normal dentro de la orden → se acepta
- recepción por encima de la orden → se rechaza citando la regla
- orden desconocida por el sistema → el comportamiento que usted decida, comprobado
- segunda entrega contra la misma orden → aceptada o rechazada según la opción
- aislamiento entre empresas y permisos, con control y tratamiento
- demostración de que cada comprobación **puede fallar** (exigencia de `R-72`)

---

## Estado de `RC-07`

```
RC-07 = OWNER_DECISION_REQUIRED   (sin cambio)
```

Sigue abierta y sigue siendo suya: **¿la mortalidad genera movimiento de inventario en SAP,
solo un indicador, o depende de la causa?** Sus tres opciones están en
`REQUIREMENT_CONFLICT_RESOLUTION §7.2`.

Lo único que cambia es su alcance: **no bloquea `GA-TD-014`**. `RR-07` ya lo había acotado
por escrito —«solo el mapeo de mortalidad a un documento SAP queda supeditado a la decisión
del propietario»— y bloquea únicamente esa parte dentro de `GA-REM-017`, que de todos modos
está detenida por el contrato técnico con SAP.

`GA-REM-010`, la otra dependencia que `C-15` citaba, está **`CERTIFIED`** desde hace dos
waves. Tampoco bloquea.

## Lo que hace falta de usted

```
OD-04  ·  ¿Opción A, B, C o D de §11?
          Basta con responder si existen entregas parciales contra una misma orden.

OD-02  ·  RC-07, mortalidad frente a SAP. Sigue pendiente, sin urgencia:
          GA-REM-017 está detenida por otro motivo.
```

**No se implementa nada de `GA-TD-014` hasta que `OD-04` esté decidida.** `BR-11` y `BR-18`
siguen inertes.

---

# RESOLUCIÓN · `OD-04` (2026-09-06)

```
OD-04 = RESOLVED
```

| | |
|---|---|
| **Decidido por** | el propietario |
| **Fecha** | 2026-09-06 |
| **Decisión** | **Una misma orden de compra puede recibirse mediante múltiples entregas parciales.** |
| **Opción elegida** | la **B** de §11 — se activa el límite de cantidad, **no** la regla de no duplicar |
| **Requisito afectado** | `G-R05` («sin validación cantidad ≤ OC», `docs/16 §13`, crítico) |
| **Deuda afectada** | `GA-TD-014` — pasa de `DIFERIDO` a **`ACTIONABLE`** |
| **Contrato afectado** | `C-15` de `FE_BE_CONTRACT_MATRIX` |
| **Spec** | `GA-REM-035` |
| **Procesos** | `P-01` · `P-03` · `P-06` |

## Consecuencia técnica

```
Repetir la referencia de una OC       →  NO es un error
Superar la cantidad acumulada         →  SÍ es un error
```

La protección se traslada del **identificador** a la **cantidad acumulada**. Una regla del
tipo «esta OC ya se usó» sería contraria a la decisión.

## Lo que la decisión NO autoriza

| | |
|---|---|
| **Tolerancia de sobre-recepción** | **no** — ningún margen porcentual ni absoluto. Sin fuente normativa, `acumulado > cantidad de la OC` se rechaza |
| **Cierre automático de la OC** | **no decidido**. La pregunta era si caben entregas parciales, no qué ocurre al llegar al 100 %. No se introduce ningún estado de cierre |

## Lo que sigue abierto

```
RC-07 = OWNER_DECISION_REQUIRED
```

Sin cambios. Es la política **contable de la mortalidad frente a SAP** y no tiene relación con
las entregas parciales. La separación entre ambas se estableció en §5 de este dossier y se
mantiene.

---

# RESOLUCIÓN · `OD-06` (2026-09-06)

```
OD-06 = RESOLVED
```

| | |
|---|---|
| **Decidido por** | el propietario |
| **Fecha** | 2026-09-06 |
| **Pregunta** | ¿de dónde sale la «curva estándar» que `spec.md §4.5` exige comparar? |
| **Requisito** | `GA-REQ-037` — pasa de bloqueado por dato ausente a **`ACTIONABLE`** |
| **Spec** | `GA-REM-037` |
| **Proceso** | `P-03` |

## La decisión

```
Global Avícola manejará curvas estándar de peso configurables por línea genética.

Líneas iniciales:  Cobb 500 · Ross 308 · Hubbard
Se pueden añadir más:  sí
Cada línea puede tener su tabla de curva
Cada lote tiene línea genética asignada
Cada lote queda asociado a una VERSIÓN concreta de la curva
```

## Parámetros derivados de la decisión

| | |
|---|---|
| Unidad de edad | **días** |
| Origen del rango de alerta | **`min` y `max` de la tabla cargada** |
| Interpolación | **lineal** entre puntos vecinos |
| Tolerancia porcentual global | **ninguna** |
| Curvas versionadas | **sí** |
| Lote fijado a su versión | **sí** — una curva nueva no reescribe la historia |

## Lo que la decisión NO autoriza

- **Sembrar curvas de producción.** Se siembran los nombres de las tres líneas; los pesos
  reales los carga el administrador. No hay fuente para inventarlos.
- **Extrapolar** fuera del rango de la tabla.
- **Abrir `P-14`.** La alerta de `§4.5` es interna (`OperationalAlert`). Elegir un canal de
  notificación —correo, push, centro de avisos— es una decisión de negocio distinta, todavía
  sin plantear al propietario y **sin número de `OD` asignado**. No es `OD-05`, que pregunta
  por la escalada de privilegios en `P-13`.

---

# RESOLUCIÓN · `OD-07` (2026-09-07)

```
OD-07 = RESOLVED
```

| | |
|---|---|
| **Decidido por** | el propietario |
| **Fecha** | 2026-09-07 |
| **Pregunta** | ¿por qué canal notifica Global Avícola? |
| **Requisito** | `docs/02 §3.14` — pasa de bloqueado por decisión a **`ACTIONABLE`** |
| **Spec** | `GA-REM-038` |
| **Proceso** | `P-14` · Notificaciones y alertas |

> **Identificador.** Se comprobó el registro antes de asignarlo: `OD-01`…`OD-06` estaban
> ocupados. `OD-05` es *«¿puede un administrador conceder permisos que él mismo no posee?»*, de
> `P-13`, y llegó a citarse por error como bloqueante de `P-14`; esa confusión se corrigió el
> 2026-09-06 en `PARTIAL_PROCESS_BLOCKER_MATRIX.md`. Este es el siguiente libre.

## La decisión

```
P-14 utilizará como canal obligatorio inicial
NOTIFICACIONES INTERNAS DENTRO DE GLOBAL AVÍCOLA.
```

Fuera del alcance inicial, por decisión expresa:

```
EMAIL · WHATSAPP · SMS · PUSH MÓVIL · WEB PUSH · TELEGRAM · otros canales externos
```

Concuerda con `spec.md §9`, que ya listaba «Notificaciones push (v2)» entre lo que el proyecto
no hace.

## Lo que la decisión NO autoriza

`OD-07` resolvió **el canal**, y solo el canal. No autoriza a inventar:

```
qué eventos notifican · a quién · con qué prioridad · cuánto se conservan · escalados
```

Eso sale de requisitos existentes. Al derivarlos —`P14_NOTIFICATION_EVENT_MATRIX.md`— resultó
que de los seis tipos de `docs/02 §3.14`, **dos** tienen disparador y destinatario escritos y
**cuatro** no. Los cuatro se declaran, no se completan a ojo.

---

# RESOLUCIÓN PARCIAL · `OD-08` (2026-09-07)

```
OD-08 · destinatarios ......... RESOLVED
OD-08 · semántica temporal .... OWNER_DECISION_REQUIRED
```

> **Sobre el identificador.** `OD-08` se abrió con **cuatro** preguntas y el propietario ha
> respondido la de destinatarios. No se crea un `OD-ID` nuevo —el registro no admite
> subdecisiones numeradas y `OD-01`…`OD-08` están ocupados—: se marca la decisión como resuelta
> **en parte**, nombrando qué mitad queda. El estado parcial ya existe en el vocabulario del
> programa (`GA-REM-027` es `PARTIALLY CERTIFIED`).

## La mitad resuelta · destinatarios

```
Para los eventos normativos de notificación interna de P-14, los destinatarios serán:

  1. la persona que cargó/registró la data que originó el evento
  2. los usuarios administradores de la empresa correspondiente
  3. los usuarios con función/rol de contraloría / contralor
  4. el gerente del área correspondiente
  5. el supervisor correspondiente

  ámbito: MISMA EMPRESA · y misma área cuando la arquitectura disponga de ella
```

Se aplica **en unión** con lo que ya exigían otras fuentes: «notificar al operador»
(`docs/02 §3.14`) y «Notificar al rol Analista SAP» (`docs/10 §6.2`) siguen vigentes. Una
decisión que amplía no retira.

Y con deduplicación: quien cumpla varias condiciones recibe **un** aviso, no uno por motivo.

### Lo que la mitad resuelta permitió cerrar

Al mapear los términos contra los roles reales —`P14_OD08_ROLE_MAPPING_MATRIX.md`— tres de los
cinco resultaron resolubles, uno ya lo era, y uno no:

| Término | Rol real | Estado |
|---|---|:--:|
| persona que cargó el dato | `OperationalEvent.registered_by_id` | resoluble |
| administradores | `Administrador de Empresa` · `Super Administrador` **con empresa** | resoluble |
| contraloría | `Contralor Avícola` | resoluble |
| supervisor | `Supervisor Avícola` | resoluble |
| **gerente del área** | **ninguno** | **`BLOCKED_BY_MODEL_GAP`** |

No hay tabla de área, departamento ni unidad organizativa, y el usuario solo se asocia a una
empresa y a un rol. Ni los roles identifican el área ni el usuario la tiene asignada.

## La mitad abierta · semántica temporal

| | |
|---|---|
| **Origen** | derivar los seis tipos de `docs/02 §3.14` al implementar `OD-07` |
| **Bloquea** | cuatro de los seis tipos de `P-14`; el canal en sí **no** está bloqueado |
| **Consecuencia** | `P-14` queda `PARTIAL` aunque el canal funcione de extremo a extremo |

## Lo que hay que preguntar

Las preguntas 1, 2 y 3 quedaron respondidas por la mitad de destinatarios: mortalidad, peso y
el aviso de las 24 horas ya tienen a quién avisar. La tercera además dejó de necesitar decisión
de mecanismo, porque **la tecnología del disparador no es del propietario**: su umbral está en
el propio nombre del evento —«> 24h»— y la condición es computable con la auditoría, que guarda
el momento exacto de la transición a `pending_review`.

Queda una, y una derivada:

```
1. «Lote próximo a cierre»
   ¿Qué es «próximo»? Se buscó en toda la jerarquía documental: la única aparición
   de la frase es la línea de `docs/02 §3.14` que la enumera. Y el modelo no la deja
   derivar — `Lot.end_date` es la fecha REAL de cierre, no una prevista, y no existe
   `planned_end_date`. Derivarla de `ProductivePhase.duration_days` sería decidir el
   requisito en vez de leerlo.
   ¿Días antes de una fecha prevista? ¿Una edad? ¿Un porcentaje del ciclo?

2. Recurrencia del aviso de «> 24h»
   ¿Se emite una vez, o se repite mientras siga pendiente? Ninguna fuente lo dice.
   Mientras tanto se emite UNA sola vez, con idempotencia: inventar una repetición
   diaria sería añadir ruido que nadie pidió.
```

**Consecuencia:** `P-14` sigue `PARTIAL`. Cinco de los seis eventos normativos quedan cubiertos;
el sexto no tiene semántica y `GA-REM-016 AC05` no admite certificar por muestra.

## Lo que NO se hizo mientras tanto

No se eligió «todos los administradores», ni «el Supervisor Avícola», ni «quien registró el
evento». Las tres se consideraron y las tres se descartaron por escrito en
`P14_NOTIFICATION_RECIPIENT_MATRIX.md §4`: cualquiera sería una decisión nuestra vestida de
requisito, y notificar a la persona equivocada es peor que no notificar, porque parece que el
sistema avisa.
