# `R-172` · Matriz de disponibilidad por tipo de huevo (`R172_EGG_TYPE_AVAILABILITY_MATRIX`)

**WAVE B · tranche 10 · pre-flight** · 2026-09-10 · hallazgo `R-172` (P2, registrado en el pre-flight del tranche 9) · spec gobernante `GA-REM-005-D`
(`BR-02`, `BR-03`) · **sin decisión del propietario** (§6) · `CAPTURADO ≠ DISPONIBLE`.

## 1. Hallazgo exacto

> `R-172` · P2 · «`get_egg_balance` suma todas las `egg_type` de la recolección (sucios, rotos, infértiles, descartados) como huevos disponibles
> para despacho; `BR-02` habla de fértiles disponibles (semántica, no concurrencia)» · `validators.py:91-114` · `REMEDIATION_BACKLOG.md:1078`.

## 2. Fuentes leídas (nivel · texto)

| Nivel | Fuente | Texto / hecho |
|---|---|---|
| 2 | `Bases` p.7-8 (vía `KPI_FORMULA_AND_DATA_SOURCE_MATRIX.md §3`) | sección **«Traslado de huevos fértiles»**: eficiencia de traslado = trasladados / fértiles |
| 2 | `Bases` p.9 (Incubadora) | **«Número de Huevos Recibidos: Cantidad de huevos fértiles recibidos»** · eclosión = nacidos / huevos fértiles |
| 2 | `Rec. central` §6.6 (vía `docs/16`) | captura «huevos recolectados, fértiles, descartados, rotos, sucios, infértiles» (todos son **hechos capturados**) |
| 3 | `docs/02 §3.6.2` | recolección: «Cantidad total, Huevos fértiles, Huevos no aptos, Huevos rotos, Huevos sucios, Huevos comerciales, Peso promedio» |
| 3 | `docs/02 §3.6.3` | clasificación (fértiles, sucios, infértiles, descartados) — paso propio, informativo |
| 3 | `docs/02 §3.6.4` | **despacho a incubadora**: «Cantidad enviada, Clasificación, Condición, …, Transporte, Guía» |
| 3 | `docs/02 §3.7.1` | **«Registro de recepción de huevos fértiles»**: «Cantidad recibida, Diferencias vs enviado, Condición de recepción» |
| 3 | `docs/02 §3.7.3` | ovoscopía: «Huevos infértiles, Embriones muertos tempranos, Embriones muertos tardíos, Huevos contaminados» |
| 3 | `docs/02 §7` R2 | «No permitir despacho de huevos mayor al **disponible**» |
| 3 | `docs/03 §…:277` | `egg_type: enum (FERTILE, DIRTY, BROKEN, INFERTILE, DISCARDED, COMMERCIAL)` |
| 4 | `spec.md :107/:164` | `egg_collection` «Recolección de huevos (fértiles, sucios, rotos, infértiles)» |
| 4 | `spec.md :166` | `egg_dispatch` «Despacho de huevos **a incubadora** (con transporte y guía)» |
| 4 | `spec.md :176/:187` | incubadora: «Recepción de huevos **fértiles** (trazados al lote de producción origen)» · `egg_reception_hatchery` «Recepción de huevos fértiles (con clasificación y condición)» |
| 4 | `spec.md :188` | `egg_classification` (incubadora): «Clasificación de huevos recibidos (aptos, no aptos para incubar)» — informativo |
| 4 | `spec.md §5` · `GA-REM-005-D D.1` | `BR-02` = Σ recolección − Σ despacho · `BR-03` = Σ recepción en incubadora − Σ `quantity_loaded` (por lote, `≠ CANCELLED`) — **sin predicado de tipo** (la enmienda D fijó el bloqueo, no qué cuenta: lo dejó registrado como `R-172`) |
| 5 | `validators.py:91-114` | docstring «**Fertile eggs available** at the farm for dispatch» — y la consulta suma **todas** las `egg_type` |
| 5 | `validators.py:118-142` | `get_hatchery_egg_balance`: suma todas las `egg_type` recibidas |
| 5 | `OperationFormPage.tsx:1003-1020` | recolección/clasificación: filas `fertile, dirty, broken, infertile, discarded` |
| 5 | `OperationFormPage.tsx:1124-1138` | **despacho**: las mismas cinco filas (`fertile, dirty, broken, infertile, discarded`) |
| 5 | `OperationFormPage.tsx:1479-1497` | recepción en incubadora: filas `fertile, infertile, dead_early, dead_late, contaminated` (categorías de **ovoscopía**, `docs/02 §3.7.3`; tres de ellas no están en el enum de `docs/03`) |
| 5 | `models.py:203` · `schemas.py:25` | `egg_type: String(30)` / `str` sin validación de valores |
| 5 | `reports/service.py` | fertilidad y eclosión usan `_huevos_fertiles(EGG_RECEPTION_HATCHERY)` (`egg_type == 'fertile'`) — el KPI ya distingue |
| 5 | `test_*.py` | 19 despachos/recolecciones con `fertile`; una prueba por cada otro tipo (captura) |

