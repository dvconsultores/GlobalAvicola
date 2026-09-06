# `GA-REM-037` · CURVAS ESTÁNDAR DE PESO Y ALERTA POR DESVIACIÓN

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-037` · `CAPABILITY SPEC` |
| **Prioridad** | **P1** · **Estado** `SPEC_READY` |
| **Requisito** | `GA-REQ-037` · `spec.md §4.5` |
| **Decisión** | **`OD-06` `RESOLVED`** (2026-09-06) |
| **Proceso** | `P-03` · Reproductoras — Cría |
| **Dependencias** | `GA-REM-028` `CERTIFIED` (`age_days` desde `start_date`) · `GA-REM-033` `CERTIFIED` (maestros) |
| **Antecedente** | `audit/remediation/P03_GENETIC_CURVE_MODEL_MATRIX.md` |

---

## 1. La decisión del propietario

```
OD-06 = RESOLVED  ·  2026-09-06
```

| | |
|---|---|
| Líneas genéticas iniciales | **Cobb 500** · **Ross 308** · **Hubbard** |
| Líneas adicionales | **sí**, configurables — nunca un enum fijo |
| Unidad de edad | **días** |
| Origen del rango | **`min_weight` y `max_weight` de la tabla cargada** |
| Interpolación | **lineal**, entre los dos puntos vecinos |
| Tolerancia porcentual global | **ninguna** |
| Curvas versionadas | **sí** |
| El lote queda fijado a una versión concreta | **sí** |

## 2. Lo que ya existe y no se reconstruye

`GeneticLine` es un maestro con su pantalla (`GA-REM-033`), y su alta dinámica **ya satisface**
la exigencia de agregar líneas nuevas. `Lot.genetic_line_id` existe. `OperationalAlert` emite
alertas desde antes. `age_days` lo certificó `R-47`.

```
Faltan: la versión de curva, sus puntos, la referencia del lote a la versión,
        el motor de evaluación y el tipo de alerta.
```

## 3. Modelo

```
GeneticLine          (existe)
   └── GeneticWeightCurve        version · is_active · source · created_at
          └── GeneticWeightCurvePoint   age_days · target_weight · min_weight · max_weight

