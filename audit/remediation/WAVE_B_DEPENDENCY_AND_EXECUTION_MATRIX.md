# MATRIZ DE DEPENDENCIAS Y EJECUCIÓN — WAVE B

**Pre-flight** · 2026-09-09 · base `874a4af` (`main` · limpio · local == remoto · Alembic `s9t0u1v2w3x4`)
· backend 830/49/0 · vitest 87/87 · `tsc` 6 preexistentes (`R-158`) · E2E `BLOCKED_RUNTIME` · `BU-D10 PENDING_RATIFICATION`

Fuentes leídas desde el repositorio: `REMEDIATION_BACKLOG.md` (alta 2026-09-09, cierres `R-127`/`R-139`),
`INDEX.md` (asignación por olas), `MASTER_REMEDIATION_MATRIX.md`, `DEPENDENCY_MAP.md`,
`WAVE_A_CLOSURE_REPORT.md`, `H360_AND_ADDENDUM_TO_OFFICIAL_BACKLOG_RECONCILIATION.md`,
`OPERATIONAL_PROCESS_STATE_AND_CLOSURE_MATRIX.md`, `GLOBAL_AVICOLA_REQUIREMENT_COMPLETENESS_360.md`,
`GA-REM-005` (regla de balance, enmienda `R-67`), `GA-REM-021`, `OD-14…OD-18`, `GA-REM-040`,
código de `operations/service.py`, `operations/validators.py`, `corrections/service.py`, `review/service.py`.

Clases (una primaria): `DATA_INTEGRITY` · `PROCESS_CONTINUITY` · `STATE_MACHINE` ·
`CORRECTION_REVERSAL` · `REQUIRED_OPERATIONAL_DATA` · `BUSINESS_RULE` · `TRACEABILITY` ·
`BUSINESS_UNIT_SCOPE` · `CERTIFICATION_GAP` · `P2_TECHNICAL` · `OWNER_DECISION_REQUIRED` ·
`DUPLICATE_EXISTING_ROOT_CAUSE` · `NOT_WAVE_B`.

## 1. Inventario y clasificación

