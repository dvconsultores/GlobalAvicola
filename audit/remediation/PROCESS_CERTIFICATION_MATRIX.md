# PROCESS CERTIFICATION MATRIX

**Fecha** 2026-09-04 · **Wave** 3 · **Spec** `GA-REM-016`

La unidad de certificación es el **proceso de negocio según la taxonomía propia del
proyecto** (`processCatalog.ts`, 15 procesos en `audit/06_PROCESS_COVERAGE.md`). No la
pantalla, ni el endpoint, ni la codificación del cliente.

Estados admitidos por la spec: `NOT_STARTED` · `PARTIAL` · `READY_FOR_E2E` · `E2E_FAILED` ·
`E2E_PASS` · `CERTIFIED`.

---

## 1. Orden de certificación ejecutado

`GA-REM-016` fija el orden por dependencia del dominio. Se ejecutaron los tres primeros:

| # | Proceso del orden | E2E | Estado |
|---|---|---:|---|
| **1** | **Recepción de aves** | **7/7** | **`CERTIFIED`** |
| **2** | **Control de producción diario** | **7/7** | **`CERTIFIED`** |
| **3** | **Revisión → Corrección → Aprobación** | **7/7** | **`CERTIFIED`** |
| 4 | Producción y despacho de huevo fértil | — | `READY_FOR_E2E` |
| 5 | Recepción en incubadora e incubación | — | `READY_FOR_E2E` |
| 6 | Nacimiento y despacho de pollitos | — | `READY_FOR_E2E` |
| 7 | Recepción en engorde y cierre de lote | — | `READY_FOR_E2E` |
| 8 | Consolidación y preparación para SAP | — | `PARTIAL` — frontera interna solo (`GA-REM-010`) |
| 9 | Trazabilidad generacional | — | `PARTIAL` — ⚠ `R-60` |

`GA-REM-016 AC04` exige que **el primer proceso del orden** alcance `CERTIFIED` con
evidencia. Se certificaron los tres primeros.

---

## 2. Matriz por proceso — formato de la spec

| Proceso | Req | Specs | FE | BE | DB | Reglas | Seguridad | Tests | E2E | Cobertura validada | Estado |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **P-01** Progenitoras — Cría | spec §4.4 | ✅ | ✅ | ✅ | ✅ | `BR-01/06/07/08/17/18/19` | ✅ | ✅ | **3/3** | `COVERED` | **`CERTIFIED`** |
| **P-02** Progenitoras — Producción de huevo | spec §4.4 | ✅ | ✅ | ✅ | ✅ | `BR-02` | ✅ | ✅ | **9/9** | `COVERED` | **`CERTIFIED`** |
| **P-03** Reproductoras — Cría | spec §4.5 | ✅ | ✅ | ✅ | ✅ | ídem P-01 · `§4.5` alertas | ✅ | ✅ | **5/5** | `COVERED` | **`CERTIFIED`** |
| **P-04** Reproductoras — Producción de huevo fértil | spec §4.6 | ✅ | ✅ | ✅ | ✅ | `BR-02` | ✅ | ✅ | **9/9** | `COVERED` | **`CERTIFIED`** |
| **P-05** Incubación | spec §4.7 | ✅ | ✅ | ✅ | ✅ | `BR-03` | ✅ | ✅ | **8/8** | `PARTIAL` | **`CERTIFIED`** |
| **P-06** Pollo de engorde | spec §4.8 | ✅ | ✅ | ✅ | ✅ | `BR-04` · `BR-05` · `R7` | ✅ | ✅ | **6/6** | `COVERED` | **`CERTIFIED`** |
| **P-07** Revisión → Corrección → Aprobación | spec §4.10 · `docs/12` | ✅ | ✅ | ✅ | ✅ | `BR-09/13/14/15/16` · `RR-01` · `RR-03` | ✅ | ✅ | **7/7** | `COVERED` | **`CERTIFIED`** |
| **P-08** Consolidación y envío a SAP | spec §4.3/§4.10 | ✅ | ✅ | ✅ | ✅ | `BR-10/12/13` | ✅ | ✅ | ⬜ | `PARTIAL` | **`PARTIAL`** — `GA-REM-017` `BLOCKED_EXTERNAL` |
| **P-09** Auditoría interna | spec §4.11 · `docs/02 §3.11` | ✅ | ✅ | ✅ | ✅ | inmutabilidad | ✅ | ✅ | **6/6** | `COVERED` | **`CERTIFIED`** |
| **P-10** Trazabilidad generacional | spec §4.9 · `RR-02` · `RR-04` | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | **5/5** | `COVERED` | **`CERTIFIED`** |
| **P-11** Activación manual de lotes | spec §4.9 | ✅ | ✅ | ✅ | ✅ | `BR-06` | ✅ | ✅ | **6/6** | `COVERED` | **`CERTIFIED`** |
| **P-12** Gestión de datos maestros | func §3.2 | ✅ | ✅ | ✅ | ✅ | pertenencia | ✅ | ✅ | **4/4** (1 `UI_E2E`) | `COVERED` | **`CERTIFIED`** |
| **P-13** Autenticación y gestión de usuarios | func §3.1 | ✅ | ✅ | ✅ | ✅ | `RR-05` · RBAC | ✅ | ✅ | **3/3** (2 `UI_E2E`) | `COVERED` | **`CERTIFIED`** |
| **P-14** Notificaciones y alertas | func §3.14 | ✅ | ⚠ | ⚠ | ✅ | umbral configurable | ✅ | ✅ | **parcial** | **`PARTIAL`** | **`PARTIAL`** |
| **P-15** Reportes y KPI | spec §4.12 · `docs/02 §3.12` | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | **4/4** | `COVERED` | **`CERTIFIED`** |

