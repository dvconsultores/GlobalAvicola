# MATRIZ DE BLOQUEANTES DE LOS PROCESOS `PARTIAL`

**`GA-REM-016`** · 2026-09-05 · análisis de alcance previo a elegir el siguiente frente

---

## 1. Estado de partida, verificado

```
15 procesos · 5 CERTIFIED · 10 PARTIAL · 0 READY_FOR_E2E
```

El encargo hablaba de **9** `PARTIAL`. La matriz dice **10**: `P-08` figura como `PARTIAL`
con bloqueo externo, no como una categoría aparte. Se usa el número real.

| Estado | Procesos |
|---|---|
| `CERTIFIED` | `P-02` · `P-04` · `P-05` · `P-07` · `P-11` |
| `PARTIAL` | `P-01` · `P-03` · `P-06` · `P-08` · `P-09` · `P-10` · `P-12` · `P-13` · `P-14` · `P-15` |

## 2. Una advertencia sobre la fuente

Los huecos por proceso vienen de `audit/06_PROCESS_COVERAGE.md`, escrito **antes** de las
Waves 1–3. Varios ya no existen y contarlos habría falseado el análisis. Se verificaron uno
a uno contra el código actual:

| Hueco del audit | Estado hoy |
|---|---|
| `mortality_recording` devuelve 500 (`P-01`, `P-03`, `P-06`) | **resuelto** — `P0-1` / `GA-REM-005` `CERTIFIED` |
| `LotDetailPage` rota (`P-03`, `P-06`, `P-10`) | **resuelto** — `FE_BE_CONTRACT_MATRIX C-03 CORREGIDO` |
| Corrección no aplica el valor (`P-07`) | **resuelto** — `RC-01` / `GA-REM-006` |
| `BR-14` eludible por `POST /review/complete` (`P-07`) | **resuelto** — `GA-REM-007` |
| Permisos «sin enforcement» (`P-13`) | **resuelto** — `GA-REM-002` |

Sin esta depuración, `LotDetailPage` habría parecido un bloqueante de fan-out 3.

## 3. La matriz

| Bloqueante | Spec | Sev. | Procesos afectados | AC que impide | Fan-out | ¿Funcional? | ¿Solo de test? |
|---|---|:--:|---|---|:--:|:--:|:--:|
| **`GA-TD-014`** · la OC SAP se guarda en `extra_data.sap_order_ref` y no en `sap_document_ref`; `BR-11` y `BR-18` quedan inertes y `validate_oc_limit` nunca se dispara | `GA-REM-010` · `C-15` **`DIFERIDO`** | **P1** | `P-01` · `P-03` · `P-06` | `VALIDATION` de la recepción contra la orden de compra | **3** | sí | no |
| **`R-73`** · `POST /lots/{id}/close` responde 500 siempre; el modelo de respuesta de la ruta no encaja con el resumen del servicio | ninguna | **P1** | `P-06` | el paso `lot_closure` de su cadena | **1** | sí | no |
| **`R-60`** · la trazabilidad automática busca el evento complementario con el **mismo** `lot_id`, de modo que nunca encuentra el par | `GA-REM-008` | P2 | `P-10` | el modo automático del proceso | **1** | sí | no |
| **`GA-TD-0xx`** · 8 de 19 maestros no registran `PUT`; `MasterListPage` lo emite para todos → `405` | — | P1 | `P-12` | edición de maestros | **1** | sí | no |
| Cobertura de auditoría: 6 de 21 acciones del enum se escriben; `AuditPage` envía parámetros que el backend no admite | — | P2 | `P-09` | registro de login, permisos, maestros e importación/exportación | **1** | sí | no |
| Notificaciones: 5 de 6 tipos exigidos no existen, y **no hay canal** (correo, push, Telegram) | `GA-REM-019` | P1 | `P-14` | el proceso entero | **1** | sí | no |
| `P-13`: roles y permisos **sin pantalla** | — | P2 | `P-13` | gestión por interfaz | **1** | sí | no |
| 4 KPI huérfanos; los KPI son cero hasta aprobar y la interfaz no lo explica | — | P2 | `P-15` | — (documental) | **1** | parcial | no |
| Alerta de peso fuera de curva (`GA-REQ-037`) | backlog | P2 | `P-01` · `P-14` | alerta de peso | 2 | sí | no |
| **`GA-REM-017`** · SAP real | `GA-REM-017` | — | `P-08` | envío real | 1 | — | `BLOCKED_EXTERNAL` |
| `R-69` · la validación del saldo de apertura rechaza datos legítimos | `GA-REM-019` | P2 | **ninguno** | caso límite de `P-11`, ya certificado | **0** | sí | no |
| `R-70` · 500 con una fase productiva inexistente | `GA-REM-019` | P2 | **ninguno** | robustez de entrada | **0** | sí | no |

