# `P-03` · REPRODUCTORAS — CRÍA — REEVALUACIÓN

`spec.md §4.5` · 2026-09-06

```
P-03 = PARTIAL — BLOCKED_BY_REQUIREMENT (GA-REQ-037)
```

---

## 1. Qué se resolvió

`GA-TD-014` está **cerrado** (`GA-REM-035`, tras `OD-04`). El paso `bird_reception` de `P-03`
aplica ya el límite acumulado de la orden de compra, igual que en `P-01`.

## 2. Qué sigue bloqueando

`spec.md §4.5` —la sección normativa de este proceso— enumera entre sus pasos:

> - **Alertas por desviaciones (peso fuera de curva estándar, mortalidad > umbral)**

La de mortalidad existe (`high_mortality`). **La de peso fuera de curva no**: el generador de
alertas produce `high_mortality`, `temperature_out_of_range` y `humidity_out_of_range`, y nada
más.

```
GA-REQ-037 = PARCIAL  ·  bloquea un paso normativo de §4.5
```

## 3. La diferencia con `P-01` y `P-06`

Merece decirse porque los tres compartían bloqueante y ahora divergen:

| Proceso | Sección | ¿Exige alertas por desviación? |
|---|---|:--:|
| `P-01` | `§4.4` | **no** |
| **`P-03`** | **`§4.5`** | **sí** |
| `P-06` | `§4.8` | **no** |

Se verificó leyendo las tres secciones, en lugar de arrastrar la anotación del blocker matrix,
que trataba `GA-REQ-037` como si afectara a los tres por igual.

## 4. Lo que falta

```
GA-REQ-037 · alerta de peso fuera de curva estándar
```

Requiere una curva estándar de referencia por línea genética y edad, que hoy no existe como
dato. **No se implementa aquí**: es funcionalidad nueva con su propio requisito, y `OD-04` no
la aborda.