**Corte.** El nivel 2 define lo que llega a la incubadora (**huevos fértiles**) y el nivel 3/4 lo que se despacha (**a incubadora**) y lo que se recibe
(**fértiles**). Nadie dice que sucios, rotos, infértiles, descartados o comerciales se despachen a la incubadora ni que se carguen. `BR-02` («disponible»)
se lee, por tanto, como **fértiles recolectados − despachados**; `BR-03` («huevos recibidos») como **fértiles recibidos − cargados** (definición del
cliente, p.9). Los demás tipos son **hechos capturados** (producción, roturas, suciedad: KPI de ola C), no disponibilidad. Ninguna «intuición avícola»:
solo lo que las fuentes nombran.

## 3. Matriz por tipo de huevo

| Tipo | Definición fuente | ¿Capturado? | ¿Cuenta como recibido? | ¿Disponible para despacho (`BR-02`)? | ¿Disponible para incubación (`BR-03`)? | ¿Descartado? | ¿Rechazado? | ¿Informativo? | ¿Afecta `BR-02`? | ¿Afecta `BR-03`? | ¿Otro saldo? | Implementación actual | Esperado por fuente | ¿Decisión? | AC | Prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `fertile` | «huevos fértiles» (`Bases` p.7-9, `docs/02 §3.6.2/§3.7.1`, `spec.md :187`) | sí (recolección, clasificación, despacho, recepción) | **sí** (p.9: «cantidad de huevos fértiles recibidos») | **sí** (lo único que se traslada) | **sí** | no | no | no | **sí, único** | **sí, único** | no | cuenta (como todos) | cuenta | no | `AC-R172-01/02` | tipo positivo |
| `dirty` | «huevos sucios» (`docs/02 §3.6.2`, `spec.md :164`) | sí (recolección) | no | **no** | **no** | no (hecho de recolección) | no | sí | hoy sí → **no** | hoy sí (si se recibe) → no | no (KPI) | cuenta | **no cuenta** | no | `AC-R172-03` | tipo negativo |
| `broken` | «huevos rotos» | sí | no | no | no | — | — | sí | hoy sí → no | ídem | no | cuenta | no cuenta | no | `AC-R172-03` | negativo |
| `infertile` | «huevos infértiles» (`§3.6.2`; en incubadora es resultado de **ovoscopía**, `§3.7.3`) | sí | no | no | no | — | — | sí | hoy sí → no | ídem | no | cuenta | no cuenta | no | `AC-R172-03/06` | negativo (ambos saldos) |
| `discarded` | «descartados» (`§3.6.3`) | sí | no | no | no | sí | — | sí | hoy sí → no | ídem | no | cuenta | no cuenta | no | `AC-R172-03` | negativo |
| `commercial` | «huevos comerciales» (`§3.6.2`; sin evento de venta en el alcance) | sí (enum) | no | no (no van a incubadora) | no | no | no | sí | hoy sí → no | — | no | cuenta | no cuenta | no | `AC-R172-03` | negativo |
| `dead_early` · `dead_late` · `contaminated` | categorías de **ovoscopía** (`§3.7.3`); no están en el enum de `docs/03`; el formulario de recepción en incubadora las envía como `egg_type` | sí (solo por ese formulario) | no | n/a | **no** | — | — | sí | — | hoy sí → no | no | cuenta | no cuenta | no (predicado positivo: solo `fertile` cuenta; el resto, sea cual sea la etiqueta, no) | `AC-R172-06` | negativo (`BR-03`) |
| cualquier otra cadena | `String(30)` sin validación | posible | — | — | — | — | — | — | hoy sí → no | ídem | — | cuenta | no cuenta | registrado `R-177` | — | — |

