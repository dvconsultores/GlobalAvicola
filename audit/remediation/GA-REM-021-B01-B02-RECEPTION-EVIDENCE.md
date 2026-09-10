# EVIDENCIA · `GA-REM-021` enmienda B · `B01` CUADRE DE RECEPCIÓN + `B02` PESOS EN RANGO EN LA RECEPCIÓN (+ `GA-REM-037` enmienda B)

**WAVE B · tranche 7** · 2026-09-10 · spec `GA-REM-021-B` + `GA-REM-037-B` + `RC-11` (commit `f878ab6`) · código (commit `a759a17`) ·
matrices `GA_REM_021_B01_RECEPTION_RECONCILIATION_MATRIX.md` · `GA_REM_021_B02_WEIGHT_RANGE_MATRIX.md` · base `f1acac3` · rama `main` ·
cabeza final `w3x4y5z6a7b8`

## 1. Entrada y descomposición

| Ítem | Valor |
|---|---|
| HEAD de partida `f1acac3` · local == remoto · árbol limpio · Alembic `v2w3x4y5z6a7` · rutas 211 | sí |
| Recuento de la ola B revalidado fila a fila desde el backlog | 22 · 8 cerrados · 4 parciales · 10 abiertos (consistente con `WAVE_B §15`; sin corrección) |
| `B01` | `H360-B01` (P2): «hembras + machos + mortalidad + rechazo cuadren contra recibido» (Rec. §6) |
| `B02` | `H360-B02` (P2): «los pesos estén dentro de rango esperado» (Rec. §6) |
| Gate `B01` | recepción de aves en granja de **reproductoras** (`bird_reception`, lote `breeder`); **no** es `OD-04`/`GA-TD-014` (viñeta distinta del mismo §6; `BR-18` intacto) |
| Gate `B02` | promedio de muestra ♀/♂ (g) de la recepción; referente = **curva estándar fijada al lote** a la edad del día (`OD-06`, `GA-REM-037`); gobernado por `GA-REQ-037`/`OD-06`: **SÍ** |
| Composición | **CASO A**: ambos gobernados, independientes, mismo `POST /operations`; implementados ambos |
| Decisión del propietario | **no requerida** (`RC-11`: `RR-12`, `RR-13`); la cautela del tranche 6 sobre `B02` queda desestimada por la traza |
| Fuera | `B03` · `B04` (`AOD-14`) · `B13` · `R-156` (`AOD-20`) · `R-152`/`R-153` · `R-161` · `R-164` · `R-166` · ola C · fase 9 · SAP · `BU-D10` · `R-158` · cierre de OC · tolerancias · desviación % · estándar por sexo |

## 2. Gobierno (`RC-11`)

| Semántica | Resuelta por | Resultado |
|---|---|---|
| `B01` qué cuadra | nivel 2 (§6: captura «Cantidad recibida», «Distribución ♀/♂», «Mortalidad al arribo»; validación con «rechazo») | `received_total == Σ alojadas + dead_on_arrival + rejected_on_arrival` (`BR-20`), igualdad exacta, sin tolerancia |
| `B01` lado derecho | nivel 2 («Cantidad recibida» es dato de la misma captura) — la hipótesis de nivel 5 «usa el saldo» cede | dato declarado; el saldo es la consecuencia (entran las alojadas), no el referente |
| `B01` mortalidad al arribo | nivel 2 (captura de la recepción) sobre la elección de nivel 5 (evento aparte) | campo de la recepción; nunca entra al saldo; riesgo `R-167` registrado |
| `B01` aplicabilidad | nivel 2 (reproductoras) · nivel 4 (`spec.md §4.8`: engorde declara «mortalidad inicial») | reproductoras: identidad obligatoria; engorde: solo `dead_on_arrival` opcional; resto prohibido |
| `B01` corrección | aritmética + `RR-01` | los sumandos no son corregibles uno a uno (excluidos explícitamente); se editan por `PUT` o se devuelve (`R-135`) |
| `B01` concurrencia / idempotencia / estado / SAP | — | N/A (intra-evento) · `idempotency_key` existente · sin estado nuevo · SAP no participa |
| `B02` medida | nivel 2 + 5 | `BirdMovement.avg_weight` por fila ♀/♂, gramos |
| `B02` referente | `OD-06` (nivel 1) · `docs/02 §3.12.1/§3.14` (3) · `spec.md §4.5` (4); el peso del proveedor es nivel 6 (`R-156`, `AOD-20`); estándar fijo de pollito: inexistente | curva fijada al lote, edad `event_date − start_date`, interpolación lineal, bordes inclusivos, sin tolerancia, sin extrapolación (`NO_REFERENCE` declarado) |
| `B02` consecuencia | `GA-REM-037 §5` (nivel 4) + «capturar la realidad de granja» (nivel 2) | se persiste, se clasifica y **alerta**; no bloquea alta ni aprobación |
| `B02` aplicabilidad | nivel 2 (§6) · `PROCESS-06-CERTIFICATION:46` (§4.8 sin alertas) | reproductoras sí; engorde, progenitoras, incubadora no |
| `B02` autoridad | `GA-REM-037 §A.4` acota la enmienda A; **enmienda B** autoriza la puerta de la alerta | motor, modelos y migración de `GA-REM-037` intactos |