### `R-69` y `R-70`, evaluados como exige el encargo

```
R-69 bloquea: ninguno
R-70 bloquea: ninguno
```

`P-11` está certificado y su cadena no atraviesa ninguno de los dos. **No se cierran por
eso**: siguen abiertos en `GA-REM-019` con su estado real.

## 4. La hipótesis, contrastada

El encargo proponía `R-73` como el de mayor impacto, «por tratarse del cierre de lote y
potencialmente afectar varias cadenas».

**La evidencia no lo sostiene.** `lot_closure` figura como paso obligatorio en **un solo
proceso**: `spec.md §4.8 Broiler / Fattening`, es decir `P-06`. `audit/06` lo confirma:
«P-06 · igual que P-03 más `lot_closure`». Ninguna otra cadena lo incluye.

```
R-73 fan-out = 1
```

El de mayor alcance es **`GA-TD-014`**, con **3**.

## 5. Por qué no se elige el de mayor fan-out

`GA-TD-014` está **deliberadamente diferido**, y la razón consta en
`FE_BE_CONTRACT_MATRIX C-15`:

> enviarlo **activa `BR-11` y `BR-18`**, que hoy están inertes. Es un cambio de
> comportamiento de negocio que puede bloquear registros de operadores. Requiere coordinarse
> con `GA-REM-010` y con la decisión de `RC-07`.

`RC-07` sigue `OWNER_DECISION_REQUIRED`. Elegirlo significaría **activar dos reglas de
negocio que hoy no se aplican**, sin autoridad para decidirlo y reabriendo una decisión ya
tomada. No es una cuestión técnica.

```
GA-TD-014 = fan-out 3 · BLOQUEADO POR DECISIÓN DEL PROPIETARIO (RC-07)
```

Queda como **el siguiente frente de mayor palanca en cuanto esa decisión exista**, y es lo
que conviene preguntar al propietario.

## 6. Selección

```
SELECTED_NEXT_BLOCKER = R-73
```

**Motivo.** Entre los bloqueantes *accionables* —los que no dependen de una decisión
pendiente— todos tienen fan-out 1, así que decide el criterio siguiente del encargo:
corrección y daño sobre el ciclo de vida.

`R-73` es el único que deja un endpoint devolviendo **500 siempre**: el cierre de lote nunca
ha funcionado. Es el paso terminal del ciclo productivo, y `BR-05` existe precisamente para
gobernarlo. Los demás son huecos de cobertura o de interfaz, no un camino roto.

Se elige, por tanto, **por corrección y criticidad de ciclo, no por fan-out** — y eso se
dice explícitamente para que nadie lea después que se eligió por alcance.

## 7. Lo que este análisis deja preparado

| Frente | Fan-out | Estado |
|---|:--:|---|
| `GA-TD-014` | 3 | espera decisión de `RC-07` — **mayor palanca disponible** |
| `R-73` | 1 | **seleccionado ahora** |
| `P-12` maestros sin `PUT` | 1 | accionable, sin dependencias |
| `P-09` cobertura de auditoría | 1 | accionable |
| `R-60` trazabilidad automática | 1 | accionable, `GA-REM-008` |
| `P-14` notificaciones | 1 | requiere canal: es desarrollo nuevo, no una corrección |
| `P-08` SAP real | 1 | `BLOCKED_EXTERNAL` |

---

# REVISIÓN · Gate A y Gate B (2026-09-05, mismo día)

La tabla de §3 se escribió antes de leer las fuentes normativas una por una. Al hacerlo
—`Gate B`— **tres entradas resultaron equivocadas**. No se borran: se corrigen aquí para que
se vea qué se creyó y por qué dejó de creerse.

## Corrección 1 · `GA-TD-014` no depende de `RC-07`

Lo escrito: *«`BLOQUEADO POR DECISIÓN DEL PROPIETARIO (RC-07)`»*, tomado de la justificación
de `C-15`.

