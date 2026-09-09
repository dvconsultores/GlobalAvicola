# PRE-FLIGHT · `R-136` — REVERSO INTERNO / `BR-16` · WAVE B tranche 5 (2026-09-09) · base `db11215`

**Resultado del pre-flight: STOP.** El reverso interno **no está gobernado** por ninguna fuente del repositorio con la
precisión que exige implementarlo; su semántica es una decisión de propietario (`AOD-21`, abajo). No se escribe código.
`R-136` sigue **OPEN · P1**, con dos componentes: interno → `OWNER_DECISION_REQUIRED`; post-SAP → `SAP_DEFERRED`.

## 1. Entrada

| Ítem | Valor |
|---|---|
| Rama · HEAD · remoto | `main` · `db11215` · `db11215` (`git ls-remote` verificado) · árbol limpio · `origin` https intacto |
| Alembic | `s9t0u1v2w3x4` |
| Recuento de la ola B (releído del backlog y de `WAVE_B §10`) | **22** · cerrados 7 · parciales 2 · abiertos 13 · P1 abiertos 2 (`R-136`, `GA-REM-021`) · P2 8 (+1 parcial) · P3 3 (+1 parcial) · bloqueados 3 (+`R-136` post-SAP) · decisiones 6 → **7 con `AOD-21`** · `R-164` `BLOCKED_RUNTIME` (no se intentó la base remota: no forma parte del flujo disponible) — **consistente, sin corrección** |

## 2. `R-136` exacto (no desde memoria)

| Campo | Valor |
|---|---|
| Título oficial | «tabla `reversals` sin servicio ni ruta; `BR-16` sin mecanismo» |
| Severidad | **P1 (SAP)** |
| Fuente | `H360-P05` (`MASTER_PROGRAM_STATUS_RECONCILIATION §STATE 5`; `OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX §5`) · `BR-16` · Rec. §24 «Reverso: cómo se anula» · `docs/16 G-R09` |
| Clase | `CORRECTION_REVERSAL` · `MODEL DEFECT` («modelo huérfano»: `Reversal`, `operations/models.py`, 0 usos fuera del modelo; `GA-TD-028`) |
| Procesos | `P-07` (revisión/aprobación) · `P-08` (SAP) |
| Spec | «spec propia» — **no existe** |
| Ola | B (modelo) · D (SAP) |

### 2.1 Qué dice cada fuente sobre el reverso (textual o parafraseado con precisión)

