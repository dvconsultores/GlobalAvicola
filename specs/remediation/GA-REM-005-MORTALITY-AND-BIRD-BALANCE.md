# GA-REM-005 — MORTALIDAD Y BALANCE DE AVES

## Metadata
| Campo | Valor |
|---|---|
| **ID** | `GA-REM-005` · **Tipo** `BUGFIX + BUSINESS RULE SPEC` · `POST-AUDIT REMEDIATION SPEC` |
| **Prioridad** | **P0** — la operación diaria más frecuente del negocio está caída |
| **Estado** | `SPEC_READY` |
| **Dependencias** | `GA-REM-001` · **`GA-REM-014`** (entorno de test, para poder cerrar los AC) |
| **Hallazgos** | P0-1 · `GA-TD-001` · `GA-REQ-042` (`ROTO`) · BR-06 defectuosa (`GA-TD-025`) · `bird_transfer` sin efecto (`GA-TD-054`) |
| **Revalidado** | 2026-09-03 — AST confirma que `get_current_bird_balance` **no está importado** en `operations/service.py`; firma real de 2 parámetros, invocación con 3 |

## Problema
Registrar mortalidad devuelve **HTTP 500**. La causa inmediata es un `NameError`, pero la spec **no se limita a añadir el import**: la revalidación mostró tres defectos concurrentes en la regla de balance de aves.

| # | Defecto | Evidencia |
|---|---|---|
| 1 | `get_current_bird_balance` invocada sin importar y con 3 argumentos frente a una firma de 2 | `backend/app/operations/service.py:242` vs `backend/app/operations/validators.py:21` |
| 2 | El balance de aves **no considera `bird_transfer`**: los traslados no suman ni restan | `validators.py:26-33` — `in_types` y `out_types` no lo incluyen |
| 3 | BR-06 (fecha ≥ activación del lote) está anulada por una condicional mal formada | `validators.py:250` — `A and B and C if hasattr(...) else False` se evalúa como `(A and B and C) if hasattr(...) else False` |

## Evidencia adicional
- El generador de alertas de mortalidad (umbrales 3 % / 8 %) se introdujo en `bdb5cde` (2026-06-27 03:12) y **desde ese commit la ruta está rota**.
- El test que lo habría detectado existe: `tests/test_full_workflow_audit.py::test_f8c_business_rule_mortality_exceeds_balance`. Nunca se ejecutó.
- Los umbrales 3 % / 8 % están **codificados en el código** (`operations/service.py:250-252`), mientras `docs/02 §3.14` exige umbral **configurable**.

## Comportamiento actual
```
POST /operations {event_type: "mortality_recording", bird_movements:[{quantity: N>0}]}
  → _apply_business_rules ✔ (BR-01 valida correctamente)
  → INSERT del evento y sus movimientos ✔
  → _check_and_create_alerts → NameError → 500 → rollback
  ⇒ el evento NO se persiste
```

## Comportamiento esperado
La mortalidad se registra, valida el saldo disponible, actualiza el balance y genera alerta cuando supera el umbral configurado — con la fecha validada contra la activación del lote.

## Alcance
1. Corregir la invocación de `get_current_bird_balance` (import + aridad).
2. **Reconstruir y documentar la regla de balance de aves**: qué tipos de evento suman, cuáles restan y cuáles son neutros, incluido `bird_transfer`.
3. Corregir la condicional de BR-06.
4. Hacer configurables los umbrales de alerta de mortalidad por compañía (requisito `docs/02 §3.14`).
5. Tests unitarios, de integración y E2E que cubran los AC.

## Fuera de alcance
Rediseñar el modelo de eventos · añadir tipos de evento nuevos · la alerta de peso fuera de curva (`GA-REQ-037`, backlog) · el canal de notificación (no existe; `GA-REM-019`).

## Reglas de negocio afectadas
| Regla | Estado |
|---|---|
| **BR-01** mortalidad ≤ saldo disponible | implementada correctamente; hoy inalcanzable por el defecto |
| **BR-06** fecha ≥ activación del lote | **anulada por defecto de código** — se restablece |
| **BR-07** lote activo | correcta |
| Balance de aves | **incompleta** — `bird_transfer` no participa |

### Regla de balance a documentar y verificar
```
SALDO = Σ(entradas) − Σ(salidas)
Entradas: bird_reception · birth_registration
Salidas : mortality_recording · cull_recording · bird_exit · chick_dispatch
Neutros : bird_distribution (redistribución interna entre galpones del mismo lote)
Pendiente de decisión: bird_transfer
```
**`RC-02` RESUELTO POR EVIDENCIA** (2026-09-03, regla `RR-02` — `audit/remediation/REQUIREMENT_CONFLICT_RESOLUTION.md §4`). `bird_transfer` y `bird_distribution` son movimientos **intra-lote entre galpones** y por tanto **neutros** en el balance del lote: no se suman a entradas ni a salidas. La evidencia es estructural — `BirdMovement` declara `source_house_id` y `target_house_id` (`operations/models.py:155-156`) y el esquema **no contiene ningún campo de lote destino**, por lo que es incapaz de expresar un traslado entre lotes. El movimiento entre lotes se representa con `bird_exit` + `bird_reception`. La exclusión vigente en `validators.py:27-33` es correcta y **no debe modificarse**.

**`RC-07`** (política de mortalidad frente a SAP) sigue abierto como `OWNER_DECISION_REQUIRED`, pero por la regla `RR-07` **no bloquea esta spec**: la captura de mortalidad, su validación contra el balance y su indicador son requisitos firmes con independencia de la opción contable elegida. Solo el mapeo a documento SAP queda supeditado, y vive en `GA-REM-017`.

Hallazgo nuevo incorporado: **`R-24`** — `bird_transfer` no valida la población del galpón origen ni la capacidad del destino; `validate_house_capacity` (`validators.py:297`) existe pero no se aplica a las transferencias.

## Backend afectado
`operations/service.py` (import, aridad, umbrales), `operations/validators.py` (BR-06, balance), posible campo de configuración de umbral en `masters/models.py::Company`.

## Frontend afectado
Ninguno para el defecto principal. Sí para umbrales configurables, si se decide exponerlos.

## Base de datos afectada
**Posible**: columnas de umbral en `companies` (p. ej. `mortality_alert_warning_pct`, `mortality_alert_critical_pct`). Si se aprueba → migración Alembic con docstring citando `GA-REM-005` y su AC.

## Seguridad
Ninguna superficie nueva. El endpoint queda cubierto por `GA-REM-002`.

## Compatibilidad
Los eventos de mortalidad que hoy fallan empezarán a persistirse. **Debe verificarse el estado de la base productiva**: puede haber días sin registro de mortalidad, lo que afecta a los saldos históricos. Se coordina con la auditoría de datos del paso 8 del programa.

## Edge cases
| Caso | Comportamiento exigido |
|---|---|
| cantidad = 0 | rechazo con mensaje de negocio (BR-01 ya lo cubre) |
| cantidad negativa | rechazo |
| cantidad > saldo | rechazo con el saldo disponible en el mensaje |
| lote inexistente | 404 |
| lote no activo | rechazo BR-07 |
| fecha anterior a la activación del lote | rechazo BR-06 |
| fecha con más de 90 días | rechazo BR-19 |
| lote con saldo previo 0 | rechazo; no división por cero en el cálculo del porcentaje |
| mortalidad exactamente en el umbral (3 %) | genera alerta `warning` |
| mortalidad ≥ 8 % | genera alerta `critical` |
| primer evento del lote sin recepción previa | saldo 0 → rechazo coherente |

## Acceptance Criteria

**AC01 — Registro válido**
```
Given un lote activo con saldo de 1 000 aves
When  un operador registra mortality_recording con quantity=10
Then  la respuesta es 201
And   el evento queda persistido en estado registered
And   el saldo del lote pasa a 990
```
**AC02 — Mortalidad superior al saldo**
```
Given un lote activo con saldo de 100 aves
When  se registra mortality_recording con quantity=101
Then  la respuesta es 400 con el identificador BR-01
And   el mensaje indica el saldo disponible
And   no se persiste ningún evento
```
**AC03 — Cantidad cero o negativa**
```
Given un lote activo
When  se registra mortality_recording con quantity=0 o quantity<0
Then  la respuesta es 400 y no se persiste nada
```
**AC04 — Alerta por umbral**
```
Given un lote con saldo previo de 1 000 aves y umbral de advertencia al 3 %
When  se registra una mortalidad de 30 aves
Then  se crea una OperationalAlert de tipo high_mortality con severidad warning
And   con 80 aves la severidad es critical
```
**AC05 — El generador de alertas no rompe el registro**
```
Given cualquier mortalidad válida
When  se ejecuta la generación de alertas
Then  no se produce ninguna excepción no controlada
And   si la generación de alertas fallara, el evento se persiste igualmente
```
**AC06 — BR-06 restablecida**
```
Given un lote activado el 2026-05-01 con activation_type distinto de "manual"
When  se registra un evento con fecha 2026-04-30
Then  la respuesta es 400 con el identificador BR-06
```
**AC07 — Balance documentado y verificado**
```
Given la secuencia recepción 1000 → mortalidad 10 → descarte 5 → salida 100
When  se consulta el saldo del lote
Then  el saldo es 885
And   la regla aplicada coincide con la documentada en esta spec
```
**AC08 — Umbral configurable**
```
Given una compañía con umbral de advertencia configurado al 5 %
When  se registra una mortalidad del 4 %
Then  no se genera alerta
And   con el 5 % sí se genera
```
**AC09 — Sin regresión en el resto de tipos de evento**
```
Given los 25 tipos de evento
When  se registra uno de cada tipo con datos válidos
Then  ninguno devuelve 500
```