## 3. Rojo previo · validez (sobre `f878ab6`: spec sin código)

`tests/test_reception_reconciliation.py` (8) + `tests/test_reception_weight_range.py` (8): **9 rojas · 7 verdes**. 0 errores de import/fixture
imputables al producto.

| Grupo | Pruebas | Observado ≠ exigido | Válida |
|---|---|---|:--:|
| `B01`: datos descartados en silencio | `b01_01_03_05` (`KeyError 'received_total'`: `201` sin los campos), `b01_16_20` (sin los datos → `201`), `b01_17` (campos aceptados en cualquier lote/tipo) | el contrato ignora `received_total`/`dead_on_arrival`/`rejected_on_arrival` (patrón `R-47`) | sí |
| `B01`: sin cuadre | `b01_04_06` (101 y 99 → `201`), `b01_08_09` (filas que no cuadran → `201`) | ninguna identidad | sí |
| `B01`: edición | `b01_18` (`PUT received_total` → `422 extra_forbidden`) | el campo no existe en `Update` | sí |
| `B02`: sin alerta en la recepción | `b02_08_09_11_19_20`, `b02_03_05` (0 alertas ≠ 2 / 1) | la puerta del gancho solo admite `weight_recording` | sí |
| arnés | `b02_01_02_04_10` (`KeyError 'bird_movements'`: la lectura del evento no expone submovimientos por clave) | **inválida como rojo**: se corrigió la prueba (peso persistido comprobado en la base) y pasa a control | — |

Controles verdes en rojo (7): `b01_02_07_19` (OC acumulada `BR-18` y saldo = Σ filas), `b01_10_14` (cadena inquilino/unidad/RBAC certificada),
`b02_06_07`, `b02_12`, `b02_18`, `b02_22`, `b02_13` — la **lectura** de evaluación (`AC26`) ya aceptaba recepciones: lo que faltaba era la alerta.

## 4. Implementación (commit `a759a17`)

