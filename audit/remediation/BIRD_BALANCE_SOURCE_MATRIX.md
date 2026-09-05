# MATRIZ DE FUENTES DEL BALANCE DE AVES

**`R-67` · `GA-REM-005` enmienda** · 2026-09-04

---

## 1. La regla

```
SALDO = saldo de apertura + Σ(entradas) − Σ(salidas)
```

Implementada en `app/operations/validators.py::get_current_bird_balance`.

## 2. Fuentes

| Fuente | Suma | Resta | Se aplica a | Lotes existentes | Lotes nuevos | Notas |
|---|:--:|:--:|---|:--:|:--:|---|
| **Saldo de apertura** `initial_male_count + initial_female_count` | ✔ | | lotes activados manualmente | **sí** | no | `R-67`. Es el saldo desde el que se continúa (`docs/02 §3.9.2`) |
| `bird_reception` | ✔ | | todos | sí | sí | aves que entran al lote |
| `birth_registration` | ✔ | | incubación | sí | sí | nacimientos |
| `mortality_recording` | | ✔ | todos | sí | sí | `BR-01` valida contra este saldo |
| `cull_recording` | | ✔ | todos | sí | sí | descarte |
| `bird_exit` | | ✔ | todos | sí | sí | salida del lote |
| `chick_dispatch` | | ✔ | incubación | sí | sí | despacho de pollitos |
| `bird_transfer` | | | neutro | — | — | intra-lote entre galpones (`RR-02`) |
| `bird_distribution` | | | neutro | — | — | redistribución interna (`RR-02`) |
| `accumulated_mortality_male/female` | | | **no participa** | — | — | histórico previo a la implantación (`RR-08`) |
| `accumulated_culls_male/female` | | | **no participa** | — | — | ídem |

Los eventos cancelados quedan excluidos en todos los casos (`status != CANCELLED`).

## 3. Por qué los acumulados no se restan

Es la decisión de fondo y viene de `docs/02 §3.9.1`, que enumera como campos **distintos**:

```
Saldos iniciales de aves (machos/hembras)
Mortalidad acumulada previa
Descartes acumulados
```

Y de §3.9.2, que fija dos reglas del módulo: «**Se evita doble conteo**» y «Se permite
**continuar operación desde el saldo inicial**».

El saldo inicial es lo que hay. La mortalidad acumulada es lo que hubo, y se captura para
que los indicadores del lote no empiecen de cero al implantar el sistema. Restarla del
saldo la contaría dos veces: ya está descontada de la población que el usuario declara.

Resuelto como `RC-08`, regla `RR-08`, por evidencia de nivel 3 —documento de proceso
operativo— frente al nivel 5 que sostenía lo contrario (el mensaje de validación de
`lots/service.py:209`).

## 4. Escenarios, con números

### Lote existente incorporado al implantar

```
activación manual: 1 000 machos + 4 000 hembras   → saldo 5 000
mortalidad de 12                                  → saldo 4 988
```

Sin ningún evento histórico inventado. `AC-R67-02` lo comprueba: la activación manual no
crea ni un solo `OperationalEvent`.

### Lote nuevo por el flujo normal

```
sin saldo de apertura                             → saldo 0
recepción de 2 000                                → saldo 2 000
mortalidad de 25                                  → saldo 1 975
```

Idéntico al comportamiento anterior a `R-67`.

### Incorporado y luego ampliado

```
activación manual: 5 000                          → saldo 5 000
recepción posterior de 500                        → saldo 5 500
```

Las aves recibidas después son aves nuevas, no las mismas.

### Con histórico acumulado declarado

```
activación manual: 5 000
  accumulated_mortality: 300 machos + 700 hembras
  accumulated_culls:      50 machos +  60 hembras
                                                  → saldo 5 000
```

El histórico no toca el saldo.

## 5. Cómo se impide el doble conteo

`docs/02 §3.9.2` exige «Se evita doble conteo» y **nada lo implementaba**. Un lote con
eventos de recepción que además recibiera un saldo de apertura contaría dos veces las
mismas aves.

La activación manual pasa a rechazarse con `409` si el lote ya tiene operaciones no
canceladas. Es coherente con su propósito: incorporar lotes que existían **antes** de la
implantación, no corregir lotes que ya operan en el sistema.

## 6. Huecos anotados, no resueltos

| Hueco | Por qué no se resuelve aquí |
|---|---|
| Saldo **de huevos y pollitos** de un lote incorporado en producción | `docs/02 §3.9.1` pide capturar «producción acumulada», que no es saldo disponible. El modelo no tiene campo para el disponible y ninguna fuente lo exige. Inventarlo sería inventar requisitos |
| `R-69` · la validación `accumulated_mortality ≤ initial_count` | Bajo `RR-08` rechaza datos legítimos: un lote con 5 000 aves vivas que acumuló 6 000 bajas a lo largo de su ciclo. Cambiar una validación de negocio merece su propia decisión |
| `R-70` · `activate-manual` devuelve 500 con una fase inexistente | Clave foránea sin validar, misma familia que `R-65` |