Lot.genetic_line_id           (existe, nulable)
Lot.weight_curve_id           (nuevo, nulable)
```

**Unidad canónica: gramos**, la que ya usan `mean_weight_g` y `avg_weight_g`. Sin conversión.

**Alcance de inquilino**: la curva pertenece a la línea y hereda su alcance, igual que
`Incubator` bajo `Hatchery`. Derivado de la arquitectura vigente.

## 4. Fuera de alcance

- **`P-14`**: no se crea canal de notificación —ni correo, ni push, ni centro—. La alerta de
  `§4.5` es un `OperationalAlert`, que es la infraestructura interna que ya existe. `OD-05`
  sigue pendiente y **no se toca**.
- **Curvas de producción sembradas**: se siembran los **nombres** de las tres líneas y nada
  más. No hay fuente para los pesos reales de Cobb, Ross o Hubbard, e inventarlos sería
  fabricar datos de negocio.
- Extrapolación fuera del rango de la tabla (§6).
- Fórmula de desviación respecto al objetivo: `§4.5` no la pide.
- `RC-07`, `R-69`, `R-70`, `R-77`, `R-80`, `R-83`, `P-08`.

## 5. La regla

```
peso < min_weight                      →  BELOW_STANDARD
min_weight ≤ peso ≤ max_weight         →  WITHIN_STANDARD
peso > max_weight                      →  ABOVE_STANDARD
sin línea, sin curva o fuera de rango  →  NO_REFERENCE
```

Los límites son **inclusivos**: un peso exactamente igual al mínimo está dentro. `target_weight`
sirve de referencia y **no** decide la alerta.

## 6. Fuera del rango de la tabla

Si la edad del lote es menor que el primer punto o mayor que el último, **no se extrapola**.
Ninguna fuente lo autoriza, y prolongar una recta más allá de los datos sería inventar la
curva donde no la hay.

```
NO_REFERENCE, declarado. Nunca WITHIN_STANDARD.
```

## 7. Criterios de aceptación

### Grupo A · el modelo

**`AC01`** · Las líneas genéticas son configurables y las tres iniciales existen tras la
siembra, sin enum fijo y sin impedir añadir otras.

**`AC02`** · Una línea admite varias versiones de curva, cada una con su número de versión y
su marca de activa.

**`AC03`** · Un punto de curva lleva `age_days`, `target_weight`, `min_weight` y `max_weight`,
y se rechaza si `min > max`, si `target` cae fuera del rango o si `age_days` es negativo.

**`AC04`** · Dos puntos con la misma edad en la misma versión se rechazan.

### Grupo B · la carga

**`AC05`** · Una tabla válida se importa entera y la versión queda con exactamente sus puntos.

**`AC06`** · Una tabla inválida se rechaza **entera**: cero puntos persistidos. El error indica
fila, campo y motivo.

### Grupo C · la asignación

**`AC07`** · Un lote guarda la **versión concreta**, no solo la línea.

**`AC08`** · Activar una versión nueva **no** cambia la de los lotes existentes.

**`AC09`** · Un lote nuevo toma por defecto la versión activa de su línea.

**`AC10`** · Una curva de otra línea genética no puede asignarse a un lote: `Ross 308` con
curva de `Cobb 500` se rechaza.

### Grupo D · la evaluación

**`AC11`** · Con punto exacto para la edad, se usa ese punto sin interpolar.

**`AC12`** · Entre dos puntos, se interpola **linealmente** cada uno de los tres valores. Se
comprueba el número exacto, no que «exista».

**`AC13`** · Por debajo del mínimo → `BELOW_STANDARD`.
**`AC14`** · Dentro → `WITHIN_STANDARD`. **`AC15`** · Por encima → `ABOVE_STANDARD`.

**`AC16`** · **Los límites son inclusivos**: exactamente el mínimo y exactamente el máximo
están dentro. Impide un `<=` mal puesto.

**`AC17`** · Sin tolerancia global: el rango sale de la tabla y de ningún otro sitio.

**`AC18`** · Fuera del rango de edades de la tabla → `NO_REFERENCE`, nunca `WITHIN_STANDARD`.

**`AC19`** · Un lote sin línea o sin curva → `NO_REFERENCE`. **No** se etiqueta como normal ni
se emite alerta sin base.

### Grupo E · la alerta

**`AC20`** · Registrar un pesaje fuera de rango crea un `OperationalAlert` con el tipo de peso,
el valor real y el límite superado.

**`AC21`** · Dentro de rango **no** se crea alerta.

**`AC22`** · **No se introduce ningún canal de notificación.** `P-14` sigue intacto.

### Grupo F · transversales

**`AC23`** · La evaluación usa la **versión asignada al lote**, no la activa del momento.

**`AC24`** · Aislamiento entre empresas en líneas y curvas, con control y tratamiento.

**`AC25`** · La evidencia puede fallar (`GA-REM-016 AC13`): mutación sobre el rango, el borde,
la interpolación, el versionado y la coincidencia de línea.

## 8. Trazabilidad

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC01`…`AC10`, `AC23`, `AC24` | `backend/tests/test_genetic_curves.py` | integración HTTP |
| `AC11`…`AC19` | `backend/tests/test_weight_curve_evaluation.py` | unidad + integración |
| `AC20`…`AC22` | `backend/tests/test_weight_alert.py` | integración HTTP |
| cadena de `P-03` | `e2e/proceso-p03-reproductoras-cria.spec.ts` | `API_E2E` |
| `AC25` | informe de certificación | mutación |

> **Sobre la modalidad.** `spec.md §4.5` dice «alertas por desviaciones» sin exigir que el
> usuario las vea en pantalla, así que la evidencia es `API_E2E`. No se fabrica `UI_E2E` por
> vocabulario (`§124` del encargo).

## 9. Definición de terminado

- Los veinticinco criterios pasan.
- Existe prueba que falla contra el código actual por la causa exacta.
- Sensibilidad demostrada sobre las cinco invariantes y revertida.
- Migración con cabeza única y sin deriva de esquema.
- Los pasos de `§4.5` se recorren.
- Regresión completa sin fallos nuevos.