### Nota sobre «parcial» en la columna E2E

Los procesos `P-01`, `P-03`, `P-06`, `P-09`, `P-12`, `P-13` y `P-14` reciben cobertura E2E
**de los tres procesos certificados**, que los atraviesan: la recepción alimenta P-01/03/06,
el control diario ejercita sus eventos y alertas, y el ciclo de revisión ejercita la
auditoría, los maestros y los permisos.

**Eso no los certifica.** Un proceso de etapa incluye además recolección de huevo,
incubación o cierre de lote, que no se han ejercitado de extremo a extremo. Declararlos
`CERTIFIED` por transitividad sería exactamente lo que `AC05` prohíbe.

---

## 3. Recuento

```
Procesos totales ................ 15
Evaluados ....................... 15
CERTIFIED .......................  1   (P-07)
E2E_PASS ........................  0
PARTIAL .........................  9
READY_FOR_E2E ...................  5
E2E_FAILED ......................  0
BLOCKED_BY_DEFECT ...............  0
BLOCKED_EXTERNAL ................  0   (P-08 es PARTIAL: su parte interna funciona)
```

Del orden de certificación de la spec: **3 de 9 pasos certificados**, los tres primeros y
por dependencia del dominio.

---

## 4. Por qué solo P-07 alcanza `CERTIFIED`

La spec dice: *«Un proceso solo alcanza `CERTIFIED` cuando **todos** sus componentes
críticos están verificados»*.

`P-07` es el único de los 15 cuyo alcance coincide exactamente con uno de los procesos
certificados: revisión, corrección y aprobación de principio a fin, con sus siete casos
—happy path, `BR-14`, rechazo, lista blanca, `R-32`, autorización y auditoría—.

Los procesos 1 y 2 del orden —recepción y control diario— son **capacidades transversales**
que atraviesan P-01 a P-06 sin agotar ninguno. Están certificados como procesos del orden de
`GA-REM-016`; los procesos de etapa que los contienen quedan `PARTIAL`.

Es una distinción incómoda y deliberada: inflar el recuento diciendo «P-01 certificado»
convertiría la matriz en propaganda.


---

## Tranche `P-02` · `P-04` · `P-05` (2026-09-05)

Los tres pasan de `READY_FOR_E2E` a **`CERTIFIED`**, cada uno con evidencia propia y su
cadena documentada completa —no solo su tramo distintivo, que §48 no admite como
certificación.

| Proceso | Casos | Cadena | Regla | Informe |
|---|:--:|:--:|---|---|
| `P-02` Progenitoras — producción de huevo | 9/9 | 10 pasos | `BR-02` | [PROCESS-02](PROCESS-02-CERTIFICATION.md) |
| `P-04` Reproductoras — huevo fértil | 9/9 | 10 pasos | `BR-02` | [PROCESS-04](PROCESS-04-CERTIFICATION.md) |
| `P-05` Incubación | 8/8 | 8 pasos | `BR-03` | [PROCESS-05](PROCESS-05-CERTIFICATION.md) |

Toda la evidencia atraviesa el filtro de
[`PROCESS_E2E_VALIDITY_MATRIX.md`](PROCESS_E2E_VALIDITY_MATRIX.md), derivado de `R-72`: un
`PASS` no cuenta hasta demostrar que puede fallar. Se demostró mutando `BR-02`, `BR-03` y
las guardas de pertenencia; nueve casos fallaron y se revirtió el código en el acto.