Lo que dicen las fuentes:

| Fuente | Dice |
|---|---|
| `REQUIREMENT_CONFLICT_RESOLUTION §7` | `RC-07` es **la política de mortalidad frente a SAP**, no la orden de compra |
| `RR-07` (literal) | «**solo** el mapeo de mortalidad a un documento SAP queda supeditado a la decisión del propietario» |
| `docs/16 §13` | `G-R05` «cantidad ≤ OC» es un hueco crítico **distinto** de `G-R02` «5 decisiones no definidas» |
| `docs/16 §14` | las cinco decisiones van a la **Fase 10A**; `G-R05` va a la **Fase 10B**, validaciones técnicas |
| `GA-REM-010` | la otra dependencia que citaba `C-15`: **`CERTIFIED`** desde la Wave 2 |

`C-15` citó una decisión que no cubre su caso. `RC-07` sigue abierta —y sigue siendo del
propietario— pero **sobre mortalidad**.

Queda una decisión real y más estrecha sobre `GA-TD-014`, registrada como **`OD-04`** en
`RC-07_BUSINESS_DECISION_DOSSIER.md §11`: si existen entregas parciales contra una misma
orden de compra. De eso depende activar una regla o dos.

```
GA-TD-014  fan-out 3  ·  BLOQUEADO POR OD-04  (no por RC-07)
```

## Corrección 2 · `P-12` ya no tiene el hueco de `PUT`

Lo escrito: *«8 de 19 maestros no registran `PUT`; `MasterListPage` lo emite para todos →
405»*, tomado de `audit/06`.

Verificado en el código de hoy: los ocho maestros que el audit señalaba —`suppliers`,
`genetic-lines`, `breeds`, `feed-types`, `vaccines`, `mortality-causes`, `transports`,
`processing-plants`— **tienen `PUT`**. El hueco se cerró en una wave anterior.

Los 7 que siguen sin esquema de actualización (`incubators`, `hatchers`,
`productive-phases`, `medications`, `cull-causes`, `rejection-reasons`, `correction-types`)
son exactamente **los 7 que no tienen pantalla**, así que nadie les emite `PUT` y no hay 405.

Lo que a `P-12` le queda de verdad:

```
7 catálogos sin pantalla        → desarrollo de interfaz, no corrección
contador de resultados erróneo  → MasterListPage.tsx:45 setTotal(response.data.length)
sin E2E de proceso
```

## Corrección 3 · `R-60` no es lo que decía la fila

Lo escrito: *«la trazabilidad automática busca el evento complementario con el **mismo**
`lot_id`, de modo que nunca encuentra el par»*.

Eso **ya se corrigió**: `GA-REM-008` está `CERTIFIED` — *«la trazabilidad enlaza lotes
distintos, usa el destino que el operador declaró y se abstiene cuando no lo hay»*—.

El `R-60` que sigue abierto es otro y más estrecho (`TENANT_RESOURCE_CLASSIFICATION §4`): las
claves de trazabilidad no comprueban pertenencia. **P2**, alcanzable solo por Super Admin,
que opera legítimamente entre compañías. No explotable por ningún otro rol.

## Tabla vigente tras la revisión

| Bloqueante | Fan-out | Naturaleza | Accionable | Cierra proceso |
|---|:--:|---|---|---|
| `GA-TD-014` | **3** | corrección + decisión acotada | **no** — `OD-04` | no por sí solo (`P-06` necesita más) |
| `R-60` | 1 | endurecimiento P2 | **sí** — pequeño, con precedente | contribuye a `P-10` |
| falta E2E de `P-10` | 1 | evidencia, no defecto | **sí** | **sí — `P-10`** |
| `GA-REQ-037` peso fuera de curva | 2 | funcionalidad nueva | sí | no (`P-06` sigue con `GA-TD-014`) |
| `P-09` cobertura de auditoría | 1 | corrección acotada | sí | probablemente |
| `P-12` 7 pantallas + contador | 1 | **desarrollo de interfaz** | sí | sí, con más trabajo |
| `P-13` 2 pantallas | 1 | **desarrollo de interfaz** | sí | sí, con más trabajo |
| `P-14` notificaciones | 1 | **desarrollo nuevo**, sin canal | sí | sí, mucho más trabajo |
| `P-15` 4 KPI huérfanos | 1 | corrección P2 | sí | probablemente |
| `R-76` cierre con registros sin aprobar | 1 | corrección P1 **nueva** | sí | no (`P-06` bloqueado) |
| `R-77` regla mal numerada | 0 | corrección P2 **nueva** | sí | no |
| `GA-REM-017` SAP real | 1 | externo | no | no |
| `R-69` · `R-70` | 0 | correcciones P2 | sí | no |

