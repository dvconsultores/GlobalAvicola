# OD-12 — LA TRANSVERSALIDAD DEL CONTRATO SAP

## Metadata
| Campo | Valor |
|---|---|
| ID | `OD-12` |
| Tipo | **Decisión normativa** (no es una remediación) |
| Fecha | 2026-09-07 |
| Origen | Resolución explícita del propietario del producto |
| Estado | **VIGENTE** |
| Alcance | Flujo 5 de `GA-REM-040` · consolidación a SAP |
| Resuelve | **`BU-D04`** |
| Complementa | `OD-09` · `OD-10` · `OD-11` |
| No toca | `P-08`, que sigue `BLOCKED_EXTERNAL` |

---

## 0. Por qué un `OD` aparte

`OD-09` declara que **visibilidad de control y acceso operativo son capacidades distintas**, y de
ahí salen contraloría y administración. `OD-10` declara que **entre unidades solo pasa el
contrato**, y de ahí salen los traspasos.

Ésta introduce algo que no es ninguna de las dos: una **capacidad operativa transversal
acotada**. No es visibilidad de control —el analista de SAP *opera*, no solo mira— y no es un
contrato entre dos cadenas —agrupa las cuatro a la vez—.

Meterla dentro de `OD-09` difuminaría precisamente la distinción de dos términos que `OD-09`
existe para hacer. Es el mismo criterio con el que `OD-11` se mantuvo aparte.

---

## 1. Declaración

```
LA TRANSVERSALIDAD SAP
    =  CAPACIDAD OPERATIVA EXPLÍCITA, LIMITADA AL CONTRATO SAP
```

Y, en negativo, que es la mitad que evita los abusos:

```
NO ES  todas las concesiones de unidad
NO ES  un salto general del alcance por cadena
NO ES  el nombre del rol
```

---

## 2. `OD-12.a` — Qué autoriza

El analista de SAP puede atravesar las cuatro cadenas —Progenitoras, Reproductora, Incubadora,
Engorde— **dentro del contrato de integración SAP de su propia empresa**.

La consolidación agrupa el movimiento de las cuatro **por definición**: filtrarla por cadena la
rompería, y con ella el proceso que la gobierna. Lo que faltaba no era el filtro: era decir que
su ausencia es una decisión.

> Una excepción que solo existe porque nadie puso el filtro es indistinguible de un fallo.

## 3. `OD-12.b` — Las cinco condiciones, todas a la vez

```
PERMITIR OPERACIÓN SAP TRANSVERSAL
   SI   la empresa efectiva es válida
  AND   el actor tiene la capacidad SAP EXPLÍCITA
  AND   la operación pertenece al contrato SAP
  AND   el recurso es de la MISMA empresa
  AND   el recurso es elegible para esa operación según sus reglas de negocio
```

Quitar cualquiera de ellas es una de las mutaciones que las pruebas deben detectar.

## 4. `OD-12.c` — Fuera del contrato, nada cambia

Cuando el mismo actor pide un lote, una mortalidad, un indicador o un panel por las superficies
**normales**, rigen las reglas de siempre:

```
empresa efectiva  +  unidades efectivas  +  RBAC  +  regla del recurso
```

```
OPERACIÓN TRANSVERSAL SAP   ≠   OPERACIÓN TRANSVERSAL GENERAL
```

Conocer el identificador de un lote ajeno **por el contrato SAP** no abre su detalle: la fase 3
sigue denegándolo.

## 5. `OD-12.d` — Lo que no concede ni modifica

```
NO concede ninguna unidad de negocio            `unidades_efectivas` no cambia
NO habilita ninguna unidad a la empresa
NO se deduce del nombre del rol
NO se hereda de la visibilidad de control
NO cruza la empresa, nunca
```

**No se resuelve concediendo las cuatro cadenas al analista.** Eso le daría acceso productivo
general fuera del contrato, que es justo lo contrario de lo que se decide.

## 6. `OD-12.e` — No es la excepción de contraloría

```
OD-09.a   contraloría   visibilidad de CONTROL de toda la empresa · operación acotada
OD-12     analista SAP  operación TRANSVERSAL acotada al contrato SAP
```

Dos excepciones distintas, con alcances distintos. **Ninguna implica la otra**: tener capacidad
de control no autoriza a operar SAP, y tener capacidad SAP no da visibilidad de control.

## 7. La capacidad ya existe en el catálogo

Auditado antes de decidir: el `RBAC` ya distingue `sap:read` y `sap:send_sap`. **No se crea
ningún permiso nuevo** — el catálogo ya sabía expresar «puede operar la integración SAP», y esta
decisión dice qué autoriza eso respecto de las cadenas.

## 8. `P-08` no se cierra por esto

```
P-08   BLOCKED_EXTERNAL   sin cambios
```

Esta decisión gobierna **quién puede operar el contrato** y sobre qué filas. No prueba que SAP
real acepte nada, y nada de lo que se implemente bajo ella certifica la integración externa.

## 9. Trazabilidad

| Decisión del dosier | Pregunta | Respuesta | Parte |
|---|---|:--:|---|
| `BU-D04` | ¿El analista de SAP ve las cuatro cadenas? | **excepción declarada** | `OD-12.a`…`OD-12.e` |
