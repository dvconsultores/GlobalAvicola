# `P-06` · POLLO DE ENGORDE — INFORME DE CERTIFICACIÓN

---

# REEVALUACIÓN tras `OD-04` y `GA-REM-035` (2026-09-06)

```
P-06 = PARTIAL — BLOCKED_BY_DEFECT (R-76)
```

Se reevalúan **uno a uno** los tres bloqueantes históricos, sin certificar por alcance:

| Bloqueante | Estado | Evidencia |
|---|---|---|
| **`GA-TD-014`** | **RESUELTO** | `OD-04` `RESOLVED` · `GA-REM-035` `CERTIFIED`. El paso `bird_reception` de `P-06` ya aplica el límite acumulado |
| **`GA-REQ-037`** | **no bloquea** | `§4.8` —la sección normativa de `P-06`— **no menciona alertas por desviación**. Las exige `§4.5`, que es `P-03`. Verificado leyendo ambas |
| **`R-76`** | **BLOQUEA** | `docs/12 R7`: «un lote no puede cerrarse si tiene registros sin aprobar». Sigue sin implementarse, y `§4.8` incluye «cierre de lote» en su cadena |

## Por qué `P-06` sigue `PARTIAL`

`R-76` es una regla de **cierre**, y el cierre es el paso terminal de `P-06`. Un lote puede
cerrarse hoy con eventos en `registered`, lo que contradice `docs/12 R7`.

**No se corrige aquí.** Es otra causa, con su propia spec de destino, y absorberla dentro de
`GA-TD-014` sería exactamente lo que el proceso de este programa prohíbe.

```
Lo que falta para certificar P-06:  R-76, y solo R-76.
```

Es la primera vez que `P-06` queda a un único hallazgo de la certificación.