| Orden | ID | Título | Sev. | Origen | Proceso | Clase | Causa raíz | Spec | Decisión | Dependencias | ¿Ejecutable ya? | Bloqueo | Mismo tranche con | Ola / tranche |
|:--:|---|---|:--:|---|---|---|---|---|---|---|:--:|---|---|---|
| **1** | **`R-130`** | descarte, salida y despacho de pollitos no validan contra el saldo de aves; cantidades cero admitidas; sin protección frente a decrementos concurrentes | **P1** | `H360-P01` | `P-01` `P-03` `P-05` `P-06` `P-11` (población) | **`DATA_INTEGRITY`** | `_apply_business_rules` solo valida `mortality_recording` (`BR-01`) y `chick_dispatch` contra un «viable» que ignora mortalidad y descartes; `cull_recording` y `bird_exit` no tienen rama; `BirdMovementSchema.quantity ge=0`; ningún bloqueo de fila al leer el saldo | `GA-REM-005` (regla `E.3`: salidas = mortalidad · descarte · salida · despacho) → **enmienda B** | **no** | ninguna (`OD-14`/`OD-16` intactas; `RR-02` neutros; `R-67` apertura) | **sí** | — | — (invariante único) | **B · tranche 1** |
| 2 | **`R-160`** *(nuevo, pre-flight)* | la **creación** y edición de eventos operativos no exigen que la unidad del lote esté concedida al actor ni habilitada para la empresa: `POST /operations` solo pasa `require_permission` + `validate_lot_active` (empresa); `exigir_acceso_a_unidad` no tiene llamadores en `app/` | **P1** | pre-flight ola B (`GA-REM-040 AC-B02`, `AC-A05` en escritura) | todos los `P-0x` | **`BUSINESS_UNIT_SCOPE`** | fase 3 acotó listados, detalle y mutación de **lotes**; la mutación de **eventos** quedó fuera (`GA_REM_040_PHASE_3_EVIDENCE.md:136-137` prueba `PUT /lots`, no `POST /operations`) | `GA-REM-040` → enmienda | **no** (semántica ya decidida: `OD-09`, `OD-16.f`) | `R-130` no depende de ella; comparte `_apply_business_rules` | sí | — | `R-159` (misma raíz: superficies de `operations` sin predicado de unidad) | **B · tranche 2** |
| 3 | `R-159` | `get_alerts` sin predicado de unidad para actores de empresa | P2 | `R-139` (fuera de alcance) | `P-14` | `BUSINESS_UNIT_SCOPE` | fase 3 dejó `operational_alerts` «parcial» (`:38`) | `GA-REM-040` enm. | no | — | sí | — | `R-160` | B · tranche 2 |
| 4 | **`R-135`** | `RETURNED` no se reenvía; `REJECTED` terminal | **P1** | `H360-P03` | `P-07` | **`STATE_MACHINE`** | `submit` solo desde `REGISTERED`; `REJECTED` no corregible | `GA-REM-006` enm. + `spec §4.10` | **`OD-17` ✓** | comparte `review/corrections` con `R-142`, `R-143`, `R-140` | sí | — | `R-143` (`docs/12 R2`, misma máquina de estados y mismo servicio) · `R-142` si se resuelve su conflicto | B · tranche 3 |
| 5 | `R-143` | `docs/12 R2` (quien corrige no aprueba) no implementada | P2 | `H360-P10` | `P-07` | `BUSINESS_RULE` | `_exigir_segregacion` compara solo con `registered_by_id` | `GA-REM-007` enm. | no (`RC-03`: configurable) | `correction_logs.corrected_by_id` existe | sí | — | `R-135` | B · tranche 3 |
| 6 | `R-142` | `CORRECTED` usado como «pendiente de aprobador» sin corrección | P2 | `H360-P06` | `P-07` | `STATE_MACHINE` | `complete_review` con ≥ 2 niveles fija `CORRECTED` | `GA-REM-006` enm. + `docs/12 §4` | **sí** — `docs/12 §4` no tiene estado «revisado, pendiente de aprobador»; añadirlo es cambio de vocabulario de estados (`REQUIREMENT_CONFLICT` → `AOD-17` provisional) | `R-135` | no | decisión | `R-135` cuando se decida | B · tras decisión |
| 7 | `R-140` | `cancel` sin motivo ni restricción de rol; no bloquea `SAP_CONFIRMED`/`SAP_ERROR` | P2 | `H360-P04` | `P-07` | `STATE_MACHINE` | ruta sin cuerpo; permiso `operations:create`; guarda incompleta | `GA-REM-006` enm. | **parcial**: «solo administrador» (`docs/12 §4` fila 13) debe traducirse a un permiso existente sin inventar nombres de rol → `AOD-18` provisional; el motivo obligatorio y la guarda de estados no necesitan decisión | `R-135` (misma máquina) | parcial | decisión sobre el permiso | `R-135` | B · tranche 3 (parte sin decisión) |
| 8 | **`R-136`** | `reversals` sin servicio ni ruta; `BR-16` sin mecanismo | **P1** (SAP) | `H360-P05` | `P-07` · `P-08` | **`CORRECTION_REVERSAL`** | modelo huérfano (`G-R09`) | spec propia | **parcial**: el reverso **interno** (post-aprobación, pre-SAP) lo gobiernan `BR-16` y `docs/12 R5`; el reverso **post-SAP** exige `AOD-04`/`OD-12` y SAP real | `R-135` (estados terminales) | interno: sí · post-SAP: **`SAP_DEFERRED`** | SAP para la mitad | — | B · tranche 4 (interno) · D (SAP) |
| 9 | `GA-REM-021` | consumo de agua (`R-13`) + `H360-B01…B04`, `B13`, `R-156` | **P1** | `Bases` p.2/4/12 · Rec. §6/§8 | `P-01` `P-03` `P-04` `P-05` `P-06` | **`REQUIRED_OPERATIONAL_DATA`** | dato exigido por el cliente sin modelo ni captura | `GA-REM-021` `SPEC_READY` (AC01–AC05) — alcance ampliado pendiente de enmienda | **parcial**: `B04` (evidencia obligatoria) → `AOD-14`; agua, cuadre, pesos en rango, alimento lote/silo, sanos/débiles: no | `R-130` (el cuadre `B01` usa el saldo) | agua: sí (vertical completa exigida por `AC01`/`AC03`: formulario) | `AOD-14` solo para `B04` | — | B · tranche 5 (agua) · 6 (cuadre y resto) |
| 10 | `R-144` | resumen de cierre sin FCR ni peso final | P2 | `H360-P08` | `P-06` | `REQUIRED_OPERATIONAL_DATA` | `close_lot` no calcula FCR | `GA-REM-029` enm. | `AOD-08` (semántica de cierre) | **`R-131`** (FCR correcto, ola C) | **no** | ola C + decisión | — | C (tras `R-131`) |
| 11 | `R-152` | `grandparent_import` sin estructura (`docs/02 §3.4.1`) | P2 | `H360A-02` | `P-01` | `REQUIRED_OPERATIONAL_DATA` | tipo sin esquema propio | spec propia | no (campos enumerados en `docs/02 §3.4.1`) | — | sí | — | `R-153` | B · tranche 7 |
| 12 | `R-153` | lote de abuelas no se crea al completar la importación | P3 | `H360A-03` | `P-01` | `PROCESS_CONTINUITY` | no implementado | spec propia | no | `R-152` | tras `R-152` | — | `R-152` | B · tranche 7 |
| 13 | `R-148` | inmutabilidad de `audit_logs` solo en aplicación | P2 | `H360-D04` | `P-09` | `P2_TECHNICAL` | sin trigger/regla en BD | `GA-REM-032` enm. | no | migración (`§54`) | sí | — | — | B · tranche 8 |
| 14 | `R-147` | constantes y tipos sin fuente: UoM · umbrales T°/H° · `sex` `String` · capacidad de incubadora · roles por nombre en `seed_default_steps` | P2 | `H360-B06/B07/B10/B12/B08` | varios | `P2_TECHNICAL` | valores fijos / tipos laxos | spec propia | **parcial**: UoM y umbrales requieren fuente normativa (`AOD-19` provisional); `sex` enum, capacidad de incubadora (`BR-17` análogo) y roles por nombre no | — | parcial | decisión para 2 de 5 | — | B · tranche 8 (partes sin decisión) |
| 15 | `R-154` | `DRAFT` sin productor · dos «cierres» · `version` no incrementa · `LotStatus.CANCELLED` sin productor | P3 | `H360-P02/P09/P11` | `P-07` `P-06` | `STATE_MACHINE` | estados/campos muertos | `GA-REM-006`/`GA-REM-029` enm. | `AOD-08` (los dos «cierres») | `R-135` | parcial (`version`, `DRAFT`) | decisión para «cierre» | `R-135` | B · tranche 3/9 |
| 16 | `R-156` | peso reportado por el proveedor vs peso en granja | P3 | `H360-B11` (legado, nivel 6) | `P-01` `P-03` | **`OWNER_DECISION_REQUIRED`** | ninguna fuente de nivel 1-4 lo exige | `GA-REM-021` enm. | **sí** (`AOD-20` provisional: ¿se adopta la paridad con la app anterior?) | — | **no** | decisión | — | B · tras decisión |
| — | `R-149` | deriva documental | P2 | `H360-D01…D05` | — | `NOT_WAVE_B` (ola A documental) | — | — | no | — | sí | — | — | A |
| — | `R-131…R-134`, `R-141` | KPI | P1/P2 | `H360-K*` | `P-15` | `NOT_WAVE_B` (ola C) | — | `GA-REM-022` | `AOD-10` | `R-130` (saldo correcto) | — | — | — | C |
| — | `R-137`, `R-138`, `R-145`, `R-155`, `R-157` | SAP | P1(D)/P2 | `H360-S*` | `P-08` | `NOT_WAVE_B` (`SAP_DEFERRED`) | — | `GA-REM-017`/`010` | `AOD-01…05`, `AOD-15` | — | — | SAP | — | D |
| — | `R-146`, `R-150`, `R-151` | frontend | P2 | `H360-S12/F02/F03` | UI | `NOT_WAVE_B` (ola E) | — | `GA-REM-011` | `AOD-16` | fase 9 | — | fase 9 `FROZEN` | — | E |

