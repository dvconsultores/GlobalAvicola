# `R-177` · Matriz de dominio: tipo de huevo ≠ resultado de ovoscopía (`R177_EGG_TYPE_OVOSCOPY_DOMAIN_MATRIX`) — PRE-FLIGHT, SIN CÓDIGO

**WAVE B · tranche 11 · pre-flight solamente** · 2026-09-10 · hallazgo `R-177` (P3, registrado en el pre-flight del tranche 10).

## 1. Corrección del registro

El registro del tranche 10 decía: «el formulario de **recepción en incubadora** envía categorías de ovoscopía (`dead_early`, `dead_late`,
`contaminated`) como tipos recibidos». **Era inexacto**: releído `OperationFormPage.tsx`, el bloque con esas categorías (`:1476-1498`) pertenece al
`case 'ovoscopy'` («Día de ovoscopía», `bird_movements.0.week_number`); el `case 'egg_reception_hatchery'` (`:1144-1197`) no lleva filas por tipo. El
hecho verdadero: **el evento `ovoscopy` persiste sus resultados como `egg_movements.egg_type`** (`fertile`, `infertile`, `dead_early`, `dead_late`,
`contaminated`), en el mismo campo y tabla que los tipos de huevo de la recolección. `AC-R172-06` (recepción con `contaminated`) demostró además que el
backend persiste cualquier cadena. La parte «`egg_type` sin enum» se confirma.

## 2. Fuentes

| Nivel | Fuente | Texto |
|---|---|---|
| 2 | `Bases` p.7-9 | traslado y recepción de **huevos fértiles**; incubadora: «cantidad de huevos fértiles recibidos» |
| 3 | `docs/02 §3.6.2` | recolección: «Cantidad total, Huevos fértiles, Huevos no aptos, Huevos rotos, Huevos sucios, Huevos comerciales» |
| 3 | `docs/02 §3.6.3` | clasificación: «fértiles, sucios, infértiles, descartados» |
| 3 | `docs/02 §3.7.1` | recepción en incubadora: «Cantidad recibida, Diferencias vs enviado, Condición de recepción» (sin lista de tipos) |
| 3 | `docs/02 §3.7.3` | **ovoscopía**: «Huevos infértiles, Embriones muertos tempranos, Embriones muertos tardíos, Huevos contaminados» |
| 3 | `docs/03 :277` | `egg_type: enum (FERTILE, DIRTY, BROKEN, INFERTILE, DISCARDED, COMMERCIAL)` |
| 4 | `spec.md :164/:165/:188` | `egg_collection` (fértiles, sucios, rotos, infértiles) · `egg_classification` (para incubación / aptos, no aptos) |
| 4 | `spec.md :192` | `ovoscopy` «Ovoscopia (infértiles, embriones muertos tempranos/tardíos, contaminados)» — **evento propio**, con sus categorías |
| 4 | `GA-REM-005-F` (`RR-17`) | solo `fertile` cuenta en `BR-02`/`BR-03`; el resto se captura y no cuenta |
| 5 | `models.py:203` · `schemas.py:25` | `egg_type: String(30)` / `str` con comentario `# fertile, dirty, broken, infertile, discarded, commercial`; sin validación; migración `7922512fdef4` sin `CHECK` |
| 5 | formularios | recolección/clasificación: `fertile, dirty, broken, infertile, discarded` · despacho: `fertile` (`R-172`) · ovoscopía: `fertile, infertile, dead_early, dead_late, contaminated` |
| 5 | `OperationDetailPage.tsx:174` · `ReviewDetail.tsx:151` | muestran `em.egg_type` **crudo** (sin `t()`), p. ej. «100 · fertile» |
| 5 | `public/locales` | `operations.fertile/dirty/broken/infertile/discarded`, `deadEarly/deadLate/contaminated` existen; **`commercial` no tiene etiqueta** |
| 5 | `reports/service.py:283` | `_huevos_por_tipo(..., tipo)` filtra por igualdad de cadena (`fertile`) |

## 3. Matriz de dominio (`§43`)

