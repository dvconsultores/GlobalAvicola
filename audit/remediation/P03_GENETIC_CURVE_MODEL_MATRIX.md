# `P-03` · MODELO DE CURVAS GENÉTICAS — AUDITORÍA

`OD-06` · `GA-REQ-037` · 2026-09-06 · antes de tocar código

---

## 1. Qué existe ya

| Capacidad | ¿Existe? | ¿Correcta? | Hueco |
|---|:--:|:--:|---|
| Línea genética | **sí** — `GeneticLine` (`masters/models.py:146`) | sí | — |
| Alta y edición de líneas | **sí** — CRUD de maestros con pantalla (`P-12`) | sí | — |
| Referencia genética en el lote | **sí** — `Lot.genetic_line_id` (`:199`), nulable | sí | — |
| Raza vinculada a la línea | **sí** — `Breed.genetic_line_id` | sí | — |
| **Versión de curva** | **no** | — | **falta la entidad** |
| **Puntos de la curva** | **no** | — | **falta la entidad** |
| **Referencia del lote a una versión** | **no** | — | **falta el campo** |
| Registro de peso | **sí** — `BirdMovement.avg_weight`, en **gramos** | sí | — |
| Cálculo de edad | **sí** — `age_days` desde `start_date` (`R-47` certificado) | sí | — |
| Infraestructura de alertas | **sí** — `OperationalAlert`, con `threshold_value` y `actual_value` | sí | falta el tipo de alerta |
| **Evaluación contra curva** | **no** | — | **falta el motor** |

```
De once capacidades, seis existen y cinco faltan.
```

## 2. Lo que **no** hay que construir

**No se crea un modelo de genética nuevo.** `GeneticLine` existe, es un maestro con su
pantalla desde `GA-REM-033`, y su alta es dinámica: la decisión de `OD-06` —«debe ser posible
agregar nuevas líneas»— **ya está satisfecha** por el CRUD de maestros. No hace falta ningún
enum, y crear uno sería justo lo que `§24` del encargo prohíbe.

**No se crea infraestructura de alertas.** `OperationalAlert` existe y ya emite tres tipos;
su propio comentario menciona `weight_deviation` como tipo previsto. Se añade el tipo, no el
mecanismo.

**No se toca el cálculo de edad.** `R-47` lo certificó y `§46` del encargo lo exige.

## 3. La unidad canónica es el gramo

`BirdMovement.avg_weight` es un `Float` sin unidad declarada en el modelo, pero el resto del
sistema la fija sin ambigüedad:

```
get_kpi_weight_uniformity  →  mean_weight_g · std_weight_g · min_weight_g · max_weight_g
get_kpi_ipe                →  avg_weight_g · ganancia_diaria_g
```

**Gramos.** Las curvas usarán la misma unidad, y no se introduce conversión alguna.

## 4. Alcance de inquilino — derivado, no inventado

`§96`-`§98` piden decidirlo desde la arquitectura y registrar hueco si no se puede.

**Se puede.** `GeneticLine.company_id` es nulable y el CRUD de maestros aplica
`_apply_company_filter`: las líneas siguen el patrón de datos maestros del producto, igual que
`vaccines` o `feed-types`. Y una curva pertenece a una línea, de modo que hereda su alcance —
exactamente como `Incubator` bajo `Hatchery` (`GA-REM-033`).

```
GeneticLine  ·  patrón de dato maestro   (company_id, con las globales como las de hoy)
Curva        ·  pertenece a la línea, y toma de ella su alcance
```

No hace falta decisión del propietario: la arquitectura vigente lo resuelve.

## 5. Cuándo se evalúa

`spec.md §4.5` dice «alertas por desviaciones» sin fijar el momento. La arquitectura sí:
`_check_and_create_alerts` se ejecuta **al crear el evento**, y así funcionan las tres alertas
existentes —mortalidad alta, temperatura y humedad—.

Se sigue ese patrón. **No** se traslada la semántica de `P-15`, cuyos indicadores solo cuentan
lo aprobado: una alerta que esperase a la aprobación llegaría cuando ya no sirve para actuar.

## 6. Lotes históricos

`Lot.genetic_line_id` ya es nulable y hay lotes sin ella. La referencia a la versión de curva
será **nulable** también.

```
Sin línea genética o sin curva  →  NO_REFERENCE
```

**Nunca** se clasifica como «dentro de norma» lo que no tiene norma contra la que compararse
(`§119`-`§120`). Y **no se inventa genética** para los lotes existentes (`§45`).

## 7. Semillas

Se sembrarán **solo los nombres** de las tres líneas: `Cobb 500`, `Ross 308` y `Hubbard`.

```
NINGUNA curva de producción se siembra.
```

No tengo fuente para los pesos reales de esas líneas, e inventarlos sería fabricar datos de
negocio (`§78`). Las curvas las carga el administrador.

Las pruebas sí usan curvas ficticias deterministas, que es otra cosa y queda declarado.

> Las semillas de desarrollo ya crean `Breed` con los nombres «Ross 308» y «Cobb 500». Son
> **razas**, no líneas: `Breed.genetic_line_id` apunta a la línea. Se siembran las líneas y no
> se tocan las razas existentes.

## 8. Migración

Una migración nueva sobre la cabeza única `l2m3n4o5p6q7`: dos tablas y una columna nulable en
`lots`. Nada obligatorio, así que **no rompe a los lotes existentes ni a los clientes de la
API** (`§133`-`§134`).

---

## Resultado (2026-09-06)

Las cinco capacidades ausentes se construyeron; las seis existentes no se tocaron. `GA-REM-037`
queda `CERTIFIED` y `P-03` con ella.

| Capacidad ausente | Dónde quedó |
|---|---|
| Versión de curva | `genetic_weight_curves` · migración `m3n4o5p6q7r8` |
| Puntos de la tabla | `genetic_weight_curve_points` |
| Referencia del lote a la versión | `lots.weight_curve_id` · `LotService._curva_del_lote` |
| Motor de evaluación | `app/operations/weight_curve.py` — **una** implementación, sin copia en el frontend |
| Alerta de desviación | `OperationsService._alertas_de_peso` → `weight_deviation` |

Dos supuestos de esta matriz se confirmaron al implementar:

**La tenencia se hereda, no se duplica.** La curva no lleva `company_id`: se comprueba sobre la
`GeneticLine` a la que cuelga, como `Incubator` bajo `Hatchery`. Dos fuentes de tenencia para
el mismo dato acaban discrepando, y `T-037-15` comprueba el aislamiento con un operador real y
no con el Super Administrador, cuya exención habría hecho pasar la prueba sin medir nada.

**La unidad es el gramo.** `BirdMovement.avg_weight` alimenta `avg_weight_g` en los KPI, de modo
que la tabla se carga en gramos y no se convierte en ningún punto del recorrido.

Un supuesto **no** se confirmó y merece constar: se anotó que las líneas genéticas podrían
sembrarse como catálogo global sin `company_id`, al modo de `ProductivePhase`. No sirve. El
filtro de maestros compara `company_id == user_company_id` sin contemplar el nulo, así que una
línea global sería invisible para todo usuario con empresa —es decir, para todos menos el
Super Administrador—. Se siembran por empresa.