```
TOTAL WAVE-B ITEMS ............ 16   (14 del backlog + R-159 + R-160 nuevo en este pre-flight)
P1 ............................  5   R-130 · R-160 · R-135 · R-136 · GA-REM-021
P2 ............................  8   R-159 · R-143 · R-142 · R-140 · R-144 · R-152 · R-148 · R-147
P3 ............................  3   R-153 · R-154 · R-156
OWNER_DECISION_REQUIRED ....... 3 totales (R-142 · R-156 · R-144 vía AOD-08) + 3 parciales (R-140 permiso · R-136 post-SAP · GA-REM-021 B04 · R-147 UoM/umbrales)
SAP_DEFERRED ..................  1 parcial (R-136 post-SAP)
CERTIFICATION_GAP .............  0   (la certificación E2E es ola F)
DUPLICADOS / FUSIONADOS .......  0   (R-159 y R-160 comparten raíz y van juntos, sin fusión de IDs)
EJECUTABLES AHORA .............  9   R-130 · R-160 · R-159 · R-135 · R-143 · R-140 (parte) · R-136 (interno) · GA-REM-021 (agua) · R-152 · R-148 · R-147 (parte)
```

## 2. Grafo de dependencias (real, no por número)

```
R-130 (invariante de población)
  ├──► GA-REM-021 B01 (cuadre de recepción usa el saldo)
  ├──► R-144 (resumen de cierre) ──► necesita R-131 (ola C)
  └──► ola C (KPI de mortalidad/viabilidad parten de un saldo correcto)

R-160 + R-159 (alcance de unidad en operations: creación/edición y alertas) — independientes de R-130; misma raíz entre sí

OD-17 ──► R-135 ──► R-143 (misma máquina de estados) ──► R-140 (parte sin decisión) ──► R-136 (reverso interno)
                └──► R-142 (bloqueada: AOD-17)   R-154 (parte: DRAFT/version; «cierres» bloqueado por AOD-08)

R-152 ──► R-153            R-148 (independiente, migración)          R-147 (partes sin decisión, independiente)
R-156 ──► AOD-20           GA-REM-021 B04 ──► AOD-14
```

