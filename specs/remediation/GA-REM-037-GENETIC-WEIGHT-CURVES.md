# `GA-REM-037` · CURVAS ESTÁNDAR DE PESO Y ALERTA POR DESVIACIÓN

| Campo | Valor |
|---|---|
| **ID** | `GA-REM-037` · `CAPABILITY SPEC` |
| **Prioridad** | **P1** · **Estado** **`CERTIFIED`** (2026-09-06, enmienda A incluida) |
| **Requisito** | `GA-REQ-037` · `spec.md §4.5` |
| **Decisión** | **`OD-06` `RESOLVED`** (2026-09-06) |
| **Proceso** | `P-03` · Reproductoras — Cría |
| **Dependencias** | `GA-REM-028` `CERTIFIED` (`age_days` desde `start_date`) · `GA-REM-033` `CERTIFIED` (maestros) |
| **Antecedente** | `audit/remediation/P03_GENETIC_CURVE_MODEL_MATRIX.md` |
| **Certificación** | `audit/remediation/PROCESS-03-CERTIFICATION.md` · `R-96-WEIGHT-CURVE-CAPABILITY-CERTIFICATION.md` |
| **Contrato de UI** | `audit/remediation/R96_WEIGHT_CURVE_FRONTEND_CONTRACT_MATRIX.md` |

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

---

# ENMIENDA A · CAPACIDAD DE PRODUCTO Y OBSERVABILIDAD DE LA EVALUACIÓN

`2026-09-06` · hallazgos `R-96` y `R-97` · estado de la spec: vuelve a `SPEC_READY`

## A.1 Por qué existe esta enmienda

La versión original de esta spec **no tenía ningún criterio de frontend**, y de esa ausencia
se concluyó que la pantalla quedaba fuera de alcance. La conclusión era incorrecta y aquí se
corrige. `OD-06` dice, con todas sus palabras, que cada línea genética puede tener su tabla de
curva estándar y que **esa tabla debe poder cargarse dentro de Global Avícola**.

```
OWNER REQUIREMENT  >  INCOMPLETE SPEC
```

La ausencia de criterios de frontend no demostraba ausencia de requisito: demostraba que esta
spec estaba **incompleta**. Es un `SPEC COVERAGE GAP`, y la spec es la responsable de cerrarlo
porque es la autoridad natural de `OD-06`; crear una spec nueva partiría en dos la misma
decisión del propietario.

```
R-96 = MISSING PRODUCT CAPABILITY + SPEC COVERAGE GAP
```

Mientras `R-96` siga abierto, **`P-03` es `PARTIAL`**. Que `POST /masters/weight-curves`
responda `201` no significa que el administrador pueda cargar la curva, y `GA-REM-016 AC05` ya
fijaba el criterio: la unidad certificada es el proceso de negocio, nunca un endpoint.

## A.2 `R-97` · la evaluación no es observable

Al derivar el contrato de la pantalla (`audit/remediation/R96_WEIGHT_CURVE_FRONTEND_CONTRACT_MATRIX.md`)
apareció un hueco que no es de interfaz sino de contrato:

```
El motor de evaluación tiene UN SOLO consumidor —el generador de alertas—
y solo actúa cuando el peso queda FUERA de rango.
```

| Situación | ¿Observable hoy? |
|---|:--:|
| `BELOW_STANDARD` · `ABOVE_STANDARD` | sí, vía `OperationalAlert` |
| `WITHIN_STANDARD` | **no** |
| `NO_REFERENCE` | **no** — indistinguible de «dentro de norma» |
| Rango esperado a una edad | **no** — solo dentro del texto del mensaje |

«Sin alerta» significa hoy dos cosas incompatibles a la vez. Deducir cuál exigiría interpolar
en el cliente, que crearía un segundo motor y contradice `AC-FE14`. Por eso la enmienda añade
un criterio de **backend**: exponer lo que el motor ya calcula, sin recalcular nada.

```
R-97 = CONTRACT GAP · la evaluación de curva no es observable salvo cuando alerta
```

## A.3 Criterios de aceptación añadidos

### Grupo E · observabilidad de la evaluación (backend)

**`AC26`** · Existe una lectura que, dado un lote y una edad o un peso, devuelve la evaluación
que el motor ya calcula: el estado, el rango esperado y la versión de curva empleada. **No se
duplica el motor**: la lectura llama a `app/operations/weight_curve.py`.

**`AC27`** · La lectura distingue `WITHIN_STANDARD` de `NO_REFERENCE`. Un lote sin curva, sin
línea genética o con una edad fuera de la tabla devuelve `NO_REFERENCE` **declarado**, nunca la
ausencia de dato ni un estado normal.

**`AC28`** · La lectura respeta la tenencia: un lote de otra empresa no es legible.

### Grupo F · capacidad de producto (frontend)

**`AC-FE01`** · Un usuario autorizado alcanza la administración de curvas **desde la línea
genética**, sin escribir una URL a mano y sin conocer la API.

**`AC-FE02`** · Ve todas las versiones de curva de la línea seleccionada, y solo de ésa.

**`AC-FE03`** · Puede iniciar la carga de una versión nueva desde esa vista.

