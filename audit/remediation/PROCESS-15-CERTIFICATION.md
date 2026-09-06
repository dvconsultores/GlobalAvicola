# `P-15` · REPORTES E INDICADORES — INFORME DE CERTIFICACIÓN

`spec.md §4.12` · `docs/02 §3.12` · `GA-REM-022` enmienda A · 2026-09-06

```
P-15 = CERTIFIED
R-14 = CERTIFIED   R-85 = CERTIFIED   R-86 = CERTIFIED
R-87 · R-88 = RETIRADOS (no eran hallazgos)
```

---

## 1. Dos correcciones de partida

**`AC13` no es el catálogo de KPI.** Es la puerta de validez de pruebas de `GA-REM-016`. Lo
que define qué debe medirse es `docs/02 §3.12.1` y `spec.md §4.12`.

**Los cuatro huérfanos no son cuatro requisitos.** `vaccination-efficiency` y
`transfer-efficiency` los exige el cliente; `animal-welfare` e `production-index` salen de
`docs/15` con prioridad media y baja y no están entre los trece de `§3.12.1`. Se dejan como
estaban: exponerlos «para completar los cuatro» sería convertir una lista interna en
requisito.

## 2. Lo que estaba roto

`reports/service.py:145` devolvía una frase en español dentro de un campo `_pct`, alegando
que faltaban los datos de carga. **La alegación era falsa** y `GA-REM-022` ya lo había
demostrado: `HatcheryParams.quantity_loaded` los guarda y `get_hatchery_egg_balance` los
sumaba desde antes. La pantalla mostraba el indicador vacío.

Y al contrastarlo con la fuente superior apareció `R-85`: `docs/02 §3.12.1` separa **tres**
cocientes con denominadores distintos, y el endpoint los fundía en un solo campo mal llamado.

```
Eclosión    = nacidos ÷ FÉRTILES      75,0 %  con la fixture de prueba
Nacimiento  = nacidos ÷ CARGADOS      60,0 %
Rendimiento = viables ÷ CARGADOS      54,0 %
```

Un documento de proceso es nivel 3 de la jerarquía y una spec de remediación nivel 4: mandó
`docs/02`. Se conserva `hatchability_pct` como alias documentado de `nacimiento_pct`, porque
retirarlo rompería un contrato que ningún requisito pide.

`R-86`: «Fertilidad» era normativa y no la calculaba nadie, aunque `EggMovement.egg_type`
distingue `fertile` de `infertile` desde siempre.

## 3. Un supuesto declarado, no escondido

`docs/02` pide «Rendimiento incubadora = **pollitos viables** ÷ huevos cargados». *Viables*
no es un campo del modelo. La única representación de pollitos no viables es el descarte, así
que se toma **nacidos − descartados**.

No se usó `get_viable_chick_balance`, que resta **despachos**: mide cuántos quedan
disponibles, no cuántos nacieron viables. Son cosas distintas y confundirlas habría dado un
indicador que baja al despachar, lo que no es un rendimiento.

Sin descartes registrados, el rendimiento coincide con el nacimiento —que es correcto— y se
afina a medida que se registran. El supuesto queda en la enmienda para que el propietario
pueda corregirlo si su operación entiende otra cosa por «viable».

## 4. Semántica de aprobación — resuelta por la norma

Los KPI solo cuentan eventos aprobados. **Es intencionado**, y `AC05` lo dice. No se
incluyeron pendientes para que los indicadores «dejaran de estar en cero»: eso habría
cambiado la semántica del negocio sin requisito.

Lo que faltaba era lo otro:

```
0     ·  se midió y dio cero
null  ·  no hay base aprobada sobre la que medir   ← ahora se distingue
texto ·  prohibido                                  ← era lo que devolvía
```

Y el aviso que `AC05` exige: la pantalla del lote declara que los indicadores se calculan
solo con datos aprobados cuando no hay base suficiente.

## 5. La cadena, paso a paso

| Mitad | Pasos | Estado |
|---|:--:|:--:|
| A · indicadores | 1-10 | **PASS 10** |
| B · reportes | 11-16 | **PASS 6** |

```
16 pasos · PASS 16 · FAIL 0
```

## 6. Dos hallazgos que registré y resultaron falsos

Declaré `R-87` («el reporte de estados no tiene productor») y `R-88` («la exportación
Excel/PDF no existe»), y anuncié que `P-15` no podría certificarse.

**Los dos eran erróneos.** Busqué ambos **solo en el backend**:

- la exportación vive en `frontend/src/utils/export.ts`, con SheetJS y jsPDF, y el propio
  fichero dice «no requiere backend»;
- la distribución por estado la devuelve el reporte de lote en `event_summary.by_status` y
  la pinta el dashboard.

Es el mismo atajo —concluir desde una búsqueda parcial— que este programa lleva tres tramos
reprochando a los documentos heredados. Queda anotado en `P15_PROCESS_CHAIN_MATRIX §3` en
lugar de borrado, y ambos hallazgos se retiran.

## 7. Evidencia

### Fase roja

| Prueba | Con el código anterior |
|---|---|
| `nacimiento_pct`, `eclosion_pct`, `rendimiento_pct` | **`KeyError`** — los campos no existían |
| `fertilidad_pct` | **`KeyError`** |
| nulo con dato insuficiente | **`KeyError`** |
| agregado entre empresas | **PASS** ya entonces — el filtro por compañía existía |

### Puerta de sensibilidad

| Mutación | Fallan | Restaurado |
|---|:--:|:--:|
| la eclosión pasa a usar el denominador del nacimiento | **2** | 7/7 |
| el conteo de nacimientos deja de exigir aprobación | **1** | 7/7 |
| el agregado deja de filtrar por compañía | **1** | 7/7 |

La primera pasada de la mutación de aprobación **no rompió nada**: muté un ayudante nuevo en
lugar del filtro que esa prueba recorre. Repetida sobre el filtro correcto, falla. Se anota
porque una mutación mal dirigida puede hacer pasar por insensible a una prueba que no lo es.

`git diff` tras revertir: solo lo previsto.

### Regresión

| | Antes | Después |
|---|---|---|
| Backend | 352 · 49 omitidas | **359 · 49 omitidas · 0 fallos** |
| E2E | 91/91 | **95/95** |
| `tsc` · `vitest` · i18n | — | **PASS · 61/61 · 866 = 866** |

## 8. `R-80`

```
R-80 = OPEN   ·   ¿bloquea P-15? NO
```

Los indicadores agregan por `event_date` —fecha de negocio— de forma homogénea. Ninguno
compara una fecha de negocio con un instante UTC, que es el desajuste que `R-80` describe.

## 9. Modalidad

`API_E2E` de proceso, conforme a `GA-REM-016 AC05`. `§3.12` no exige comportamiento visible
en ninguna de sus reglas; el cambio de `LotReportPage` se verifica por revisión del diff y
`tsc`, que es lo que `AC07` pide.

## 10. Veredicto

```
P-15 = CERTIFIED   ·   15 de 15 indicadores obligatorios · 6 de 6 reportes
```
