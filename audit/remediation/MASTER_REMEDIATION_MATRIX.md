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


---

## 14. `OD-07` · `GA-REM-038` · el canal de `P-14` (2026-09-07)

| | Sev. | Estado |
|---|:--:|---|
| `OD-07` · ¿por qué canal notifica Global Avícola? | — | **`RESOLVED`** — interno |
| `GA-REM-038` · bandeja interna | **P1** | **`PARTIALLY CERTIFIED`** — 2 de 6 tipos |
| `OD-08` · ¿quién recibe los avisos operativos? | — | **`OWNER_DECISION_REQUIRED`** |

```
P-14 = PARTIAL          CERTIFIED 13 / 15        PARTIAL 2 / 15
```

Tres cosas que conviene conservar de este tramo.

**Se construyó el canal y aun así no se certificó el proceso.** `docs/02 §3.14` enumera seis
tipos; solo dos dicen a quién avisar. `GA-REM-016 AC05` no admite certificar por muestra, y era
tentador: la campana funciona de extremo a extremo. Es el mismo salto que obligó a revertir
`P-03` el día anterior, evitado esta vez antes de darlo.

**Los destinatarios se leyeron, no se dedujeron.** «Notificar al operador» y «Notificar al rol
Analista SAP» están escritos con esas palabras en `docs/02 §3.14` y `docs/10 §6.2`. Los otros
cuatro no están escritos en ninguna parte, y `Lot` no tiene responsable asignado —se
enumeraron sus campos—. Se descartaron tres candidatos por escrito antes de abrir `OD-08`.

**Una guarda obligó a modelar mejor en vez de a ceder.** `test_ac08b` limita a seis las rutas
públicas y ya estaban las seis. En lugar de subir el límite, se separó lo que la lista
mezclaba: rutas **sin sesión** frente a rutas que exigen sesión y autorizan por
**titularidad**. `/me` figuraba como pública cuando exige token. Las públicas de `/api` bajaron
de seis a dos y el límite bajó con ellas.


---

## 15. `OD-08` · destinatarios de `P-14` (2026-09-07)

| | Sev. | Estado |
|---|:--:|---|
| `OD-08` · ¿quién recibe los avisos? | — | **`RESOLVED`** |
| `OD-08` · ¿qué es «lote próximo a cierre»? | — | **`OWNER_DECISION_REQUIRED`** |
| `GA-REM-038` enmienda A | **P1** | **`PARTIALLY CERTIFIED`** — 5 de 6 tipos |

```
P-14 = PARTIAL          CERTIFIED 13 / 15        PARTIAL 2 / 15
```

Cuatro cosas que conviene conservar.

**Los nombres literales importaban.** El informe anterior agrupó dos eventos como «temporales
sin definir». Al transcribirlos de `docs/02 §3.14` en vez de citarlos de memoria, uno llevaba su
umbral en el propio nombre —«> 24h»— y el otro no. Uno pasó a accionable; el otro sigue
bloqueado. Leer la fuente literal cambió un veredicto.

**`Super Administrador` no entra por serlo.** Su nombre de rol contiene «administrador» y se
siembra con `company_id = None`. Sin la condición de pertenencia habría recibido el detalle
operativo de todas las empresas: una fuga que parecía una función.

**Una guarda señaló que el código estaba en el archivo equivocado.** `R-26` prohíbe
`except Exception` en `main.py`; la tarea de fondo necesita una. En vez de eximir la guarda se
movió la lógica a `notifications/sla.py`, que es donde iba.

**Una sola prueba no habría bastado para el destinatario explícito.** Quitarlo de la unión
rompió el aviso de SAP y **no** el del rechazo: allí el operador entra también como originador.
Quien distingue las dos vías es el evento donde el `Analista SAP` no es originador de nada.


---

## 16. `OD-08` completa · `GA-REM-039` · `P-14` certificado (2026-09-07)

| | Sev. | Estado |
|---|:--:|---|
| `OD-08` · destinatarios · área · próximo a cierre | — | **`RESOLVED`** |
| `GA-REM-039` · áreas funcionales | **P1** | **`CERTIFIED`** |
| `GA-REM-038` · notificaciones internas | **P1** | **`CERTIFIED`** — 6 de 6 tipos |

```
P-14 = CERTIFIED        CERTIFIED 14 / 15        PARTIAL 1 / 15
```

Cinco cosas que conviene conservar.

**Los dos bloqueos no eran la misma clase de cosa.** «Lote próximo a cierre» era una decisión
—qué significa «próximo»—; el gerente del área era un modelo que no existía. Distinguirlos
evitó pedir al propietario que decidiera sobre el esquema.

**Una fuente única para el gerente.** Se resolvió con `User.area_id` **más** el rol, sin
`Area.manager_user_id`: tenerlo en los dos sitios habría creado dos verdades sin regla de
autoridad. Y hacen falta las dos condiciones — un usuario con rol de gerencia y sin área no es
gerente de nada, con prueba dedicada.

**Ventana en vez de igualdad.** `== 3` habría exigido que el evaluador corriera exactamente ese
día; con el sistema apagado el aviso no saldría nunca.

**`T-025-04` obligó a clasificar mejor, no a aflojar.** El `TRUNCATE ... CASCADE` del reset vacía
toda tabla que referencie a la truncada, sin mirar el `ON DELETE`: borrar las áreas se habría
llevado a los usuarios. Un organigrama es estructura, no historia ficticia.

**`tsc` no es un build.** Dio limpio sobre un JSX con elementos adyacentes sin envolver y la
aplicación no arrancaba: 46 pruebas de navegador en rojo. Lo delató `vite build`, que pasa a
formar parte de la verificación.

---

## `OD-09` · plano de control frente a unidad de negocio (2026-09-07)

| Decisión del dosier | Pregunta | Respuesta | Parte |
|---|---|:--:|---|
| `BU-D11` | ¿Contraloría y administración ven las cuatro líneas aunque solo tengan dos? | **C** | `OD-09.a` |
| `BU-D12` | ¿Administrar usuarios y roles pertenece a alguna línea? | **B** | `OD-09.b` |
| `BU-D09` | ¿Puede entrar alguien sin ninguna línea asignada? | **B** | `OD-09.c` |

```
CONTROL VISIBILITY  y  OPERATIONAL ACCESS  SON CAPACIDADES DISTINTAS
```

Formalizadas en `specs/remediation/OD-09-CONTROL-PLANE-VS-BUSINESS-UNIT.md`. Un solo `OD` porque
son una sola resolución —el mismo patrón de `OD-08`—, y porque cambiar una obligaría a revisar
las otras dos.

**`OD-08` y `P-14` se preservan.** Los avisos de administración y contraloría **no** se filtran
por concesión de unidad: recibir un aviso es visibilidad de control, no autoridad operativa.

```
BLOQUEANTES DE LA SPEC GA-REM-040     5  →  2        quedan BU-D01 y BU-D02
DECISIONES DEL DOSIER RESUELTAS       3 / 12
CERTIFICACIÓN FUNCIONAL               14 / 15        sin cambios
CÓDIGO MODIFICADO                     ninguno
```

`OD-05` sigue abierta y no se resuelve aquí: de ella depende quién puede conceder qué.

---

## `OD-10` · contrato de traspaso y clasificación pendiente (2026-09-07)

| Decisión del dosier | Pregunta | Respuesta | Parte |
|---|---|:--:|---|
| `BU-D01` | ¿Qué sigue viendo cada línea cuando el producto cambia de manos? | **B** | `OD-10.a` |
| `BU-D01` bis | ¿El despacho declara su destino al crearse? | **A** | `OD-10.b` |
| `BU-D02` | ¿Quién ve un registro cuya línea no se puede determinar? | **C** | `OD-10.c` |

```
ENTRE UNIDADES SOLO PASA EL CONTRATO
Y LO QUE NO SE PUEDE CLASIFICAR QUEDA NOMBRADO
```