## Siguiente frente recomendado

```
NEXT_ACTIONABLE_BLOCKER = P-10 · trazabilidad generacional
```

**Motivo.** Es el único proceso `PARTIAL` cuyos defectos funcionales **ya están corregidos**:
`GA-REM-008` certificó el enlace automático y `C-03` reparó `LotDetailPage`. Le falta
endurecer `R-60` —pequeño, con el patrón `verificar_pertenencia` ya usado en `P-11`— y
**escribir su E2E de proceso**, que es lo que `GA-REM-016` pide.

Los demás exigen desarrollo de interfaz o funcionalidad nueva (`P-12`, `P-13`, `P-14`), o no
pueden cerrar su proceso aunque se resuelvan (`GA-REQ-037` y `R-76`, ambos en `P-06`, que
seguiría detenido por `GA-TD-014`).

Se prefiere la corrección acotada al desarrollo nuevo, conforme al criterio del encargo.

**No se inicia en este checkpoint**, que es documental.


---

# REVISIÓN · tras `GA-REM-030` (2026-09-05)

`R-60` queda `CERTIFIED`, y **`P-10` no**. La fila que lo daba por «único proceso con los
defectos funcionales ya corregidos» era correcta con la evidencia de entonces y ha resultado
falsa: esa evidencia se apoyaba en una aserción que no puede fallar (`R-79`).

| Bloqueante | Fan-out | Naturaleza | Accionable | Cierra proceso |
|---|:--:|---|---|---|
| `GA-TD-014` | **3** | corrección + decisión acotada | **no** — `OD-04` | no por sí solo |
| **`R-78`** · el vínculo automático no se crea en el orden natural | **1** | **corrección P1** | **sí** | **sí — `P-10`** |
| `R-79` · evidencia vacua de `GA-REM-008 AC01` | 0 | validez de prueba | sí | no |
| `GA-REQ-037` peso fuera de curva | 2 | funcionalidad nueva | sí | no (`P-06` con `GA-TD-014`) |
| `P-09` cobertura de auditoría | 1 | corrección acotada | sí | probablemente |
| `P-12` 7 pantallas + contador | 1 | desarrollo de interfaz | sí | sí, con más trabajo |
| `P-13` 2 pantallas | 1 | desarrollo de interfaz | sí | sí, con más trabajo |
| `P-14` notificaciones | 1 | desarrollo nuevo, sin canal | sí | sí, mucho más trabajo |
| `P-15` 4 KPI huérfanos | 1 | corrección P2 | sí | probablemente |
| `R-76` cierre con registros sin aprobar | 1 | corrección P1 | sí | no (`P-06` bloqueado) |
| `R-77` regla mal numerada | 0 | corrección P2 | sí | no |
| `GA-REM-017` SAP real | 1 | externo | no | no |
| `R-69` · `R-70` | 0 | correcciones P2 | sí | no |

## Siguiente frente recomendado

```
NEXT_ACTIONABLE_BLOCKER = R-78   (con R-79 en el mismo movimiento)
```

**Motivo.** Sigue siendo `P-10` el proceso más cercano, ahora con el obstáculo real
identificado y medido en la pila. `R-78` es P1, de causa conocida y acotada —hacer que la
rama de recepción cree el vínculo cuando no existe, igual que ya hace la del despacho—, y es
lo único que separa a `P-10` de la certificación: los pasos 1, 2, 5, 6, 9, 11 y 12 ya pasan.

`R-79` va en el mismo movimiento porque es su causa de supervivencia: mientras esa aserción no
pueda fallar, cualquier corrección de `R-78` podría volver a certificarse sin evidencia.

**No se inicia aquí**, conforme al encargo.


---

# REVISIÓN · tras `GA-REM-031` (2026-09-05)

`P-10` sale de la lista: **`CERTIFIED`**. Quedan **9** procesos `PARTIAL`.