---

## `P-11` · Activación manual de lotes (2026-09-05)

Pasa de `READY_FOR_E2E ⚠ R-47` a **`CERTIFIED`**, 6/6 casos, con las seis reglas de
`docs/02 §3.9.2` ejecutadas.

Estuvo bloqueado por dos defectos, ambos resueltos antes de certificarlo:

| Hallazgo | Spec | Estado |
|---|---|---|
| `R-67` el saldo de apertura no alimentaba el balance | `GA-REM-005` enmienda | `CERTIFIED` |
| `R-47` la fecha de inicio se descartaba | `GA-REM-028` | `CERTIFIED` |

Informe: [PROCESS-11](PROCESS-11-CERTIFICATION.md).

---

## Reevaluación tras `GA-REM-029` (2026-09-05)

`R-73`, `R-74` y `R-75` quedaron certificados y el paso terminal de `P-06` —el cierre de
lote, roto desde siempre— ya funciona, con la cadena recorrida de extremo a extremo
(`e2e/proceso-p06-pollo-de-engorde.spec.ts`, 5/5).

**Ningún proceso cambia de estado.** `P-06` sigue `PARTIAL` porque dos de sus once pasos
siguen incompletos:

| Paso | Hueco | Por qué no se cierra aquí |
|---|---|---|
| `bird_reception` | `GA-TD-014` · `BR-18` inerte por el campo equivocado | diferido en `C-15`, pendiente de `RC-07` |
| `weight_recording` | `GA-REQ-037` · sin alerta de peso fuera de curva | abierto en el backlog |

`P-01` y `P-03` comparten el primero de los dos, así que tampoco se mueven. Detalle en
`R-73-LOT-CLOSE-CERTIFICATION.md` §5.


---

## Gate A · modalidad de evidencia (2026-09-05)

Se comprobó, criterio por criterio, si la evidencia que sostiene cada certificación es de la
clase que su spec exige. Detalle en `E2E_EVIDENCE_MODALITY_MATRIX.md`.

`GA-REM-016 AC05` es explícito: *«ninguna unidad certificada es una pantalla, un endpoint o
un componente»*. La spec de certificación **no pide interfaz**; pide `E2E` de proceso, y
prohíbe justamente lo contrario de lo que se temía.

| Proceso | Exigido | Disponible | ¿Válida? |
|---|---|---|:--:|
| `P-02` | `E2E` de proceso | `API_E2E` 9/9 | sí |
| `P-04` | `E2E` de proceso | `API_E2E` 9/9 | sí |
| `P-05` | `E2E` de proceso | `API_E2E` 8/8 | sí |
| `P-07` | `E2E` de proceso | `API_E2E` 7/7 | sí |
| `P-11` | `E2E` de proceso | `API_E2E` 6/6 | sí |

```
CERTIFIED = 5 / 15   ·   sin degradación
```

Se corrige solo la etiqueta: esas suites son `API_E2E`, no `UI_E2E`. La afirmación errónea
vivió en la salida de consola de un checkpoint anterior; **ningún documento del repositorio
dijo nunca «UI E2E»** —los informes de certificación dicen textualmente que la unidad es el
proceso, no la pantalla—.

No se crean pruebas de interfaz para conservar vocabulario: sería trabajo artificial.

---

## `P-10` tras `GA-REM-030` (2026-09-05)

```
R-60 = CERTIFIED        P-10 = PARTIAL — BLOCKED_BY_DEFECT (R-78)
CERTIFIED = 5 / 15      PARTIAL = 10 / 15      (sin cambio)
```

Cerrar `R-60` **no certificó el proceso**. Al ejercitar la cadena completa —12 pasos— apareció
`R-78`: el vínculo generacional automático **no se crea en el orden natural** (despacho antes
de recepción), porque la creación vive solo en la rama del despacho y las dos ramas de
recepción se limitan a actualizar un vínculo previo.

| Pasos | PASS 7 · FAIL 1 · BLOCKED 3 |
|---|---|

Y con él `R-79`: la prueba que certificaba `GA-REM-008 AC01` contiene
`"egg_batch" in crudo.lower()`, cierto siempre. **`GA-REM-008 AC01` queda `NOT_EVIDENCED`** —
el informe histórico se conserva sin modificar—, que es cómo `R-78` sobrevivió a una
certificación.

La recomendación del checkpoint anterior —`P-10` como la menor distancia— era correcta con la
evidencia de entonces y ha resultado falsa. Solo se supo recorriendo el proceso entero.

---

## `P-10` certificado tras `GA-REM-031` (2026-09-05)