## Tests requeridos
| ID | Cubre | Tipo |
|---|---|---|
| `T-005-01` | AC01 | integración |
| `T-005-02` | AC02 — reactiva `test_f8c` existente | integración |
| `T-005-03` | AC03 | integración |
| `T-005-04` | AC04 — umbral warning y critical | integración |
| `T-005-05` | AC05 — el fallo del generador no tumba el registro | unitario |
| `T-005-06` | AC06 — BR-06 | unitario sobre `validate_event_date` |
| `T-005-07` | AC07 — balance con secuencia completa | unitario sobre `get_current_bird_balance` |
| `T-005-08` | AC08 | integración |
| `T-005-09` | AC09 — paramétrico sobre los 25 tipos | integración |
| `T-005-10` | E2E: operador registra mortalidad desde el formulario y la ve en el listado | Playwright |

## Riesgos
| Riesgo | Mitigación |
|---|---|
| Corregir el import sin entender la regla deja el defecto latente | la spec exige documentar y verificar la regla de balance (AC07) |
| Los saldos históricos están corrompidos por meses sin registro | auditoría de datos previa (paso 8 del programa) |
| `bird_transfer` se implementa con la semántica equivocada | `RR-02` la fija: intra-lote, **neutro** en el balance. Un test debe fijar que un `bird_transfer` no altera el balance del lote |

## Rollback lógico
Cambios de código reversibles por commit. Si se añaden columnas de umbral, la migración debe tener `downgrade()` funcional. No hay pérdida de datos.

## Definition of Done
- [x] `RC-02` resuelto (`RR-02`) · [x] `RC-07` acotado (`RR-07`), no bloquea · [ ] AC01–AC09 verificados · [ ] `T-005-01..10` en verde · [ ] Regla de balance documentada en la spec · [ ] Control de regresiones · [ ] Certification report


---

# ENMIENDA DE SPEC — `AC08` · Wave 2.5 · 2026-09-04

## AC original

```
AC08 — Umbral configurable
Given una compañía con umbral de advertencia configurado al 5 %
When  se registra una mortalidad del 4 %
Then  no se genera alerta
And   con el 5 % sí se genera
```

## Genealogía

La Wave 2 difirió este AC afirmando que «ningún hallazgo lo requiere». **Esa afirmación
era incorrecta** y la revisión formal de la Wave 2.5 lo corrige:

| Fuente | Qué dice | Veredicto |
|---|---|---|
| `docs/02-functional-spec.md:516` (§3.14 Notificaciones y Alertas) | «Mortalidad > umbral **configurable**» | **requisito real** |
| `audit/06_PROCESS_COVERAGE.md:259` | «implementado con umbral **fijo** 3 % / 8 % en código» — registrado como hueco | **hallazgo real** |
| `spec.md:99` | «Alertas por desviaciones (… mortalidad > umbral)» | menciona el umbral, no su configurabilidad |
| Documentación del cliente | **silencio** | — |
| Cualquier fuente sobre alcance **por empresa** | **ninguna** | — |

## Análisis

El requisito de que el umbral sea **configurable** existe y está documentado. Lo que
**no** existe en ninguna fuente es el alcance **«por empresa»**: esa precisión la añadió
esta misma spec de remediación al redactar el AC.

Es un caso de sobrealcance parcial: el AC tomó un requisito legítimo y le añadió una
dimensión que nadie pidió. Implementar la configurabilidad por empresa exigiría una
columna nueva, su migración, su pantalla de administración y su modelo de precedencia —
todo ello para una necesidad que ninguna fuente enuncia.

## Decisión de alcance

| Elemento | Disposición |
|---|---|
| Umbral **configurable** | **implementado** en la Wave 2.5, por el mismo mecanismo que gobierna el resto del sistema: `Settings` y variables de entorno (`MORTALITY_ALERT_WARNING_PCT`, `MORTALITY_ALERT_CRITICAL_PCT`) |
| Alcance **por empresa** | **`REMEDIATION_SPEC_OVERREACH`** — trasladado a `GA-REM-019` como **mejora opcional**, no como deuda crítica |

No se sustituye el AC por otro más fácil: se retira del alcance obligatorio exactamente
aquello que nunca debió formar parte de esta remediación, y se satisface por completo lo
que la fuente sí exige.

## `AC08` enmendado

```
AC08 — Umbral configurable
Given los umbrales de alerta declarados en la configuración de la aplicación
When  se registra una mortalidad cuyo porcentaje sobre el saldo previo los alcanza
Then  se genera la alerta con la severidad correspondiente
And   los umbrales no aparecen como literales en el generador de alertas
And   cambiar la configuración cambia el comportamiento
```

**Trazabilidad:** `docs/02-functional-spec.md:516` · `audit/06_PROCESS_COVERAGE.md:259` ·
verificado por `tests/test_mortality.py::test_ac08_*` (3 tests).

## Nota anexa

`_check_and_create_alerts` conserva umbrales fijos de temperatura (`18.0`/`35.0`) y
humedad. `docs/02 §3.14` no los enumera entre los tipos de alerta exigidos, de modo que
quedan **fuera del alcance** de esta spec y se registran como `R-49` (P3) en
`GA-REM-019`. No se amplía el alcance por simetría estética.


---

# ENMIENDA · `R-67` — EL SALDO DE APERTURA COMO FUENTE DEL BALANCE

**2026-09-04** · origen: baseline limpio de `GA-REM-025` · prioridad **P1**

Esta enmienda vive aquí y no en una spec nueva porque el alcance §2 de `GA-REM-005` es
literalmente «reconstruir y documentar la regla de balance de aves». `R-67` es un hueco de
esa misma regla.

## E.1 El defecto

`POST /lots/activate-manual` guarda un `OpeningBalance` con la población del lote, y
`get_current_bird_balance` **no lo consulta**: suma únicamente movimientos de eventos de
entrada. Ningún otro punto del código lo lee tampoco.

```
activate-manual → 201, initial_male=1000 initial_female=4000
mortalidad de 12 → 400 «Mortalidad (12) excede el saldo de aves disponibles (0)»
```

Un lote incorporado manualmente queda **inoperable**: no admite mortalidad, ni descarte, ni
salida. La regla vigente de esta spec lo describe sin advertirlo, en su tabla de casos
límite: «primer evento del lote sin recepción previa → saldo 0 → rechazo coherente». Ese
«coherente» sólo es cierto para un lote nuevo; para uno incorporado es un bloqueo.

Importa porque la activación manual es el mecanismo previsto para incorporar **lotes ya en
marcha cuando el sistema se instale en un cliente** (`docs/02 §3.9`, prioridad «Crítica
(para implantación)»). Era invisible mientras todos los lotes del entorno compartido venían
de eventos de recepción sembrados.

## E.2 `RC-08` — qué significa «saldo inicial»

Al resolverlo apareció una contradicción entre dos piezas existentes, y se resolvió por la
jerarquía de evidencia de `REQUIREMENT_CONFLICT_RESOLUTION.md §1`.

| Alternativa | Sostenida por |
|---|---|
| **A** · `initial_*_count` es el **saldo vivo** al activar; los acumulados son histórico para KPI | `docs/02 §3.9.1` distingue «**Saldos iniciales de aves** (machos/hembras)» de «**Mortalidad acumulada previa**» y «Descartes acumulados» · `docs/02 §3.9.2` «Se permite **continuar operación desde el saldo inicial**» y «**Se evita doble conteo**» · `reports/service.py:193` ya lo calcula así |
| **B** · `initial_*_count` es la población original y hay que restarle los acumulados | el mensaje de `lots/service.py:209` «Mortalidad acumulada no puede exceder **población inicial**» |

**Decisión: A · `RESOLVED_BY_EVIDENCE`, nivel 3 (documento de proceso operativo).**

> **`RR-08`.** El saldo de apertura de un lote activado manualmente es
> `initial_male_count + initial_female_count`. Los campos `accumulated_*` son **histórico
> acumulado previo a la implantación**, capturados para continuidad de indicadores, y
> **no se restan** del saldo: restarlos sería exactamente el doble conteo que
> `docs/02 §3.9.2` prohíbe.

La alternativa B se apoya sólo en el nivel 5 (implementación) y no puede contradecir al
nivel 3.

## E.3 Regla de balance, corregida

```
SALDO = saldo_de_apertura + Σ(entradas) − Σ(salidas)

Saldo de apertura : initial_male_count + initial_female_count   (0 si no hay activación manual)
Entradas          : bird_reception · birth_registration
Salidas           : mortality_recording · cull_recording · bird_exit · chick_dispatch
Neutros           : bird_transfer · bird_distribution            (RR-02, intra-lote)
No participan     : accumulated_mortality_* · accumulated_culls_*  (histórico, RR-08)
```

