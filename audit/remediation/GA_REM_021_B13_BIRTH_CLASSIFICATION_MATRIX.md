# `GA-REM-021` · `B13` · MATRIZ DE CONTABILIDAD Y CONTRATO DEL NACIMIENTO (SANOS / DÉBILES)

**WAVE B · tranche 8 · pre-flight** · 2026-09-10 · `H360-B13` (P2) · fuente `Bases Consideradas…pdf` p.9 «Incubadora · 4. Nacimiento de
Pollitos» · método `REQUIREMENT_CONFLICT_RESOLUTION §1` · hallazgo colateral **`R-170`** (P1, activo, reproducido).

## 1. Requisito exacto (nivel 2, textual, p.9-10)

```
4. Nacimiento de Pollitos:
   • Fecha de Nacimiento: fecha en que los pollitos nacen.
   • Número de Pollitos Nacidos: cantidad total de pollitos nacidos.
   • Número de Pollitos Sanos: cantidad de pollitos nacidos sanos y viables.
   • Número de Pollitos Débiles: cantidad de pollitos nacidos débiles o con problemas.
   • Tasa de Eclosión: porcentaje de huevos fértiles que eclosionan con éxito.
   • Observaciones.
KPI (p.10): Tasa de eclosión = nacidos / huevos fértiles · Tasa de mortalidad de pollitos = muertos / total nacidos ·
            Porcentaje de pollitos sanos = sanos / total nacidos · Eficiencia de traslado = trasladados / nacidos
```

Rec. §12 (incubadora): la app captura «Nacimientos · Pollitos descartados · Clasificación». `docs/02 §3.7.5` (nivel 3): «Pollitos nacidos,
Pollitos viables, Pollitos descartados, % eclosión, % nacimiento». `spec.md §4.7` (nivel 4): `birth_registration` «(viables, descartados,
mortalidad en planta, vacunación)». `GA-REM-005-B` (nivel 4, certificado): «viable» = nacidos − mortalidad − descartes − despachados
(«lo que “viable” significa (`Bases` p.9: sanos frente a débiles)»). Nivel 6 (legado): `healthy_chicks`, `weak_chicks` (`docs/15:148-149`).

## 2. Gate — ¿qué nace, en qué unidad, qué significan las categorías?

| Pregunta | Respuesta | Nivel |
|---|---|---|
| ¿Qué se cuenta? | pollitos nacidos vivos en la nacedora del lote de incubación (`birth_registration`) | 2 (p.9) · 4 (`spec.md §4.7`) |
| ¿Unidad de negocio? | **Incubadora** (`hatchery`) únicamente; la colocación en engorde es `bird_reception` (`B01`) | 2 (sección «Incubadora») · `COMPLETENESS_360:47` |
| ¿Sanos? | «nacidos sanos y viables» — subconjunto de los nacidos; la fuente iguala sano ≡ viable **al nacer** | 2 |
| ¿Débiles? | «nacidos débiles o con problemas» — subconjunto de los nacidos, excluyente con sanos por definición; **no** es descarte ni mortalidad (p.9 no tiene viñeta de descartados; el descarte es otro hecho: Rec. §12 «pollitos descartados», `cull_recording`) | 2 · 4 (`GA-REM-005-B`) |
| ¿Partición completa (sanos + débiles = nacidos)? | **no la afirma ninguna fuente**: las definiciones garantizan `sanos + débiles ≤ nacidos` (dos subconjuntos disjuntos del total), no la igualdad | — → `AOD-23` |
| ¿Sexo? | ninguna fuente de nivel 1-4 exige sanos/débiles por sexo (`GA-REM-005:420`); el sexado al nacer (♂/♀) es dato existente de las filas | — |
| ¿Nacedora / incubadora? | `docs/02 §3.7.5` los lista como campos; `HatcheryParams` existe pero el nacimiento no lo persiste hoy; **fuera** de `B13` (no cambia la contabilidad) | 3 |