`OD` aparte y no enmienda de `OD-09` porque su declaración es otra: `OD-09` trata de **quién**
atraviesa el eje —control frente a operación—, y `OD-10` de **qué pasa** entre unidades en el
plano operativo. Las dos preguntas van juntas porque `BU-D02` es anterior a `BU-D01`: un registro
que no se sabe de quién es no puede entrar en ningún contrato.

`P-10` se conserva: la **cadena** generacional es categoría `B` y se ve entera; el **interior** de
cada eslabón queda en `C`.

```
BLOQUEANTES DE LA SPEC GA-REM-040     2  →  0
DECISIONES DEL DOSIER RESUELTAS       5 / 12    (las otras 7 no bloquean)
CERTIFICACIÓN FUNCIONAL               14 / 15   sin cambios
CÓDIGO MODIFICADO                     ninguno
```

---

## `GA-REM-040` · especificada, no construida (2026-09-07)

```
ESTADO                   SPEC_READY
CÓDIGO ESCRITO           ninguno
MIGRACIONES              ninguna
PRUEBAS EJECUTABLES      ninguna
RUTAS MODIFICADAS        0 de 198
```

Primera spec del programa que introduce una **dimensión nueva** en lugar de corregir un defecto.
Gobierna catálogo de unidades, habilitación por empresa, concesión por usuario, resolutor central,
clasificación de rutas, aislamiento por fila, agregados, los siete contratos de traspaso,
clasificación pendiente, sesión, interfaz, notificaciones, tareas de fondo y auditoría.

```
CRITERIOS DE ACEPTACIÓN   10 grupos · A…J
TAREAS                    T-040-01 … T-040-30
FASES                     11
MUTACIONES DE SENSIBILIDAD 9
```

Dos puntos del orden no son negociables: clasificar las rutas antes de filtrar filas, y **los
agregados no van al final** — una fuga por diferencia no deja rastro y nadie la reporta.

```
CERTIFICACIÓN FUNCIONAL                14 / 15   sin cambios · ningún proceso se reabre
CERTIFICACIÓN DE ACCESO POR UNIDAD      0 / 15   dimensión nueva
                                                 PROCESS_BUSINESS_UNIT_ACCESS_MATRIX.md
```

`BU-D05` queda como gate aparte —`FIRST_REAL_CUSTOMER_READINESS`— y no bloquea la construcción.
`R-98` recibirá infraestructura de aquí, y **eso no lo cierra**: la dependencia se registra y nada
más.

---

## `GA-REM-040` fase 1 · fundamento construido (2026-09-07)

```
FASE 1 DE 11             catálogo · habilitación por empresa · concesión por usuario · resolutor
TABLAS NUEVAS            3        business_units · company_business_units · user_business_units
MIGRACIÓN                p6q7r8s9t0u1    cabeza única
PRUEBAS                  23 / 23
SENSIBILIDAD             5 / 5 mutaciones detectadas
REGRESIÓN                516 passed · 49 skipped     (eran 493 · 49)
FRONTEND                 0 archivos
RUTAS MODIFICADAS        0 de 198
```

`T-040-01` concluyó que **no existe** modelo de habilitación ni de alcance de usuario
reutilizable: decisión `CREATE`, documentada en
`audit/remediation/GA_REM_040_PHASE_1_EVIDENCE.md`.

Los 22 maestros quedan clasificados —`MASTER_DATA_BUSINESS_UNIT_SCOPE_MATRIX.md`, 22/22— y el
resultado útil es que **ninguno necesita columna de unidad**: los cuatro que son de una unidad la
derivan de su naturaleza, `breeds` ya lleva `bird_type`, y al resto asignarle una falsearía el
dato.

```
CERTIFICACIÓN FUNCIONAL                14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD      0 / 15   sin cambios
```

Nada de lo construido impide todavía que un usuario vea un lote de otra unidad: el filtro por
fila es la fase 3. Otorgar un `PASS` por tener tablas y un resolutor sería la evidencia que
`GA-REM-016 AC13` prohíbe.

---

## `GA-REM-040` fase 1.1 · la concesión se acota a la empresa (2026-09-07)

La fase 1 cerró anotando una duda; el propietario pidió comprobarla. **El riesgo era real y se
comprobó ejecutando**: al mover un usuario de la empresa A a la B, su concesión de A se
reactivaba en B porque la fila no decía de qué empresa venía.

```
ANTES   user_business_units  →  business_units          `breeder` de A y de B, indistinguibles
AHORA   user_business_units  →  company_business_units  la fila dice quién la otorgó
```

Formalizado como **`OD-09.d`**, enmienda de `OD-09` y no `OD` nuevo: no es una decisión nueva,
es lo que `OD-09.b` ya implicaba —si administrar el acceso es un acto del plano de control de una
empresa, lo concedido pertenece a esa empresa—.

```
AC NUEVOS            AC-B07 … AC-B11        TAREA   T-040-31
PRUEBAS              31 / 31                (eran 23)
SENSIBILIDAD         4 / 4 mutaciones detectadas
MIGRACIÓN            q7r8s9t0u1v2 · cabeza única · se detiene antes que adivinar
REGRESIÓN            524 passed · 49 skipped
FRONTEND             0 archivos             RUTAS   0 de 198
```

`BU-D10` sigue `PENDIENTE DE RATIFICACIÓN` y esta corrección no la toca. Queda declarado sin
decidir si volver a la empresa anterior reactiva la concesión.

```
CERTIFICACIÓN FUNCIONAL                14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD      0 / 15   sin cambios
```

---

## `GA-REM-040` fase 2 · seguridad central (2026-09-07)

```
EMPRESA EFECTIVA         centralizada en `app/tenancy.py` · `OD-11`
GUARDA DE UNIDAD         `exigir_acceso_a_unidad` · invocable sin `Request`
RUTAS CLASIFICADAS       198 / 198 · 0 sin clasificar · guarda de arranque
CICLO DE VIDA            `revoked_at` con unicidad parcial · `OD-09.e`
AUDITORÍA                `CONTEXT_SWITCHED` en `P-09`
PRUEBAS                  25 nuevas · 549 passed / 49 skipped
SENSIBILIDAD             10 / 10 mutaciones detectadas
FRONTEND                 0 archivos          FILAS FILTRADAS   0
```

La regla de empresa efectiva **ya era correcta** desde `R-48`; lo que faltaba era poder
invocarla fuera de una petición, revalidarla en cada una —una empresa puede desactivarse con la
sesión viva— y dejar constancia de que alguien se situó en otra.

`AC-B12` obligó a un hallazgo que no estaba previsto: **volver a una empresa es indistinguible
de no haberse ido** si no se registra la salida. De ahí el ciclo de vida de la concesión.

```
CLASIFICAR UNA RUTA   ≠   PROTEGER SUS FILAS
```

`/lots` figura como `MULTI_UNIDAD` y sigue devolviendo lotes de todas las unidades.

```
CERTIFICACIÓN FUNCIONAL             14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD   0 / 15   sin cambios
```

---

## `GA-REM-040` fase 3 · aislamiento por fila (2026-09-07)

```
PERTENECER A LA EMPRESA ES NECESARIO PERO NO SUFICIENTE
```

La fuga que la fase 2 dejó demostrada queda cerrada: `/lots` ya no devuelve lotes de cadenas
que el usuario no tiene concedidas — ni en el listado, ni en el detalle, ni en la mutación, ni
en el total.

```
ENTIDADES ACOTADAS       3 / 16    lots · lot_phases · opening_balances
APLAZADAS A LA FASE 5    3         son contratos de traspaso, no filas de un dueño
PENDIENTES DE LA FASE 6  8         dependen de que lo no clasificable tenga estado
PRUEBAS                  21 / 21   con CONTROL y TRATAMIENTO en el mismo escenario
SENSIBILIDAD             10 / 10
REGRESIÓN                570 passed · 49 skipped
MIGRACIÓN                ninguna · FRONTEND 0
```

