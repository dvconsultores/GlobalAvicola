# MATRIZ MAESTRA DE REMEDIACIÓN

Documento vivo. Se actualiza tras el cierre de cada `GA-REM`.

**Última actualización:** 2026-09-04 (cierre de **Wave 3**) · **Commit base:** `bfccdfb`

---

## 1. Matriz

| GA-REM | Problema | Prior. | Dependencias | Spec | Implementación | Tests | E2E | Estado |
|---|---|---|---|---|---|---|---|---|
| `001` | Constitución sin ratificar | P0 | — | ✅ | ✅ | ✅ 6/6 | n/a | **`CERTIFIED`** |
| `020` | Documentación del cliente sin usar para validar (R-15) | P1 | 001 | ✅ | ✅ | ✅ 4/4 | n/a | **`CERTIFIED`** |
| `014` | Sin entorno de test aislado | P0 | 001 | ✅ | ✅ | ✅ 6/6 + 25 | n/a | **`CERTIFIED`** |
| `004` | Credenciales públicas · rate limit off | P0 | 001 | ✅ | ✅ | ✅ | n/a | **`CERTIFIED`** |
| `009` | Evidencias se pierden en cada despliegue | P0 | 001 | ✅ | ✅ | ✅ | ⬜ | **`CERTIFIED`** |
| `010` | SAP simulado marca `sent_to_sap` | P0 | 001 | ✅ | ✅ | ✅ | ⬜ | **`CERTIFIED`** |
| `011` | 18 desajustes de contrato · 5 pantallas caídas | P0 | 001, 014 | ✅ | ✅ 10/18 | ✅ | ⬜ | **`PARTIALLY CERTIFIED`** |
| `013` | CI nunca ejecutado | P1 | 001, 014 | ✅ | ✅ | ✅ 8/8 | n/a | **`CERTIFIED`** |
| `005` | Mortalidad → 500 · `R-38`…`R-41` | P0 | 001, 014, 023 | ✅ *(enmendada)* | ✅ | ✅ 16/16 | ⬜ | **`CERTIFIED`** |
| `002` | RBAC no aplicado · `R-36` `R-44` `R-48` | P0 | 001, 014, **024** | ✅ | ✅ | ✅ 21+35 | ⬜ | **`CERTIFIED`** |
| `003` | Refresh degrada la identidad · **`R-43`** el refresco nunca funcionó | P0 | 001, 014 | ✅ | ✅ | ✅ | ⬜ | **`CERTIFIED`** |
| `007` | BR-14 eludible · `R-23` | P0 | 001, 002, 014 | ✅ | ✅ | ✅ | ⬜ | **`CERTIFIED`** |
| `012` | Cambio de contraseña inoperante (`P0-13`) | P0 | 001, 002, 003, 014 | ✅ | ✅ | ✅ 11/11 | ⬜ | **`CERTIFIED`** |
| `006` | Correcciones no aplican el valor (`P0-2`) | P0 | 001, 011, 014 | ✅ | ✅ | ✅ 18/18 | ⬜ | **`CERTIFIED`** |
| `008` | Trazabilidad auto-referencial | P0 | 001, 011, 014 | ✅ | ✅ | ✅ 4/4 | ⬜ | **`CERTIFIED`** — `RC-04` resuelto (`RR-04`) |
| `015` | 101 tests nunca ejecutados · addendum **`R-28`** | P1 | 014 | ✅ | ✅ | ✅ 5/5 + 7/7 | n/a | **`CERTIFIED`** |
| `021` | Consumo de agua no capturado (R-13) | P1 | 001 | ✅ | ⬜ | ⬜ | ⬜ | `SPEC_READY` — Wave 2 |
| `022` | KPI incompletos (R-14, R-17) | P1 | 001, 011 | ✅ | ⬜ | ⬜ | ⬜ | `SPEC_READY` — Wave 2 |
| `016` | 0 procesos certificados | P1 | 7 specs | ⚠ draft | ⬜ | ⬜ | ⬜ | `SPEC_DRAFT` |
| `018` | Trazabilidad metodológica perdida | P1 | 001 | ✅ | ⬜ | n/a | n/a | `SPEC_READY` |
| `017` | Sin integración SAP real | P1 | externo | ⚠ prelim | ⬜ | ⬜ | ⬜ | **`BLOCKED_EXTERNAL`** |
| **`023`** | `P0-14` 14 columnas descartadas · `R-26` 7 reglas devuelven 500 · `R-27` `R-30` `R-32` `R-34` | **P0** | 001, 014 | ✅ | ✅ | ✅ 33/33 | ⬜ | **`CERTIFIED`** |
| **`024`** | **`GA-TD-013`** el despliegue no ejecutaba migraciones | **P0** | — | ✅ | ✅ | ✅ 4 escenarios de arranque real | n/a | **`CERTIFIED`** |
| `019` | Deuda P2/P3 + hallazgos de W1, W1.5, W2 y W2.5 | P2 | Fases A–G | ✅ | ⬜ | n/a | n/a | `DEFERRED` |