## E.4 Cómo se evita el doble conteo

`docs/02 §3.9.2` exige «Se evita doble conteo» y hasta ahora **nada lo implementaba**.
Un lote que ya tuviera eventos de recepción y recibiera además un saldo de apertura
contaría dos veces las mismas aves.

La activación manual pasa a rechazarse si el lote ya tiene eventos que afectan al balance.
Es coherente con su propósito: sirve para lotes que existían **antes** de la implantación,
no para corregir lotes ya operando en el sistema.

## E.5 Casos límite, revisados

| Caso | Comportamiento exigido |
|---|---|
| lote nuevo sin recepción **ni** saldo de apertura | saldo 0 → rechazo, como hasta ahora |
| lote activado manualmente con saldo N | saldo N; admite mortalidad ≤ N |
| lote activado manualmente + recepción posterior de M | saldo N + M — aves nuevas, no las mismas |
| lote con eventos previos al que se le intenta activar manualmente | **rechazo**: evitaría el doble conteo |
| saldo de apertura 0 | permitido; el lote queda con saldo 0 y BR-01 rechaza toda mortalidad |
| valores negativos | ya rechazados por `OpeningBalanceBase.validate_positive` |
| doble activación manual del mismo lote | ya rechazada con 409 |

## E.6 Acceptance Criteria de la enmienda

| AC | Criterio | Verificación |
|---|---|---|
| **AC-R67-01** | Una activación manual con cantidad N produce saldo N de inmediato | consulta del balance |
| **AC-R67-02** | No hace falta ningún evento histórico ficticio para establecer el saldo | no se crea ningún `OperationalEvent` en la activación |
| **AC-R67-03** | La mortalidad posterior reduce el saldo correctamente | N − muertos |
| **AC-R67-04** | Las entradas posteriores lo aumentan correctamente | N + recibidos |
| **AC-R67-05** | El saldo de apertura no se cuenta dos veces | activación rechazada si ya hay eventos; acumulados no restados |
| **AC-R67-06** | El flujo normal de un lote nuevo no cambia | saldo idéntico al anterior sin saldo de apertura |
| **AC-R67-07** | Las correcciones y ajustes siguen las reglas vigentes | sin cambios; ninguna regla nueva |
| **AC-R67-08** | Un lote cerrado o inactivo se comporta igual que antes | `BR-07` intacta |
| **AC-R67-09** | `BR-01` usa el saldo correcto | mortalidad > saldo rechazada con el saldo real en el mensaje |
| **AC-R67-10** | La auditoría de la activación manual se conserva | `is_manual_activation`, `activated_by_id` |
| **AC-R67-11** | El aislamiento entre empresas se mantiene | `R-42`/`R-59` verdes |
| **AC-R67-12** | La regresión completa sigue en verde | suite |

## E.7 Fuera del alcance de la enmienda

El saldo **de huevos y pollitos** de un lote incorporado en fase de producción. `docs/02
§3.9.1` pide capturar «Producción acumulada de huevos», «Huevos enviados a incubadora» y
«Pollitos nacidos/transferidos», que son **producción acumulada**, no saldo disponible; el
modelo no tiene campo para el disponible y ninguna fuente lo exige. Queda anotado como
hueco, no se inventa.

También queda fuera —y se registra como `R-69`— la validación
`accumulated_mortality_* ≤ initial_*_count` de `lots/service.py:209`: bajo `RR-08` rechaza
datos legítimos (un lote de 5 000 aves vivas que acumuló 6 000 bajas a lo largo de su
ciclo). Cambiar una validación de negocio merece su propia decisión.

---

# ENMIENDA B · `R-130` — EL SALDO DE AVES NUNCA ES NEGATIVO (2026-09-09 · WAVE B · tranche 1)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-005-B` · `DATA INTEGRITY + BUSINESS RULE` · **Estado** `SPEC_READY` |
| **Hallazgo** | **`R-130`** (P1) · origen `H360-P01` · `OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX.md §4` |
| **Requisito raíz** | invariante del propietario «la población nunca es negativa» (encargo Master 360) · `spec.md BR-01` («mortalidad no puede exceder saldo disponible») · `docs/02 §5 R1` · Recomendación central §17 («mortalidad superior a población actual») · **esta spec, `E.3`**: `SALDO = apertura + Σ(entradas) − Σ(salidas)` con **salidas = `mortality_recording` · `cull_recording` · `bird_exit` · `chick_dispatch`** |
| **Proceso** | `P-01`, `P-03`, `P-06` (cría/engorde: descarte y salida) · `P-05` (incubación: despacho de pollitos) · `P-11` (saldo de apertura) |
| **Decisión** | ninguna requerida (`RR-02` neutros vigente; `R-67` apertura vigente; `OD-14`/`OD-16` intactas) |
| **Fuera de alcance** | `R-160`/`R-159` (alcance de unidad) · `R-135`, `R-140`, `R-142`, `R-143`, `R-154` (máquina de estados) · `R-136` (reverso) · `GA-REM-021` · `R-144`, `R-131…R-134`, `R-141` (ola C) · `R-152`/`R-153` · `R-147`/`R-148` · `R-156` · `R-158` · fase 9 · SAP real · `BU-D10` · saldos de huevos e incubación (`BR-02`/`BR-03`: **`R-161`**) |

## B.1 El defecto

`E.3` define cuatro salidas del saldo; `_apply_business_rules` (`operations/service.py`) solo valida
una contra él (`mortality_recording`, `BR-01`) y otra contra un saldo distinto (`chick_dispatch`,
`BR-04` sobre `get_viable_chick_balance` = nacidos − despachados, **que ignora mortalidad y
descartes**). `cull_recording` y `bird_exit` **no tienen rama**: un descarte o una salida a planta
mayor que el saldo se registra con `201` y `get_current_bird_balance` queda negativo; una cantidad
de **cero** se admite (`BirdMovementSchema.quantity ge=0`) y contamina indicadores. Además, el saldo
se lee sin bloqueo: dos decrementos concurrentes del mismo lote pueden leer el mismo saldo y
aprobarse ambos (`READ COMMITTED`, sesión por petición, `RutaTransaccional`).

## B.2 Invariante y ecuación (del modelo real, no inventada)

```
SALDO(lote) = apertura + Σ bird_reception + Σ birth_registration
              − Σ mortality_recording − Σ cull_recording − Σ bird_exit − Σ chick_dispatch
              (eventos con status ≠ CANCELLED · bird_transfer y bird_distribution neutros · RR-02)

INVARIANTE  para todo decremento D ∈ {mortalidad, descarte, salida, despacho de pollitos}:
            cantidad(D) > 0   ∧   cantidad(D) ≤ SALDO(lote) antes de D   ⇒   SALDO después ≥ 0
            evaluado bajo bloqueo de la fila del lote, de modo que decrementos concurrentes se serializan
```

- La regla se codifica como **`BR-01`** para mortalidad, descarte y salida («no exceder el saldo disponible de aves»): es la misma regla de `spec §5` aplicada a las tres salidas humanas que `E.3` ya enumera; no se inventa un `BR-` nuevo.
- Para `chick_dispatch` sigue **`BR-04`**; su «viable» pasa a ser **nacidos − mortalidad − descartes − despachados**, que es lo que «viable» significa (`Bases` p.9: sanos vs débiles) y coincide con el saldo del lote de incubación. Sin mortalidad ni descartes, el comportamiento es idéntico al actual.
- **Sexo y galpón**: el saldo es por lote (`E.3`); ninguna fuente de nivel 1-4 exige saldo por sexo o por galpón → no se añade.
- **Corrección**: las cantidades son inmutables tras crear (`OperationalEventUpdate` excluye `SUBMOVEMENT_FIELDS`; `campos_corregibles` son campos del evento) → el invariante se aplica en la **creación**, único camino de escritura de cantidades. `cancel` retira el evento del saldo (`status ≠ CANCELLED`) y no puede dejarlo negativo (solo lo aumenta).
- **Estado del lote**: `BR-07` (activo) sigue previo a toda validación.

## B.3 Comportamiento exigido

| Situación | Antes | Después |
|---|---|---|
| descarte ≤ saldo | `201` | `201` |
| descarte > saldo | **`201`, saldo negativo** | `400 BR-01` «Descarte (n) excede el saldo de aves disponibles (s)» · sin fila, sin movimiento, sin auditoría de creación, sin alerta |
| salida (`bird_exit`) > saldo | **`201`** | `400 BR-01` |
| descarte / salida = 0 | **`201`** | `400 BR-01` («debe ser mayor a cero») |
| descarte / salida < 0 | `422` (esquema) | `422` (sin cambio) |
| despacho de pollitos > nacidos − mortalidad − descartes − despachados | **`201`** si ≤ nacidos − despachados | `400 BR-04` con el viable real en el mensaje |
| N decrementos concurrentes cuya suma > saldo | **todos `201`** | solo los que quepan en orden de llegada; los demás `400 BR-01`/`BR-04`; saldo final ≥ 0 |
| mortalidad (todas las filas anteriores) | `BR-01` vigente | sin cambio de contrato; gana el bloqueo |
| lote ajeno · ubicación ajena · lote inactivo · sin permiso · clave de idempotencia repetida | `400 BR-07` · `400 BR-07` · `400 BR-07` · `403` · evento original | sin cambio |