| Fuente | Dice | No dice |
|---|---|---|
| `spec.md §5 BR-16` | «Ajustes **post-SAP** requieren reverso, corrección auditada o nuevo movimiento autorizado» | qué es un reverso, quién lo hace, desde qué estado, qué efecto produce |
| `docs/02 §5 R16` | ídem (módulo **SAP**) | ídem |
| `docs/02 §4` · `docs/12 §2/§4` fila 13 | «Anulado (con auditoría)»: solo administrador, requiere motivo; alcanzable desde **Borrador** y **Registrado** | anulación de un **aprobado**; reverso |
| `docs/13 §` auditoría | «Anulación: usuario, fecha/hora, motivo, registro completo» | reverso |
| `OD-17.a` | clase **terminal** = `CANCELLED`, **reverso (`BR-16`)**, cierre final; «no vuelve al flujo; solo por reverso o nuevo movimiento autorizado» · §5: «no cambia `CANCELLED` ni el reverso (`H360-P04`, `H360-P05`)» | la semántica del reverso: la **nombra** como distinta de `CANCELLED` |
| Rec. central 7.17 (vía `docs/16`) | «Corrección sobre aprobado sin versión/reverso» → `BR-15/BR-16` · «Cancel existe, reverso no» | el contrato |
| `docs/16 §8` | estado recomendado `ANULADO/REVERSADO` ↔ `CANCELLED` (**parcial**): «no hay REVERSADO con registro compensatorio» | — |
| `docs/16 G-R09` | «Sin reverso verdadero: cancel existe pero no hay **contrapartida**» → «mecanismo de reverso con registro compensatorio» | forma de la contrapartida |
| Rec. §24 «Reverso: cómo se anula» | **PDF fuente no versionado en el repositorio** (`docs/16` es su análisis) | — |
| `Reversal` (modelo) | `original_event_id` · `reversal_event_id` (evento compensatorio, **nulable**) · `company_id` · **`reason` NOT NULL** · `reversed_by_id` · `original_data_snapshot` · `reversal_data` · docstring «reversal of an approved/**sent** event» | estado del original tras el reverso; permiso; si el compensatorio pasa por aprobación |
| `WAVE_B §1` fila 8 (pre-flight del tranche 1) | «el reverso **interno** (post-aprobación, pre-SAP) lo gobiernan `BR-16` y `docs/12 R5`» | **verificado aquí: no lo gobiernan** — `BR-16`/`R16` son post-SAP y `R5` («enviado a SAP no se edita») no define ningún reverso. La afirmación se corrige (§5) |

## 3. Vocabulario (mapeado a los nombres del repositorio; nada se renombra)

| Concepto | Nombre en el repo | Qué es | ≠ |
|---|---|---|---|
| CORRECTION | `POST /corrections` → `CORRECTED` (`RR-01`) | cambiar un valor de un registro **no finalizado**, original conservado | REVERSAL |
| CANCELLATION / ANNULMENT | `POST …/cancel` → `CANCELLED` (`docs/12` fila 13) | detener un registro **antes** de que haya efecto aceptado; terminal; excluido de saldos | REVERSAL (el aprobado no se cancela: `NO_CANCELABLES`, tranche 4) |
| REJECTION | `approvals/reject` → `REJECTED` | devolución interna, **viva** (`OD-17.a`) | REVERSAL |
| RETURNED | `review/return` → `RETURNED` | observado, **vivo**, corregible y reenviable | REVERSED |
| INTERNAL REVERSAL | **no existe** (`Reversal` huérfano; sin estado `REVERSED` en `EventStatus`) | neutralizar el efecto de un registro **aceptado** (aprobado, pre-SAP) con contrapartida y traza | SAP DOCUMENT REVERSAL |
| SAP DOCUMENT REVERSAL | **no existe** (`OD-17.c`, `GA-REM-017` `BLOCKED_EXTERNAL`) | anular un documento ya contabilizado en SAP (documento de reverso) | interno |

## 4. Descomposición

| Componente `R-136` | INTERNO / SAP | Requisito | Estado actual | ¿Ejecutable ahora? | Bloqueo | ¿Seleccionado? |
|---|---|---|---|---|---|---|
| Reverso de un registro **aprobado** aún no enviado (pre-SAP) con contrapartida | INTERNO | Rec. 7.17 · `G-R09` · `OD-17.a` (existe como clase terminal) | sin servicio, sin ruta, sin estado, sin permiso, sin AC | **NO** | semántica no definida (§5) → **`AOD-21`** | **no** (STOP) |
| Reverso de un registro **consolidado** (pre-envío) | INTERNO | `docs/12 R8` (consolidación atómica por lote) | ídem | **NO** | además exige des-consolidar el lote (R8) → parte de `AOD-21` | no |
| Reverso de un documento **enviado/confirmado** por SAP | SAP | `BR-16` · `R16` · `R5` · `OD-17.c` | `Reversal.reversal_event_id` previsto; sin conector | **NO** | `GA-REM-017` `BLOCKED_EXTERNAL` · `AOD-04`/`OD-12` · `P-08` | no (**`SAP_DEFERRED`**) |

## 5. Por qué el reverso interno exige decisión (lo que ninguna fuente resuelve)

1. **Vocabulario de estado.** No hay `REVERSED` en `EventStatus`. `docs/16 §8` mapea `ANULADO/REVERSADO` a `CANCELLED` (parcial); `OD-17.a` los distingue. Reusar `CANCELLED` para un aprobado contradice `docs/12 §2` (Anulado solo desde Borrador/Registrado) y el mapa certificado en el tranche 4 (`NO_CANCELABLES`); añadir `REVERSED` es cambio de vocabulario + migración. El programa ya calificó esta clase como decisión de propietario (`R-142` → `AOD-17`).
2. **Forma de la contrapartida.** En esta arquitectura el efecto de negocio es **derivado**: los saldos suman las filas no `CANCELLED` (`get_current_bird_balance`, `get_egg_balance`, `get_hatchery_egg_balance`, `get_viable_chick_balance`), los KPI cuentan `APPROVED`+; no hay libro materializado. «Registro compensatorio» puede ser (a) excluir el original del conjunto (estado terminal) con fila `Reversal`, (b) un evento inverso que pase por el flujo (`R13`: nada llega a SAP sin aprobación), (c) ambas. La opción define el modelo de datos, la aprobación y el payload SAP futuro (`AOD-04`).
3. **Autoridad.** `docs/12` fila 13 («solo administrador») es la misma clase pendiente de `AOD-18`; ningún permiso existente nombra el reverso. Separación de actores (¿el aprobador reversa su aprobación?): no especificada.
4. **Estados elegibles.** `APPROVED` sí por Rec. 7.17; `CONSOLIDATED` choca con `R8`; `SENT_TO_SAP`+ es SAP.
5. **Motivo.** `Reversal.reason` es NOT NULL y `docs/13` exige motivo en la anulación: es lo único que las fuentes fijan.

Con 1-4 abiertos, cualquier implementación sería **decidir por el propietario** (`NO DECIDIR POR EL PROPIETARIO`)
o **inventar** (`NO SPEC = NO DEVELOPMENT`). Encargo §21/§111: «si `R-136` interno exige semántica de negocio no
resuelta: STOP tras el pre-flight».

## 6. `R-165` — evaluación (no ejecutada en este tranche)

| Pregunta | Respuesta |
|---|---|
| Rutas · método | `POST /review/start/{id}` · `POST /review/return` · `POST /review/complete` · `POST /approvals/approve` · `POST /approvals/reject` (+ `batch-*`) |
| Servicio | `review/service.py` (`ReviewService`, `ApprovalService`): `_get_event`/`_get_event_for_approval` con `_ambito_de_unidad()` → `[]` para `is_super_admin` |
| Transición | `PENDING_REVIEW→IN_REVIEW`, `IN_REVIEW→RETURNED/APPROVED/CORRECTED`, `CORRECTED/IN_REVIEW→APPROVED/REJECTED` |
| Clase de superficie | **`PRODUCTIVE_REVIEW`** (mutación de estado de dato productivo de inquilino): `OD-14.c` «dato productivo = INQUILINO»; no es `CONTROL_GLOBAL` |
| Semántica del actor | actor de empresa: ya acotado por `unidades_efectivas` (apagada → fuera) · autoridad global: exenta de concesión (certificado) y **hoy también de la habilitación** (defecto) |
| Guarda compartida | la misma que `operations`/`lots`/`corrections`: `business_units.service.exigir_unidad_operativa` (`G.3`/`H.5`), una línea por método tras resolver el evento |
| ¿Mismo camino que `R-136`? | **no hay camino de `R-136`** (no existe el reverso); comparte **primitivo** (guarda de habilitación) con las enmiendas G/H, no con `R-136` |
| ¿Decisión pendiente? | **no** (`OD-16.e/f`, aclaración H.2) |
| ¿Incluible? | técnicamente sí, como tranche propio o acompañante de uno ejecutable; **no** como forma admitida de este tranche (encargo §21: solo A `R-136` o B `R-136 + R-165`; `R-136` detiene) → **`R-165` sigue OPEN**, listo para su propio pre-flight (`GA-REM-040` enmienda I) |

## 7. Puerta de composición (encargo §21)

```
R-136 interno ejecutable ............... NO  (semántica no gobernada: §5)
R-136 depende de decisión no resuelta .. SÍ  (AOD-21, nueva; y AOD-18 para «solo administrador»)
R-136 depende de SAP ................... interno NO · post-SAP SÍ (SAP_DEFERRED)
R-165 misma raíz/camino ................ NO  (comparte guarda con G/H, no con R-136)
R-165 incluible con seguridad .......... SÍ, pero no en una forma admitida sin R-136
FORMA DEL TRANCHE ...................... NINGUNA → STOP tras el pre-flight
```

## 8. Lo que este pre-flight deja hecho

- `AOD-21` registrada (opciones sin preferencia) en `AUDIT_OWNER_DECISIONS_REQUIRED.md`.
- `R136_INTERNAL_REVERSAL_EFFECT_MATRIX.md`: inventario de efectos **derivables del código** (qué cuenta cada evento y dónde), con las columnas de acción de reverso marcadas `OWNER_DECISION_REQUIRED`, para que la decisión se tome sobre hechos.
- Corrección de la afirmación del pre-flight del tranche 1 («lo gobiernan `BR-16` y `docs/12 R5`»).
- `R-136`: OPEN · P1 · interno `OWNER_DECISION_REQUIRED (AOD-21)` · post-SAP `SAP_DEFERRED`. `R-165`: OPEN · P2 · ejecutable.
- Sin código, sin migración, sin pruebas nuevas, sin cambio de frontend. Nada certificado.

## 9. Siguiente tranche (identificado, NO iniciado)

Releída `WAVE_B §3`: con `R-136` detenido, el siguiente ejecutable de mayor prioridad y verdad de negocio es
**`GA-REM-021` — captura exigida por el cliente: agua (`B05`)** (P1, `SPEC_READY`; `B01` desbloqueado por `R-130`;
`B04` fuera hasta `AOD-14`). Acompañante de coste mínimo posible: **`R-165`** (una línea por método con la guarda
compartida + pruebas). `R-164` sigue a la espera de acceso a la base configurada.