**Tres hallazgos que no eran de unidades de negocio.** `/lots/{id}/phases` y
`/lots/{id}/opening-balance` consultaban por `lot_id` sin comprobar pertenencia alguna —ni de
empresa—, y `add_phase` creaba la fila sin comprobar de quién era el lote. `IDOR` de inquilino y
escritura contra lo ajeno, anteriores a esta capacidad. Cerrados por el mismo camino acotado.

**Una mutación encontró un hueco de cobertura, no de implementación**: el atajo por nombre de
rol no rompía ninguna prueba porque ninguna lo sujetaba por ese lado. Se añadió la que faltaba.

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios · ningún PASS por transitividad
```

---

## `R-111` · trazabilidad de un `IDOR` anterior (2026-09-07)

Los tres caminos que la fase 3 encontró abiertos quedan registrados formalmente. **No son un
hueco de unidades de negocio**: son pertenencia de inquilino, anterior a `GA-REM-040`, y su
autoridad ya existía.

```
UN HALLAZGO RAÍZ · TRES SUPERFICIES     GET phases · GET opening-balance · POST phases
SPEC                                    GA-REM-002 · enmienda A · AC12
GA-REM NUEVO                            NO — la autoridad ya existía
ESTADO                                  CORREGIDO en la fase 3 · con pruebas
```

```
DETALLE PROTEGIDO   ≠   SUB-RECURSO PROTEGIDO
```

La ruta exigía sesión y permiso; lo que faltaba era comprobar de quién era el **padre** en el
camino anidado. Es la lección que `GA-REM-002` ya había escrito para las claves foráneas, un
nivel más abajo.

No se registra como regresión de la fase 3: la fase 3 lo **encontró**. Y los cuatro fallos de
fixture que aparecieron en el camino no se registran como defectos de producto, porque no lo
eran.

---

## `GA-REM-040` fase 4 · agregados e indicadores (2026-09-07)

```
LO QUE NO SE PUEDE VER COMO FILAS NO PUEDE REAPARECER COMO TOTAL
```

**La forma del riesgo no era la que se suponía.** `/kpis/mortality` no sumaba la empresa: exige
`lot_id`. Casi todos los indicadores de `P-15` son por lote, y lo que hacían era devolver el
detalle de cualquier lote cuyo identificador alguien conociera — población inicial, muertes y
tasa, más de lo que el listado ocultaba.

La fuga de empresa de verdad estaba en el panel, y era la de manual: `lots_by_type` **nombraba**
las cadenas ajenas con su recuento.

```
SUPERFICIES ACOTADAS     16 / 16
PRUEBAS                  15 / 15   con valores discriminantes, 10 frente a 7
SENSIBILIDAD             8 / 8     dos encontraron huecos de cobertura, no de implementación
REGRESIÓN                585 passed · 49 skipped
FÓRMULAS P-15            intactas · comprobado con un registro sin aprobar que no cuenta
MIGRACIÓN                ninguna · FRONTEND 0
```

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

Acotar los quince indicadores **no certifica `P-15`**: certificar por endpoint es lo que
`GA-REM-016 AC05` prohíbe.

---

## `GA-REM-040` fase 5 · contratos de traspaso (2026-09-07)

```
VISIBILIDAD DE TRASPASO ≠ ACCESO A LA UNIDAD AJENA
```

**De trece comprobaciones del contrato, diez ya pasaban.** Las proyecciones de lectura ya eran
acotadas y las fases 1 a 4 ya impedían pivotar del identificador ajeno a su detalle. Faltaban
tres cosas, todas de escritura: el destino era opcional, el origen no se acotaba, y el flujo no
se validaba.

`T-040-14` se responde solo: **la columna de destino ya existía**. Decisión `REUSE`, sin
migración — lo que `OD-10.b §3.2` había anticipado.

```
FLUJOS IMPLEMENTADOS     4 / 7    aplazados 2 (fase 6) · excepción declarada 1 (BU-D04)
CAMPOS SIN CLASIFICAR    0
PRUEBAS                  13 / 13   SENSIBILIDAD  6 / 6 aplicables · 3 N/A con razón
REGRESIÓN                598 passed · 49 skipped · P-10 verde
```

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

Certificar `P-10` por tener su cadena protegida sería tan inválido como certificar por endpoint.

---

## `GA-REM-040` fase 6 · clasificación pendiente (2026-09-07)

```
SIN CLASIFICAR ≠ DE TODA LA EMPRESA ≠ UNA QUINTA CADENA ≠ BORRADO
```

**Un campo nulable no es un pendiente**: primero se deriva. Sin esa distinción la bandeja se
habría llenado de registros que no necesitan a nadie.

Un solo mecanismo para siete entidades: `operational_events` es la única con `lot_id` y las seis
dependientes heredan **por construcción** —no tienen ruta propia—, que es más fuerte que una
comprobación que alguien pueda olvidar (`R-111`).

```
ENTIDADES ACOTADAS       13 / 16   eran 3
FLUJOS IMPLEMENTADOS      6 / 7    4 y 6 desbloqueados · 5 sigue siendo excepción (BU-D04)
PRUEBAS                  25 / 25   SENSIBILIDAD  9 / 9
REGRESIÓN                623 passed · 49 skipped
MIGRACIÓN                s9t0u1v2w3x4 · FRONTEND 0
```

Dos mutaciones sobrevivieron por huecos **de prueba**, no de implementación. Una de ellas pasaba
en vacío por leer `items` donde el endpoint devuelve `events` — el mismo error de forma que la
fase 4 ya había cazado en el panel, cometido otra vez.

Las semillas pasan a **configurar la empresa**: es lo que hará un cliente real en su alta, y la
alternativa sería el `fail open` que esto existe para impedir.

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

Tener bandeja y acción de clasificar no certifica ningún proceso.

---

## `GA-REM-040` fase 6 · cierre (2026-09-07)

```
PRIMERA CLASIFICACIÓN ≠ RECLASIFICACIÓN
```

`OD-10.d` formaliza que corregir una atribución es **alto control**: permiso propio, motivo
obligatorio, y **denegada en el sitio si el registro ya produjo efectos** —aprobado, consolidado,
enviado a SAP o participante en un traspaso—. Cambiar la cadena de algo ya ocurrido reinterpreta
hechos pasados.

Y `GA-REM-040` enmienda C formaliza la semilla: una empresa de certificación válida configura sus
cadenas explícitamente.

```
CORRECCIÓN DE INFORME    19 → 20 pruebas afectadas (18 de notificaciones, no 19)
PRUEBAS                  35 / 35     SENSIBILIDAD  8 / 8
REGRESIÓN                633 passed · 49 skipped
FRONTEND                 0 · MIGRACIÓN ninguna
```

De las ocho mutaciones, tres no salieron a la primera: una la corrí contra la suite equivocada,
otra estaba rota —lanzaba `NameError` y mi propio `except` lo tragaba— y solo la tercera era un
hueco de cobertura real. Registrado, porque la diferencia importa.

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
```

---

## `OD-12` · `BU-D04` resuelta · la fase 5 se cierra (2026-09-07)

```
LA TRANSVERSALIDAD SAP = CAPACIDAD OPERATIVA EXPLÍCITA, ACOTADA AL CONTRATO
```

**No hizo falta cambiar comportamiento.** Las quince pruebas del contrato pasaron sin tocar una
línea: el permiso ya era explícito, la empresa ya se filtraba y las superficies normales ya
seguían acotadas para el mismo actor. El hueco era de gobernanza — la transversalidad existía
**por ausencia de filtro**.

Se añadió una declaración con dientes: una prueba comprueba que la lista de superficies
transversales coincide con las rutas reales, de modo que una ruta SAP nueva no hereda la
excepción en silencio.