⚠ = bloqueada por un `REQUIREMENT_CONFLICT` pendiente de decisión. **Tras Wave 1.5 no queda ninguna.**

`RC-01`, `RC-02`, `RC-03` y `RC-05` resueltos por evidencia; `RC-07` acotado a `GA-REM-017`.
Detalle → `REQUIREMENT_CONFLICT_RESOLUTION.md`.

## 2. Marcador de métricas

Se actualiza tras cada cierre. **No se espera al final del programa para volver a medir.**

| Métrica | Baseline | W1 | W1.5 | W2 | W2.5 | W2.75 | **Wave 3** | Objetivo |
|---|---|---|---|---|---|---|---|---|
| Requerimientos vigentes | 56 | 60 (baseline V1.1) | 60 | 60 | 60 | 60 | 60 | 60 |
| Requerimientos E2E completos | 12 / 56 | 12 / 60 | 12 / 60 | **12 / 60** *(sin cambio: E2E no ejecutado)* | 12 / 60 *(sin cambio: E2E no ejecutado)* | 12 / 60 *(sin cambio: E2E no ejecutado)* | **21 / 60** | ≥ 30 |
| **Cobertura funcional E2E** | 21,4 % | 20,0 % | 20,0 % | **20,0 %** *(no se aumenta sin certificación real)* | 20,0 % *(no se aumenta sin certificación real)* | 20,0 % *(no se aumenta sin certificación real)* | **35 %** | ≥ 50 % |
| Procesos certificados | 0 / 15 | 0 / 15 | 0 / 15 | **0 / 15** | 0 / 15 | 0 / 15 | **1 / 15** *(+3 de 9 pasos del orden)* | ≥ 3 |
| Tests backend PASS | 0 (nunca ejecutados) | 0 | 74 / 101 | 211 / 211 | **229 / 229** + **35 / 35** (actualización) | **253 / 253** + 35 + 14 | **265 / 265** | 100 % |
| Tests backend existentes | 76 | 100 | 101 | 211 | **264** (229 + 35) | **302** | 302 | — |
| Tests frontend PASS | 61 / 61 | 61 / 61 | 61 / 61 | **61 / 61** | 61 / 61 | 61 / 61 | 61 / 61 | mantener |
| Tests E2E PASS | 0 | 0 | 0 | **0** *(no ejecutados por encargo)* | 0 *(no ejecutados por encargo)* | 0 *(no ejecutados por encargo)* | **21 / 21** | > 0 |
| **Bloqueadores P0 abiertos** | 12 | 8 | 10 | 0 | **0** | 0 | 0 | 0 |
| Riesgos P1 abiertos | 16 | 13 | 16 | 4 | **3** *(`R-42`, `R-45`, `R-47`)* | 3 *(`R-42`, `R-45`, `R-47`)* | 3 *(`R-42`, `R-45`, `R-47`)* | ≤ 4 |
| Desajustes de contrato FE↔BE | 13 (18 al inventariar) | 8 | 8 | **8** | 8 | 8 | 8 | 0 |
| Pantallas caídas | 5 | 0 | 0 | **0** | 0 | 0 | 0 | 0 |
| Endpoints con PUT de maestros | 4 / 12 | 12 / 12 | 12 / 12 | 12 / 12 | 12 / 12 | 12 / 12 | 12 / 12 | 12 |
| Operaciones OpenAPI | 168 | 176 | 176 | **178** (+ cambio de contraseña) | 178 (+ cambio de contraseña) | 178 (+ cambio de contraseña) | 178 (+ cambio de contraseña) | — |
| Deriva de esquema | 0 | 0 | 0 | 0 | **0** tablas · **0** columnas · **0** enums | 0 tablas · 0 columnas · 0 enums | 0 tablas · 0 columnas · 0 enums | 0 |
| Paridad i18n | 865 = 865 | 865 = 865 | 865 = 865 | **866 = 866** | 866 = 866 | 866 = 866 | 866 = 866 | mantener |
| `TODO` en el backend | 1 | 0 | 0 | **0** | 0 | 0 | 0 | 0 |
| Deuda Spec Development | 16 | 14 | 13 | **9** | 9 | 9 | 9 | ≤ 4 |
| Quality gates ejecutándose | no | sí — 8/8 | sí — 8/8 | **sí — 8/8** | sí — 8/8 | sí — 8/8 | sí — 8/8 | sí |
| **Rutas con autorización declarada** | 0 / 78 | 0 / 78 | 0 / 78 | 177 / 177 | **177 / 177** | **177 / 177** | 177 / 177 | 100 % |
| **Camino de actualización certificado** | no | no | no | no | **sí** | **sí, en arranque real** | sí, en arranque real | sí |
| **Migraciones aplicadas en el despliegue** | **no** | no | no | no | **sí** (`GA-REM-024`) | **sí, certificado en runtime** | sí, certificado en runtime | sí |
| Madurez | NIVEL 3 | NIVEL 3 | NIVEL 3 | NIVEL 3 | **NIVEL 3** *(NIVEL 4 exige E2E certificado)* | NIVEL 3 *(NIVEL 4 exige E2E certificado)* | **NIVEL 4 — OPERATIONAL BETA** | NIVEL 4 |