## 3. Orden de ejecución

| Tranche | Contenido | Por qué en ese orden |
|:--:|---|---|
| **1** | **`R-130`** | única `DATA_INTEGRITY` P1; corrompe la verdad operativa (población negativa, decrementos concurrentes); sin decisión, sin SAP, sin fase 9, sin `BU-D10`; el resto de la ola y la ola C dependen de un saldo correcto |
| 2 | `R-160` + `R-159` | P1 de alcance de unidad en escrituras y alertas; misma raíz; no toca la máquina de estados |
| 3 | `R-135` + `R-143` (+ `R-140` motivo/guarda · `R-154` `DRAFT`/`version`) | máquina de estados de `P-07`, `OD-17` ya decidida |
| 4 | `R-136` (reverso interno) | requiere los estados de 3 estables |
| 5 | `GA-REM-021` agua | dato exigido, vertical completa |
| 6 | `GA-REM-021` cuadre, pesos en rango, alimento, sanos/débiles | usa el saldo (1) |
| 7 | `R-152` → `R-153` | Progenitoras |
| 8 | `R-148`, `R-147` (partes) | técnicas |
| decisión | `R-142` (`AOD-17`) · `R-140` permiso (`AOD-18`) · `R-147` UoM/umbrales (`AOD-19`) · `R-156` (`AOD-20`) · `R-144`/`R-154` cierre (`AOD-08`) · `GA-REM-021 B04` (`AOD-14`) | esperan al propietario |

## 4. Selección del primer tranche

```
PRIMER TRANCHE       R-130 · invariante de población (saldo de aves ≥ 0 en todo decremento)
POR QUÉ PRIMERO      P1 de integridad de datos; el resto se apoya en el saldo; ninguna dependencia abierta
INCLUYE              cull_recording · bird_exit (sin validación) · chick_dispatch (validado contra un «viable»
                     que ignora mortalidad y descartes) · cantidad cero · lectura del saldo sin bloqueo (concurrencia)
EXCLUYE              R-160/R-159 (alcance de unidad: otra raíz) · R-135… (estados) · R-136 (reverso) · GA-REM-021 ·
                     ola C · fase 9 · SAP · BU-D10 · R-158 · saldos de huevos (BR-02/BR-03; se registra R-161)
DECISIÓN PENDIENTE   NO      SAP   NO      FASE 9   NO      BU-D10   NO
SPEC                 GA-REM-005 · enmienda B (la regla de balance E.3 ya nombra las cuatro salidas)
```