**Y una mutación encontró un defecto real** (`R-112`): `/sap/consolidated` no declaraba
`response_model`, así que la proyección existía en el fichero y no se aplicaba. Hoy no filtraba
nada por coincidencia —el modelo no tiene relaciones—, no por contrato. Corregida esa ruta; las
otras ocho quedan registradas.

```
FLUJOS         7 / 7 clasificados · 7 / 7 implementados · 0 excepciones sin resolver
FASE 5         COMPLETE
PRUEBAS        15 / 15     SENSIBILIDAD  6 / 6
REGRESIÓN      648 passed · 49 skipped
PERMISO NUEVO  ninguno · REUSE de `sap:read` y `sap:send_sap`
```

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
P-08                                 BLOCKED_EXTERNAL   sin cambios
```

---

## `GA-REM-040` fase 7 · la administración del acceso (2026-09-08)

```
ADMINISTRAR EL ACCESO  ≠  ACCEDER AL DATO        probado como par, no como afirmación
```

Seis rutas de plano de control, un módulo `RBAC` propio, **cero migraciones**: el esquema de la
fase 1 ya sostenía las dos relaciones y lo que faltaba era la forma de administrarlas.

Tres superficies se cerraron por diseño en lugar de vigilarse: la empresa no se recibe —se
resuelve con `OD-11`—, la unidad se direcciona por código y el cuerpo de la concesión no acepta
empresa. `AC-B10` se cumple porque la fila inválida no se puede **nombrar**.

```
PRUEBAS        39 / 39      SENSIBILIDAD  10 / 10 detectadas
SUITES DE FASE 238          REGRESIÓN     687 passed · 49 skipped
MIGRACIÓN      ninguna · head sigue `s9t0u1v2w3x4`
FRONTEND       0 ficheros
```

Y una pregunta que la fase devolvió al propietario en vez de contestar: **ningún rol sembrado
administra esto** (`R-113`). Lo detectaron los propios guardianes del proyecto, y su diagnóstico
era correcto. Dárselo a «Supervisor Avícola» habría convertido a todo supervisor en alguien
capaz de concederse las cuatro cadenas.

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
CERTIFICACIÓN DE ACCESO POR UNIDAD    0 / 15   sin cambios
BU-D10                               PENDING_RATIFICATION · no resuelta
R-112                                registrado · no remediado
P-08                                 BLOCKED_EXTERNAL · intacto
FASE 7                               COMPLETE
```

---

## AUDITORÍA MAESTRA DE SPEC/PRODUCTO — 2026-09-08

```
¿ESTAMOS AVANZANDO?   PARCIALMENTE
DECISIÓN              B · CONGELAR FASE 8 · RECUPERAR FUNDAMENTO PRIMERO
```

El backend operativo es sólido y lo certificado sigue siendo cierto. Lo que faltaba era alguien
preguntando si la **suma** de esas dimensiones era un producto.

```
CAPACIDAD TÉCNICA      alta     tres guardas de arranque · 207/207 rutas · 687 pruebas
CAPACIDAD DE PROCESO   alta     14/15 procesos funcionales certificados
CAPACIDAD DE PRODUCTO  media    falta toda la administración multiempresa
CAPACIDAD DE UI        baja     0 comprobaciones de permiso en 28 pantallas
CAPACIDAD DE RUNTIME   media    lo operativo funciona; lo administrativo no se puede usar
```

**Cuatro `P0` nuevos**, todos la misma ausencia: el filtro de empresa nunca llegó a la superficie
de administración, y ninguna guarda lo vigila. `R-114`, `R-115`, `R-116`, `R-117`.

**Tres preocupaciones del propietario no son defectos**: compañías desde SAP, granjas desde SAP y
módulos por empresa tienen **cero** presencia en `docs/` y `specs/`. El código hace lo que
`docs/02 §3.2.1` manda. `R-124` y `R-125` van al propietario, no al backlog técnico.

```
COBERTURA DE REQUISITO DE PRODUCTO — 2026-09-08     14 / 38 = 37 % COMPLETE
HISTÓRICO 21 / 60 = 35 %                            sin tocar · mide otra cosa
CERTIFICACIÓN FUNCIONAL      14 / 15                sin cambios · sigue válida
ACCESO POR UNIDAD             0 / 15                sin cambios
CERTIFICACIONES INVALIDADAS   NINGUNA
```

Entregables: `GLOBAL_AVICOLA_MASTER_GAP_ANALYSIS.md` · `..._REQUIREMENT_MASTER_MATRIX.md` ·
`..._SPEC_INVENTORY.md` · `..._RECOVERY_ROADMAP.md` · `MASTER_DATA_SOURCE_OF_TRUTH_MATRIX.md` ·
`COMPANY_MODULE_ACCESS_MATRIX.md` · `COMPANY_CONFIGURATION_MATRIX.md` ·
`FRONTEND_SCREEN_IMPLEMENTATION_MATRIX.md` · `BACKEND_API_IMPLEMENTATION_MATRIX.md`

---

## `GA-REM-002` enmienda B · cierre de los cuatro `P0` de inquilino (2026-09-08)

```
LA `AC` EXISTÍA DESDE EL PRIMER DÍA · LA LISTA QUE LA APLICABA, NO
```

`AC05` exigía que un usuario de la compañía A no alcanzara «un recurso de la compañía B». Un
usuario es uno. Lo que falló fue `TENANT_RESOURCE_CLASSIFICATION.md`, construido desde el modelo
operativo: `users` nunca entró, y con él se quedó fuera toda la administración.

```
ROJO DEMOSTRADO   9 de 13 pruebas antes de tocar código
SENSIBILIDAD      9 / 9 detectadas · 2 exigieron corregirme
BACKEND           708 passed · 49 skipped
FRONTEND          87 passed · 8 ficheros
MIGRACIÓN         ninguna · head sigue `s9t0u1v2w3x4`
```

```
R-114 · R-117 · R-118 · R-120     CERRADOS
R-115 · R-116 · R-119 · R-121     ABIERTOS  ·  no se cierran por vecindad
R-126                             NUEVO · decisión de propietario
R-113 · FASE 8                    CONGELADOS, sin tocar
BU-D10 · R-112 · P-08             intactos
SAP y MÓDULOS                     ningún defecto falso creado
```

```
COBERTURA DE REQUISITO DE PRODUCTO   16 / 38 = 42 %   (antes 14 / 38 = 37 %)
CERTIFICACIÓN FUNCIONAL              14 / 15          sin cambios
ACCESO POR UNIDAD                     0 / 15          sin cambios
CERTIFICACIONES INVALIDADAS           NINGUNA
```

---

## `RQ-03` · cierre de `R-115` y `R-116` · expediente `R-126` (2026-09-08)

```
SIN `GA-REM` NUEVA — `RQ-03` y `AC05` ya gobernaban los dos huecos
```

La clasificación de recursos se rehízo **desde `Base.metadata`**: 54 recursos, cero sin
clasificar, con un paso que falla ruidosamente si aparece una tabla que no encaja. La lista
anterior era de lo que alguien miró; ésta es del universo.

```
R-115  CERRADO   `Company` se acota por su propia clave: es el inquilino
R-116  CERRADO   sin empresa efectiva → cero filas
R-127  NUEVO     `/masters/companies` da 500 con `sap_config` poblado — no remediado
R-126  EXPEDIENTE DE DECISIÓN — sin una línea de código
R-121  ABIERTO   `roles` sin acotar · es lo que mantiene `RQ-03` en PARTIAL
```

```
PRUEBAS        12 / 12   ·  rojo previo 8 fallando, 4 controles pasando
SENSIBILIDAD   7 / 7 detectadas · 1 rehecha por inválida y contada como tal
REGRESIÓN      720 passed · 49 skipped   ·   frontend 0 ficheros
```

```
RQ-03                                PARTIAL   · faltan `roles` y `permissions`
COBERTURA DE REQUISITO DE PRODUCTO   16 / 38 = 42 %
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
ACCESO POR UNIDAD                     0 / 15   sin cambios
R-113 · FASE 8                       CONGELADOS
```

