# `R-171` · MATRIZ DE VERDAD DE LA MORTALIDAD Y EL DESCARTE EN INCUBADORA

**WAVE B · tranche 9 · pre-flight** · 2026-09-10 · `R-171` (P2): «la etapa `hatchery` del catálogo no ofrece `cull_recording` ni `mortality_recording`,
que son lo que viables y rendimiento restan» (`processCatalog.ts:226-229, 403-412`).

## 1. Fuentes

- `Bases` p.10 (Incubadora, KPI): «Tasa de mortalidad de pollitos = pollitos muertos / total nacidos» → existe una **mortalidad de pollitos** posterior al nacimiento.
- `Rec. §12` (incubadora, la app captura): «Nacimientos · **Pollitos descartados** · Vacunación · Clasificación · Transferencia a granja».
- `docs/02 §3.7.5` (nivel 3): campos del nacimiento «Pollitos nacidos, Pollitos viables, **Pollitos descartados**». `spec.md §4.7` (nivel 4): `birth_registration` «(viables, descartados, mortalidad en planta, vacunación)».
- `GA-REM-005-B` (nivel 4, certificado, `R-130`): `viables = nacidos − mortalidad − descartes − despachados`, donde mortalidad y descartes son los eventos `mortality_recording` y `cull_recording` del lote de incubación.
- `GA-REM-021-C` (`B13`, `RR-15`): débil ≠ descarte ≠ muerto; `AOD-23` pendiente (igualdad de la partición).

## 2. Matriz de verdad

| Concepto | Etapa | Recurso | Fuente | ¿Captura exigida? | ¿Evento o atributo? | Cantidad | ¿Afecta huevos? | ¿Afecta nacidos? | ¿Afecta viables? | ¿Afecta saldo? | ¿Ya lo representa `B13`? | ¿Ya lo representa `R-170`? | ¿Solapa? | ¿Excluyente? | Corrección | Aprobación | Auditoría | FE actual | API actual | BD actual | Brecha | ¿Decisión? |
|---|---|---|---|:--:|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|---|---|---|---|---|---|:--:|
| huevos sucios/rotos/descartados en la recolección | huevo, granja | `egg_collection` (`egg_type`) | Rec. §11 | sí (existe) | filas de `egg_movements` | por tipo | **sí** (hoy inflan `BR-02`: `R-172`) | no | no | no | no | no | — | — | no (submov.) | `P-07` | sí | sí | sí | sí | no es `R-171` | no |
| huevos infértiles en ovoscopía | huevo, incubadora | `ovoscopy` | Rec. §12 | sí (existe) | evento informativo | — | no (no resta de `BR-03`; sin fuente) | no | no | no | no | no | — | — | — | — | sí | sí | sí | sí | no es `R-171` | no |
| **pollitos muertos tras el nacimiento** | pollito, incubadora (post-nacimiento) | `mortality_recording` sobre el lote `hatchery` | `Bases` p.10 | **sí** | **evento** (el mismo de §9 para aves; `GA-REM-005-B` lo resta de viables) | `bird_movements.quantity` | no | no | **resta** | **−** (una vez, `R-130`, bloqueado) | no (`B13` = atributos al nacer) | no (`BR-21` = filas del nacimiento) | no | con descarte: hechos distintos | no (submov.) | `P-07` | sí | **NO se ofrece** (catálogo) | **sí** (`validate_mortality` acepta lotes `hatchery`; sin ubicación exigida) | sí | **UI_ONLY** | **no** |
| **pollitos descartados** | pollito, incubadora (post-nacimiento) | `cull_recording` sobre el lote `hatchery` | Rec. §12 · `docs/02 §3.7.5` · `spec.md §4.7` | **sí** | **evento** (`GA-REM-005-B` lo resta de viables). `docs/02` lo lista como campo del nacimiento: un **atributo** además del evento duplicaría el efecto (clase `R-170`) → el evento lo satisface (`RR-16`) | `bird_movements.quantity` | no | no | **resta** | **−** (una vez) | no: débil ≠ descarte (`RR-15`) | no | no | con mortalidad: hechos distintos | no | `P-07` | sí | **NO se ofrece** | **sí** (`validate_bird_decrement`) | sí | **UI_ONLY** | **no** |
| pollitos débiles | nacimiento | `chicks_weak` | `Bases` p.9 | sí (cerrado, `B13`) | atributo | — | no | no | **no** | no | **es `B13`** | — | no | — | sí (revalidada) | — | sí | sí | sí | sí | — | `AOD-23` (igualdad) |

## 3. Clasificación

```
R-171 ............ UI_ONLY · GOBERNADO · SIN DECISIÓN: el backend acepta y contabiliza mortality_recording y cull_recording sobre lotes de
                   incubadora (viables los resta una vez, R-130 bloqueado); el catálogo de la etapa hatchery no los ofrece.
etapa ............ post-nacimiento (pollito); las pérdidas de huevo son otras capturas (existen) y no son R-171
evento/atributo .. evento (RR-16): el «Pollitos descartados» de docs/02 §3.7.5 se satisface con el evento de descarte del flujo de
                   incubadora; un atributo del nacimiento además del evento sería una segunda contabilidad (R-170)
efecto ........... resta de viables y del saldo exactamente una vez (fórmula certificada); sin efecto en huevos ni en nacidos
B13 .............. intacto (débil ≠ descarte ≠ muerto; AOD-23 sigue pendiente)
misma raíz que R-161 ... NO → no se implementa en este tranche (CASO B); queda OPEN, listo para el siguiente (catálogo + pasos de flujo + i18n + vitest)
control ......... AC-R161-16 (prueba de API): mortalidad y descarte sobre un lote de incubadora → 201 y viables restan una vez
```