Hallazgos nuevos del pre-flight, registrados en el backlog: **`R-160`** (creación/edición de eventos sin
alcance de unidad, P1) y **`R-161`** (los saldos de huevos e incubación —`BR-02`, `BR-03`— se leen sin
bloqueo: la misma carrera que `R-130` cierra para las aves, P2, misma familia, tranche posterior).

## 5. Estado tras el tranche 1 (2026-09-09)

```
TOTAL ......................... 17   (canónico, tranche 2: 14 R del backlog + GA-REM-021 [1 ítem] + R-159 + R-160 + R-161; R-161 es de la ola B desde su alta)
CERRADOS ......................  1   R-130 (técnico; certificación de proceso BLOCKED_RUNTIME)
P1 ABIERTOS ...................  4   R-160 · R-135 · R-136 (interno) · GA-REM-021
P2 ABIERTOS ....................  9   R-159 · R-143 · R-142 · R-140 · R-144 · R-152 · R-148 · R-147 · R-161
P3 ABIERTOS ....................  3   R-153 · R-154 · R-156
BLOQUEADOS .....................  2   R-144 (R-131, ola C) · R-136 post-SAP (SAP_DEFERRED)
DECISIONES DEL PROPIETARIO .....  AOD-17 (R-142) · AOD-18 (R-140 permiso) · AOD-19 (R-147 UoM/umbrales) · AOD-20 (R-156) · AOD-08 · AOD-14
ESTADO ......................... IN PROGRESS
SIGUIENTE TRANCHE .............. R-160 + R-159 — misma raíz (superficies de `operations` sin predicado de unidad); P1; independiente de R-130;
                                 gobernado por GA-REM-040 (enmienda) y OD-09/OD-16; sin decisión, sin SAP, sin BU-D10 (las fixtures siembran su estado)
```

## 7. Estado tras el tranche 2 (2026-09-09) — recalculado

```
TOTAL ......................... 19   17 canónicos + R-162 + R-163 (registrados en el pre-flight del tranche 2; misma raíz que R-160/R-159)
CERRADOS ......................  3   R-130 · R-160 · R-159 (técnicos; certificación de proceso BLOCKED_RUNTIME)
P1 ABIERTOS ...................  3   R-135 · R-136 (interno) · GA-REM-021
P2 ABIERTOS ................... 10   R-143 · R-142 · R-140 · R-144 · R-152 · R-148 · R-147 · R-161 · R-162 · R-163
P3 ABIERTOS ....................  3   R-153 · R-154 · R-156
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131, ola C + AOD-08) · R-156 (AOD-20) · [+ R-136 post-SAP parcial, SAP_DEFERRED]
                                      (corregido en el pre-flight del tranche 3: decía 2 y omitía R-142/R-156, que sí figuran abajo como decisiones)
DECISIONES DEL PROPIETARIO .....  6   AOD-08 (R-144/R-154 cierre) · AOD-14 (GA-REM-021 B04) · AOD-17 (R-142) · AOD-18 (R-140 permiso) · AOD-19 (R-147) · AOD-20 (R-156)
ESTADO ......................... IN PROGRESS
TRANCHE 3 (ejecutado antes que el «siguiente» abajo, por decisión del propietario: R-163 + R-162, misma raíz que el tranche 2;
           el orden §3 sitúa R-135 + R-143 después, sin cambio)
SIGUIENTE TRANCHE (identificado, NO iniciado)
  R-135 + R-143 (+ R-140 motivo/guarda · R-154 DRAFT/version) — máquina de estados de P-07; OD-17 ya decidida; P1;
  sin SAP (el reenvío con SAP queda descrito, no conectado), sin fase 9, sin BU-D10; R-142 sigue bloqueada por AOD-17
  y no entra; R-140 permiso (AOD-18) no entra. Spec esperada: enmienda de GA-REM-011/GA-REM-013 (la que gobierne P-07)
  o spec nueva — se decide en su propio pre-flight, no aquí.
```

## 6. Recuento canónico (tranche 2 · 2026-09-09) — leído de los objetos del repositorio