---

## `OD-13` · `OD-14` · `RQ-03` cerrado (2026-09-08)

```
EL PERMISO ES DE PRODUCTO · EL ROL TIENE ALCANCE · CADA SUPERFICIE DECLARA SU CLASE
```

```
R-121  CERRADO   ·  R-126  CERRADO  ·  RQ-03  PARTIAL → COMPLETE
R-113  READY_TO_RESUME   ·  R-128 nuevo (segregación) · FASE 8 sigue sin empezar
```

```
PRUEBAS NUEVAS   12 roles + 4 de `OD-14`     ·  BACKEND  738 passed · 49 skipped
SENSIBILIDAD     11 en esta tanda, todas detectadas · 27 acumuladas en aislamiento
FRONTEND         87 passed · 0 ficheros de implementación cambiados
MIGRACIÓN        ninguna · head sigue `s9t0u1v2w3x4`
```

```
COBERTURA DE REQUISITO DE PRODUCTO   18 / 38 = 47 %   (antes 42 %)
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
ACCESO POR UNIDAD                     0 / 15   sin cambios
BU-D10 · R-112 · R-127 · P-08        intactos
```

---

## `OD-15` · la administración de acceso queda operable (2026-09-09)

```
ADMINISTRAR EL ACCESO  ≠  ELEVAR EL PROPIO
```

```
R-128  CERRADO  ·  R-113  CERRADO  ·  RQ-03  COMPLETE (sin cambios)
SOLO_SUPER_ADMIN  17 → 15   primera bajada del programa
```