| Pieza | Qué hace |
|---|---|
| `alembic/versions/w3x4y5z6a7b8_reception_reconciliation.py` | tres enteros nulos en `operational_events` (`received_total`, `dead_on_arrival`, `rejected_on_arrival`); sin relleno; la bajada se detiene si hay cuadres declarados |
| modelo · `OperationalEventBase` (`ge=1`/`ge=0`) · `OperationalEventUpdate` | contrato de alta, lectura y edición |
| `validators.validate_reception_reconciliation` (`BR-20`) | una regla, dos puntos de aplicación (alta y edición): obligatoriedad explícita en reproductoras, identidad exacta con las **alojadas calculadas por el servidor**, `dead_on_arrival` opcional en engorde, campos prohibidos fuera |
| `corrections.service.NO_CORREGIBLES_POR_IDENTIDAD` | los tres sumandos quedan fuera de `campos_corregibles()` (excepción documentada a `RR-01`) |
| `service.py` puerta de alerta | `BIRD_RECEPTION` en lote `breeder` entra al mismo gancho que `weight_recording` (`GA-REM-037-B`); `evaluar_pesajes` y `weight_curve.py` intactos |
| autorización | ninguna lógica nueva: cadena certificada (`R-160`, `B05`) |
| frontend (vertical mínima) | `OperationFormPage`: tres campos del cuadre cuando la etapa es `breeder_rearing` + línea aritmética informativa (sin regla en cliente); `OperationDetailPage`: `WeightEvaluation` también para `bird_reception`; tipos y textos es/en |
| guardianes | cabeza → `w3x4y5z6a7b8`; rutas 211; `test_clean_baseline` (55 tablas) y `test_time_determinism` en el verde dirigido |
| fixtures (solo setup) | recepciones de reproductoras de 6 suites declaran su cuadre (`received_total = Σ`, `0`, `0`): `test_population_invariant`, `test_operations_bu_enforcement`, `test_lot_closure`, `test_lot_start_date`, `test_notification_recipients`, `test_opening_balance` — aserciones intactas; los lotes sembrados son de engorde y no necesitaron cambio |

Corrección de redacción del spec en este commit: `B.1(13)`, `AC-B01-18`, `B01-S7` y la matriz §8 decían «corregibles; se revalida en corrección»;
corregir un solo sumando de un registro cuadrado lo descuadra siempre, así que los sumandos se **excluyen** de la corrección y se editan juntos.

## 5. Verde dirigido

| Suite | Resultado |
|---|---|
| `test_reception_reconciliation.py` · **`B01`** | **8/8** |
| `test_reception_weight_range.py` · **`B02`** | **8/8** |
| obligatorias (regla permanente §5): `test_clean_baseline` · `test_time_determinism` · guardianes de cabeza/rutas/catálogo · enumerados | verdes |
| relacionadas: recepción contra OC (`GA-TD-014`) · linaje de recepción · `R-130` (21) · genética (curvas, evaluación, alerta, lectura) · `B05` (16) · correcciones · reversos · `R-135`/`R-143` · `R-159`/`R-160` · `R-162`/`R-163` · `OD-14` · RBAC · unidades · acceso · sesión · migración de roles · cierre de lote · fecha de inicio · saldo inicial · notificaciones · flujo completo · humo · transacción · contrato de error · persistencia · maestros · aislamiento | **662/664 en una invocación no alfabética (las 2 rojas, `t_037_01` y `t_025_07`, son residuo de otra suite: no se reproducen por pares ordenados ni en la regresión completa)** |
| `vitest` | **89/89** |
| `tsc -b --noEmit` | 6 errores, los mismos (`AuditPage.tsx` ×2, `LotFormPage.tsx` ×4) = `R-158` |

## 6. Sensibilidad (`GA-REM-021-B §B.7`)

Cada mutación se aplica marcada `MUTACION` (aplicación atómica), se ejecuta la suite del subrequisito, se revierte con `git checkout --`
y se comprueba `git diff --quiet -- app/`. Todas revertidas limpias.