| ID | Título | Sev. | Estado | Ola |
|---|---|:--:|---|:--:|
| `R-130` | saldo de aves nunca negativo | P1 | **CERRADO** (técnico) | B |
| `R-160` | creación/edición de eventos sin alcance de unidad | P1 | abierto → tranche 2 | B |
| `R-159` | `get_alerts` sin predicado de unidad | P2 | abierto → tranche 2 | B |
| `R-135` | `RETURNED`/`REJECTED` sin reenvío | P1 | abierto (`OD-17`) | B |
| `R-136` | reverso sin mecanismo | P1 (SAP) | abierto · post-SAP `SAP_DEFERRED` | B · D |
| `GA-REM-021` | brechas de captura del cliente (agua + B01…B04, B13) | P1 | `SPEC_READY` | B |
| `R-140` | `cancel` sin motivo/rol/guarda | P2 | abierto (parte con `AOD-18`) | B |
| `R-142` | `CORRECTED` doble semántica | P2 | bloqueado por `AOD-17` | B |
| `R-143` | `docs/12 R2` corrector ≠ aprobador | P2 | abierto | B |
| `R-144` | cierre sin FCR ni peso final | P2 | bloqueado por `R-131` (C) y `AOD-08` | B/C |
| `R-147` | constantes y tipos sin fuente | P2 | abierto (parte con `AOD-19`) | B/C |
| `R-148` | auditoría inmutable solo en aplicación | P2 | abierto | B |
| `R-152` | importación de abuelas sin estructura | P2 | abierto | B |
| `R-153` | lote de abuelas automático | P3 | tras `R-152` | B |
| `R-154` | estados/campos sin productor | P3 | abierto (parte con `AOD-08`) | B |
| `R-156` | peso del proveedor (legado) | P3 | bloqueado por `AOD-20` | B |
| `R-161` | saldos de huevos/incubación sin bloqueo | P2 | abierto | B |

```
TOTAL 17 · CERRADOS 1 · ABIERTOS 16 · P1 5 (1 cerrado) · P2 9 · P3 3
BLOQUEADOS 3 (R-142 · R-144 · R-156) · DECISIÓN REQUERIDA 6 (AOD-08 · 14 · 17 · 18 · 19 · 20) · SAP_DEFERRED 1 parcial (R-136)
Convención: GA-REM-021 cuenta como UN ítem (spec) aunque agrupe R-13 + H360-B01…B04, B13.
Registrados en este pre-flight, fuera del tranche: R-162 (P2, descarga de evidencia sin unidad) · R-163 (P2, lots: global sobre unidad apagada) → TOTAL 19 tras su alta.
```

## 8. Estado tras el tranche 3 (2026-09-09) — recalculado desde el backlog

```
TOTAL ......................... 19
CERRADOS ......................  5   R-130 · R-160 · R-159 · R-163 · R-162 (técnicos; certificación de proceso BLOCKED_RUNTIME)
P1 ABIERTOS ...................  3   R-135 · R-136 (interno) · GA-REM-021
P2 ABIERTOS ....................  8   R-143 · R-142 · R-140 · R-144 · R-152 · R-148 · R-147 · R-161
P3 ABIERTOS ....................  3   R-153 · R-154 · R-156
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131, ola C + AOD-08) · R-156 (AOD-20) · [+ R-136 post-SAP parcial]
DECISIONES DEL PROPIETARIO .....  6   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20
ESTADO ......................... IN PROGRESS
SIGUIENTE TRANCHE (identificado, NO iniciado)
  R-135 + R-143 (+ R-140 motivo/guarda · R-154 DRAFT/version) — máquina de estados de P-07; OD-17 vigente; P1;
  sin SAP, sin fase 9, sin BU-D10; R-142 (AOD-17) y R-140 permiso (AOD-18) no entran; su pre-flight decide la spec.
```

## 9. Pre-flight del tranche 4 (2026-09-09) — recuento revalidado desde el backlog