Impacto: **inquilino** ninguno (`validate_lot_active` por empresa, `verificar_ubicacion` intactos) ·
**unidad** ninguno (la creación no está acotada por unidad hoy: `R-160`, fuera de alcance; esta
enmienda no lo empeora ni lo mejora) · **RBAC** ninguno · **auditoría**: un rechazo no produce
`audit_logs` (la excepción precede a `db.add`) · **API**: sin rutas nuevas; mismo contrato `400 {detail, rule}` ·
**BD**: sin migración; bloqueo `SELECT … FOR UPDATE` sobre `lots.id` dentro de la transacción de la
petición · **frontend**: ninguno · **SAP**: ninguno.

## B.4 Criterios de aceptación

| `AC` | Familia | Criterio (dado / cuando / entonces) |
|---|---|---|
| `AC-R130-01` | A happy | lote activo con saldo 100 · descarte 10 y salida 40 → `201` ambos · saldo 50 |
| `AC-R130-02` | B/E límites | descarte 1 → `201` · descarte = saldo → `201` y saldo 0 · después cualquier decremento de 1 → `400 BR-01` |
| `AC-R130-03` | F sobre saldo | descarte = saldo + 1 → `400 BR-01` con el saldo real en el mensaje · salida = saldo + 1 → `400 BR-01` |
| `AC-R130-04` | D cero/negativo | descarte 0 y salida 0 → `400 BR-01` · cantidad negativa → `422` (esquema, sin cambio) |
| `AC-R130-05` | S/Q sin efectos | tras un rechazo: ninguna fila en `operational_events` ni `bird_movements`, saldo intacto, ninguna entrada `audit_logs` de creación, ninguna alerta |
| `AC-R130-06` | secuencia | recepción 100 → mortalidad 30 → descarte 30 → salida 40 → saldo 0 → salida 1 → `400` |
| `AC-R130-07` | O cancelación | descarte 30 → `cancel` → saldo vuelve a 100 → salida 100 → `201` |
| `AC-R130-08` | Progenitoras | el mismo invariante, verificado de forma independiente sobre un lote `grandparent` (sin inferir de `breeder`) |
| `AC-R130-09` | incubación | nacimientos 100 · mortalidad 10 · descarte 5 → despacho 90 → `400 BR-04` (viable 85) · despacho 85 → `201` · despacho 1 → `400` |
| `AC-R130-10` | P concurrencia | saldo 100 · tres descartes de 60 **concurrentes** → exactamente un `201`, dos `400`; saldo final 40 |
| `AC-R130-11` | G duplicado | la misma `idempotency_key` dos veces → un solo evento y un solo decremento |
| `AC-R130-12` | H/L/M/K controles | lote de otra empresa → `400 BR-07` · granja ajena en la salida → `400 BR-07` · lote cerrado → `400 BR-07` · sin `operations:create` → `403` (sin cambio) |
| `AC-R130-13` | mortalidad | `BR-01` de mortalidad conserva mensaje y contrato (`test_mortality.py` intacto) |
| `AC-R130-14` | sin migración · sin rutas | cabeza Alembic `s9t0u1v2w3x4`; 208 rutas; guardianes intactos |
| `AC-R130-15` | I/J unidad | **`N/A` con evidencia**: la creación no está acotada por unidad (`R-160`); no se promete lo que no gobierna esta enmienda |

## B.5 Tareas

| Tarea | Contenido |
|---|---|
| `T-130-01` | pruebas rojas `backend/tests/test_population_invariant.py` (fixture propia: dos empresas, unidades habilitadas **explícitamente**, lotes `breeder`, `grandparent`, `hatchery`, lote cerrado; actores con y sin permiso) |
| `T-130-01b` | ajuste documentado de una fixture que dependía del defecto: `test_master_management.py::test_t_090_06` descartaba 3 aves sobre el lote sembrado con saldo 0; pasa a recibir población antes. Su aserción (`AC10` de `GA-REM-033`: el maestro creado se usa) no cambia |
| `T-130-02` | `validators.py`: `bloquear_saldo_del_lote` (`SELECT lots.id … FOR UPDATE`) · `validate_bird_decrement(db, lot_id, quantity, etiqueta)` (`> 0`, `≤ saldo`, `BR-01`) · `validate_mortality` delega en él · `get_viable_chick_balance` resta mortalidad y descartes · `validate_chick_dispatch` bloquea antes de leer |
| `T-130-03` | `operations/service._apply_business_rules`: ramas `CULL_RECORDING` y `BIRD_EXIT` → `validate_bird_decrement`; mortalidad y despacho bajo bloqueo |
| `T-130-04` | sensibilidad `S1–S7`, regresión, evidencia `R-130-POPULATION-INVARIANT-EVIDENCE.md`, cierre en backlog/INDEX/matrices |

## B.6 Sensibilidad

| Mutación | Retira | Debe caer |
|---|---|---|
| `S1` | la cota superior en `validate_bird_decrement` | `AC-R130-03` (sobre saldo) |
| `S2` | `CULL_RECORDING` de las salidas del saldo (saldo sobrestimado → resultado negativo posible) | `AC-R130-02` (exacto + 1) · `AC-R130-06` |
| `S3` | el bloqueo de fila | `AC-R130-10` (concurrencia) |
| `S4` | puerta de unidad | **`N/A`**: no existe en la creación (`R-160`) |
| `S5` | el filtro de empresa en `validate_lot_active` | `AC-R130-12` (lote ajeno) |
| `S6` | el rechazo de cantidad cero | `AC-R130-04` |
| `S7` | mortalidad y descartes del «viable» (restaurar el cálculo anterior) | `AC-R130-09` |

## B.7 Definición de terminado

`AC-R130-01…15` verdes · rojo previo documentado por criterio · `S1–S7` válidas o `N/A` con motivo ·
regresión completa verde · vitest y `tsc` sin cambio de línea base · evidencia publicada ·
`R-130 CERRADO` técnicamente; la certificación de proceso (`P-01/03/05/06`) sigue exigiendo E2E (`BLOCKED_RUNTIME`).

---

# ENMIENDA C · `R-170` — UNA SOLA CONTABILIDAD DE NACIMIENTOS (2026-09-10 · WAVE B · tranche 8)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-005-C` · `DATA INTEGRITY` · **Estado** **`CERTIFIED`** (frontera técnica, 2026-09-10) · evidencia `WAVE_B_TRANCHE_8_PREFLIGHT_AND_B13_EVIDENCE.md` · commit `c653ff8` |
| **Hallazgo** | **`R-170`** (P1, activo, reproducido): el formulario de nacimiento emite «Total nacidos» + machos + hembras + «Débiles» como cuatro filas de `bird_movements`; `get_viable_chick_balance`, `get_current_bird_balance` y `total_chicks_born` suman todas. Observado por API: 100 + 48 + 47 + 5 → `201`, 4 filas, **viables = 200, saldo = 200** para 100 pollitos. `BR-04` admite despachar el doble; el KPI de eclosión se duplica. Sin rama de reglas para `BIRTH_REGISTRATION` (`service.py:852-892`) |
| **Raíz** | dos contabilidades del mismo hecho (total y desglose) en la misma tabla; ninguna regla fija qué filas son «nacidos» |
| **Invariante** | **UN HECHO = UN EFECTO**: `NACIDOS = Σ bird_movements.quantity` del nacimiento, con **una fila por sexo** (`male`, `female`, `mixed`) y `mixed` **excluyente** con las filas sexadas; el total no se declara, se deriva |
| **Relación** | `R-130` intacto (`viables = nacidos − mortalidad − descartes − despachados`); `B13` (`GA-REM-021-C`) añade sanos/débiles como **atributos** que no entran en ningún saldo |
| **Sin cambio** | `AC-R130-01…15` · `validate_chick_dispatch` · `_suma_neta` · `get_viable_chick_balance` |

## C.1 Regla `BR-21` (nacimiento)

```
BIRTH_REGISTRATION:
  Σ quantity ≥ 1                                          (un nacimiento sin nacidos no es un nacimiento)
  a lo sumo una fila por valor de sex                     (dos filas «mixed» o dos «male» → 400)
  «mixed» excluye «male»/«female» en el mismo evento       (total + desglose → 400)
  chicks_healthy + chicks_weak ≤ Σ quantity               (B13; ver GA-REM-021-C)
en caso contrario → 400 · rule = "BR-21" · el mensaje nombra las filas o los números
```

## C.2 Criterios de aceptación

| AC | Criterio |
|---|---|
| `AC-R170-01` | la forma del formulario (`mixed` 100 + `male` 48 + `female` 47 + `mixed` 5) → `400 BR-21`; cero filas, viables 0 |
| `AC-R170-02` | `mixed` + filas sexadas → `400 BR-21` |
| `AC-R170-03` | dos filas del mismo sexo → `400 BR-21` |
| `AC-R170-04` | Σ = 0 → `400 BR-21` |
| `AC-R170-05` | nacimiento sexado (48 + 47) → `201`, viables 95, saldo 95; sin sexar (`mixed` 60) → `201`, viables 60 |
| `AC-R170-06` | el KPI de incubadora (`total_chicks_born`) cuenta Σ filas del nacimiento aprobado, sin inflar |
| `AC-R170-07` | el formulario de nacimiento no registra una fila «Total nacidos»: filas por sexo + sanos/débiles como datos de evento; el total se muestra derivado |