| Mut. | Qué retira | Debía caer | Cayó | Válida |
|---|---|---|---|:--:|
| `B01-S1` | la identidad (`received_total == Σ + dead + rejected`) | `AC-B01-04` | **3**: `b01_04_06` (101 y 99 → `201`: se persiste el descuadre), `b01_08_09` (filas que no cuadran → `201`), `b01_18` (la edición descuadrada → `200`) | sí |
| `B01-S2` | «ignorar recepciones previas» | — | **`N/A`**: `B01` no acumula (la acumulación es `GA-TD-014`, con su propia sensibilidad) | — |
| `B01-S3` | la protección de concurrencia | — | **`N/A`**: sin agregado compartido entre peticiones | — |
| `B01-S4` | el servidor confía en un total alojado enviado por el cliente (`extra_data.placed_total`) | `AC-B01-08` | **1**: `b01_08_09` — el servidor toma `extra_data.placed_total` (95) y acepta filas que suman 90 (`201` ≠ `400`) | sí |
| `B01-S5` | la obligatoriedad explícita de los tres datos en reproductoras | `AC-B01-16` | **1**: `b01_16_20` — la recepción de reproductoras sin `received_total`/`dead_on_arrival`/`rejected_on_arrival` se registra | sí |
| `B01-S6` | la aplicabilidad por cadena (identidad y campos admitidos en cualquier lote/tipo) | `AC-B01-17` | **1**: `b01_17` — engorde acepta `received_total`/`rejected_on_arrival`, y `feed_registration`, progenitoras y lote sin cadena aceptan los tres | sí |
| `B01-S7` | la exclusión de los sumandos de la corrección uno a uno | `AC-B01-18` | **1**: `b01_18` — el corrector modifica un sumando y la recepción queda **descuadrada** (`correction_logs` con fila) | sí |
| `SEC-S1` | la empresa en las cuatro capas del alta (`_unidad_del_lote`, `_tipo_de_lote`, `lotes_alcanzables`, `validate_lot_active`) | `AC-B01-10` con fila observada | **1**: `b01_10_14` — el actor de `B` **escribe** la recepción sobre el lote de `A` (`201` observado; fila creada) | sí |
| `SEC-S2` | la habilitación de la unidad en la guarda compartida | `AC-B01-11` (global) | **1**: `b01_10_14` — la autoridad global situada en `A` registra sobre `broiler` apagada (`201` ≠ `403`) | sí |
| `SEC-S3` | la concesión del actor | `AC-B01-11/12` | **1**: `b01_10_14` — el operador sin la unidad del lote y el de concesión histórica sobre unidad apagada registran | sí |
| `SEC-S4` | `operations:create` → `read` en la ruta | `AC-B01-13` | **1**: `b01_10_14` — `sin_perm`, el Administrador de Accesos y el actor de control-lectura registran con `operations:read` | sí |
| `B02-S1` | la puerta de la alerta para la recepción | `AC-B02-08/09` | **2**: `b02_08_09_11_19_20` (0 alertas ≠ 2), `b02_03_05` (0 alertas ≠ 1) — la lectura `AC26` sigue clasificando; solo desaparece la alerta | sí |
| `B02-S2` | la interpolación del motor (devuelve el punto anterior) — sobre el motor certificado, revertida | `AC-B02-05` | **1**: `b02_03_05` — el día 5 devuelve el punto del día 0 (`38/40/42` ≠ `69/80/91`); el mismo motor sirve a la recepción | sí |
| `B02-S3` | la clasificación (todo `WITHIN_STANDARD`) — sobre el motor certificado, revertida | `AC-B02-08/09` | **2**: `b02_08_09_11_19_20` (30 y 50 g → `within_standard`, sin alerta), `b02_03_05` (68 g → dentro) | sí |
| `B02-S4` | confiar en línea/edad del cliente | — | **`N/A`**: el cuerpo no lleva línea ni edad (`AC-B02-11` es control) | — |
| `B02-S5` | evaluar con la versión activa de la línea en vez de la fijada al lote | `AC-B02-22` | **1**: `b02_22` — con `v2` activa, la recepción se evalúa contra `v2` (40 g → `below_standard`, alerta) en vez de contra la `v1` fijada al lote | sí |

Contabilidad: intentadas 13 (`B01-S1/S4/S5/S6/S7`, `SEC-S1…S4`, `B02-S1/S2/S3/S5`) · inicialmente inválidas 0 · reconstruidas 0 · válidas finales 13 ·
`N/A` 3 (`B01-S2`, `B01-S3`, `B02-S4`, declaradas así en `§B.7`) · acreditadas inválidas 0 · residuo `MUTACION` 0 · 13 reversiones limpias
(`git diff --quiet -- app/`). `B02-S2` y `B02-S3` mutan el motor certificado de `GA-REM-037` y se revirtieron: demuestran que la recepción
usa **ese** motor y no una copia. `SEC-S1` retira cuatro capas de empresa a la vez (lección del tranche 4): la fuga se **observa**
(`201` y fila), no se infiere. La pasada se ejecutó dos veces (la primera sobre `a759a17` con la regresión encadenada; la sesión se
reinició y sus registros se perdieron con el directorio temporal; la segunda, idéntica, regeneró los registros): mismos resultados.