## 4. Ecuaciones: actual vs exigida

```
ACTUAL   BR-02(lote) = Σ egg_movements.quantity [egg_collection, status ≠ CANCELLED, TODOS los egg_type]
                       − Σ egg_movements.quantity [egg_dispatch, ≠ CANCELLED, TODOS]
         BR-03(lote) = Σ egg_movements.quantity [egg_reception_hatchery, ≠ CANCELLED, TODOS]
                       − Σ hatchery_params.quantity_loaded [incubation_load, ≠ CANCELLED]

EXIGIDA  cuenta_como_disponible(egg_type) := egg_type == 'fertile'          (un solo predicado, un solo sitio)
         BR-02(lote) = Σ quantity [egg_collection, ≠ CANCELLED, disponible] − Σ quantity [egg_dispatch, ≠ CANCELLED, disponible]
         BR-03(lote) = Σ quantity [egg_reception_hatchery, ≠ CANCELLED, disponible] − Σ quantity_loaded [incubation_load, ≠ CANCELLED]
         egg_dispatch: toda fila con egg_type no disponible → 400 BR-02 «El despacho a incubadora es de huevo fértil» (sin fila, sin auditoría)
```

Sobrecontabilización confirmada: recolección `fertile 100 + dirty 50 + broken 10` → hoy `BR-02` admite despachar **160**; fuente: **100**.
`R-172` **CONFIRMADO** (`§30` del prompt: la agregación actual suma todos los tipos y la fuente restringe).

## 5. Dos disponibilidades, trazadas por separado (`§29`)

| Saldo | Recurso | Entrada | Salida | Predicado de entrada | Predicado de salida | Relación con `R-161` |
|---|---|---|---|---|---|---|
| `BR-02` (granja) | `lots.id` del lote de producción | `egg_collection` | `egg_dispatch` | `fertile` | `fertile` (las demás filas se rechazan en el alta; las históricas no fértiles, si las hubiera, **no** cuentan: nunca fueron disponibilidad) | mismo bloqueo, mismo orden; solo cambia **qué** se suma |
| `BR-03` (incubadora) | `lots.id` del lote de incubación | `egg_reception_hatchery` | `incubation_load` (`quantity_loaded`, sin tipo) | `fertile` (p.9) | n/a (la carga no lleva tipo) | ídem |

Mismo predicado, **dos saldos distintos**: no se fusionan ni se crea un tercero. La recepción en incubadora **sí** admite filas no fértiles (son las
«diferencias vs enviado» y la condición de recepción de `docs/02 §3.7.1`): se capturan y no cuentan. El despacho **no** las admite: nada de nivel 2-4
despacha a la incubadora huevo que no sea fértil.

## 6. Clasificación y puerta