| Valor UI | Etiqueta UI | Campo API | Persistido | Significado fuente | Concepto | ¿Tipo de huevo? | ¿Resultado de ovoscopía? | ¿Calidad? | `BR-02`? | `BR-03`? | Unidad válida | Etapa válida | ¿Cadena libre? | ¿Puede persistir un valor inválido? | Efecto en informes | Efecto en saldo | Autoridad | ¿Decisión? | Remediación futura |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `fertile` | Fértiles | `egg_movements[].egg_type` | `fertile` | huevo fértil (`Bases`, `docs/02`) | tipo de huevo **y** resultado de ovoscopía (en el formulario de ovoscopía también aparece «Fértiles») | sí | sí (ambiguo) | — | **sí** | **sí** | breeder/grandparent (recolección, despacho) · hatchery (recepción, ovoscopía) | producción · incubadora | sí | sí (mayúsculas, espacios) | fertilidad/eclosión (`_huevos_fertiles`) | único que cuenta | `RR-17` | no | cerrar el conjunto |
| `dirty` | Sucios | ídem | `dirty` | huevo sucio (`§3.6.2`) | tipo de huevo | sí | no | sí | no | no | producción | producción | sí | sí | agregados de huevos (`_sum_egg_quantity`: recolección + clasificación) | no | `docs/02` | no | ídem |
| `broken` | Rotos | ídem | `broken` | huevo roto | tipo | sí | no | sí | no | no | producción (y «diferencias vs enviado» en recepción) | ídem | sí | sí | ídem | no | `docs/02` | no | ídem |
| `infertile` | Infértiles | ídem | `infertile` | huevo infértil (`§3.6.2`) **y** resultado de ovoscopía (`§3.7.3`) | **ambos conceptos, mismo valor** | sí | sí | — | no | no | producción · incubadora | ambas | sí | sí | fertilidad usa recepción; ovoscopía no tiene KPI | no | `docs/02` | **sí** (§5) | separar conceptos |
| `discarded` | Descartados | ídem | `discarded` | descartado (`§3.6.3`) | clasificación de calidad/disposición | sí | no | sí | no | no | producción | producción | sí | sí | agregados | no | `docs/02` | no | cerrar el conjunto |
| `commercial` | **sin etiqueta** | ídem | `commercial` | huevo comercial (`§3.6.2`) | tipo/destino comercial | sí | no | — | no | no | producción | producción | sí | sí | agregados; UI muestra la clave cruda | no | `docs/02`/`docs/03` | no | etiqueta + cerrar |
| `dead_early` | Muertos tempranos | ídem (evento `ovoscopy`) | `dead_early` | «embriones muertos tempranos» (`§3.7.3`) | **resultado de ovoscopía** (no es un tipo de huevo de `docs/03`) | **no** | **sí** | — | no | no | hatchery | incubadora | sí | sí | ninguno (no hay KPI de ovoscopía) | no | `spec.md :192` | **sí** | modelo propio |
| `dead_late` | Muertos tardíos | ídem | `dead_late` | «embriones muertos tardíos» | resultado de ovoscopía | no | sí | — | no | no | hatchery | incubadora | sí | sí | ninguno | no | ídem | sí | ídem |
| `contaminated` | Contaminados | ídem | `contaminated` | «huevos contaminados» | resultado de ovoscopía | no | sí | — | no | no | hatchery | incubadora | sí | sí | ninguno | no | ídem | sí | ídem |
| cualquier otra cadena (`Fertile`, `fértil`, `banana`) | — | ídem | tal cual | ninguno | — | — | — | — | no | no | cualquiera | cualquiera | **sí** | **sí** (`AC-R172-06` lo demostró con `contaminated` en una recepción) | fragmenta agregados; UI cruda | no (solo `fertile` cuenta) | ninguna | no (defecto de calidad de dato) | validación por conjunto cerrado o maestro (§5) |

## 4. Distinción conceptual (`§42`) y control de calidad de dato (`§44`)

Cuatro conceptos conviven en un campo: **tipo de huevo** (fértil/sucio/roto/comercial: `docs/02 §3.6.2`), **clasificación de calidad/disposición**
(aptos/no aptos, descartados: `§3.6.3`, `spec.md :188`), **resultado de ovoscopía** (`§3.7.3`, `spec.md :192`) y **disponibilidad** (`RR-17`: solo
`fertile`). `infertile` y `fertile` aparecen en dos de ellos con el mismo valor. Impacto aunque el saldo esté a salvo (`R-172`): valores inválidos
persistibles (nada los rechaza), fragmentación de agregados por variantes ortográficas, UI sin traducir (`em.egg_type` crudo; `commercial` sin etiqueta),
filtros por igualdad de cadena, ambigüedad futura si alguien intenta un KPI de ovoscopía sobre `egg_movements`. **Sin efecto en `BR-02`/`BR-03`** (predicado
positivo `fertile`). No hay «silent fallback»: el valor se guarda tal cual.

## 5. Puerta de decisión (`§45`)

| Opción | ¿Documentada? | Fuente que la sostiene |
|---|---|---|
| A · enum cerrado único | sí, parcialmente | `docs/03 :277` (seis valores) — **pero** no incluye los resultados de ovoscopía que `spec.md :192` exige capturar |
| B · maestro configurable | **no** | `docs/02 §2` (catálogo de maestros) no lista tipos de huevo ni categorías de ovoscopía |
| C · dos campos: `egg_type` + `ovoscopy_result` | sí | `docs/02 §3.6.2` vs `§3.7.3` y `spec.md :164` vs `:192` los definen como datos de **eventos distintos** |
| D · reutilizar un maestro existente | **no** | ninguno aplicable |
| E · otro modelo (p. ej. tabla propia de ovoscopía) | no documentado | — |

Ninguna fuente de nivel 1-4 decide entre A y C (ni el nombre del campo, ni si la ovoscopía debe dejar de usar `egg_movements`), y la elección cambia el
modelo de datos y la captura → **`OWNER_DECISION_REQUIRED` (`AOD-24`)** para el modelo; la **validación de valores** (rechazar cadenas fuera del conjunto
gobernado de cada evento) depende de esa misma decisión (qué conjunto), así que **no se implementa aquí**. Sin preferencia en código.

## 6. Clasificación (`§46`)

```
R-177 ............ PARTIAL: (1) registro corregido (el bloque es del evento ovoscopy, no de la recepción) · (2) DATA QUALITY DEFECT confirmado (cadena libre,
                   valores inválidos persistibles, UI cruda, `commercial` sin etiqueta) · (3) CONFIRMED DOMAIN MODEL DEFECT (tipo de huevo ≠ resultado de
                   ovoscopía en el mismo campo) → OWNER_DECISION_REQUIRED (AOD-24) para el modelo · severidad P3 (sin efecto en saldos ni inquilino)
estado ........... OPEN · OWNER_DECISION_REQUIRED (AOD-24) · sin código en esta tranche · dependencia: R-172 intacto (predicado `fertile`)
siguiente ........ cuando AOD-24 se resuelva: enmienda (GA-REM-005 o spec propia), migración si C, formularios, etiquetas (`commercial`, detalle/revisión con t())
```