---

## 3. Nota sobre el aumento de P0 tras Wave 1.5

Los bloqueadores P0 subieron de 8 a 10 y los riesgos P1 de 13 a 16. **Esto no es un
retroceso.** `P0-13`, `P0-14`, `R-23`, `R-26` y `R-28` no se crearon en esta Wave: ya
estaban en el producto. Se hicieron visibles porque, por primera vez, la suite backend se
ejecuta contra una base de datos real y porque se persiguió cada `RC` hasta su evidencia.

Un programa de remediación honesto sube su recuento de defectos cuando mejora su capacidad
de detección. El indicador sano no es «P0 bajando siempre», sino «P0 conocidos, trazados y
con spec de destino»: **10 / 10**.

---

## 4. `GA-REM-029` · Contrato de cierre de lote (2026-09-05)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-73` · `POST /lots/{id}/close` respondía 500 siempre | P1 | **`CERTIFIED`** |
| `R-74` · `BR-05` colgaba del evento `lot_closure`, que no cierra el lote | P1 | **`CERTIFIED`** |
| `R-75` · `end_date` a medianoche local → el cierre se releía con la fecha de ayer | P1 | **`CERTIFIED`** |

El endpoint es el único punto del backend que asigna `status = "closed"`, así que ningún
lote pudo cerrarse nunca hasta ahora.

**No certificó ningún proceso.** El frente se eligió con evidencia y la propia matriz de
alcance ya avisaba: `R-73` tenía fan-out 1. `P-06` sigue `PARTIAL` por `GA-TD-014` y
`GA-REQ-037`. Sirve de recordatorio de que cerrar un defecto real y certificar un proceso
son cosas distintas.

Evidencia: `R-73-LOT-CLOSE-CERTIFICATION.md` · `R73_CLOSE_LOT_CONTRACT_MATRIX.md`.


---

## 5. `GA-REM-030` · `GA-REM-031` · `P-10` certificado (2026-09-05)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-60` · los vínculos de trazabilidad no comprobaban pertenencia ni existencia | P2 | **`CERTIFIED`** |
| `R-78` · el vínculo no se creaba desde la recepción: en el orden natural no se creaba ninguno | **P1** | **`CERTIFIED`** |
| `R-79` · la evidencia de `GA-REM-008 AC01` no podía fallar | P2 | **`CERTIFIED`** |
| `R-80` · el día de negocio es local y `created_at` es UTC | P2 | abierto |