```
ROL NUEVO      «Administrador de Accesos» · 4 permisos exactos · sin comodín · sin `users:*`
PRUEBAS        16 · SENSIBILIDAD 10/10 · BACKEND 754 passed · 49 skipped
FRONTEND       87 passed · 0 ficheros · MIGRACIÓN ninguna
```

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
ACCESO POR UNIDAD                     0 / 15   sin cambios
COBERTURA DE REQUISITO DE PRODUCTO   20 / 38 = 53 %
BU-D10 · R-112 · R-127 · P-08        intactos
FASE 8                               NOT STARTED · prerrequisitos satisfechos
```

---

## `GA-REM-040` fase 8 · la sesión (2026-09-09)

```
LA SESIÓN REPRESENTA LA AUTORIDAD  ·  NO LA DEFINE
```

El endpoint compone: ni un `if` sobre roles, empresas o comodines. Cuatro conceptos, cuatro
campos, y una prueba dedicada a que **concedidas y efectivas difieran** — si nunca pudieran,
una de las dos sobraría.

```
PRUEBAS        16 · rojo previo 15/16   ·  SENSIBILIDAD  11 / 11 · 1 rehecha
BACKEND        770 passed · 49 skipped  ·  FRONTEND  87 passed · 0 ficheros
MIGRACIÓN      ninguna · head sigue `s9t0u1v2w3x4`   ·  CONTRATO  aditivo
```

```
FASE 8                               COMPLETE
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
ACCESO POR UNIDAD                     0 / 15   sin cambios
COBERTURA DE REQUISITO DE PRODUCTO   22 / 38 = 58 %
RQ-03 · BU-D10 · R-112 · R-127 · P-08          intactos
R-129 nuevo · dependencia de la fase 9
```


---

## Fase 8 cerrada · `R-129` cerrado · fase 9 bloqueada (2026-09-09)

```
DESCUBRIR A QUIÉN CONCEDER  ≠  ADMINISTRAR USUARIOS
```

```
FASE 8   COMPLETE  ·  R-129  CERRADO  ·  RQ-03  COMPLETE (sin cambios)
FASE 9   BLOQUEADA por R-127 — el selector de empresa solo puede leer de una ruta rota
```

```
PRUEBAS        14 · rojo previo 12/14   ·  SENSIBILIDAD  8/8 · 0 inválidas · 2 N/A
BACKEND        784 passed · 49 skipped  ·  FRONTEND  87 · 0 ficheros
MIGRACIÓN      ninguna                 ·  users:read  NO
```

```
CERTIFICACIÓN FUNCIONAL              14 / 15   sin cambios
ACCESO POR UNIDAD                     0 / 15   sin cambios
COBERTURA DE REQUISITO DE PRODUCTO   23 / 38 = 61 %
R-127   OPEN → BLOQUEO DURO DE LA FASE 9   ·   R-112 · BU-D10 · P-08   intactos
```

---

## Reconciliación post-Master-360 (2026-09-09 · WAVE A0-P / A0-G)

`§1` de este documento es histórico y no se reescribe. El estado consolidado de las 40 specs
vive en `specs/remediation/INDEX.md` (reconciliado hoy) y su justificación en
`MASTER_PROGRAM_STATUS_RECONCILIATION.md §2`.

```
OD-16   requisito de producto: cuatro unidades productivas · activación por empresa · encender ≠ conceder
OD-17   un rechazo corregible no es terminal (AOD-09)
OD-18   el catálogo de empresas no expone sap_config (AOD-12) → gobierna R-127
H360 + H360A → backlog     75 hallazgos · 0 sin disposición · R-130…R-157 (28 nuevos) · 20 mapeados
A01                        verificado: 8 sitios no conformes con OD-14.c/d → R-139 (P1, WAVE A, tanda propia)
BU-D10                     PENDING_RATIFICATION
Progenitoras               14 COMPLETE · 11 PARTIAL · 2 MISSING · 1 BLOCKED · 0 P0
Activación por empresa     requisito existe · implementación existe · certificación 0/15 (sin cambio)
P1 de la Master 360        11 → 12 (H360-A01 confirmado)
```

## `R-127` cerrado · `GA-REM-033` enmienda A certificada · fase 9 sigue `FROZEN` (2026-09-09 · WAVE A1)

```
GA-REM-033-A   CERTIFIED   AC13–AC24 · rojo 9/11 → verde 11/11 · S1–S3 válidas · S4/S5 N/A con motivo
R-127          CERRADO     R-127.b DEFERRED (OD-18.b)
regresión      **795 passed · 49 skipped · 0 failed** (539 s; 784 previas + 11 de `test_company_catalog.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 87 passed / 8 archivos · tsc sin errores
fase 9         READY AFTER REMEDIATION (R-139) · FROZEN
```

## `R-139` cerrado · `GA-REM-002` enmienda C certificada · `WAVE A COMPLETE` (2026-09-09)

```
GA-REM-002-C   CERTIFIED   AC17–AC26 · 8 superficies INQUILINO · rojo 24/35 → verde 35/35 · S1–S9: 8 válidas, S3 N/A, S5 reconstruida
R-139          CERRADO     R-159 registrado (alcance de unidad en alertas, WAVE B)
regresión      **830 passed · 49 skipped · 0 failed** (542 s; 795 previas + 35 de `test_od14_productive_surfaces.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Por archivo: aislamiento de maestros 16 · usuarios 18 · roles 12 · unidades 31 · guarda 25 · administración 39 · sesión 16 · accesos 16 · candidatos 14 · `test_rbac` 21 (`SOLO_SUPER_ADMIN` ≤ 15 sin tocar) · clasificación pendiente 35 · curvas 16 · multiempresa 5 + 12 · saldo de apertura 12 · filas por unidad 21 · KPI por unidad 15 · catálogo de empresas 11 · vitest 87 passed / 8 archivos · tsc 6 errores preexistentes (`AuditPage.tsx`, `LotFormPage.tsx`), mismo número y mismos ficheros que en `7ee72a1` (`R-158`, sin cambio)
WAVE A         COMPLETE    (R-127 · R-139) · fase 9 TECHNICALLY READY · FROZEN
```

## WAVE B · tranche 1 · `R-130` cerrado · `GA-REM-005` enmienda B certificada (2026-09-09)

```
pre-flight      WAVE_B_DEPENDENCY_AND_EXECUTION_MATRIX.md · 16 ítems · 5 P1 · 8 P2 · 3 P3 · nuevos R-160 (P1) y R-161 (P2)
GA-REM-005-B    CERTIFIED (frontera técnica) · AC-R130-01…14 · rojo 11/21 → verde 21/21 · S1–S7: 6 válidas, S4 N/A
R-130           CERRADO · regresión **851 passed · 49 skipped · 0 failed** (589 s; 830 previas + 21 de `test_population_invariant.py`; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado). Primera pasada: 850/49/**1** — `test_master_management.py::test_t_090_06` descartaba 3 aves sobre el lote sembrado con saldo 0 (fixture que dependía del defecto); ajustada con recepción previa (`T-130-01b`, aserción intacta) y regresión repetida entera hasta leerla en verde · vitest 87 passed / 8 archivos · tsc 6 errores preexistentes (`AuditPage.tsx`, `LotFormPage.tsx`), mismo número y ficheros que la línea base `R-158`
WAVE B          IN PROGRESS · siguiente: R-160 + R-159
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION
```

## WAVE B · tranche 2 · `R-160` + `R-159` cerrados · `GA-REM-040` enmienda G certificada (2026-09-09)

```
recuento        canónico corregido a 17 (R-161 ya era de la ola B) · +R-162, +R-163 registrados (P2, misma raíz, fuera del tranche) → 19
GA-REM-040-G    CERTIFIED (frontera técnica) · AC-W01…W15 · AC-A01…A13 · rojo 23/39 → verde 40/40 · S1–S9: 8 válidas, S3/S8 N/A
R-160           CERRADO · guarda central exigir_unidad_operativa · unidad derivada en el servidor · global: situada + habilitada, sin concesión
R-159           CERRADO · lot_id IN lotes_alcanzables en la consulta antes de paginar · cero unidades → [] · resolve con el mismo predicado
regresión       **891 passed · 49 skipped · 0 failed** (838 s; 851 previas + 40 de `test_operations_bu_enforcement.py`; 2.ª pasada tras la dependencia de fixture de `test_t_073_06`, montaje reordenado: la concesión de unidades antes de escribir eventos)
WAVE B          IN PROGRESS · 3/19 cerrados · siguiente (no iniciado): R-135 + R-143 (+ R-140 motivo/guarda · R-154 DRAFT/version)
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-161 OPEN
```

## WAVE B · tranche 3 · `R-163` + `R-162` cerrados · `GA-REM-040` enmienda H certificada (2026-09-09)

```
recuento        revalidado desde el backlog: 19 · BLOQUEADOS corregido a 3 (R-142 · R-144 · R-156) + R-136 parcial
GA-REM-040-H    CERTIFIED (frontera técnica) · AC-L01…L15 · AC-E01…E08 · rojo 13/28 (+1 control de fixture) → verde 28/28 · S1, S2, S4, S5, S7, S9 válidas · S3/S6/S8 N/A
                aclaración del propietario registrada como CLARIFIES/PROPAGATES OD-16 (sin OD nueva) · guarda compartida con operations
R-163           CERRADO · cinco escrituras de lots (create para todo actor; update/close/activate-manual/phases para la autoridad global sobre unidad apagada)
R-162           CERRADO · descarga de evidencia por unidad (empresa 403 → evento 404 → fichero) · visibilidad de control de la global preservada
regresión       **919 passed · 49 skipped · 0 failed** (719 s; 891 previas + 28 de `test_lots_bu_enforcement.py`; 2.ª pasada tras la dependencia de fixture de `test_t_038_49`, montaje reordenado: la concesión de unidad antes de registrar el lote)
WAVE B          IN PROGRESS · 5/19 cerrados · siguiente (no iniciado): R-135 + R-143 (+ R-140 motivo/guarda · R-154 DRAFT/version)
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-161 OPEN
```

## WAVE B · tranche 4 · `R-135` + `R-143` cerrados · `R-140`/`R-154` parciales · `GA-REM-006-A` y `GA-REM-007-A` certificadas (2026-09-09)

```
pre-flight      R-163 = P1 (normalizada) · lots.company_id IS NULL: BLOCKED_RUNTIME, UNKNOWN, nada limpiado · R-164 (modelo nulable) · R-165 · R-166 · ola B = 22
GA-REM-006-A    CERTIFIED (frontera técnica) · continuidad de estados de P-07 (OD-17.a/b) · AC-S/R/D/U · rojo 13/24 → verde 24/24
GA-REM-007-A    CERTIFIED (frontera técnica) · corrector/rechazador ≠ aprobador (docs/12 R2, OD-17.b, RR-03) · AC-G01…G07 · rojo 3/6 → verde 6/6
R-135           CERRADO · R-143 CERRADO · R-140 PARTIAL (PARTE A) · R-154 PARTIAL (DRAFT/version)
sensibilidad    S1–S8, S10, S11 válidas · S9 N/A (sin rama de doble efecto)
regresión       **949 passed · 49 skipped · 0 failed** (735 s; 919 previas + 30 de `test_state_continuity.py`/`test_segregation_r143.py`)
WAVE B          IN PROGRESS · 7/22 cerrados + 2 parciales · siguiente (no iniciado): R-136 parte interna + R-165 (alternativa: GA-REM-021 agua)
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-161 OPEN · R-164 BLOCKED_RUNTIME
```

## WAVE B · tranche 5 · pre-flight de `R-136` · **STOP sin código** (2026-09-09)

```
R-136           OPEN · P1 · interno OWNER_DECISION_REQUIRED (AOD-21: estado · contrapartida · elegibilidad · autoridad) · post-SAP SAP_DEFERRED
                ninguna fuente del repositorio define el reverso pre-SAP (BR-16/R16 post-SAP; OD-17.a lo nombra; Rec. §24 no versionada; Reversal huérfano)
R-165           OPEN · P2 · evaluado (PRODUCTIVE_REVIEW; guarda compartida; sin decisión) · no admitido solo en este tranche → sigue OPEN
artefactos      R136_INTERNAL_REVERSAL_PREFLIGHT.md · R136_INTERNAL_REVERSAL_EFFECT_MATRIX.md · AOD-21 · corrección de WAVE_B §1 fila 8
WAVE B          IN PROGRESS · 7/22 cerrados + 2 parciales · decisiones 7 · siguiente (no iniciado): GA-REM-021 agua (+ R-165 posible)
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-161 OPEN · R-164 BLOCKED_RUNTIME
```

## WAVE B · tranche 5 · `R-136` interno cerrado (`R-136` PARTIAL) · `R-165` cerrado · `OD-19` · `GA-REM-041` certificada (2026-09-09)

```
decisión        AOD-21 → OD-19 (propietario, 24 cláusulas) · pre-flight previo STOP (d20e008) → spec (651bca3) → código (83437a2)
GA-REM-041      CERTIFIED (frontera técnica) · AC-RV01…07 · AC-EF01…07 · AC-S01…09 · AC-AU01…06 · AC-165-01…05 · rojo 22/27 → verde 27/27
R-136           PARTIAL · interno CERRADO (REVERSED, contrapartida aprobada, exactamente una, saldos netos) · SAP SAP_DEFERRED · consolidados DEFERRED · huevos BLOCKED_BY_R-161
R-165           CERRADO · plano de revisión con habilitación de unidad para la autoridad global
migración       t0u1v2w3x4y5 (eventstatus + auditaction 'REVERSED') · rutas 208 → 211 · SOLO_SUPER_ADMIN 13 → 15
regresión       **976 passed · 49 skipped · 0 failed** (807 s; 949 previas + 27 nuevas)
WAVE B          IN PROGRESS · 8/22 cerrados + 3 parciales · siguiente (no iniciado): GA-REM-021 agua
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-161 OPEN · R-164 BLOCKED_RUNTIME · R-166 OPEN
```

## WAVE B · tranche 6 · roles del reverso (`OD-19` Acl. A) · `B05` agua cerrado (`GA-REM-021` PARTIAL) · `GA-REM-021-A` y `GA-REM-041-A` certificadas (2026-09-09)

```
pre-flight      OD-19 Aclaración A (propietario): Supervisor Avícola create+read · Contralor read · Access Admin/operativos ninguno · SOLO_SUPER_ADMIN 15 → 13
GA-REM-041-A    CERTIFIED (frontera técnica) · REV-R01…R08 · test_reversal_role_matrix 5/5 · sensibilidad S9 a/b/c válidas
GA-REM-041-B    CERTIFIED (frontera técnica) · REV-R09…R12 · migración de datos v2w3x4y5z6a7 · baseline compuesto (AC03 48) · hallazgo de la 1ª regresión completa
GA-REM-021-A    CERTIFIED (frontera técnica) · B05 = R-13 = H360-B05 · gobernado sin escalado (nivel 2 + RR-10 + RR-11) · AC-W/V/S/BU/C/AU · rojo 15/16 → verde 16/16
B05             CERRADO (técnico) · water_consumption + water_liters (L, > 0) · breeder/broiler · aditivo · corregible · no reversible · cadena BU certificada
GA-REM-021      PARTIAL · B01/B02/B03/B13 abiertos (enmienda B pendiente) · B04 ◄── AOD-14 · R-156 ◄── AOD-20
migraciones     u1v2w3x4y5z6 (eventtype 'WATER_CONSUMPTION' + operational_events.water_liters) · v2w3x4y5z6a7 (roles: +reversals al Supervisor) · rutas 211
sensibilidad    S1–S6, S9(a/b/c/d/e), S10 válidas · S7/S8 N/A (contrato sin company_id; modelo aditivo)
regresión       1ª pasada 995 passed · 2 failed (t_025_02 defecto real · t028_04 higiene) → corregidas → 2ª pasada **1000 passed · 49 skipped · 0 failed** (819 s, 2ª pasada; la 1ª dejó 2 rojas corregidas por `GA-REM-041-B`; 976 previas + 16 agua + 5 matriz de roles + 3 migración de roles; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 89/89 · tsc 6 (R-158)
WAVE B          IN PROGRESS · 8/22 cerrados + 4 parciales · siguiente (no iniciado): GA-REM-021 B01 + B02 (Rec. §6; enmienda B previa) · alternativa R-152 → R-153
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-161 OPEN · R-164 BLOCKED_RUNTIME · R-166 OPEN
```

## WAVE B · tranche 7 · `B01` cuadre + `B02` pesos en rango en la recepción cerrados (`GA-REM-021` PARTIAL) · `GA-REM-021-B` y `GA-REM-037-B` certificadas (2026-09-10)

```
pre-flight      B01 ≠ OD-04/GA-TD-014 (viñeta distinta de Rec. §6; BR-18 intacto) · B02 gobernado por GA-REQ-037/OD-06 (referente = curva fijada al lote;
                cautela del tranche 6 desestimada) · CASO A · sin decisión del propietario · RC-11 (RR-12 · RR-13) · R-167/R-168/R-169 registrados
GA-REM-021-B    CERTIFIED (frontera técnica) · AC-B01-01…20 · AC-B02-01…22 · rojo 9/16 → verde 16/16
GA-REM-037-B    CERTIFIED (frontera técnica) · AC29…AC32 · puerta de la alerta para la recepción de reproductoras · motor, modelos y migración intactos
B01             CERRADO (técnico) · received_total / dead_on_arrival / rejected_on_arrival · BR-20 · alojadas del servidor · saldo = alojadas
B02             CERRADO (técnico) · curva del lote a la edad del día · alerta sin bloqueo · NO_REFERENCE declarado · engorde N/A
GA-REM-021      PARTIAL · B03 · B13 abiertos (enmienda C) · B04 ◄── AOD-14 · R-156 ◄── AOD-20
migración       w3x4y5z6a7b8 (tres enteros en operational_events) · rutas 211 · SOLO_SUPER_ADMIN 13 · t_025_02 48
sensibilidad    B01-S1/S4/S5/S6/S7 · SEC-S1…S4 · B02-S1/S2/S3/S5 válidas · B01-S2/S3 · B02-S4 N/A
regresión       **1016 passed · 49 skipped · 0 failed** (935 s; 1000 previas + 16 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 89/89 · tsc 6 (R-158)
WAVE B          IN PROGRESS · 8/22 cerrados + 4 parciales · siguiente (no iniciado): GA-REM-021 B03 (+ B13) · alternativa R-152 → R-153
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-161 OPEN · R-164 BLOCKED_RUNTIME · R-166 OPEN
```

## WAVE B · tranche 8 · pre-flight de consistencia · `R-170` (P1) y `B13` cerrados · `R-169`/`R-168` cerrados · `R-167` no reproducido · `B03` a decisión (2026-09-10)

```
pre-flight      R-167 NOT_REPRODUCED (matriz + prueba) · R-169 ACTIVE_UI (cantidad vs OC, no peso; 2 ocurrencias) · R-168 ACTIVE (pérdida silenciosa) ·
                R-170 nuevo P1 CONFIRMED (viables 200 para 100 pollitos) · R-171 nuevo P2 · alta formal R-167…R-171 → recuento canónico 27
GA-REM-005-C    CERTIFIED (frontera técnica) · BR-21 · AC-R170-01…07 · rojo 1/1 → verde
GA-REM-035-A    CERTIFIED (frontera técnica) · AC15…17 · contrato estático del formulario · BR-18 intacto
GA-REM-021-C    CERTIFIED (frontera técnica) · AC-B13-01…15 · AC-R168-01/02 · rojo 5/6 (+1 arnés) → verde 6/6
B13             CERRADO (técnico) · B03 OWNER_DECISION_REQUIRED (AOD-22 + AOD-19) · AOD-23 (igualdad de la partición; no bloquea)
migración       x4y5z6a7b8c9 (chicks_healthy · chicks_weak) · rutas 211 · SOLO_SUPER_ADMIN 13 · t_025_02 48
sensibilidad    S-R170-1 · S-B13-1/2/3/5/6/7/8/9 · SEC-S1 · S-R169-1 · S-R168-1 válidas · S-B13-4 · S-R169-2 N/A
regresión       **1024 passed · 49 skipped · 0 failed** (857 s; 1016 previas + 8 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 95/95 · tsc 6 (R-158)
WAVE B          IN PROGRESS · 12/27 cerrados + 4 parciales · decisiones 8 · siguiente (no iniciado): R-161 (+ R-171) · alternativa R-152 → R-153
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-161 OPEN · R-164 BLOCKED_RUNTIME · R-166 OPEN
```

## WAVE B · tranche 9 · `R-161` cerrado (`GA-REM-005-D` certificada) · `R-171` UI_ONLY (siguiente) · `R-172`/`R-173`/`R-174` registrados (2026-09-10)

```
pre-flight      dos saldos (BR-02 lote/granja · BR-03 lote/incubadora), un decremento cada uno, fila autoritativa lots.id · corrección/aprobación N/A ·
                R-171 UI_ONLY con raíz distinta → R161_ONLY · altas R-172 (egg_type en BR-02) · R-173 (PUT de lote / cancel de entradas) · R-174 (chick_dispatch 0)
GA-REM-005-D    CERTIFIED (frontera técnica) · AC-R161-01…16 (08/09 N/A) · rojo 3/7 con carrera observada (−250) → verde 7/7
R-161           CERRADO (técnico) · bloqueo antes de leer · relectura · > 0 y ≤ saldo · por recurso · sin migración
sensibilidad    R161-S1…S10 válidas (S1/S2/S3 reproducen la carrera al retirar/mover/ignorar el bloqueo; S4 cobertura de escritores)
regresión       **1031 passed · 49 skipped · 0 failed** (1210 s; 1024 previas + 7 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 95/95 · tsc 6 (R-158)
WAVE B          IN PROGRESS · 13/31 cerrados + 4 parciales · R-175 registrado (aislamiento de pruebas) · siguiente (no iniciado): R-171 (+ R-173) · alternativa R-152 → R-153
fase 9          FROZEN · ola C no iniciada · SAP no iniciado · BU-D10 PENDING_RATIFICATION · R-164 BLOCKED_RUNTIME · R-166 OPEN
```

## WAVE B · tranche 10 · pre-flight (2026-09-10) · `R-173` P1 gobernado · `R-172` gobernado · `R-174` gobernado · `R-171` UI_ONLY · `R-175` control
R-173           ACTIVE · P1 (normalizado desde P2: saldo negativo al cancelar entradas; efecto movido por PUT/corrección de lot_id sin regla ni bloqueo;
                corrección de lot_id sin empresa/unidad/activo/fecha/ubicación → reasignación entre empresas) · modelo B gobernado · GA-REM-005-E · RC-15
R-172           ACTIVE · P2 · solo el huevo fértil cuenta en BR-02 y BR-03 (Bases p.7-9; docs/02; spec.md) · GA-REM-005-F · RC-14 · sin borrar filas
R-174           ACTIVE · P3 · B.2 exige cantidad > 0 al despacho de pollitos · GA-REM-005-E §E.3 (retirar la guarda if total_qty > 0)
R-171           UI_ONLY confirmado · GA-REM-021-D (catálogo de incubadora: mortality_recording · cull_recording; pasos de flujo; i18n existente)
R-175           NON-BLOCKING · matriz de control (aisladas 4/4 · B→A 3/3 · A→B 3/3 rojas «5 fases») · OPEN · sin limpieza
altas           R-176 · R-177 · R-178 (P3, fuera) → recuento canónico 34 · 13 cerrados · 4 parciales · 17 abiertos (P1 1 · P2 8 · P3 8) · decisiones 8
WAVE B          IN PROGRESS · modo A (R-173 → R-172 → R-174 → R-171) · sin migración · COMMIT 1 = solo spec

## WAVE B · tranche 10 · cierre · `R-173` `R-172` `R-174` `R-171` cerrados (técnico) · `GA-REM-005-E/F` y `GA-REM-021-D` certificadas (2026-09-10)
R-173           CERRADO (técnico) · P1 · guarda central de edición/corrección/anulación bajo el invariante del saldo y el bloqueo de los lotes · 16/16 · S1…S5
R-172           CERRADO (técnico) · solo el huevo fértil cuenta en BR-02/BR-03 · 9/9 + vitest · S1…S5 · R-161 intacto
R-174           CERRADO (técnico) · chick_dispatch de 0 → 400 BR-04 sin fila · S1
R-171           CERRADO (técnico) · catálogo de incubadora con mortalidad y descarte · vitest 5/5 · S1/S1b
WAVE B          IN PROGRESS · 17/34 cerrados + 4 parciales · decisiones 8 · regresión 1056 passed · 49 skipped · 0 failed · siguiente (no iniciado): R-152 → R-153 · alternativa R-176 + R-178 / R-175

## WAVE B · tranche 11 · pre-flight (2026-09-10) · `R-176` P2 gobernado (absorbe `R-45`) · `R-178` gobernado · `R-177` AOD-24 · `R-175` control
R-176           ACTIVE · P2 (normalizado desde P3: misma raíz que R-45 P2; BR-18 permite superar la OC moviendo el acumulado) · paridad de validación pura
                (BR-17 · BR-18 · BR-06 · BR-19 · BR-08 · BR-11) sobre el estado candidato en PUT y POST /corrections · GA-REM-023-B · sin decisión
R-178           ACTIVE · P3 · linaje = trazabilidad generacional · histórico conservado + efectivo derivado del estado de los eventos + reasignación denegada si hay
                vínculo · OD-10 · GA-REM-031-A · sin decisión · sin migración
R-177           OPEN · P3 · pre-flight completo · registro corregido (evento ovoscopy) · DATA QUALITY + modelo → OWNER_DECISION_REQUIRED (AOD-24) · sin código
R-175           control ampliado (T11) antes de la regresión · NON-BLOCKING salvo prueba
R-45            (Wave 2, P2) absorbido por R-176
WAVE B          IN PROGRESS · 17/34 cerrados + 4 parciales · decisiones 9 · modo R176_PLUS_R178 · COMMIT 1 = solo spec

## WAVE B · tranche 11 · cierre · `R-176` (+`R-45`) · `R-178` · `R-175` cerrados (técnico) · `GA-REM-023-B`, `GA-REM-031-A`, `GA-REM-015-B` certificadas (2026-09-10)
R-176           CERRADO (técnico) · P2 · paridad de validación pura (BR-08/06/19/11/17/18) sobre el estado candidato en PUT y POST /corrections · 7/7 · S1…S5 · absorbe R-45
R-178           CERRADO (técnico) · linaje efectivo derivado del estado de los eventos · historia conservada · reasignación de eventos casados denegada · 7/7 · S1…S3
R-175           CERRADO (técnico) · teardown por prefijo en las tres suites · matriz de control ampliada verde · guardián intacto
R-177           OPEN · P3 · OWNER_DECISION_REQUIRED (AOD-24)
WAVE B          IN PROGRESS · 20/34 cerrados + 4 parciales · decisiones 9 · regresión 1070 passed · 49 skipped · 0 failed · siguiente (no iniciado): R-152 → R-153 · alternativa R-166

## WAVE B · tranche 12 · pre-flight (2026-09-10) · `R-152` gobernado (`GA-REM-042`) · `R-153` AOD-25 · modo R152_ONLY
R-152           ACTIVE · P2 · importación de abuelas sin plan tipado ni identidades ni adjuntos clasificados · PROGENITORAS_SPECIFIC (no copia de Reproductoras) ·
                GA-REM-042 (BR-22 · RC-16/RR-19) · sin decisión · sin migración
R-153           OPEN · P3 · OWNER_DECISION_REQUIRED (AOD-25) · depende de R-152 (HARD) · sin código
R-179           registrado (P3, fuera): FK de maestros de otra empresa en eventos
WAVE B          IN PROGRESS · 20/35 cerrados + 4 parciales · decisiones 10 · COMMIT 1 = solo spec

## WAVE B · tranche 12 · cierre · `R-152` cerrado (técnico) · `GA-REM-042` certificada · `R-153` AOD-25 (2026-09-10)
R-152           CERRADO (técnico) · P2 · plan de importación tipado (BR-22), adjuntos clasificados, revalidación en edición/corrección, documental · 18/18 + vitest 6/6 · sensibilidad válida
R-153           OPEN · P3 · OWNER_DECISION_REQUIRED (AOD-25)
WAVE B          IN PROGRESS · 21/35 cerrados + 4 parciales · decisiones 10 · regresión 1088 passed · 49 skipped · 0 failed · siguiente (no iniciado): R-166 · alternativa R-179

## WAVE B · tranche 13 · pre-flight (2026-09-10) · `R-179` P1 gobernado (`GA-REM-002-D`) · `R-166` P2 gobernado (`GA-REM-007-B`) · modo R179_PLUS_R166
R-179           ACTIVE · P1 (normalizado desde P3 tras reproducir por API: 7 familias de catálogo × alta/PUT/corrección, fila persistida entre empresas) ·
                regla ya escrita en GA-REM-002 ADDENDUM Wave 3 · control positivo: el catálogo compartido sigue aceptándose · sin decisión · sin migración
R-166           ACTIVE · P2 (normalizado desde P3: dos decisiones efectivas, dos auditorías de éxito, notificación de rechazo sobre evento aprobado) ·
                bloqueo de la fila del evento antes de releer el estado · sin decisión · sin migración
R-180           registrado (P2, fuera): galpones origen/destino de los submovimientos
WAVE B          IN PROGRESS · 21/36 cerrados + 4 parciales · decisiones 10 · COMMIT 1 = solo spec