| Bloqueante | Fan-out | Naturaleza | Accionable | Cierra proceso |
|---|:--:|---|---|---|
| `GA-TD-014` | **3** | corrección + decisión acotada | **no** — `OD-04` | no por sí solo |
| `P-09` cobertura de auditoría | 1 | corrección acotada | **sí** | **probablemente** |
| `P-15` 4 KPI huérfanos | 1 | corrección P2 | sí | probablemente |
| `P-12` 7 pantallas + contador | 1 | desarrollo de interfaz | sí | sí, con más trabajo |
| `P-13` 2 pantallas | 1 | desarrollo de interfaz | sí | sí, con más trabajo |
| `P-14` notificaciones | 1 | desarrollo nuevo, sin canal | sí | sí, mucho más trabajo |
| `GA-REQ-037` peso fuera de curva | 2 | funcionalidad nueva | sí | no (`P-06` con `GA-TD-014`) |
| `R-76` cierre con registros sin aprobar | 1 | corrección P1 | sí | no (`P-06` bloqueado) |
| `R-80` marcos horarios mezclados | 0 | corrección P2 **nueva** | sí | no |
| `R-77` regla mal numerada | 0 | corrección P2 | sí | no |
| `GA-REM-017` SAP real | 1 | externo | no | no |
| `R-69` · `R-70` | 0 | correcciones P2 | sí | no |

## Siguiente frente recomendado

```
NEXT_ACTIONABLE_BLOCKER = P-09 · cobertura de auditoría interna
```

**Motivo.** Es la única remediación **acotada** que queda con posibilidad de cerrar su
proceso: 6 de las 21 acciones del enum `AuditAction` se escriben —faltan login, permisos,
maestros e importación/exportación— y `AuditPage` envía tres parámetros que el backend no
admite. Backend y modelo existen; falta emitir y filtrar.

Los demás candidatos exigen desarrollo de interfaz (`P-12`, `P-13`) o funcionalidad nueva
sin canal (`P-14`), y `P-01`/`P-03`/`P-06` siguen esperando `OD-04`.

Advertencia aprendida en `P-10`: la distancia aparente de un proceso vale lo que valga la
evidencia que la sostiene. La de `P-09` no se ha auditado con `AC13` en la mano.

**No se inicia aquí.**


---

# REVISIÓN · tras `GA-REM-032` (2026-09-06)

`P-09` sale de la lista: **`CERTIFIED`**. Quedan **8** procesos `PARTIAL`.

| Bloqueante | Fan-out | Naturaleza | Accionable | Cierra proceso |
|---|:--:|---|---|---|
| `GA-TD-014` | **3** | corrección + decisión acotada | **no** — `OD-04` | no por sí solo |
| `P-15` 4 KPI huérfanos | 1 | corrección P2 | **sí** | **probablemente** |
| `P-12` 7 pantallas + contador | 1 | desarrollo de interfaz | sí | sí, con más trabajo |
| `P-13` 2 pantallas | 1 | desarrollo de interfaz | sí | sí, con más trabajo |
| `P-14` notificaciones | 1 | desarrollo nuevo, sin canal | sí | sí, mucho más trabajo |
| `GA-REQ-037` peso fuera de curva | 2 | funcionalidad nueva | sí | no (`P-06` con `GA-TD-014`) |
| `R-76` cierre con registros sin aprobar | 1 | corrección P1 | sí | no (`P-06` bloqueado) |
| `R-80` `R-83` marcos y atribución | 0 | correcciones P2 | sí | no |
| `R-77` regla mal numerada | 0 | corrección P2 | sí | no |
| `GA-REM-017` SAP real | 1 | externo | no | no |
| `R-69` · `R-70` | 0 | correcciones P2 | sí | no |

## Siguiente frente recomendado

```
NEXT_ACTIONABLE_BLOCKER = P-15 · reportes e indicadores
```

**Motivo.** Es la última remediación acotada que puede cerrar un proceso sin desarrollo de
interfaz nuevo: cuatro KPI huérfanos y la advertencia documental de que los indicadores son
cero hasta aprobar. Backend y modelo existen.

Los tres candidatos restantes —`P-12`, `P-13`, `P-14`— exigen pantallas o un canal de
notificación que no existe, y `P-01`/`P-03`/`P-06` siguen esperando `OD-04`.

**Advertencia que ya lleva tres tramos cumpliéndose**: la distancia aparente de un proceso
vale lo que valga la evidencia que la sostiene. La de `P-15` no se ha auditado con `AC13` en
la mano, y en `P-09` esa auditoría descubrió un 500 que nadie había visto.