Sensibilidad `S-R170-1`: retirar la regla de filas → `AC-R170-01/02/03` rojas. Pruebas: `tests/test_birth_classification.py` (R-170) ·
contrato estático del formulario (`vitest`). Fixtures existentes (una fila `mixed`) siguen válidas.

---

# ENMIENDA D · `R-161` — LOS SALDOS DE HUEVOS E INCUBACIÓN SE LEEN BAJO EL BLOQUEO DEL LOTE (2026-09-10 · WAVE B · tranche 9)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-005-D` · `DATA INTEGRITY` · **Estado** **`CERTIFIED`** (frontera técnica, 2026-09-10) · evidencia `R-161-EGG-INCUBATION-CONCURRENCY-EVIDENCE.md` · commits `22476bb` · `abd3179` |
| **Hallazgo** | `R-161` (P2): `validate_egg_dispatch` (`BR-02`) y `validate_incubation_load` (`BR-03`) leen `get_egg_balance` / `get_hatchery_egg_balance` **sin** `bloquear_saldo_del_lote`; dos decrementos concurrentes leen el mismo saldo y ambos confirman (la carrera que `R-130`/enmienda B cerró para las aves). Además el servicio salta la validación cuando la cantidad es 0 (`if total > 0`), por lo que un despacho o una carga de 0 se registra |
| **Matriz** | `audit/remediation/R161_EGG_INCUBATION_BALANCE_WRITER_MATRIX.md` (escritores, grafo, fila autoritativa, criterios de bloqueo) |
| **Fila autoritativa** | `lots.id` — los dos saldos se agrupan por `lot_id`; los dos escritores (uno por saldo) convergen en el lote; misma primitiva que `R-130` |
| **Sin cambio** | `get_egg_balance`, `get_hatchery_egg_balance` (fórmulas), `_suma_neta`, saldos de aves, `AC-R130-*`, `BR-21`, `B13`, `R-166` (carrera approve/reject: otro invariante), `OD-19 §18` (huevos siguen no reversibles hasta enmienda de `GA-REM-041`) |
| **Registrados, fuera** | `R-172` (todas las `egg_type` cuentan como disponibles) · `R-173` (`PUT` con cambio de lote y `cancel` de entradas sin revalidar saldos) · `R-174` (`chick_dispatch` de 0 aceptado) |

## D.1 Contrato

1. **Saldos**: `BR-02` = Σ recolección − Σ despacho (por lote, ≠ `CANCELLED`); `BR-03` = Σ recepción en incubadora − Σ `quantity_loaded` (por lote).
2. **Escritores (decrementos)**: `egg_dispatch` → `BR-02`; `incubation_load` → `BR-03`. Incrementos (`egg_collection`, `egg_reception_hatchery`): sin bloqueo (solo suben el saldo; nunca lo exceden).
3. **Bloqueo**: `bloquear_saldo_del_lote(lot_id)` (`SELECT … FOR UPDATE` sobre `lots`) **antes** de leer el saldo; el saldo se recalcula bajo el bloqueo; la validación usa ese saldo; el alta ocurre en la misma transacción (`RutaTransaccional`); el rollback no deja efecto parcial (la regla corre antes de `db.add`).
4. **Invariante**: `cantidad > 0` y `cantidad ≤ saldo` bajo el bloqueo; tras cualquier conjunto confirmado, `saldo ≥ 0`. Sin tolerancia. El servicio **no** salta la validación por cantidad 0: la regla la rechaza (`BR-02`/`BR-03` «mayor a cero»), como `R-130 AC04`.
5. **Orden de bloqueos**: uno solo (la fila del lote); sin cadena; sin interbloqueo posible. **Alcance**: por recurso (lote) → dos lotes o dos empresas no se serializan entre sí; sin mutex de proceso.
6. **Error**: `400` con `rule = BR-02` / `BR-03` (contrato existente); mensaje con cantidad y saldo.
7. **Corrección**: N/A (los submovimientos no son corregibles). **Aprobación**: N/A (el efecto nace en el alta; la aprobación no muta cantidades). **Reverso**: fuera (`OD-19 §18`).
8. **Seguridad**: cadena certificada (`OD-14`, `OD-16`, `R-160`, `R-139`); sin permiso nuevo; sin lógica por nombre de rol.
9. **Auditoría**: el alta confirmada audita `created`; la denegada no deja auditoría de éxito ni filas.
10. **`R-130` / `R-170` / `B13`**: intactos; el bloqueo es la misma primitiva.

## D.2 Criterios de aceptación

| AC | Criterio | Contrato |
|---|---|---|
| `AC-R161-01` | control secuencial: recolección 100 → despacho 60 → saldo 40 (`BR-02`); recepción 100 → carga 60 → saldo 40 (`BR-03`) | `201` |
| `AC-R161-02` | el resto exacto se acepta (40 tras 60; 100 de una vez) — distingue `>` de `>=` | `201` |
| `AC-R161-03` | una unidad de más se rechaza con cero efectos (sin evento, sin filas, saldo intacto, sin auditoría de éxito) | `400 BR-02/03` |
| `AC-R161-04` | cantidad 0 → `400` (sin fila «vacía») | `400` |
| `AC-R161-05` | **carrera** `egg_dispatch`: saldo 100, tres despachos de 70 lanzados concurrentemente → exactamente uno confirma; códigos `[201, 400, 400]`; saldo final 30 ≥ 0; una sola fila de despacho | verdad final |
| `AC-R161-06` | **carrera** `incubation_load`: recepción 100, tres cargas de 70 concurrentes → `[201, 400, 400]`; saldo 30 | verdad final |
| `AC-R161-07` | dos lotes distintos, un despacho de 70 en cada uno concurrentemente → ambos `201` (bloqueo por recurso, no global) | `201, 201` |
| `AC-R161-08` | multi-escritor: **N/A** (un decremento por saldo; documentado en la matriz) | — |
| `AC-R161-09` | corrección: **N/A** (submovimientos no corregibles) | — |
| `AC-R161-10` | otra empresa → `400 BR-07`; sin fila; saldo intacto | `400` |
| `AC-R161-11` | unidad apagada: global situada → `403`; concesión histórica → `BR-07` | `403`/`400` |
| `AC-R161-12` | sin la unidad → `BR-07` | `400` |
| `AC-R161-13` | global sin contexto → `BR-07` | `400` |
| `AC-R161-14` | sin `operations:create` (sin permiso, Administrador de Accesos, control-lectura) → `403` | `403` |
| `AC-R161-15` | auditoría: la operación confirmada audita `created`; la denegada en la carrera no | auditoría |
| `AC-R161-16` | control `R-171`: `mortality_recording` y `cull_recording` sobre un lote de incubadora → `201` y restan de viables una vez (el backend ya los admite: `R-171` es `UI_ONLY`) | control |

## D.3 Sensibilidad

| Mut. | Retira | Debe caer |
|---|---|---|
| `R161-S1` | el bloqueo en los dos validadores | `AC-R161-05/06` (doble `201`, saldo negativo observado) |
| `R161-S2` | el bloqueo pasa a **después** de leer el saldo | `AC-R161-05/06` |
| `R161-S3` | se bloquea pero se valida contra el saldo leído **antes** del bloqueo (relectura descartada) | `AC-R161-05/06` |
| `R161-S4` | el bloqueo solo en `egg_dispatch` (se omite en `incubation_load`) | `AC-R161-06` (cobertura completa de escritores) |
| `R161-S5` | la cota `cantidad ≤ saldo` | `AC-R161-03` |
| `R161-S6` | la empresa (cuatro capas del alta) | `AC-R161-10` con fila observada |
| `R161-S7` | la habilitación de la unidad | `AC-R161-11` |
| `R161-S8` | la concesión del actor | `AC-R161-11/12` |
| `R161-S9` | `operations:create` en la ruta | `AC-R161-14` |
| `R161-S10` | vuelve el salto `if total > 0` | `AC-R161-04` |

## D.4 Definición de terminado

`AC-R161-01…07, 10…16` verdes (`08`, `09` N/A con evidencia) · rojo válido con carrera **observada** (ambas confirman; saldo negativo) ·
sensibilidad válida · `R-130` 21/21 · `R-170`/`B13` 6/6 · `B01` 10/10 · `B02` 8/8 · `B05` 16/16 · reversos · `R-135`/`R-143` · `R-159`/`R-160` ·
`R-162`/`R-163` · `R-139` · `R-165` · `OD-14`/`OD-16` · guardianes exactos (rutas 211, cabeza `x4y5z6a7b8c9`, sin migración) · `test_clean_baseline`
(N/A por cambio, ejecutada) · `test_time_determinism` · regresión completa **leída** · `R-161` cerrado (técnico) · `R-171` OPEN (siguiente) ·
certificación de proceso `BLOCKED_RUNTIME`.

---