```
P-10 = CERTIFIED        CERTIFIED 6 / 15        PARTIAL 9 / 15
```

La cadena de causas es la lección del tramo: una afirmación que no podía fallar dejó pasar un
defecto de dominio, y ese defecto mantuvo un proceso en `PARTIAL` sin que ninguna matriz lo
mostrara. De ahí la enmienda F de `GA-REM-016`: la validez de la evidencia alcanza a toda
prueba invocada como tal, la escribiera quien la escribiera.


---

## 6. `GA-REM-032` · `P-09` certificado (2026-09-06)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-81` · seis de once módulos sin un solo registro de auditoría | **P1** | **`CERTIFIED`** |
| `R-82` · la vista aparentaba filtrar y no filtraba | **P1** | **`CERTIFIED`** |
| `R-84` · el filtro de fecha devolvía 500 | **P1** | **`CERTIFIED`** |
| `R-83` · una acción sin empresa no puede auditarse | P2 | abierto |

```
P-09 = CERTIFIED        CERTIFIED 7 / 15        PARTIAL 8 / 15
```

Dos correcciones de medición que conviene conservar: las acciones emitidas eran **12**, no 6;
y **21 valores de enum no son 21 requisitos** — dos quedan fuera por no tener superficie que
auditar, y decirlo es más honesto que completarlas por estética.


---

## 7. `GA-REM-022` enmienda A · `P-15` certificado (2026-09-06)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-14` · la tasa de eclosión devolvía texto en un campo numérico | **P1** | **`CERTIFIED`** |
| `R-85` · tres cocientes de incubadora con denominadores distintos, fundidos en uno | P2 | **`CERTIFIED`** |
| `R-86` · «Fertilidad» normativa y sin productor | P2 | **`CERTIFIED`** |
| ~~`R-87`~~ · ~~reporte de estados ausente~~ | — | **RETIRADO** |
| ~~`R-88`~~ · ~~exportación ausente~~ | — | **RETIRADO** |

```
P-15 = CERTIFIED        CERTIFIED 8 / 15        PARTIAL 7 / 15
```

Dos lecciones del tramo. La primera: **21 valores de enum no son 21 requisitos**, y de los
cuatro KPI «huérfanos» solo dos los exigía el cliente. La segunda es propia y menos cómoda:
registré dos hallazgos —`R-87` y `R-88`— buscando **solo en el backend**, y los dos estaban
implementados en el cliente. Retirados y anotados, no borrados.


---

## 8. `GA-REM-033` · `P-12` certificado (2026-09-06)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-90` · siete maestros normativos sin capacidad de gestión | **P1** | **`CERTIFIED`** |
| `R-91` · esos mismos siete no admitían edición | P2 | **`CERTIFIED`** |
| `R-89` · el listado descartaba el total que calculaba | P2 | **`CERTIFIED`** |

```
P-12 = CERTIFIED        CERTIFIED 9 / 15        PARTIAL 6 / 15
```

Dos cosas que conviene conservar. La primera: **la auditoría bidireccional funcionó**. Tras el
error de `R-87`/`R-88` —dos huecos falsos por mirar un solo lado— aquí se comprobó cada uno en
backend y frontend antes de anotarlo, y la hipótesis se confirmó con dos matices que cambiaron
el trabajo: no eran siete pantallas sino siete entradas en una lista, y faltaba también la
capacidad de edición.

La segunda: **una spec puede necesitar enmienda al implementarla**. `AC01` pedía cambiar la
forma del cuerpo del listado; contar los consumidores reveló 43 puntos de llamada, y un
defecto P2 de contador no justifica moverlos. Se enmendó el criterio antes de escribir el
código, no después.


---

## 9. `GA-REM-034` · `P-13` certificado (2026-09-06)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-92` · no existía superficie para administrar roles | **P1** | **`CERTIFIED`** |
| `R-93` · `RoleUpdate` no incluía permisos | P2 | **`CERTIFIED`** |
| `R-94` · no había catálogo de permisos | P2 | **`CERTIFIED`** |
| `OD-05` · ¿quién puede conceder qué permiso? | — | **`OWNER_DECISION_REQUIRED`** |
| `OD-07` · ¿por qué canal notifica Global Avícola? | — | **`RESOLVED`** — interno / in-app |
| `OD-08` · ¿quién recibe los avisos operativos, y qué es «lote próximo a cierre»? | — | **`OWNER_DECISION_REQUIRED`** |