```
TOTAL ......................... 22   19 + R-164 (lots.company_id nulable · deuda UNKNOWN) + R-165 (revisión: global sobre unidad apagada) + R-166 (carrera approve/reject)
CERRADOS ......................  5   R-130 (P1) · R-160 (P1) · R-163 (P1, normalizada) · R-159 (P2) · R-162 (P2)
P1 ABIERTOS ...................  3   R-135 · R-136 (interno) · GA-REM-021
P2 ABIERTOS ................... 10   R-143 · R-142 · R-140 · R-144 · R-152 · R-148 · R-147 · R-161 · R-164 · R-165
P3 ABIERTOS ....................  4   R-153 · R-154 · R-156 · R-166
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131, ola C + AOD-08) · R-156 (AOD-20) · [+ R-136 post-SAP parcial]
DECISIONES DEL PROPIETARIO .....  6   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20
SAP_DEFERRED ...................  R-136 (parcial) · OD-17.c (reenvío SAP)
BLOCKED_RUNTIME ................  R-164 (verificación de datos)
TRANCHE 4 ...................... R-135 + R-143 + R-140 PARTE A + R-154 subconjunto DRAFT/version  (GA-REM-006-A · GA-REM-007-A)
```

## 10. Estado tras el tranche 4 (2026-09-09) — recalculado desde el backlog

```
TOTAL ......................... 22
CERRADOS ......................  7   R-130 · R-160 · R-163 (P1) · R-159 · R-162 (P2) · R-135 (P1) · R-143 (P2)
PARCIALES ......................  2   R-140 (PARTE A cerrada; motivo → UI · permiso → AOD-18) · R-154 (DRAFT/version; cierres → AOD-08)
P1 ABIERTOS ...................  2   R-136 (interno; SAP diferido) · GA-REM-021
P2 ABIERTOS ....................  8   R-142 · R-144 · R-152 · R-148 · R-147 · R-161 · R-164 · R-165   (+ R-140 parcial)
P3 ABIERTOS ....................  3   R-153 · R-156 · R-166   (+ R-154 parcial)
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131, ola C + AOD-08) · R-156 (AOD-20) · [+ R-136 post-SAP parcial]
DECISIONES DEL PROPIETARIO .....  6   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20
SAP_DEFERRED ...................  R-136 (parcial) · OD-17.c
BLOCKED_RUNTIME ................  R-164
ESTADO ......................... IN PROGRESS
SIGUIENTE TRANCHE (identificado, NO iniciado)
  R-136 parte interna (reverso con registro compensatorio, BR-16, docs/16 G-R09; tabla reversals sin servicio) + R-165
  (habilitación en el plano de revisión para la autoridad global; misma guarda). Por qué: P1 de integridad de estados,
  «requiere los estados de 3 estables» (§3) — ya lo están; sin decisión pendiente; SAP diferido. Alternativa si el propietario
  prioriza la captura: GA-REM-021 agua (P1, SPEC_READY). R-164 espera acceso a la base configurada.
```

## 11. Pre-flight del tranche 5 (2026-09-09) — `R-136` detenido · recuento revalidado

```
TOTAL ......................... 22   (sin cambio; consistente con §10)
CERRADOS ......................  7   R-130 · R-160 · R-163 · R-159 · R-162 · R-135 · R-143
PARCIALES ......................  2   R-140 · R-154
P1 ABIERTOS ...................  2   R-136 (interno: OWNER_DECISION_REQUIRED AOD-21 · post-SAP: SAP_DEFERRED) · GA-REM-021
P2 ABIERTOS ....................  8   R-142 · R-144 · R-152 · R-148 · R-147 · R-161 · R-164 · R-165
P3 ABIERTOS ....................  3   R-153 · R-156 · R-166
BLOQUEADOS .....................  4   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · R-136 (AOD-21 · SAP)
DECISIONES DEL PROPIETARIO .....  7   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-21
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c
BLOCKED_RUNTIME ................  R-164
CORRECCIÓN ..................... la fila 8 de §1 («el reverso interno lo gobiernan BR-16 y docs/12 R5») no se sostiene: R-136 sale de
                                 «EJECUTABLES AHORA» (§1 línea 52) y pasa a decisión; el orden §3 tranche 4 (R-136) queda suspendido por AOD-21
SIGUIENTE TRANCHE (identificado, NO iniciado)
  GA-REM-021 — captura exigida por el cliente: agua (B05), P1, SPEC_READY; B01 desbloqueado por R-130; B04 fuera hasta AOD-14.
  Acompañante de coste mínimo: R-165 (guarda compartida en el plano de revisión; sin decisión). R-164 espera acceso a la base.
```