**No se inicia aquí.**


---

# REVISIÓN · tras `GA-REM-022` enmienda A (2026-09-06)

`P-15` sale de la lista: **`CERTIFIED`**. Quedan **7** procesos `PARTIAL`.

| Bloqueante | Fan-out | Naturaleza | Accionable | Cierra proceso |
|---|:--:|---|---|---|
| `GA-TD-014` | **3** | corrección + decisión acotada | **no** — `OD-04` | no por sí solo |
| `P-12` 7 pantallas + contador | 1 | **desarrollo de interfaz** | sí | sí |
| `P-13` 2 pantallas | 1 | **desarrollo de interfaz** | sí | sí |
| `P-14` notificaciones | 1 | **desarrollo nuevo**, sin canal | sí | sí, mucho más trabajo |
| `GA-REQ-037` peso fuera de curva | 2 | funcionalidad nueva | sí | no (`P-06` con `GA-TD-014`) |
| `R-76` cierre con registros sin aprobar | 1 | corrección P1 | sí | no (`P-06` bloqueado) |
| `R-80` `R-83` marcos y atribución | 0 | correcciones P2 | sí | no |
| `R-77` regla mal numerada | 0 | corrección P2 | sí | no |
| `GA-REM-017` SAP real | 1 | externo | no | no |
| `R-69` · `R-70` | 0 | correcciones P2 | sí | no |

## El punto de inflexión

**Se acabaron las remediaciones acotadas.** Los cuatro tramos anteriores —`P-10`, `P-09`,
`P-15`— cerraban defectos: cosas que la spec exigía y el código hacía mal. Lo que queda es de
otra naturaleza:

| Proceso | Qué falta | Naturaleza |
|---|---|---|
| `P-12` | 7 catálogos sin pantalla + un contador erróneo | **construir interfaz** |
| `P-13` | pantallas de roles y de permisos | **construir interfaz** |
| `P-14` | 5 de 6 tipos de notificación y **ningún canal** | **desarrollo nuevo** |
| `P-01` `P-03` `P-06` | `GA-TD-014` | **decisión del propietario** |
| `P-08` | SAP real | **externo** |

## Siguiente frente recomendado

```
NEXT_ACTIONABLE_BLOCKER = P-12 · gestión de datos maestros
```

**Motivo.** Entre los tres que exigen interfaz es el más acotado y el de menor riesgo: siete
pantallas de catálogo sobre un patrón que ya existe —`MasterListPage` sirve a doce— más un
contador que usa el tamaño de la página en lugar del total. No hay reglas de negocio nuevas
que decidir.

`P-13` es comparable pero toca permisos, y `P-14` no tiene canal: elegir uno —correo, push,
Telegram— es una decisión que no me corresponde.

**Antes de empezarlo conviene un aviso**, y esta vez por experiencia propia: la distancia de
`P-12` procede de `audit/06`, que ya se ha demostrado obsoleto tres veces —el hueco de `PUT`
que declaraba ya estaba cerrado—. Y en este mismo tramo registré dos hallazgos buscando solo
en el backend cuando la capacidad vivía en el cliente. **`P-12` merece que se compruebe en
ambos lados antes de dimensionarlo.**

**No se inicia aquí.**


---

# REVISIÓN · tras `GA-REM-033` (2026-09-06)

`P-12` sale de la lista: **`CERTIFIED`**. Quedan **6** procesos `PARTIAL`.

| Proceso | Qué falta | Naturaleza | Accionable |
|---|---|---|---|
| `P-01` `P-03` `P-06` | `GA-TD-014` | **decisión del propietario** (`OD-04`) | **no** |
| `P-06` | además `GA-REQ-037` y `R-76` | funcionalidad nueva · corrección | sí, pero no cierra |
| `P-08` | SAP real | **externo** | **no** — `GA-REM-017` |
| `P-13` | pantallas de roles y de permisos | **desarrollo de interfaz** | sí |
| `P-14` | 5 de 6 tipos de notificación y **ningún canal** | **desarrollo nuevo** | sí, con decisión |

## Lo que queda, dicho sin rodeos

```
3 procesos esperan una decisión del propietario (OD-04)
1 proceso espera un contrato externo (SAP)
2 procesos requieren desarrollo, no remediación
```