## 3. Hallazgo colateral `R-170` (P1, activo, reproducido)

El formulario de nacimiento (`OperationFormPage.tsx:1568-1590`) emite **cuatro filas** de `bird_movements`: «Total nacidos» (`mixed`),
«Machos viables» (`male`), «Hembras viables» (`female`), «Débiles» (`mixed`). El backend no tiene ninguna regla para `BIRTH_REGISTRATION`
(`service.py:852-892`: sin rama) y **suma todas las filas** como nacidos en `get_viable_chick_balance`, `get_current_bird_balance` y
`total_chicks_born`.

```
Observado (API, forma del formulario): mixed 100 · male 48 · female 47 · mixed 5  →  201 · 4 filas · viables = 200 · saldo = 200
Verdad: 100 pollitos. Consecuencia: BR-04 (despacho ≤ viables) admite despachar el doble de lo nacido; el KPI de eclosión se duplica.
```

Ninguna prueba enviaba esa forma (todas usan una fila `mixed`), por eso `R-130` está verde y el defecto pasó inadvertido.
Raíz: **dos contabilidades del mismo hecho** (un total + su desglose) en la misma tabla sin distinguirlas. Autoridad: `GA-REM-005`
(saldo de aves) → **enmienda C · `BR-21`** (una sola contabilidad de nacimientos). Severidad **P1** (verdad de población; misma clase que `R-130`).

## 4. Matriz de contabilidad

| Campo / categoría | Significado (fuente) | ¿En nacidos? | ¿En sanos? | ¿En débiles? | ¿En mortalidad? | ¿En descarte? | ¿En viables? | ¿Despachable? | ¿Excluyente? | ¿Solapa? | ¿Afecta saldo? | Fuente | Modelo actual | Brecha |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|---|---|
| fila `bird_movements` (`male`) | nacidos machos | **sí** | según clasificación | según clasificación | no | no | sí | sí | con `female`/`mixed` | no | **+** | 2 (total) · 5 (sexado) | existe | una fila por sexo (`BR-21`) |
| fila `bird_movements` (`female`) | nacidos hembras | **sí** | ídem | ídem | no | no | sí | sí | ídem | no | **+** | ídem | existe | ídem |
| fila `bird_movements` (`mixed`) | nacidos sin sexar | **sí** | ídem | ídem | no | no | sí | sí | **excluye** `male`/`female` | no | **+** | 2 | existe | `mixed` exclusivo (`BR-21`) |
| «Total nacidos» (fila UI) | duplicado del Σ | **NO** (es Σ) | — | — | — | — | — | — | — | **sí** (duplica) | **debe ser 0** | — | fila `mixed` extra (`R-170`) | se elimina; el total se **deriva** |
| `chicks_healthy` | «nacidos sanos y viables» | subconjunto | **es** | no | no | no | sí (son nacidos) | sí | con débiles | no | **no** (atributo) | 2 | no existe | columna de evento |
| `chicks_weak` | «nacidos débiles o con problemas» | subconjunto | no | **es** | no | **no** | sí (siguen nacidos hasta descarte/muerte) | sí, salvo descarte posterior | con sanos | no | **no** (atributo) | 2 | fila `mixed` «Débiles» que **sumaba nacidos** (`R-170`) | columna de evento |
| resto sin clasificar | nacidos − sanos − débiles | sí | no | no | — | — | sí | sí | — | — | — | ninguna fuente lo prohíbe ni lo exige → `AOD-23` | — | admitido (≥ 0) |
| `mortality_recording` | pollitos muertos tras nacer | no | — | — | **sí** | no | resta | — | — | — | **−** | p.10 · `R-130` | existe | — (`R-171`: la UI de incubadora no lo ofrece) |
| `cull_recording` | descartados | no | — | — | no | **sí** | resta | — | — | — | **−** | Rec. §12 · `GA-REM-005-B` | existe | ídem (`R-171`) |
| `chick_dispatch` | trasladados | no | — | — | no | no | resta | — | — | — | **−** | p.10 · `BR-04` | existe | — |

