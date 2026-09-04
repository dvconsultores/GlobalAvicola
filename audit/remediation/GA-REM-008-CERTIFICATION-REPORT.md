# GA-REM-008 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-008` — Trazabilidad generacional |
| **Wave** | 2 · **Stage 8** · **Conflicto** `RC-04` |
| **Fecha** | 2026-09-04 |
| **Estado final** | **`CERTIFIED`** |

## Original finding

La creación automática de `EggBatch` y `ChickBatch` emparejaba despacho y recepción
**exigiendo que ambos compartieran `lot_id`**, y después asignaba el lote destino como
`reception.lot_id` — el mismo lote.

Por definición del dominio, el despacho se registra en el lote origen y la recepción en el
destino: son lotes distintos. La coincidencia **nunca ocurre**, de modo que no se creaba
ningún vínculo; si por accidente coincidiera, se habría creado un lote enlazado consigo
mismo.

## `RC-04` — resuelto por evidencia

`spec.md §4.9` dice «para el mismo lote de huevos». La implementación lo leyó como «el mismo
`lot_id`». La evidencia decisiva es estructural:

```
backend/app/lots/models.py:109   source_lot_id    -> lots.id
backend/app/lots/models.py:111   hatchery_lot_id  -> lots.id
```

**Existen dos columnas de lote porque son dos lotes distintos.** Si «el mismo lote»
significara un identificador compartido, la segunda no tendría razón de ser. Es el mismo
argumento que resolvió `RC-02`: el esquema no puede expresar la alternativa, luego la
alternativa no era una opción de negocio.

> **`RR-04`.** «El mismo lote de huevos» designa el mismo lote **físico** viajando de un
> lote productivo a otro, no un `lot_id` compartido. El vínculo une siempre dos lotes
> distintos. El emparejamiento automático usa el **destino declarado por el operador**
> (`destination_farm_id` / `destination_plant_id`). Sin destino declarado no se crea vínculo
> automático: `spec.md §4.9` ya contempla el enlace manual, y adivinar la correspondencia
> sería peor que no establecerla.

Clasificación secundaria: **`SPEC_DEFECT`** — la redacción ambigua es la que produjo el
defecto.

## Implementation

Dos ayudas simétricas, una por sentido —el despacho puede llegar antes que la recepción o
después—, que aplican el mismo criterio y por eso producen el mismo vínculo:

| Método | Busca |
|---|---|
| `_recepcion_en_el_destino_declarado` | la recepción en un lote de la granja que el despacho declaró como destino |
| `_despacho_dirigido_a_este_lote` | el despacho cuyo destino declarado es la granja de este lote |

Ambas excluyen explícitamente `lot_id` iguales. **Nunca se crea un lote enlazado consigo
mismo.**

El criterio solo es utilizable desde el **Stage 1**: `destination_farm_id` es uno de los 14
campos que `P0-14` descartaba en silencio. La trazabilidad automática no podía funcionar
mientras el dato que la sostiene no se guardaba — dos defectos que se tapaban mutuamente.

## Tests

`tests/test_traceability.py` — **4 PASS · 0 FAIL**

| Test | Verifica |
|---|---|
| `test_rc04_el_vinculo_une_dos_lotes_distintos` | despacho en el origen, recepción en el destino declarado, vínculo visible en el árbol |
| `test_ningun_lote_queda_enlazado_consigo_mismo` | barrido sobre `EggBatch` y `ChickBatch` |
| `test_sin_destino_declarado_no_se_inventa_el_vinculo` | sin destino, cero vínculos |
| `test_el_enlace_manual_sigue_disponible` | la alternativa que la spec sanciona funciona |

## Hallazgo anotado

`R-47` *(P1, nuevo)*: `POST /lots` **ignora el `start_date` recibido** y activa el lote en el
momento de la creación. Se detectó porque `BR-06` —que sí funciona— rechazó una recepción
fechada días atrás en un lote recién creado. Destino `GA-REM-019`.

## Regression

Suite completa **211 PASS · 0 FAIL**. Cero regresiones.

## Final status

**`CERTIFIED`.** La trazabilidad enlaza lotes distintos, usa el destino que el operador
declaró y se abstiene cuando no lo hay, en lugar de adivinar.
