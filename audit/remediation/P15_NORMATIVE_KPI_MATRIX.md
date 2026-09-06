# `P-15` · QUÉ INDICADORES EXIGE LA NORMA

Fase de análisis · 2026-09-06 · sin desarrollo

Se parte de la documentación, no del código: `docs/02 §3.12.1` y `spec.md §4.12`.

---

## 1. Los trece de `docs/02 §3.12.1`

| # | KPI | Fórmula normativa | Fuente del dato | Estado de aprobación |
|:--:|---|---|---|---|
| 1 | Mortalidad diaria | aves muertas hoy | `BirdMovement` · `mortality_recording` | solo aprobados |
| 2 | Mortalidad acumulada | % acumulado del lote | ídem | solo aprobados |
| 3 | Viabilidad | % de aves vivas sobre iniciales | balance de aves | solo aprobados |
| 4 | Peso promedio vs estándar | comparación con curva estándar | `weight_recording` | solo aprobados |
| 5 | Uniformidad | % dentro de ±10 % del peso promedio | ídem | solo aprobados |
| 6 | Consumo de alimento | kg acumulados | `FeedMovement` | solo aprobados |
| 7 | Conversión alimenticia | kg alimento / kg peso ganado | ídem + pesajes | solo aprobados |
| 8 | Producción de huevos | huevos / ave / día | `EggMovement` | solo aprobados |
| 9 | **Fertilidad** | **% huevos fértiles** | `EggMovement.egg_type` | solo aprobados |
| 10 | **Eclosión** | **% eclosionados sobre fértiles** | nacimientos ÷ fértiles | solo aprobados |
| 11 | **Nacimiento** | **% nacidos sobre huevos cargados** | nacimientos ÷ `quantity_loaded` | solo aprobados |
| 12 | Rendimiento incubadora | pollitos viables ÷ huevos cargados | ídem | solo aprobados |
| 13 | Diferencias SAP vs App | comparación de cantidades | `/reports/sap-comparison` | — |

`spec.md §4.12` añade **auditoría por usuario/lote/documento SAP** —cubierto por `P-09`— y
**exportación Excel/PDF**.

## 2. Un conflicto terminológico que la norma resuelve

`docs/02 §3.12.1` separa **tres** cocientes distintos de incubadora:

```
Eclosión                = eclosionados ÷ FÉRTILES
Nacimiento              = nacidos      ÷ CARGADOS
Rendimiento incubadora  = viables      ÷ CARGADOS
```

`GA-REM-022 AC01` llama «Tasa de Eclosión» a *«nacidos viables dividido entre huevos
cargados»*, que según `docs/02` es **Nacimiento / Rendimiento**, no Eclosión.

Por la jerarquía de evidencia (`REQUIREMENT_CONFLICT_RESOLUTION §1`), un documento de proceso
—nivel 3— manda sobre una spec de remediación —nivel 4—. **`docs/02` decide.**

```
R-85 · P2 · GA-REM-022 AC01 nombra «Eclosión» una fórmula que docs/02 §3.12.1 llama
            «Nacimiento». No es un detalle de vocabulario: son dos denominadores distintos
            —fértiles frente a cargados— y confundirlos da cifras distintas.
```

## 3. Un indicador normativo sin productor

**Fertilidad** (`% huevos fértiles`, nº 9) no lo calcula ningún endpoint. El dato existe:
`EggMovement.egg_type` distingue `fertile` de `infertile`.

```
R-86 · P2 · «Fertilidad» es uno de los trece indicadores de docs/02 §3.12.1 y no tiene
            productor. El dato está en el sistema.
```

## 4. Los cuatro sospechosos, clasificados

`§13` del encargo advierte de no confundir presencia en el código con requisito. Ninguno de
los cuatro está en los trece de `docs/02 §3.12.1`; hay que ir a las otras fuentes.

| Endpoint | ¿Normativo? | Fuente | Clasificación |
|---|:--:|---|---|
| `/kpis/vaccination-efficiency` | **sí** | el cliente lo exige — «Eficiencia de Vacunación», citado en `GA-REM-022` | **C · calculado y no expuesto** |
| `/kpis/transfer-efficiency` | **sí** | el cliente lo exige — «Eficiencia de Traslado» | **C · calculado y no expuesto** |
| `/kpis/animal-welfare` | **no** | `docs/15 G-01`, prioridad **media**, «KPI mencionado en doc original» | **I · implementado sin ser exigido** |
| `/kpis/production-index` | **no** | `docs/15 G-05`, prioridad **baja** | **I · implementado sin ser exigido** |

**Dos de los cuatro son obligatorios, dos no.** Los dos últimos se dejan como están: existen,
funcionan y nadie los pidió. Exponerlos «para completar los cuatro» sería convertir una lista
interna en requisito, que es justo lo que `§64` prohíbe.

> `docs/15` los daba por «no implementados como endpoint»: eso está **obsoleto**, los cuatro
> existen. Lo que sigue siendo cierto es que no son exigidos por `§3.12.1`.

## 5. Estado de aprobación — resuelto por la norma

`reports/service.py` filtra todos los KPI a `APPROVED`, `CONSOLIDATED`, `SENT_TO_SAP` y
`SAP_CONFIRMED`. De ahí que un lote con registros pendientes muestre ceros.

**Es intencionado y correcto**, y `GA-REM-022 AC05` lo confirma sin ambigüedad:

> Given que los KPI **solo consideran eventos aprobados** … Then la interfaz lo indica, en
> lugar de mostrar cero sin explicación.

Es decir: **no se incluyen pendientes** —eso sería cambiar la semántica del negocio sin
requisito, lo que `§21` prohíbe— y **el hueco está en la interfaz**, que no lo declara.

## 6. Sin datos suficientes — resuelto por la norma

`GA-REM-022 AC02` decide, y no hay que elegir:

> Then se devuelve un **valor nulo con un indicador explícito** de dato insuficiente
> And **no un texto en español embebido en un campo numérico**.

```
0        →  se midió y dio cero
null     →  no hay datos aprobados suficientes
texto    →  prohibido
```