## 7. Regresión

| Comprobación | Resultado |
|---|---|
| backend completo (`scripts/run_tests.sh`: `alembic upgrade head` → semillas → pytest) | **1016 passed · 49 skipped · 0 failed** (935 s; 1000 previas + 8 de `test_reception_reconciliation.py` + 8 de `test_reception_weight_range.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) |
| `R-130` 21/21 · `GA-TD-014` 7/7 · `R-78` linaje · genética 4 suites · `B05` 16/16 · `R-136`/`R-165` 27/27 · `R-135`/`R-143` 30/30 · `R-159/R-160` 40/40 · `R-162/R-163` 28/28 · `R-139` 35/35 · roles del reverso 5/5 + 3/3 | verdes |
| `authorization_coverage` (211) · `route_scope` · `SOLO_SUPER_ADMIN` 13 · `t_025_02` 48 · BU admin `== 7` · cabeza `w3x4y5z6a7b8` | exactos |
| migración | `w3x4y5z6a7b8` aplicada por `upgrade` en la base de pruebas (55 tablas); sin enumerados nuevos |
| `vitest` · `tsc` | 89/89 · 6 (`R-158`) |
| E2E | `BLOCKED_RUNTIME` (los `e2e/*.spec.ts` que registran recepciones de reproductoras deberán declarar el cuadre cuando el runtime esté disponible; no se editan a ciegas) |

Nota de proceso: la sesión se reinició durante la primera regresión completa encadenada a la sensibilidad y el directorio temporal con los
registros se perdió. La regresión completa se **relanzó y se leyó entera** antes de este commit; la sensibilidad se repitió con el mismo
driver y produjo los mismos resultados.

## 8. Cierre

```
B01 / H360-B01 ....... CERRADO (técnico): identidad exacta · datos explícitos · alojadas del servidor · aplicabilidad por cadena ·
                       edición revalidada · sumandos no corregibles uno a uno · cero efectos al denegar · saldo = alojadas (R-130)      ✔
B02 / H360-B02 ....... CERRADO (técnico): curva fijada al lote · edad del día · interpolación · bordes · NO_REFERENCE declarado ·
                       alerta sin bloqueo · engorde N/A · detalle con evaluación                                                     ✔
GA-REM-021-B ......... CERTIFIED (frontera técnica)                                                                                  ✔
GA-REM-037-B ......... CERTIFIED (frontera técnica)                                                                                  ✔
GA-REM-021 ........... PARTIAL (B03 · B13 abiertos, enmienda C pendiente · B04 ◄── AOD-14 · R-156 ◄── AOD-20)                        ◐
E2E .................. BLOCKED_RUNTIME → certificación de proceso NO                                                                   —
```

## 9. Riesgos restantes y fuera de alcance

`R-167` (doble contabilización de la mortalidad al arribo con un evento de mortalidad del mismo día; KPI de mortalidad, ola C) ·
`R-168` (`sample_size` por galpón descartado por el esquema) · `R-169` (±10 % del formulario sin fuente) — registrados, no resueltos.
La carrera del acumulado de la OC sigue documentada y decidida en `GA-REM-035 §6`. Sin estándar de peso por sexo (`OD-06` no lo distingue).
Sin desviación %. El bloqueo de la aprobación por peso fuera de rango no está en ninguna fuente y no se implementó. `R-161` OPEN ·
`R-164` BLOCKED_RUNTIME · `R-166` OPEN · `BU-D10` no tocado · `R-158` no tocado.

## 10. Siguiente tranche (identificado, NO iniciado)

`GA-REM-021` **`B03`** (alimento por transferencia: lote/batch de alimento, silo o almacén destino, diferencias; `Rec. §8`, P2) con
**`B13`** (sanos/débiles al nacer, `Bases` p.9, P2) como acompañante si la traza los muestra independientes — restos ejecutables de
`GA-REM-021` sin decisión pendiente (paso 6 de `WAVE_B §3`). Exige **enmienda C previa**. Alternativa sin decisión aparente:
`R-152` → `R-153` (Progenitoras, `docs/02 §3.4.1`, paso 7).
