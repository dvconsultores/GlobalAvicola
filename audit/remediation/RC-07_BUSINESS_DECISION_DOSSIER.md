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