```
CERTIFIED = 6 / 15      PARTIAL = 9 / 15      READY_FOR_E2E = 0
```

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-02` · `P-04` · `P-05` · `P-07` · `P-10` · `P-11` |
| `PARTIAL` | `P-01` · `P-03` · `P-06` · `P-08` · `P-09` · `P-12` · `P-13` · `P-14` · `P-15` |

Los 12 pasos de la cadena pasan. Costó tres hallazgos: `R-60` (pertenencia en los vínculos
manuales), `R-78` (el vínculo no se creaba desde la recepción, de modo que en el orden natural
no se creaba ninguno) y `R-79` (la evidencia de `GA-REM-008 AC01` no podía fallar, que es
cómo `R-78` sobrevivió a una certificación previa).

`GA-REM-008 AC01` vuelve a estar `EVIDENCED`: su afirmación demuestra por mutación que puede
fallar.

**`21 / 60` de cobertura de requisitos permanece histórico y NO se recalcula.**

---

## `P-09` certificado tras `GA-REM-032` (2026-09-06)

```
CERTIFIED = 7 / 15      PARTIAL = 8 / 15      READY_FOR_E2E = 0
```

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-02` · `P-04` · `P-05` · `P-07` · `P-09` · `P-10` · `P-11` |
| `PARTIAL` | `P-01` · `P-03` · `P-06` · `P-08` · `P-12` · `P-13` · `P-14` · `P-15` |

Los 14 pasos de la cadena pasan. **19 de 19** acciones obligatorias se emiten —dos del enum
quedan fuera por no tener superficie que auditar— y **7 de 7** filtros normativos se aplican
en servidor.

Costó tres hallazgos: `R-81` (seis módulos sin un solo registro), `R-82` (la vista aparentaba
filtrar) y `R-84` (el único filtro que la interfaz enviaba devolvía 500). `R-83` queda
abierto y declarado: una acción no atribuible a ninguna empresa no puede auditarse.

**`21 / 60` de cobertura de requisitos permanece histórico y NO se recalcula.**

---

## `P-15` certificado tras `GA-REM-022` enmienda A (2026-09-06)

```
CERTIFIED = 8 / 15      PARTIAL = 7 / 15      READY_FOR_E2E = 0
```

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-02` · `P-04` · `P-05` · `P-07` · `P-09` · `P-10` · `P-11` · `P-15` |
| `PARTIAL` | `P-01` · `P-03` · `P-06` · `P-08` · `P-12` · `P-13` · `P-14` |

Los 16 pasos pasan: **15 de 15** indicadores obligatorios y **6 de 6** reportes.

Costó `R-14` (la eclosión devolvía texto), `R-85` (tres cocientes con denominadores distintos
fundidos en uno) y `R-86` (fertilidad sin productor). `R-87` y `R-88` se registraron y
resultaron **falsos**: la exportación y el reporte de estados existían en el cliente y se
buscaron solo en el backend. Retirados y anotados.

**`21 / 60` de cobertura de requisitos permanece histórico y NO se recalcula.**

---

## `P-12` certificado tras `GA-REM-033` (2026-09-06)

```
CERTIFIED = 9 / 15      PARTIAL = 6 / 15      READY_FOR_E2E = 0
```

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-02` · `P-04` · `P-05` · `P-07` · `P-09` · `P-10` · `P-11` · `P-12` · `P-15` |
| `PARTIAL` | `P-01` · `P-03` · `P-06` · `P-08` · `P-13` · `P-14` |

Los 8 pasos pasan y los **19** maestros son gestionables. Costó `R-90` (siete sin gestión),
`R-91` (siete sin edición) y `R-89` (el total descartado).

Primera certificación del programa que incluye un caso **`UI_E2E`**, y por requisito: lo que
`R-89` rompía es el número que el usuario lee.

**`21 / 60` de cobertura de requisitos permanece histórico y NO se recalcula.**

---

## `P-13` certificado tras `GA-REM-034` (2026-09-06)

