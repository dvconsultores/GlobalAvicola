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