# ENMIENDA E · `R-173` + `R-174` — LAS MUTACIONES POSTERIORES AL ALTA (CAMBIO DE LOTE, CORRECCIÓN DE LOTE, CANCELACIÓN) RESPETAN EL INVARIANTE DEL SALDO; EL DESPACHO DE POLLITOS ES > 0 (2026-09-10 · WAVE B · tranche 10)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-005-E` · `DATA INTEGRITY` + `TENANT` · **Estado** **`CERTIFIED`** (frontera técnica, 2026-09-10) · evidencia `WAVE_B_TRANCHE_10_BALANCE_INTEGRITY_EVIDENCE.md` · commits `c56b2de` · `64dff76` |
| **Hallazgos** | **`R-173`** (registrado P2 → **P1** normalizado: saldo negativo, efecto movido sin validación, reasignación entre empresas por `POST /corrections`, sin bloqueo) · **`R-174`** (P3: `chick_dispatch` de 0 aceptado por la guarda `if total_qty > 0`) |
| **Matrices** | `audit/remediation/R173_EDIT_CANCEL_BALANCE_EFFECT_MATRIX.md` (superficies, reasignación, modelo, bloqueos, fronteras) · `audit/remediation/R174_ZERO_QUANTITY_DISPATCH_AUTHORITY_TRACE.md` |
| **Fuentes** | `docs/12 §2-3` (editar antes de enviar; Registrado → Anulado auditado) · `docs/13 §2` (edición: campo, valor anterior, valor nuevo) · `B.2`/`E.3`/`D.1.4` (invariante; cuatro salidas; saldo ≥ 0 tras cualquier conjunto confirmado) · `GA-REM-040-G AC-W09` (destino de una edición = alta) · `GA-REM-006-A` (mapa de transiciones) · `OD-19`/`GA-REM-041` (reverso ≠ cancelación) |
| **Modelo** | **B**: reasignación permitida en `EDITABLES`/estados corregibles (contrato vigente); efecto viejo neutralizado por construcción (agregado dinámico); efecto nuevo validado **como un alta** en el destino; origen conserva `saldo ≥ 0`; cancelación de entradas conserva `saldo ≥ 0`; todo bajo el bloqueo de las filas de lote, atómico en la transacción de la petición. **Sin decisión del propietario** (matriz §7) |
| **Sin cambio** | fórmulas de los cuatro saldos · `_suma_neta` · `EDITABLES` / `NO_CANCELABLES` / estados corregibles · permisos · rutas · `R-140` residual (motivo, «solo administrador») · `R-154` (`DRAFT`, `version`) · `OD-19 §18` · reverso · `EggBatch`/`ChickBatch` (`R-178`) · reglas no keyed por lote en la edición (`R-176`) |
| **Migración** | ninguna (cabeza `x4y5z6a7b8c9`) |

## E.1 La premisa de `B.2` se corrige

`B.2` afirmaba: «`cancel` retira el evento del saldo (`status ≠ CANCELLED`) y no puede dejarlo negativo (solo lo aumenta)» y «el invariante se aplica en
la creación, único camino de escritura de cantidades». Ambas frases valen para las **salidas** y para la **cantidad**; no para las **entradas** ni para el
**lote**: cancelar una recepción, un nacimiento, una recolección o una recepción en incubadora **resta** del saldo, y cambiar `lot_id` (por `PUT` o por
corrección) traslada el efecto entero a otro lote. Texto vigente desde esta enmienda:

> El invariante `saldo ≥ 0` (`B.2`, `D.1.4`) gobierna **toda** mutación que cambie qué filas cuentan en qué lote: el alta (`B.2`, `D.1`), la
> **cancelación** (excluye una fila) y la **reasignación de lote** (`lot_id` por `PUT` o por `POST /corrections`: quita la fila de un lote y la pone en
> otro). Las cantidades siguen siendo inmutables tras el alta.

## E.2 Contrato (`§54` del prompt, 1-30)

1. **Hallazgo**: `R-173` (matriz §1) — `update_event` y `create_correction` mueven el efecto entre lotes sin regla de saldo ni bloqueo (la corrección, además, sin empresa/unidad/activo/fecha/ubicación); `cancel_event` excluye una entrada sin comprobar que el saldo del lote quede `≥ 0` y sin bloqueo.
2. **Tipos afectados** (matriz §3): entradas `bird_reception`, `birth_registration`, `egg_collection`, `egg_reception_hatchery`; salidas `mortality_recording`, `cull_recording`, `bird_exit`, `chick_dispatch`, `egg_dispatch`, `incubation_load`. Neutros y sin efecto: sin cambio de contrato.
3. **Dinámico vs materializado**: las cuatro familias son `DYNAMIC_AGGREGATE` (`status ≠ CANCELLED`, `lot_id` actual). No hay compensación: la neutralización del efecto viejo es la propia exclusión/reasignación de la fila. Materializados fuera del saldo (`egg_batches`, `chick_batches`, alertas, notificaciones): fuera (`R-178`).
4. **Edición de cantidad**: no existe (`bird_movements`, `egg_movements`, `hatchery_params` solo en el alta; `422` por `extra="forbid"`; no corregibles, `400`). Control `AC-R173-01`.
5. **Cambio de lote** (`PUT` y `POST /corrections` con `field_name = lot_id`): permitido en los estados de hoy. El servidor deriva `n` de las filas persistidas (`Σ bird_movements.quantity`; `Σ egg_movements.quantity` **disponibles** —`GA-REM-005-F`—; `Σ hatchery_params.quantity_loaded`). El cliente no aporta cantidades, lote viejo, saldo ni compensación.
6. **Cancelación**: permitida en los estados de hoy (`∉ NO_CANCELABLES`). Salidas: el saldo sube (sin regla, `AC-R130-07`). **Entradas**: `saldo(lote) − n ≥ 0`, y para `birth_registration` además `viables(lote) − n ≥ 0`; si no, `400` con la regla de la familia (`BR-01` aves · `BR-04` nacimiento con despachos · `BR-02` huevos · `BR-03` incubadora), mensaje «La anulación dejaría el saldo del lote en −k», evento intacto, sin auditoría `CANCELLED`. Nada en cascada.
7. **Saldo viejo (origen A)**: salida movida → A sube (sin regla). Entrada movida → `saldo(A) − n ≥ 0` (y viables para nacimientos); si no, `400` con la regla de la familia y el evento intacto.
8. **Saldo nuevo (destino B)**: entrada movida → B sube (sin regla de saldo). Salida movida → **la misma validación del alta** sobre B: `validate_mortality` / `validate_bird_decrement(etiqueta)` / `validate_chick_dispatch` / `validate_egg_dispatch` / `validate_incubation_load` con `n` persistido (`n > 0`, `n ≤ saldo(B)` bajo bloqueo). `400 BR-01/02/03/04` con el saldo de B en el mensaje.
9. **Validación del destino, siempre** (ambos caminos): `validate_lot_active(company)` → `validate_event_date` → `verificar_ubicacion` (si cambia `farm_id`/`house_id`/`destination_farm_id`) → `exigir_unidad_operativa(lot_id=destino)` → reglas de saldo (7, 8). Orden fijo; la primera que falla responde; nada se escribe.
10. **Bloqueos**: `cancel`: la fila `lots.id` del evento. Cambio de lote con efecto: las filas de A y B.
11. **Orden**: `bloquear_saldo_del_lote(min(A, B))` y después `bloquear_saldo_del_lote(max(A, B))` — clave primaria ascendente, sentencias sucesivas; los validadores del alta vuelven a bloquear B (reentrante en la misma transacción). Una sola convención para todos los escritores → sin interbloqueo A→B/B→A. Sin mutex de proceso; alcance por recurso.
12. **Atomicidad**: lectura del original → bloqueos → relectura (`refresh`) → validaciones → `setattr`/`CANCELLED` → auditoría, en la transacción de la petición (`RutaTransaccional`); cualquier fallo deja el evento como estaba, sin `lot_id` parcial y sin auditoría de éxito.
13. **Idempotencia**: segunda cancelación → `400` (`CANCELLED ∈ NO_CANCELABLES`), sin efecto; cancelaciones concurrentes: el bloqueo serializa y la relectura hace que solo una transicione. Un `PUT` repetido con el mismo `lot_id` no mueve nada (destino = origen → sin guarda de saldo).
14. **Inquilino**: destino de otra empresa → `400 BR-07` en `PUT` (hoy) y en corrección (nuevo). Los saldos de la otra empresa no se tocan.
15. **Unidad**: destino en unidad apagada → `403`; sin concesión → `400 BR-07`; en ambos caminos (`OD-14`, `OD-16`, `R-160`).
16. **RBAC**: `operations:update` (`PUT`), `corrections:correct` (corrección), `operations:create` (`cancel`): **sin cambio**; ningún permiso nuevo; nada por nombre de rol.
17. **Actor global**: sin empresa efectiva → `400 BR-07` (fail-closed, `R-139`); situado en A → no mueve a B (`AC-W09`); en unidad apagada de A → `403`.
18. **Administrador de Accesos**: `403` (RBAC) en los tres caminos, cero filas.
19. **Contraloría** (lectura): `403`, cero filas.
20. **Auditoría**: `PUT` audita `UPDATED` con `previous_values`/`new_values` de los campos cambiados (`docs/13 §2`; columnas existentes de `audit_logs`); corrección: `CORRECTED` con campo/valor anterior/valor nuevo (hoy); `cancel` confirmado: `CANCELLED` (hoy). Denegaciones: sin auditoría de éxito.
21. **`R-130`**: intacto; se reutilizan `validate_bird_decrement`/`validate_mortality`/`validate_chick_dispatch` y `bloquear_saldo_del_lote`; `AC-R130-07` (cancelar un descarte devuelve el saldo) sigue.
22. **`R-161`**: intacto; `validate_egg_dispatch`/`validate_incubation_load` con el bloqueo; el predicado de tipo lo fija `GA-REM-005-F`.
23. **`R-140`** (residual): el `cancel` sigue sin motivo obligatorio y con `operations:create`; solo se añade la guarda de saldo y el bloqueo. No se cierra por transitividad.
24. **`R-154`** (residual): `DRAFT` sigue editable y cancelable; `version` avanza como hoy; nada de cierres.
25. **`R-136` / reverso**: `CANCELLED ≠ REVERSED`; el original `REVERSED` no se cancela ni edita; la contrapartida no se edita ni corrige; cancelar una contrapartida pendiente no cambia saldos (`_suma_neta` solo resta las `REVERSED`). Sin cambio.
26. **AC**: §E.4.
27. **Rojo**: `tests/test_edit_cancel_balance.py` (prefijo `MUTA-`): `AC-R173-02/04/05/08/09/11/12/13/14` rojas en `4f70273` por el defecto exacto (efecto movido/saldo negativo/reasignación sin control); `AC-R173-01/03/06/07/15/17` controles; `AC-R174-01` roja (evento de 0 persistido).
28. **Sensibilidad**: §E.6.
29. **Regresión**: `R-130` (21) · `R-161` (7) · `R-170`/`B13` · `B01` · `B02` · `B05` · reversos · `R-135`/`R-143` (estado, correcciones) · `R-159`/`R-160` · `R-162`/`R-163` · `R-139` · `R-165` · `OD-14`/`OD-16` · `test_clean_baseline` · `test_time_determinism` · regresión completa leída.
30. **Cierre**: `R-173` CERRADO (técnico) y `R-174` CERRADO (técnico) solo con evidencia; certificación de proceso sigue `BLOCKED_RUNTIME`.