**Ya no quedan defectos que corregir para certificar.** Los nueve certificados agotaron esa
vía; lo que resta es construir capacidad o decidir.

## Siguiente frente recomendado

```
NEXT_ACTIONABLE_BLOCKER = P-13 · usuarios, roles y permisos
```

**Motivo.** Es el único de los dos de desarrollo que **no exige una decisión previa**. `P-14`
necesita elegir canal —correo, push, Telegram—, y eso no me corresponde.

`P-13` tiene el backend hecho —`GA-REM-002` certificó el enforcement de permisos, y los
endpoints de roles existen y ahora se auditan (`GA-REM-032`)— y le faltan las pantallas de
roles y de permisos. Es el mismo perfil que `P-12`: capacidad de interfaz sobre un backend
que ya cumple.

**Con la advertencia de siempre, que aquí acertó**: la dimensión de `P-13` procede de
`audit/06`, que se ha demostrado obsoleto cuatro veces —su nota «permisos sin enforcement» ya
lo era—. Debe auditarse en ambos lados antes de dimensionarlo.

**No se inicia aquí.**


---

# REVISIÓN FINAL · tras `GA-REM-034` (2026-09-06)

`P-13` sale de la lista. Quedan **5**, y ninguno es trabajo técnico accionable.

| Proceso | Qué falta | Naturaleza | ¿Accionable sin decisión externa? |
|---|---|---|:--:|
| `P-01` | `GA-TD-014` | **decisión** — `OD-04` | **no** |
| `P-03` | `GA-TD-014` | **decisión** — `OD-04` | **no** |
| `P-06` | `GA-TD-014` + `GA-REQ-037` + `R-76` | **decisión** + funcionalidad | **no** |
| `P-08` | contrato SAP | **externo** — `GA-REM-017` | **no** |
| `P-14` | canal de notificación y 5 de 6 tipos | **decisión** + desarrollo | **no** |

```
NEXT_ACTIONABLE_BLOCKER = NINGUNO SIN DECISIÓN EXTERNA
```

## Lo que hace falta ahora, y no es código

| # | Decisión | Desbloquea |
|:--:|---|---|
| **`OD-04`** | ¿existen entregas parciales contra una misma orden de compra? | `P-01` `P-03` `P-06` — tres procesos |
| **canal de `P-14`** | correo · push · Telegram · en la propia aplicación | `P-14` |
| **`OD-05`** | ¿puede un administrador conceder permisos que no posee? | nada — endurece `P-13` |
| **contrato SAP** | acceso al entorno S/4HANA | `P-08` |

`OD-04` es la de mayor alcance: **tres procesos** dependen de una respuesta que cabe en una
frase. Su dossier está en `RC-07_BUSINESS_DECISION_DOSSIER.md`, escrito para decidirse sin
leer código.

## Trabajo técnico que queda, sin cerrar ningún proceso

`R-69` · `R-70` · `R-76` · `R-77` · `R-80` · `R-83` — correcciones P1/P2 abiertas, ninguna
bloquea una certificación.


---

# REVISIÓN · tras `OD-04` y `GA-REM-035` (2026-09-06)

`P-01` sale de la lista. Quedan **4**.

| Proceso | Qué falta | Naturaleza | ¿Accionable? |
|---|---|---|:--:|
| **`P-06`** | **`R-76`** — un lote se cierra con registros sin aprobar (`docs/12 R7`) | **corrección P1** | **sí** |
| `P-03` | `GA-REQ-037` — alerta de peso fuera de curva | funcionalidad nueva: exige una curva estándar por línea genética y edad, que no existe como dato | sí, con más trabajo |
| `P-08` | contrato SAP | **externo** — `GA-REM-017` | no |
| `P-14` | canal de notificación | **decisión** — `OD-05` + desarrollo | no |

## Siguiente frente recomendado

```
NEXT_ACTIONABLE_BLOCKER = R-76 · el cierre de lote admite registros sin aprobar
```

**Motivo.** Es lo único que separa a `P-06` de la certificación, es una corrección acotada
—`docs/12 R7` está escrito y la guarda tiene dónde vivir: `close_lot` ya aplica `BR-05`— y no
depende de ninguna decisión externa.

`P-03` requiere una curva estándar de referencia que hoy no existe como dato: es desarrollo
con requisito propio, no una corrección.

**No se inicia aquí.**