**`AC-FE04`** · La carga usa el contrato real del backend: `POST /masters/weight-curves` con
`genetic_line_id`, `version_label` y `points`. No se inventa multipart, ni `version`, ni
ningún campo que el esquema no declare.

**`AC-FE05`** · Un rechazo del backend se presenta de forma utilizable: la fila, el campo y el
motivo, legibles. Nunca JSON crudo, nunca trazas.

**`AC-FE06`** · Tras una carga válida, la versión aparece en la lista sin recargar el navegador.

**`AC-FE07`** · La versión activa se distingue de las demás por **texto**, no solo por color.

**`AC-FE08`** · Las versiones históricas siguen visibles tras activar una nueva.

**`AC-FE09`** · La interfaz **no ofrece** ninguna acción que reasigne lotes existentes a una
curva nueva. `OD-06` lo prohíbe.

**`AC-FE10`** · El alta de lote muestra la línea genética y **qué versión de curva** quedará
asociada, incluido el caso de que no haya ninguna activa.

**`AC-FE11`** · La pantalla del pesaje muestra la evaluación **del backend** (`AC26`).

**`AC-FE12`** · `BELOW_STANDARD`, `WITHIN_STANDARD` y `ABOVE_STANDARD` se representan de forma
distinguible entre sí.

**`AC-FE13`** · `NO_REFERENCE` se representa **explícitamente** y jamás como normal, como cero
ni como ausencia.

**`AC-FE14`** · No hay interpolación, clasificación ni tolerancia en el cliente. El motor sigue
viviendo en un solo sitio.

**`AC-FE15`** · No se introduce ningún canal de notificación. `P-14` sigue intacto.

**`AC-FE16`** · La interfaz respeta `RBAC`: quien solo lee no ve acciones de escritura, y el
backend sigue siendo la autoridad —ocultar un botón no es autorizar—.

**`AC-FE17`** · Todo texto nuevo pasa por `i18n`, con paridad `es`/`en` mantenida.

**`AC-FE18`** · El flujo es utilizable en escritorio y en móvil, con el patrón responsive ya
existente.

**`AC-FE19`** · Las pruebas satisfacen `GA-REM-016 AC13`: ninguna se invoca como evidencia sin
demostrar que puede fallar. Aserciones no vacuas.

**`AC-FE20`** · La sensibilidad demuestra que las pruebas detectan la retirada de la capacidad:
del control de carga, del mapeo de la petición, de la representación de `NO_REFERENCE` y de la
alerta.

## A.4 Alcance — lo que la enmienda NO autoriza

- **Una página de primer nivel nueva.** El requisito es la capacidad operativa. Se integra en
  el maestro `GeneticLine` que ya existe (`GA-REM-033`), reutilizando el patrón de `P-12`.
- **Un segundo sistema de administración.** Lista, diálogos, paginación, estados de carga,
  vacío y error salen del patrón certificado.
- **Borrado físico de curvas.** El backend no lo ofrece y el histórico se conserva.
- **Un endpoint de *preview*.** No existe; no se inventa.
- **Parsear reglas de negocio en el cliente.** La conversión de la tabla a filas es aritmética
  de formato; toda regla la valida el backend.
- **Tocar el motor certificado**, sus modelos, su migración o sus alertas.

## A.5 Trazabilidad añadida

| `AC` | Prueba | Nivel |
|---|---|---|
| `AC26`…`AC28` | `backend/tests/test_weight_evaluation_endpoint.py` | integración HTTP |
| `AC-FE01`…`AC-FE08` | `e2e/proceso-p03-curvas-ui.spec.ts` | **`UI_E2E`** |
| `AC-FE10`…`AC-FE13` | `e2e/proceso-p03-curvas-ui.spec.ts` | **`UI_E2E`** |
| `AC-FE05`, `AC-FE07`, `AC-FE12`, `AC-FE13`, `AC-FE16` | `frontend/src/**/__tests__` | `vitest` |
| `AC-FE14` | inspección + `vitest` | estático |
| `AC-FE17` | paridad de `translation.json` | conteo |
| `AC-FE19`, `AC-FE20` | informe de certificación | mutación |

> **Sobre la modalidad — corrección.** La nota original decía que `§4.5` no exige que el
> usuario vea nada en pantalla, y por eso fijaba `API_E2E`. Para las alertas eso sigue siendo
> cierto. **No lo es para la carga de la curva**: `OD-06` exige que el usuario pueda cargar la
> tabla dentro del producto, y una capacidad operativa de producto no se demuestra por API.
> `AC-FE01`…`AC-FE13` exigen `UI_E2E`. Esto no contradice `§124` del encargo —no se fabrica
> `UI_E2E` por vocabulario—: se exige porque el requisito del propietario es de producto.

## A.6 Definición de terminado — ampliada

- Los veinticinco criterios originales siguen pasando.
- `AC26`…`AC28` y `AC-FE01`…`AC-FE20` pasan.
- `R-96` y `R-97` cerrados con evidencia propia.
- Sensibilidad demostrada sobre la capacidad de carga, el mapeo, `NO_REFERENCE` y la alerta.
- Paridad `i18n` mantenida.
- Sin migración nueva: el trabajo de frontend no la necesita.
- `P-03` recertificado de extremo a extremo, no por «el endpoint responde».