## E.3 `R-174` · el despacho de pollitos es un decremento de `B.2`

`B.2` incluye «despacho de pollitos» en `D` y exige `cantidad(D) > 0`; `validate_chick_dispatch` ya lo rechaza con `BR-04`; la rama `CHICK_DISPATCH`
de `_apply_business_rules` lo esquiva con `if total_qty > 0`. Fila que `B.3` no listaba y ahora lista:

| Situación | Antes | Después |
|---|---|---|
| despacho de pollitos = 0 | **`201`** (fila, movimiento de 0, auditoría, notificación, cola de revisión) | `400 BR-04` «La cantidad de pollitos debe ser mayor a cero» · sin fila · sin auditoría de alta · sin notificación · viables intactos |
| despacho de pollitos < 0 | `422` (esquema) | `422` (sin cambio; se registra el código real en la prueba) |

Cambio: retirar la guarda, como hizo la enmienda D para `egg_dispatch`/`incubation_load`. Sin validador nuevo, sin frontend, sin migración.

## E.4 Criterios de aceptación

| AC | Criterio | Verdad final exigida |
|---|---|---|
| `AC-R173-01` | control: `PUT` con `bird_movements` → `422`; corrección de `bird_movements` → `400` «no es corregible»; saldo intacto | filas y saldo iguales |
| `AC-R173-02` | salida creada en A (con saldo) movida a B **sin saldo suficiente** → `400 BR-01` (mortalidad/descarte/salida), `BR-04` (despacho de pollitos), `BR-02` (despacho de huevos), `BR-03` (carga); `lot_id` sigue A | `saldo(A)` y `saldo(B)` iguales a los previos, evento en A, `version` igual |
| `AC-R173-03` | salida movida a B **con** saldo → `200`; `saldo(A)` sube `n`, `saldo(B)` baja `n`; auditoría `UPDATED` con `previous_values.lot_id = A`, `new_values.lot_id = B` | verdad final exacta en A y B |
| `AC-R173-04` | entrada movida cuyo origen quedaría `< 0` → `400` (regla de la familia), evento en A · entrada movida con origen suficiente → `200`, A baja `n`, B sube `n` | ambos casos, cuatro familias donde aplique |
| `AC-R173-05` | cancelar una entrada tras salidas que dejarían `< 0` → `400` (`BR-01` recepción · `BR-04` nacimiento con despachos · `BR-02` recolección · `BR-03` recepción en incubadora); estado intacto; sin auditoría `CANCELLED` | saldo igual al previo |
| `AC-R173-06` | cancelar una entrada con saldo suficiente → `200`, saldo exacto; cancelar una salida → `200`, saldo restaurado (`AC-R130-07`) | verdad final |
| `AC-R173-07` | segunda cancelación → `400`; saldo y estado iguales | sin segundo efecto |
| `AC-R173-08` | carrera: recepción de 100 en A; `asyncio.gather` de `cancel` + cinco salidas de 20 → resultado serializado: `saldo(A) ≥ 0` y `= Σ entradas vigentes − Σ salidas vigentes`; nunca recepción cancelada **y** salidas confirmadas que la excedan | verdad final, tres lotes frescos |
| `AC-R173-09` | carrera: recepción de 100 en A; `gather` de `PUT lot_id → B` + salida de 100 en A → a lo sumo una confirma; `saldo(A) ≥ 0`, `saldo(B) ≥ 0` | verdad final |
| `AC-R173-10` | la auditoría de la edición conserva valor anterior y nuevo de cada campo cambiado | dentro de `_03` |
| `AC-R173-11` | corrección de `lot_id` a lote de **otra empresa** → `400 BR-07`; evento en A; saldos de B intactos | tenant |
| `AC-R173-12` | corrección de `lot_id` a lote de unidad **apagada** → `403`; a unidad **sin concesión** del actor → `400 BR-07`; evento intacto | unidad |
| `AC-R173-13` | corrección de `lot_id` a destino sin saldo → `400 BR-0x`; a lote inactivo → `400 BR-07`; a fecha anterior al lote → `400` | destino como alta |
| `AC-R173-14` | corrección de `farm_id` (o `house_id`) a ubicación de otra empresa → `400 BR-07` | ubicación |
| `AC-R173-15` | `PUT` de `lot_id` a otra empresa / unidad apagada / sin concesión → `400 BR-07` / `403` / `400 BR-07` (`AC-W09`, `test_operations_bu_enforcement`) | regresión |
| `AC-R173-16` | toda denegación: cero cambios en `operational_events`, cero auditoría de éxito, cero notificaciones nuevas | en cada prueba |
| `AC-R173-17` | evento sin efecto en saldo (p. ej. `feed_registration`) cambia de lote como hoy (`200`) | control |
| `AC-R173-18` | regresión §E.2.29 verde | — |
| `AC-R174-01` | `chick_dispatch` de 0 → `400 BR-04`; **cero** filas en `operational_events`/`bird_movements`; sin auditoría `created`; sin notificación; viables intactos | fila ausente |
| `AC-R174-02` | cantidad negativa → denegada (código real del esquema, registrado) | control |
| `AC-R174-03` | despacho de 1 con viables suficientes → `201` | control |
| `AC-R174-04` | despacho del resto exacto → `201`, viables 0 | control |
| `AC-R174-05` | resto + 1 → `400 BR-04`, sin fila | control |

## E.5 Tareas

| Tarea | Descripción |
|---|---|
| `T-005-E1` | pruebas rojas `tests/test_edit_cancel_balance.py` (escenario propio: empresas A/B; en A `breeder` ON, `hatchery` ON, `broiler` OFF; en B `breeder` ON; operador con `operations:create/read/update` + `corrections:correct` en `breeder` + `hatchery`; `operador_r` solo `breeder`; sin permiso; Administrador de Accesos; Contraloría; actor B; global; lotes `lr`/`lr2`/`lr3` breeder A, `lh`/`lh2` hatchery A, `lbo` broiler A (unidad apagada), `lc` breeder A inactivo, `lb` breeder B; fechas por `tests.time_reference`) |
| `T-005-E2` | `operations/service.py`: guarda central `verificar_destino_de_edicion(event, cambios)` (cadena §E.2.9 + bloqueos §E.2.10-11 + reglas §E.2.7-8), usada por `update_event`; `cancel_event` con bloqueo, relectura y regla §E.2.6; auditoría con `previous_values`/`new_values` |
| `T-005-E3` | `corrections/service.py`: `lot_id`, `farm_id`, `house_id`, `destination_farm_id` pasan por la misma guarda antes de `setattr` |
| `T-005-E4` | `operations/service.py`: rama `CHICK_DISPATCH` sin `if total_qty > 0` (`R-174`) |
| `T-005-E5` | sensibilidad §E.6 con el driver atómico; regresión §E.2.29; evidencia; cierre |