```
P-13 = CERTIFIED        CERTIFIED 10 / 15        PARTIAL 5 / 15
```

Se separó **enforcement** de **administración**: `GA-REM-002` certificó lo primero y no se
tocó; lo que faltaba era lo segundo. Confundirlos habría llevado a reabrir una spec cerrada.

Y `OD-05` quedó abierta sin bloquear: nada impide que quien tiene `users:create` se conceda
`module="*"`. No hay regla normativa y **no se inventó una política de seguridad**.

---

# ESTADO DEL PROGRAMA · 2026-09-06

```
CERTIFIED 10 / 15        PARTIAL 5 / 15
```

Los cinco restantes **no son trabajo técnico pendiente**:

| Categoría | Procesos | Qué falta |
|---|---|---|
| decisión del propietario | `P-01` `P-03` `P-06` | `OD-04` |
| dependencia externa | `P-08` | contrato SAP |
| decisión + desarrollo | `P-14` | elegir canal de notificación |

**El cierre de procesos por corrección de defectos está agotado.**


---

## 10. `OD-04` resuelta · `GA-REM-035` · `P-01` certificado (2026-09-06)

| | Sev. | Estado |
|---|:--:|---|
| `OD-04` · ¿entregas parciales contra una misma OC? | — | **`RESOLVED`** — sí |
| `GA-TD-014` · la OC al campo tipado, con límite acumulado | **P1** | **`CERTIFIED`** |
| `R-95` · `SapReferenceCreate` no declaraba `quantity` | **P1** | **`CERTIFIED`** |

```
P-01 = CERTIFIED        CERTIFIED 11 / 15        PARTIAL 4 / 15
P-03 = PARTIAL (GA-REQ-037)     P-06 = PARTIAL (R-76)      ← estado en ese momento; §11 y §12 los cierran
```

Tres cosas que conviene conservar de este tramo.

**Activar el campo no habría bastado.** `validate_oc_limit` comparaba solo la recepción en
curso, de modo que tres entregas de 400 contra una orden de 1000 pasaban las tres. El límite
acumulado —que es lo que la decisión del propietario protege— nunca se había comprobado.

**Y ni siquiera eso habría bastado.** `SapReferenceCreate` no declaraba `quantity`: toda orden
importada quedaba sin cantidad ordenada y `BR-18` era inaplicable estuviera o no poblado el
campo. Es el patrón de `R-47` por tercera vez en el programa — el cliente envía, el esquema
descarta, la respuesta es `2xx`.

**Los tres procesos divergieron.** Compartían bloqueante y se reevaluaron uno a uno: `§4.4` no
exige alertas, `§4.5` sí y `§4.8` no. Certificar por alcance habría dado tres certificaciones
falsas.


---

## 11. `GA-REM-036` · `R-76` y `P-06` certificados (2026-09-06)

| Hallazgo | Sev. | Estado |
|---|:--:|---|
| `R-76` · `docs/12 R7` sin implementar | **P1** | **`CERTIFIED`** |

```
P-06 = CERTIFIED        CERTIFIED 12 / 15        PARTIAL 3 / 15
```

Dos cosas que conviene conservar.

**Acotar antes de programar.** `R7` dice «registros sin aprobar», y ninguna de las dos palabras
se resolvió por atajo: «registro» es el `OperationalEvent` porque `docs/12 §4` trata de esa
entidad, y «sin aprobar» son siete de los trece estados. `rejected` bloquea —no está aprobado
y no es terminal—; `sap_error` no —solo se alcanza tras aprobar—. `AC04` comprueba los seis que
**no** bloquean, porque una regla que bloquea de más es tan defectuosa como una que no bloquea.

**Cambiar una precondición rompe fixtures ajenas, y eso se repara sin tocar aserciones.** Tres
suites certificadas dejaron de poder cerrar sus lotes. Se les añadió la aprobación; lo que
miden no cambió. El caso más delicado distinguía dos contadores dejando un evento sin aprobar:
ahora lo distingue con uno **anulado**, que `R7` no gobierna.


---

## 12. `GA-REM-037` · `OD-06`, `GA-REQ-037` y `P-03` (2026-09-06)