```
R-172 ............ ACTIVE · GOBERNADO · SIN DECISIÓN DEL PROPIETARIO · P2
predicado ........ cuenta_como_disponible(egg_type) = (egg_type == 'fertile') — un helper, usado por BR-02 y BR-03 (misma semántica probada por fuente)
datos ............ ninguna fila se borra ni se reescribe (CAPTURADO ≠ DISPONIBLE); sin migración
frontend ......... el formulario de egg_dispatch ofrece solo la fila «Fértiles» (las otras cuatro pasarían a 400); recolección/clasificación/recepción sin cambio
spec ............. GA-REM-005 enmienda F (BR-02/BR-03: qué cuenta) · RC-14 / RR-17
```

¿Por qué no `OWNER_DECISION_REQUIRED`? La pregunta «¿qué se traslada a la incubadora?» la responde el cliente (nivel 2: fértiles) y la documentación
funcional (nivel 3: recepción de huevos fértiles); la única voz discrepante es la implementación (nivel 5), que suma todo. `REQUIREMENT_CONFLICT_RESOLUTION.md §1`:
se corta en el nivel más alto que habla; no se escala.

## 7. Residuales registrados (fuera del tranche)

| ID | P | Qué |
|---|---|---|
| `R-177` | P3 | `egg_type` es `String(30)`/`str` sin lista de valores (enum de `docs/03` no aplicado); el formulario de **recepción en incubadora** envía categorías de ovoscopía (`dead_early`, `dead_late`, `contaminated`) como tipos de huevo recibidos (`docs/02 §3.7.3` las asigna a la ovoscopía). Informativo tras `R-172` (solo `fertile` cuenta); alinear formulario y enum exige su propia traza de `docs/02 §3.7.1` |
| — | — | `egg_reception_classification` / `egg_classification` (aptos / no aptos) siguen **informativos**: ninguna fuente los conecta con `BR-03`; se deja constancia, sin decisión (no cambia el comportamiento) |

## 8. AC → prueba (contrato completo en `GA-REM-005-F`)

| AC | Qué | Prueba (`tests/test_egg_type_availability.py`, prefijo `TIPO-`) |
|---|---|---|
| `AC-R172-01` | recolección `fertile 100` → `BR-02` = 100; despacho 100 → `201`; 1 más → `400 BR-02` | positivo |
| `AC-R172-02` | recolección mixta `fertile 100 + dirty 50 + broken 10 + infertile 5 + discarded 5` → `BR-02` = **100**; despacho 101 → `400 BR-02`; 100 → `201` | mixto (la suma es selectiva) |
| `AC-R172-03` | cada tipo no disponible por separado (`dirty`, `broken`, `infertile`, `discarded`, `commercial`): recolección de 50 → `BR-02` = 0; despacho de 1 → `400 BR-02` | negativos, uno por tipo real |
| `AC-R172-04` | despacho con fila `dirty` (o cualquier tipo no disponible) → `400 BR-02`, sin fila, sin auditoría de alta | contrato del despacho |
| `AC-R172-05` | las filas capturadas persisten (`egg_movements` conserva `dirty 50`); nada se borra | `CAPTURADO ≠ DISPONIBLE` |
| `AC-R172-06` | recepción en incubadora `fertile 100 + broken 5 + contaminated 3` → `BR-03` = 100; carga 101 → `400 BR-03`; 100 → `201` | `BR-03` independiente |
| `AC-R172-07` | `R-161`: carreras `AC-R161-05/06` siguen verdes (bloqueo intacto) | regresión |
| `AC-R172-08` | formulario de `egg_dispatch`: solo la fila `fertile` (contrato estático `vitest`); recolección conserva las cinco | `frontend/src/pages/operations/__tests__/eggDispatchFormContract.test.ts` |

Sensibilidad: `R172-S1` (restaurar «todos los tipos cuentan») → `AC-R172-02/03` rojas · `R172-S2` (quitar `fertile` del predicado) → `AC-R172-01` roja ·
`R172-S3` (aceptar filas no fértiles en el despacho) → `AC-R172-04` roja.