Grafo canónico (único): `NACIDOS = Σ filas (una por sexo)` → `sanos + débiles ≤ NACIDOS` (atributos) → `VIABLES = NACIDOS − mortalidad −
descartes − despachados` (`R-130`, sin cambio) → `BR-04`. Sanos/débiles **no** entran en ninguna ecuación de saldo: son los dos datos que
el cliente pide y el KPI «% sanos» (ola C, `H360-K11`) consumirá.

## 5. Contrato de datos

| Recurso | Campos | Tipo | Obligatorio | Identidad | Fecha | Estado | Actor | RBAC | Aprobación | Corrección | Auditoría | Efecto en saldo | `R-130` | `R-161` | Persistencia | Brecha |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `birth_registration` (lote `hatchery`) | `bird_movements[]` (`sex` ∈ {male, female, mixed}, `quantity` ≥ 0) | existente | Σ ≥ 1 | **`BR-21`**: una fila por sexo; `mixed` excluye sexadas | `event_date` | `P-07` | operador | `operations:create/update` | existente | no corregible (submovimientos) | existente | `+ Σ` (una vez) | intacto | N/A (agregado de aves, con bloqueo) | `bird_movements` | regla nueva |
| ídem | `chicks_healthy`, `chicks_weak` | `int ≥ 0` | **sí, explícitos** (p.9 los lista como datos diarios) | **`BR-21`**: `sanos + débiles ≤ Σ` | — | — | — | — | — | corregibles uno a uno con revalidación (`≤`, no tupla de igualdad) | existente | **ninguno** | intacto | N/A | `operational_events.chicks_healthy/chicks_weak` (migración `x4y5z6a7b8c9`) | columnas nuevas |
| otros tipos de evento / otras cadenas | ídem | — | prohibidos (`400`) | — | — | — | — | — | — | — | — | — | — | — | — | regla |

## 6. Aplicabilidad por unidad

| Unidad | `birth_registration` | `chicks_healthy`/`chicks_weak` | `BR-21` filas | Fuente |
|---|---|:--:|:--:|---|
| Incubadora (`hatchery`) | sí | **obligatorios** | sí | `Bases` p.9 |
| Progenitoras · Reproductoras · Engorde | no nacen pollitos en granja | prohibidos | (la regla de filas rige donde haya nacimiento) | sin fuente |

## 7. Relación con `R-161`

`R-161` afecta a `get_egg_balance` (`BR-02`) y `get_hatchery_egg_balance` (`BR-03`), agregados de **huevos** leídos sin bloqueo. `B13` y
`BR-21` operan sobre las filas de aves del nacimiento, cuyos agregados ya se leen con bloqueo (`R-130`). **Independiente.** No se añade
«nacidos ≤ huevos cargados» (leería el agregado sin bloqueo y no lo pide ninguna fuente de nivel 1-2).

## 8. Hallazgo registrado `R-171` (P2, no se resuelve aquí)

La etapa `hatchery` del catálogo (`processCatalog.ts:226-229`, `:403-412`) no ofrece `mortality_recording` ni `cull_recording`, que son
exactamente lo que `viables` y el rendimiento restan; desde el flujo de incubadora `viables ≡ nacidos`. `Bases` p.10 («tasa de mortalidad
de pollitos») y Rec. §12 («pollitos descartados») los exigen. Corrección documental: `FUNCTIONAL_COVERAGE_MATRIX CV-D23` daba por
«COVERED» sanos/débiles por las etiquetas de la UI; el modelo no los tenía.

## 9. Frontera

Fuera: `R-161` · `R-171` · `AOD-23` (igualdad) · KPI «% sanos» (ola C) · nacedora/incubadora en el nacimiento · sexo de sanos/débiles ·
«pollitos descartados» como campo del nacimiento (`docs/02 §3.7.5`; el descarte sigue siendo `cull_recording`) · fase 9.