| | Sev. | Estado |
|---|:--:|---|
| `OD-06` · ¿de dónde sale la curva estándar de peso? | — | **`RESOLVED`** — la administra Global Avícola |
| `GA-REQ-037` · alerta de peso fuera de curva | **P1** | **`CERTIFIED`** |
| `R-96` · no hay pantalla para administrar curvas | P2 | `OPEN` — sin spec de frontend |

```
P-03 = CERTIFIED        CERTIFIED 13 / 15        PARTIAL 2 / 15
```

Cuatro cosas que conviene conservar de este tramo.

**No era un defecto, era un dato que no existía.** `spec.md §4.5` exige comparar el peso contra
«la curva estándar», y en el repositorio entero no había curva: ni tabla, ni versión, ni forma
de que un lote apuntara a una. Ninguna de las seis fuentes de la jerarquía la definía. Por eso
se elevó como `OD-06` en vez de programarse: cualquier umbral que se hubiera escrito habría
sido inventado, y un umbral inventado da veredictos que **parecen** correctos.

**Seis de las once capacidades ya existían.** `GeneticLine` era un maestro con pantalla desde
`GA-REM-033`, de modo que el «debe ser posible añadir líneas nuevas» de `OD-06` estaba
satisfecho antes de empezar; introducir el enum fijo que el enunciado parecía sugerir habría
sido una **regresión**. Se contaron una a una antes de escribir código
(`P03_GENETIC_CURVE_MODEL_MATRIX.md`).

**La guarda `R-32` disparó, y tenía razón.** El campo de versión de la curva se llamaba
`version`, que este proyecto reserva para lo que fija el servidor. Aquí lo escribe el
administrador y es lo que publica el proveedor: dos conceptos opuestos con la misma palabra. Se
renombró a `version_label` en vez de eximir la guarda, que es lo que habría sido cómodo. Otras
dos guardas —clasificación de datos y cobertura de la purga— detuvieron que las tablas nuevas
quedaran fuera del inventario y que el `CASCADE` las vaciara a espaldas de él.

**La ausencia de referencia se declara, no se adivina.** Sin curva cargada, fuera del rango de
edades de la tabla, o sin línea genética, el motor responde `NO_REFERENCE` y no se emite
alerta. Es la traducción literal de «sin tolerancia global»: no hay un ±10 % de reserva para
cuando falta el dato.


---

## 13. `R-96` · `R-97` · la capacidad, no el endpoint (2026-09-06)

| | Sev. | Estado |
|---|:--:|---|
| `R-96` · la tabla de curva no podía cargarse desde el producto | **P1** | **`CERTIFIED`** |
| `R-97` · la evaluación solo era observable cuando alertaba | **P1** | **`CERTIFIED`** |
| `R-98` · ninguna pantalla oculta escritura por permiso | P2 | `OPEN` — transversal, `P-13` |

```
P-03 = CERTIFIED        CERTIFIED 13 / 15        PARTIAL 2 / 15
```

Tres cosas que conviene conservar de este tramo.

**Una spec incompleta no es un requisito ausente.** Se concluyó que, al no tener `GA-REM-037`
criterios de frontend, la pantalla quedaba fuera de alcance. El razonamiento iba al revés:
`OD-06` exige que la tabla pueda cargarse **dentro de Global Avícola**, y la ausencia de
criterios demostraba que la spec estaba incompleta, no que el requisito no existiera. Se
enmendó `GA-REM-037` —autoridad natural de `OD-06`— en lugar de abrir una spec nueva que
habría partido en dos la misma decisión del propietario.

**Derivar el contrato del `openapi()` y no de la memoria encontró un hueco.** `R-97` no se
descubrió leyendo código sino preguntando qué puede saber una pantalla: el motor tenía un solo
consumidor y solo hablaba al salirse del rango, de modo que la ausencia de alerta significaba
«bien» y «no sé» a la vez. Deducirlo en React habría creado el segundo motor que todo este
tramo evita.

**Una reversión con `git checkout` destruyó trabajo sin confirmar y la guarda de residuo lo dio
por limpio**, porque el código sospechoso ya no existía. Lo delató la suite completa con diez
fallos. Las reversiones se hacen desde una salvaguarda previa, no desde el último commit.