```
CERTIFIED = 10 / 15      PARTIAL = 5 / 15      READY_FOR_E2E = 0
```

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-02` · `P-04` · `P-05` · `P-07` · `P-09` · `P-10` · `P-11` · `P-12` · `P-13` · `P-15` |
| `PARTIAL` | `P-01` · `P-03` · `P-06` · `P-08` · `P-14` |

Nombre normativo corregido: `docs/02 §3.1` lo llama **Autenticación y Gestión de Usuarios**,
más ancho que «usuarios, roles y permisos». 14 pasos, todos en verde.

Costó `R-92` (sin superficie de administración), `R-93` (los permisos de un rol no se podían
editar) y `R-94` (sin catálogo de permisos). Queda abierta `OD-05`, que **no bloquea**.

**`21 / 60` de cobertura de requisitos permanece histórico y NO se recalcula.**

---

## Los cinco que quedan, por naturaleza

| Categoría | Procesos | Qué hace falta |
|---|---|---|
| **decisión del propietario** | `P-01` · `P-03` · `P-06` | `OD-04` — `GA-TD-014` |
| **dependencia externa** | `P-08` | contrato SAP · `GA-REM-017` |
| **decisión + desarrollo** | `P-14` | elegir canal de notificación, y construirlo |

**Ya no queda ningún proceso puramente técnico accionable sin decisión externa.**

---

## `OD-04` resuelta · `GA-TD-014` certificado (2026-09-06)

```
CERTIFIED = 11 / 15      PARTIAL = 4 / 15      READY_FOR_E2E = 0
```

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-01` · `P-02` · `P-04` · `P-05` · `P-07` · `P-09` · `P-10` · `P-11` · `P-12` · `P-13` · `P-15` |
| `PARTIAL` | `P-03` · `P-06` · `P-08` · `P-14` |

**Los tres procesos que dependían de `OD-04` divergieron**, y se reevaluaron uno a uno en
lugar de certificarse por alcance:

| Proceso | Resultado | Motivo |
|---|---|---|
| `P-01` | **`CERTIFIED`** | `GA-TD-014` era su único hueco; `§4.4` no exige alertas |
| `P-03` | `PARTIAL` | `§4.5` **sí** exige la alerta de peso fuera de curva — `GA-REQ-037` |
| `P-06` | `PARTIAL` | `§4.8` no exige alertas, pero `R-76` bloquea su paso de cierre |

Se verificó leyendo `§4.4`, `§4.5` y `§4.8` por separado, en vez de arrastrar la anotación que
trataba `GA-REQ-037` como si afectara a los tres por igual.

**`21 / 60` de cobertura de requisitos permanece histórico y NO se recalcula.**

---

## `R-76` certificado · `P-06` certificado (2026-09-06)

```
CERTIFIED = 12 / 15      PARTIAL = 3 / 15      READY_FOR_E2E = 0
```

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-01` · `P-02` · `P-04` · `P-05` · `P-06` · `P-07` · `P-09` · `P-10` · `P-11` · `P-12` · `P-13` · `P-15` |
| `PARTIAL` | `P-03` · `P-08` · `P-14` |

`P-06` cerró sus tres bloqueantes históricos uno a uno: `GA-TD-014` (`GA-REM-035`), `R-76`
(`GA-REM-036`) y `GA-REQ-037`, que **no aplica** — `§4.8` no exige alertas por desviación, y se
reverificó leyendo la sección entera en vez de heredarlo de `P-03`.

**`21 / 60` de cobertura de requisitos permanece histórico y NO se recalcula.**


---

## `OD-06` resuelta · `GA-REQ-037` cerrado · `P-03` certificado (2026-09-06)

```
CERTIFIED = 13 / 15      PARTIAL = 2 / 15      READY_FOR_E2E = 0
```

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-01` · `P-02` · `P-03` · `P-04` · `P-05` · `P-06` · `P-07` · `P-09` · `P-10` · `P-11` · `P-12` · `P-13` · `P-15` |
| `PARTIAL` | `P-08` · `P-14` |

`P-03` era el último proceso bloqueado por un **requisito** y no por una dependencia externa
ni por una decisión pendiente. `spec.md §4.5` exige alertar cuando el peso se sale de la curva
estándar, y la curva no existía como dato: no había tabla, ni versión, ni forma de que un lote
apuntara a una. `OD-06` resolvió de dónde sale —una tabla por línea genética, versionada, que
carga el administrador— y `GA-REM-037` la implementó.

Lo que **no** se hizo, y conviene que conste: no se inventó ninguna tolerancia global. `OD-06`
fue explícita, y sin curva cargada el sistema responde `NO_REFERENCE` y calla, en lugar de
aplicar un ±10 % que ninguna fuente respalda.

Los dos `PARTIAL` que quedan no son tareas técnicas:

| Proceso | Qué falta | Naturaleza |
|---|---|---|
| `P-08` | contrato SAP real | **dependencia externa** — `GA-REM-017` `BLOCKED_EXTERNAL` |
| `P-14` | elegir canal de notificación y construirlo | **decisión + desarrollo** |

**`21 / 60` de cobertura de requisitos permanece histórico y NO se recalcula.**