## E.6 Sensibilidad

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| `R173-S1` | la regla de saldo del destino (salidas) en la guarda | `AC-R173-02` (mover a B sin saldo → `200`, `saldo(B) < 0`) |
| `R173-S2` | el bloqueo del lote en `cancel` (y la relectura) | `AC-R173-08` (recepción cancelada y salidas confirmadas: saldo `< 0`) — si el tiempo no lo manifiesta, se documenta como no observable y no se acredita |
| `R173-S3` | el invariante del origen en la cancelación de entradas | `AC-R173-05` (cancel → `200`, saldo `< 0`) |
| `R173-S4` | la relectura del estado bajo el bloqueo en `cancel` | `AC-R173-07`/`08` si se manifiesta; si el estado ya impide la doble transición sin relectura, **N/A con evidencia** |
| `R173-S5` | la cadena de inquilino/unidad de la corrección de `lot_id` (las capas necesarias para que el movimiento **ocurra**: `validate_lot_active`, `exigir_unidad_operativa`; protocolo del tranche 4) | `AC-R173-11`/`12` (evento movido a lote de B / unidad apagada) |
| `R174-S1` | restaurar `if total_qty > 0` | `AC-R174-01` (fila de 0 persistida) |

## E.7 Definición de terminado

`AC-R173-01…18` y `AC-R174-01…05` verdes · rojo válido leído en `4f70273` · sensibilidad válida (N/A solo con evidencia) · regresión §E.2.29 ·
guardianes exactos (rutas 211, cabeza `x4y5z6a7b8c9`, sin migración) · `test_clean_baseline` (N/A por cambio, ejecutada) · `test_time_determinism` ·
`R-175`: control de orden documentado (`R175_TEST_ORDER_DEPENDENCY_CONTROL.md`) · regresión completa **leída** · `R-173` y `R-174` cerrados (técnico) ·
certificación de proceso `BLOCKED_RUNTIME`.

---

# ENMIENDA F · `R-172` — QUÉ CUENTA COMO DISPONIBLE EN `BR-02` Y `BR-03`: EL HUEVO FÉRTIL (2026-09-10 · WAVE B · tranche 10)

| Campo | Valor |
|---|---|
| **Enmienda** | `GA-REM-005-F` · `DATA INTEGRITY` (semántica del saldo) · **Estado** **`CERTIFIED`** (frontera técnica, 2026-09-10) · evidencia `WAVE_B_TRANCHE_10_BALANCE_INTEGRITY_EVIDENCE.md` · commits `c56b2de` · `64dff76` |
| **Hallazgo** | `R-172` (P2): `get_egg_balance` y `get_hatchery_egg_balance` suman **todas** las `egg_type`; las fuentes de nivel 2-4 despachan y reciben en la incubadora **huevos fértiles** → sobrecontabilización (recolección `fertile 100 + dirty 50 + broken 10` admite despachar 160) |
| **Matriz** | `audit/remediation/R172_EGG_TYPE_AVAILABILITY_MATRIX.md` (tipos × `BR-02`/`BR-03`; ecuaciones; corte por niveles) · `RC-14` / `RR-17` |
| **Fuentes** | `Bases` p.7-8 («Traslado de huevos fértiles»), p.9 («Número de Huevos Recibidos: Cantidad de huevos fértiles recibidos») · `docs/02 §3.6.4` (despacho a incubadora) · `§3.7.1` («recepción de huevos fértiles») · `§7 R2` · `spec.md :166/:176/:187` · `D.1` |
| **Sin cambio** | bloqueo y orden de `D.1` (`R-161`) · filas capturadas (ninguna se borra ni reescribe) · `egg_collection`, `egg_classification`, `egg_reception_classification` (informativos; aceptan todos los tipos) · `egg_reception_hatchery` acepta filas no fértiles (diferencias vs enviado) que **no** cuentan · KPI (ola C) · `R-177` (enum/formulario de recepción) |
| **Migración** | ninguna |

## F.1 Contrato

1. **Predicado único**: `cuenta_como_disponible(egg_type) := egg_type == "fertile"` (`operations/validators.py`), usado por `BR-02` y `BR-03`. Un solo sitio; ninguna lista blanca/negra por intuición: solo el tipo que las fuentes nombran.
2. **`BR-02`** = Σ `egg_movements.quantity` de `egg_collection` **disponibles** − Σ `egg_movements.quantity` de `egg_dispatch` **disponibles** (por lote, `≠ CANCELLED`).
3. **`BR-03`** = Σ `egg_movements.quantity` de `egg_reception_hatchery` **disponibles** − Σ `hatchery_params.quantity_loaded` de `incubation_load` (por lote, `≠ CANCELLED`).
4. **Despacho**: toda fila de `egg_dispatch` con tipo no disponible → `400 BR-02` «El despacho a incubadora es de huevo fértil»; sin fila, sin auditoría de alta. La cantidad validada contra `BR-02` es la suma de las filas (todas fértiles).
5. **Captura**: `egg_collection`, `egg_classification`, `egg_reception_classification`, `egg_reception_hatchery` siguen aceptando cualquier tipo; las filas no disponibles se persisten y **no** cuentan (`CAPTURADO ≠ DISPONIBLE`). Datos históricos: intactos; el saldo se recalcula con el predicado (las filas no fértiles dejan de inflarlo).
6. **`R-161`**: mismo bloqueo, mismo orden; cambia **qué** se suma bajo el bloqueo. `R-173` (enmienda E) deriva `n` con el mismo predicado.
7. **Frontend** (vertical mínima): el formulario de `egg_dispatch` ofrece **solo** la fila «Fértiles» (`operations.fertile`); recolección/clasificación/recepción conservan sus filas. Contrato estático `vitest`.
8. **Seguridad, auditoría, API**: sin cambio (`400 {detail, rule}`).

## F.2 Criterios de aceptación

| AC | Criterio |
|---|---|
| `AC-R172-01` | recolección `fertile 100` → `BR-02` = 100; despacho 100 → `201`; 1 más → `400 BR-02` |
| `AC-R172-02` | recolección mixta `fertile 100 + dirty 50 + broken 10 + infertile 5 + discarded 5` → `BR-02` = **100**; despacho 101 → `400 BR-02`; 100 → `201`; saldo 0 |
| `AC-R172-03` | cada tipo no disponible por separado (`dirty`, `broken`, `infertile`, `discarded`, `commercial`), recolección de 50 → `BR-02` = 0; despacho de 1 → `400 BR-02` |
| `AC-R172-04` | despacho con una fila `dirty` (junto a una fértil dentro del saldo) → `400 BR-02`, sin fila, sin auditoría de alta |
| `AC-R172-05` | tras `AC-R172-02`, `egg_movements` conserva las filas no fértiles (nada se borra) |
| `AC-R172-06` | recepción en incubadora `fertile 100 + broken 5 + contaminated 3` → `BR-03` = 100; carga 101 → `400 BR-03`; 100 → `201`; saldo 0 |
| `AC-R172-07` | `AC-R161-05/06/07` verdes (carreras; bloqueo intacto) |
| `AC-R172-08` | contrato estático: el `case 'egg_dispatch'` registra solo `egg_movements.0.egg_type = fertile`; el `case 'egg_collection'` conserva `fertile, dirty, broken, infertile, discarded` |

## F.3 Tareas

| Tarea | Descripción |
|---|---|
| `T-005-F1` | pruebas rojas `tests/test_egg_type_availability.py` (prefijo `TIPO-`; escenario propio mínimo: empresa A con `breeder` + `hatchery`; operador; lotes `lr` (breeder) y `lh` (hatchery)) + `frontend/src/pages/operations/__tests__/eggDispatchFormContract.test.ts` |
| `T-005-F2` | `validators.py`: `TIPO_DISPONIBLE = "fertile"`, `cuenta_como_disponible`, predicado en `get_egg_balance` (entrada y salida) y `get_hatchery_egg_balance` (entrada); `validate_egg_dispatch_types(egg_types)` |
| `T-005-F3` | `service.py`: rama `EGG_DISPATCH` valida los tipos antes de la cantidad |
| `T-005-F4` | `OperationFormPage.tsx`: `case 'egg_dispatch'` con una sola fila (`fertile`) |
| `T-005-F5` | sensibilidad §F.4; regresión `R-161` + `R-173`; evidencia; cierre |

## F.4 Sensibilidad

| Mutación | Qué quita | Prueba que debe caer |
|---|---|---|
| `R172-S1` | el predicado en `get_egg_balance` (vuelven a contar todos los tipos) | `AC-R172-02`/`03` (despacho de 101/1 → `201`) |
| `R172-S2` | `fertile` del predicado (nada cuenta) | `AC-R172-01` (despacho de 100 → `400`) |
| `R172-S3` | la validación de tipos del despacho | `AC-R172-04` (fila `dirty` → `201`) |
| `R172-S4` | el predicado en `get_hatchery_egg_balance` | `AC-R172-06` (carga 101 → `201`) |
| `R172-S5` | la fila única del formulario de despacho (frontend) | `AC-R172-08` |

## F.5 Definición de terminado

`AC-R172-01…08` verdes · rojo válido leído en `4f70273` (despacho de 160 sobre 100 fértiles aceptado) · sensibilidad válida · `R-161` 7/7 · `R-173`
(enmienda E) verde con el predicado · KPI de incubadora (`test_kpi_hatchery`) verde · regresión completa leída · `R-172` CERRADO (técnico).
