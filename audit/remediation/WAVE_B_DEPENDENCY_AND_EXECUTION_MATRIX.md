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

## 12. Tranche 5 · `OD-19` resuelve `AOD-21` (2026-09-09)

```
R-136 interno ................. READY_FOR_SPEC → GA-REM-041 (SPEC_READY) · forma B: R-136 interno + R-165
R-136 post-SAP ................ SAP_DEFERRED (sin cambio)
R-165 ......................... incluido (el reverso se aprueba por el plano de revisión; OD-19 §13)
DECISIONES DEL PROPIETARIO .....  6   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20   (AOD-21 → OD-19)
BLOQUEADOS .....................  3   R-142 · R-144 · R-156 (+ R-136 post-SAP parcial)
migración autorizada .......... t0u1v2w3x4y5 (eventstatus + auditaction ADD VALUE 'REVERSED') · SPEC + AC antes del código
```

## 13. Estado tras el tranche 5 (2026-09-09) — recalculado desde el backlog

```
TOTAL ......................... 22
CERRADOS ......................  8   R-130 · R-160 · R-163 (P1) · R-159 · R-162 · R-143 · R-165 (P2) · R-135 (P1)
PARCIALES ......................  3   R-140 · R-154 · R-136 (interno cerrado; SAP diferido)
P1 ABIERTOS ...................  1   GA-REM-021   (+ R-136 parcial)
P2 ABIERTOS ....................  7   R-142 · R-144 · R-152 · R-148 · R-147 · R-161 · R-164   (+ R-140 parcial)
P3 ABIERTOS ....................  3   R-153 · R-156 · R-166   (+ R-154 parcial)
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · [+ R-136 SAP]
DECISIONES DEL PROPIETARIO .....  6   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c
BLOCKED_RUNTIME ................  R-164
ESTADO ......................... IN PROGRESS
SIGUIENTE TRANCHE (identificado, NO iniciado)
  GA-REM-021 — captura exigida por el cliente: agua (B05), P1, SPEC_READY; B01 desbloqueado por R-130; B04 fuera hasta AOD-14.
```

## 14. Tranche 6 · pre-flight (2026-09-09)

```
recuento ....................... 22 · 8 cerrados · 3 parciales · 11 abiertos (consistente con §13; sin corrección)
pre-flight A ................... OD-19 Aclaración A (propietario): Supervisor Avícola → reversals:create/read · Contralor Avícola → read ·
                                 Administrador de Accesos y operativos → ninguno · SOLO_SUPER_ADMIN 15 → 13 · GA-REM-041 enmienda A
B05 ............................ GA-REM-021 enmienda A · matriz GA_REM_021_B05_WATER_CAPTURE_MATRIX.md · gobernado por completo:
                                 nivel 2 (qué, cuándo, dónde, etapas) + RR-10 (litros, nivel 5/6) + RR-11 (> 0, nivel 5) · sin escalado ·
                                 AOD-19 no lo gobierna · migración u1v2w3x4y5z6 (enum + columna) · frontend mínimo (catálogo + campo)
fuera .......................... B04 (AOD-14) · resto de GA-REM-021 · KPI de agua (ola C) · reverso del dato (GA-REM-041 §3.5)
```

## 15. Estado tras el tranche 6 (2026-09-09) — recalculado desde el backlog

```
TOTAL ......................... 22
CERRADOS ......................  8   R-130 · R-160 · R-163 (P1) · R-159 · R-162 · R-143 · R-165 (P2) · R-135 (P1)   [R-13/B05 cerrado dentro de GA-REM-021]
PARCIALES ......................  4   R-140 · R-154 · R-136 (interno cerrado; SAP diferido) · GA-REM-021 (B05 cerrado; B01–B04, B13, R-156 abiertos)
P1 ABIERTOS ...................  0   (GA-REM-021 y R-136 parciales)
P2 ABIERTOS ....................  7   R-142 · R-144 · R-152 · R-148 · R-147 · R-161 · R-164   (+ R-140 parcial)
P3 ABIERTOS ....................  3   R-153 · R-156 · R-166   (+ R-154 parcial)
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · [+ R-136 SAP · GA-REM-021 B04 (AOD-14)]
DECISIONES DEL PROPIETARIO .....  6   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20   (OD-19 Aclaración A resuelta en este tranche; sin AOD nuevo)
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c
BLOCKED_RUNTIME ................  R-164
ESTADO ......................... IN PROGRESS
TRANCHE 6 ...................... roles del reverso (GA-REM-041-A/B, 5/5 + 3/3, S9 a…e) + B05 agua (GA-REM-021-A, 16/16, S1–S6/S9/S10)
                                 commits c8447de · cdb0670 · 72600f1 · 8df04f7 · daa0c0e · commit de evidencia (este) · cabeza v2w3x4y5z6a7
                                 regresión 1000 passed · 49 skipped · 0 failed (819 s, 2ª pasada; la 1ª dejó 2 rojas corregidas por `GA-REM-041-B`; 976 previas + 16 agua + 5 matriz de roles + 3 migración de roles; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 89/89 · tsc 6
SIGUIENTE TRANCHE (identificado, NO iniciado)
  GA-REM-021 B01 + B02 — cuadre de recepción (♀+♂+mortalidad+rechazo) y pesos en rango en recepción (Rec. §6; P2; ambos sobre el
  evento de recepción y el saldo de R-130). Exige enmienda B previa (NO SPEC = NO DEVELOPMENT); «pesos en rango» necesita fuente
  normativa del rango — si ninguna fuente por encima de la implementación lo fija, OWNER_DECISION_REQUIRED (no se inventa).
  Alternativa sin decisión aparente: R-152 → R-153 (Progenitoras: importación con estructura de docs/02 §3.4.1; spec propia).
```

## 16. Tranche 7 · pre-flight (2026-09-10)

```
recuento ....................... 22 (21 R + GA-REM-021) · 8 cerrados (R-130 · R-135 · R-143 · R-159 · R-160 · R-162 · R-163 · R-165) ·
                                 4 parciales (R-136 · R-140 · R-154 · GA-REM-021) · 10 abiertos (R-142 · R-144 · R-147 · R-148 · R-152 ·
                                 R-153 · R-156 · R-161 · R-166 · R-164 BLOCKED_RUNTIME) · P1 abiertos 0 · P2 abiertos 7 · P3 abiertos 3 ·
                                 bloqueados 3 (R-142 AOD-17 · R-144 R-131+AOD-08 · R-156 AOD-20) · decisiones 6 · SAP_DEFERRED R-136 post-SAP
                                 — consistente con §15; sin corrección de recuento. Recontado fila a fila desde REMEDIATION_BACKLOG (líneas de
                                 estado de los bloques de cierre) — no reutilizado.
gate B01 ....................... bird_reception de reproductoras (Rec. §6) · identidad recibido = Σ alojadas + mortalidad al arribo + rechazo ·
                                 ≠ OD-04/GA-TD-014 (viñeta distinta; BR-18 intacto) · sin acumulación · sin tolerancia · sin estado · concurrencia N/A ·
                                 tres columnas nuevas (migración w3x4y5z6a7b8 tras el commit de spec) · GOBERNADO · independiente de B02
gate B02 ....................... peso promedio de muestra ♀/♂ (g) de la recepción de reproductoras · referente = curva fijada al lote a la edad
                                 del día (OD-06 · GA-REM-037; RR-13) · alerta, no bloqueo · NO_REFERENCE declarado en día 0 sin punto ·
                                 GOBERNADO (GA-REQ-037/OD-06: SÍ) · la cautela «OWNER_DECISION_REQUIRED» del tranche 6 queda desestimada ·
                                 engorde/progenitoras/incubadora N/A
composición .................... CASO A (ambos) · mismo POST /operations · reglas y datos distintos · cierre independiente posible
corrección documental .......... §2 y DEPENDENCY_MAP decían «B01 usa el saldo de R-130»: B01 no lee el saldo; gobierna lo que entra en él
                                 (las alojadas). La dependencia real es de vocabulario (aves alojadas = entradas), no de cálculo.
hallazgos nuevos ............... R-167 (doble contabilización de la mortalidad al arribo; KPI, ola C) · R-168 (sample_size por galpón descartado)
                                 · R-169 (±10 % del formulario sin fuente) — P3, registrados, no resueltos
artefactos ..................... GA_REM_021_B01_RECEPTION_RECONCILIATION_MATRIX.md · GA_REM_021_B02_WEIGHT_RANGE_MATRIX.md · GA-REM-021-B ·
                                 GA-REM-037-B · RC-11 (RR-12 · RR-13)
```

## 17. Estado tras el tranche 7 (2026-09-10) — recalculado desde el backlog

```
TOTAL ......................... 22
CERRADOS ......................  8   R-130 · R-160 · R-163 (P1) · R-159 · R-162 · R-143 · R-165 (P2) · R-135 (P1)   [B05 · B01 · B02 cerrados dentro de GA-REM-021]
PARCIALES ......................  4   R-140 · R-154 · R-136 (interno cerrado; SAP diferido) · GA-REM-021 (B05/B01/B02 cerrados; B03, B04, B13, R-156 abiertos)
P1 ABIERTOS ...................  0   (GA-REM-021 y R-136 parciales)
P2 ABIERTOS ....................  7   R-142 · R-144 · R-152 · R-148 · R-147 · R-161 · R-164   (+ R-140 parcial)
P3 ABIERTOS ....................  3   R-153 · R-156 · R-166   (+ R-154 parcial)   [+ R-167 · R-168 · R-169 registrados en este tranche, P3, fuera del recuento canónico de 22 hasta su alta formal en §1]
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · [+ R-136 SAP · GA-REM-021 B04 (AOD-14)]
DECISIONES DEL PROPIETARIO .....  6   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20   (sin AOD nuevo)
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c
BLOCKED_RUNTIME ................  R-164
ESTADO ......................... IN PROGRESS
TRANCHE 7 ...................... B01 (8/8) + B02 (8/8) · commits f878ab6 · a759a17 · commit de evidencia (este) · cabeza w3x4y5z6a7b8 · rutas 211
                                 regresión 1016 passed · 49 skipped · 0 failed (935 s; 1000 previas + 16 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 89/89 · tsc 6
SIGUIENTE TRANCHE (identificado, NO iniciado)
  GA-REM-021 B03 — alimento por transferencia (Rec. §8: lote/batch de alimento, silo o almacén destino, diferencias; P2) — con B13
  (sanos/débiles al nacer, Bases p.9; P2) como acompañante si la traza los muestra independientes. Exige enmienda C previa
  (NO SPEC = NO DEVELOPMENT); el gate documental decide qué recurso es «lote de alimento» y qué es «silo» antes de cualquier código.
  Alternativa sin decisión aparente: R-152 → R-153 (Progenitoras, docs/02 §3.4.1; paso 7 de §3).
```

## 18. Tranche 8 · pre-flight (2026-09-10) — alta formal de `R-167…R-171` y recuento canónico

Los hallazgos del tranche 7 estaban «registrados fuera del recuento canónico de 22 hasta su alta formal». Precedente: `R-159…R-166` entraron
al recuento en su alta (17 → 19 → 22). Se aplica el mismo criterio: **todo hallazgo de ola B registrado en el backlog cuenta**.

| ID | Título | Sev. (normalizada) | Fuente | Ola | Estado al pre-flight | ¿Cuenta? | Padre / spec | Razón |
|---|---|:--:|---|:--:|---|:--:|---|---|
| `R-167` | doble contabilización de la mortalidad al arribo | P3 → **NO_DEFECTO** | `B01` (tranche 7) | B | **CERRADO · NOT_REPRODUCED** (prueba `test_r167_…`; `R167_ARRIVAL_MORTALITY_ACCOUNTING_MATRIX.md`) | sí | `GA-REM-021-B` / `R-130` | ninguna ruta descuenta `dead_on_arrival`; residuo = doble captura por el operador (instrucción de proceso; KPI → ola C) |
| `R-168` | `sample_size` por galpón descartado | P3 → **P2** | `OperationFormPage.tsx:730` | B | OPEN → este tranche | sí | `GA-REM-021-C §C.2` | pérdida silenciosa de «Muestra tomada» (Rec. §6); clase `R-47` |
| `R-169` | tolerancia ±10 % sin fuente en la recepción (cantidad vs OC; **no** peso) | P3 → **P2** | `OperationFormPage.tsx:384-395, 613-614, 743-751` | B | OPEN → este tranche | sí | `GA-REM-035-A` | segunda definición normativa contraria a `OD-04`; inyecta un veredicto en `observations` |
| **`R-170`** | **doble contabilidad de nacimientos** (fila «Total» + desglose sumados como nacidos) | **P1** | `OperationFormPage.tsx:1568-1590` · `service.py` sin rama de nacimiento | B | **ACTIVO, REPRODUCIDO** (viables 200 para 100) → este tranche | sí | `GA-REM-005-C` (`BR-21`) | verdad de población; `BR-04` admite despachar el doble; clase `R-130` |
| **`R-171`** | la etapa de incubadora no ofrece `cull_recording` ni `mortality_recording` (viables ≡ nacidos desde la UI) | P2 | `processCatalog.ts:226-229, 403-412` | B | OPEN (registrado; no se resuelve aquí) | sí | `GA-REM-021` (enmienda pendiente) | `Bases` p.10 y Rec. §12 exigen esas capturas |

```
TOTAL CANÓNICO ................ 27   (22 + R-167 + R-168 + R-169 + R-170 + R-171; ningún duplicado: R-167 ≠ R-130, R-170 ≠ R-130 (nacimiento, no decremento))
CERRADOS ......................  9   R-130 · R-135 · R-143 · R-159 · R-160 · R-162 · R-163 · R-165 · R-167 (no reproducido)
PARCIALES ......................  4   R-136 · R-140 · R-154 · GA-REM-021
ABIERTOS ....................... 14   R-142 · R-144 · R-147 · R-148 · R-152 · R-153 · R-156 · R-161 · R-164 (BLOCKED_RUNTIME) · R-166 · R-168 · R-169 · R-170 · R-171
P1 ABIERTOS ...................  1   R-170          P2 ABIERTOS  10   (R-142 · R-144 · R-147 · R-148 · R-152 · R-161 · R-164 · R-168 · R-169 · R-171)          P3 ABIERTOS  3   R-153 · R-156 · R-166
DECISIONES DEL PROPIETARIO .....  8   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 (B03) · AOD-23 (B13 igualdad; no bloquea)
gates .......................... R-167 NOT_REPRODUCED · R-169 ACTIVE_UI_CLASSIFICATION (fix) · R-168 ACTIVE (fix) · R-170 CONFIRMED (fix primero) ·
                                 B13 gobernado (≤; igualdad AOD-23) · B03 OWNER_DECISION_REQUIRED (AOD-22 + AOD-19) → modo C: B13 ONLY + R-170/R-169/R-168
corrección documental .......... la fila R-169 del tranche 7 decía «±10 % de peso»: es cantidad vs OC · docs/16:177 (mortalidad al arribo = evento) superada por B01 ·
                                 FUNCTIONAL_COVERAGE_MATRIX CV-F07 (±10 % como validación) y CV-D23 (sanos/débiles «COVERED» por etiquetas) corregidas
```

## 19. Estado tras el tranche 8 (2026-09-10) — recalculado desde el backlog (recuento canónico 27)

```
TOTAL ......................... 27
CERRADOS ...................... 12   R-130 · R-135 · R-143 · R-159 · R-160 · R-162 · R-163 · R-165 · R-167 (no reproducido) · R-168 · R-169 · R-170
PARCIALES ......................  4   R-136 (SAP diferido) · R-140 · R-154 · GA-REM-021 (B05 · B01 · B02 · B13 cerrados; B03 ◄── AOD-22 · B04 ◄── AOD-14 · R-156 ◄── AOD-20)
ABIERTOS ....................... 11   R-142 · R-144 · R-147 · R-148 · R-152 · R-153 · R-156 · R-161 · R-164 (BLOCKED_RUNTIME) · R-166 · R-171
P1 ABIERTOS ...................  0          P2 ABIERTOS  8   (R-142 · R-144 · R-147 · R-148 · R-152 · R-161 · R-164 · R-171)          P3 ABIERTOS  3   R-153 · R-156 · R-166
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · [+ R-136 SAP · GA-REM-021 B03 (AOD-22) · B04 (AOD-14)]
DECISIONES DEL PROPIETARIO .....  8   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c
BLOCKED_RUNTIME ................  R-164
ESTADO ......................... IN PROGRESS
TRANCHE 8 ...................... commits ec974f0 · c653ff8 · commit de evidencia (este) · cabeza x4y5z6a7b8c9 · rutas 211 · regresión 1024 passed · 49 skipped · 0 failed (857 s; 1016 previas + 8 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 95/95 · tsc 6
SIGUIENTE TRANCHE (identificado, NO iniciado)
  R-161 — saldos de huevos e incubación (BR-02, BR-03) leídos sin bloqueo de fila: la carrera de decrementos concurrentes que R-130 cerró
  para las aves (validate_egg_dispatch, validate_incubation_load sin bloquear_saldo_del_lote). DATA_INTEGRITY P2, sin decisión, misma
  clase que el tranche 1; desbloquea el reverso de huevos/incubación (OD-19 §18). Acompañante: R-171 (catálogo de incubadora: descarte y
  mortalidad, Bases p.10 · Rec. §12). Alternativa: R-152 → R-153 (Progenitoras). B03 espera AOD-22.
```

## 20. Tranche 9 · pre-flight (2026-09-10)

```
recuento ....................... 27 · 12 cerrados · 4 parciales · 11 abiertos — recontado desde las líneas de cierre del backlog; consistente con §19
gate R-161 ..................... saldos BR-02 (lote, granja) y BR-03 (lote, incubadora) · escritores: egg_dispatch, incubation_load (uno por saldo) ·
                                 fila autoritativa lots.id · bloqueo antes de leer · corrección/aprobación N/A · cantidad 0 saltaba la validación ·
                                 GOBERNADO (GA-REM-005-B patrón · BR-02/BR-03) · sin decisión · sin migración
gate R-171 ..................... UI_ONLY (el backend ya acepta mortalidad y descarte en lotes de incubadora y viables los resta una vez) · evento, no
                                 atributo (RR-16) · post-nacimiento · B13 intacto · sin decisión · raíz DISTINTA de R-161 → no se combina (CASO B)
modo ........................... R161_ONLY · R-171 queda OPEN, listo para el siguiente tranche
altas .......................... R-172 (egg_type en BR-02) · R-173 (PUT de lote / cancel de entradas sin revalidar) · R-174 (chick_dispatch 0) → recuento canónico 30
artefactos ..................... R161_EGG_INCUBATION_BALANCE_WRITER_MATRIX.md · R171_HATCHERY_MORTALITY_DISCARD_TRUTH_MATRIX.md · GA-REM-005-D · RC-13 (RR-16)
```

## 21. Estado tras el tranche 9 (2026-09-10) — recalculado desde el backlog (recuento canónico 31)

```
TOTAL ......................... 31   (27 + R-172 + R-173 + R-174, alta formal en §20 · + R-175, aislamiento de pruebas, registrado en el cierre)
CERRADOS ...................... 13   R-130 · R-135 · R-143 · R-159 · R-160 · R-161 · R-162 · R-163 · R-165 · R-167 · R-168 · R-169 · R-170
PARCIALES ......................  4   R-136 · R-140 · R-154 · GA-REM-021
ABIERTOS ....................... 14   R-142 · R-144 · R-147 · R-148 · R-152 · R-153 · R-156 · R-164 (BLOCKED_RUNTIME) · R-166 · R-171 · R-172 · R-173 · R-174 · R-175
P1 ABIERTOS ...................  0        P2 ABIERTOS  9   (R-142 · R-144 · R-147 · R-148 · R-152 · R-164 · R-171 · R-172 · R-173)        P3 ABIERTOS  5   R-153 · R-156 · R-166 · R-174 · R-175
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · [+ R-136 SAP · B03 (AOD-22) · B04 (AOD-14)]
DECISIONES DEL PROPIETARIO .....  8   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c          BLOCKED_RUNTIME ....... R-164
ESTADO ......................... IN PROGRESS
TRANCHE 9 ...................... commits 22476bb · abd3179 · commit de evidencia (este) · sin migración · rutas 211 · regresión 1031 passed · 49 skipped · 0 failed (1210 s; 1024 previas + 7 nuevas; los 49 saltados son `test_upgrade_path` y `test_runtime_startup`, que exigen su script dedicado) · vitest 95/95 · tsc 6
SIGUIENTE TRANCHE (identificado, NO iniciado)
  R-171 — catálogo de la etapa de incubadora con mortality_recording y cull_recording (UI_ONLY; RR-16; sin decisión; pasos de flujo, i18n,
  contrato estático) — con R-173 (PUT de lote y cancel de entradas contra los saldos; DATA_INTEGRITY P2, misma primitiva de bloqueo) si la traza
  lo muestra independiente. Alternativa: R-152 → R-153 (Progenitoras).
```

## 22. Tranche 10 · pre-flight (2026-09-10) — recuento revalidado y puerta de composición

```
recuento ....................... 31 · 13 cerrados · 4 parciales · 14 abiertos — recontado desde la última línea de estado de cada ID en el backlog; consistente con §21
                                 + altas de este pre-flight: R-176 (edición sin reglas no keyed por lote) · R-177 (egg_type sin enum; formulario de recepción en incubadora)
                                 · R-178 (linaje egg_batches/chick_batches no neutralizado) → recuento canónico 34 · 13 · 4 · 17
gate R-173 ..................... ACTIVE · GOBERNADO (docs/12 §3 · AC-W09 · B.2/D.1.4 · docs/13) · modelo B · sin decisión · P1 normalizado (saldo negativo, efecto
                                 movido sin validación, reasignación entre empresas por POST /corrections, sin bloqueo) · GA-REM-005-E · RC-15/RR-18
gate R-172 ..................... ACTIVE · GOBERNADO (Bases p.7-9, docs/02 §3.6.4/§3.7.1, spec.md :166/:187: huevo fértil) · predicado único, dos saldos ·
                                 sin borrar filas · GA-REM-005-F · RC-14/RR-17
gate R-174 ..................... ACTIVE · GOBERNADO (B.2 nombra al despacho de pollitos en D; validate_chick_dispatch ya rechaza 0) · GA-REM-005-E §E.3
gate R-171 ..................... UI_ONLY confirmado (backend acepta/persiste/resta una vez: AC-R161-16; catálogo sin los dos tipos; i18n existente) · GA-REM-021-D
gate R-175 ..................... NON-BLOCKING (aisladas 4/4 · B→A 3/3 · A→B 3/3 rojas «5 fases», residuo reproducido bajo control) · OPEN · sin limpieza
modo ........................... A (R-173 → R-172 → R-174 → R-171) · sin decisión nueva · sin migración prevista
P1 abiertos .................... 1 (R-173, este tranche)      P2 abiertos 8 (R-142 · R-144 · R-147 · R-148 · R-152 · R-164 · R-171 · R-172)      P3 abiertos 8 (R-153 · R-156 · R-166 · R-174 · R-175 · R-176 · R-177 · R-178)
bloqueados ..................... R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · [+ R-136 SAP · B03 (AOD-22) · B04 (AOD-14)] · BLOCKED_RUNTIME R-164 · SAP_DEFERRED R-136 post-SAP
decisiones del propietario ..... 8 (AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23) — ninguna nueva
artefactos ..................... R173_EDIT_CANCEL_BALANCE_EFFECT_MATRIX.md · R172_EGG_TYPE_AVAILABILITY_MATRIX.md · R174_ZERO_QUANTITY_DISPATCH_AUTHORITY_TRACE.md ·
                                 R171_…_TRUTH_MATRIX.md §4 · R175_TEST_ORDER_DEPENDENCY_CONTROL.md · GA-REM-005-E/F · GA-REM-021-D · RC-14 · RC-15
```

## 23. Estado tras el tranche 10 (2026-09-10) — recalculado desde el backlog (recuento canónico 34)

```
TOTAL ......................... 34   (31 + R-176 + R-177 + R-178, alta formal en §22)
CERRADOS ...................... 17   R-130 · R-135 · R-143 · R-159 · R-160 · R-161 · R-162 · R-163 · R-165 · R-167 · R-168 · R-169 · R-170 · R-171 · R-172 · R-173 · R-174
PARCIALES ......................  4   R-136 · R-140 · R-154 · GA-REM-021
ABIERTOS ....................... 13   R-142 · R-144 · R-147 · R-148 · R-152 · R-153 · R-156 · R-164 (BLOCKED_RUNTIME) · R-166 · R-175 · R-176 · R-177 · R-178
P1 ABIERTOS ...................  0        P2 ABIERTOS  6   (R-142 · R-144 · R-147 · R-148 · R-152 · R-164)        P3 ABIERTOS  7   R-153 · R-156 · R-166 · R-175 · R-176 · R-177 · R-178
BLOQUEADOS .....................  3   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · [+ R-136 SAP · B03 (AOD-22) · B04 (AOD-14)]
DECISIONES DEL PROPIETARIO .....  8   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c          BLOCKED_RUNTIME ....... R-164
ESTADO ......................... IN PROGRESS
TRANCHE 10 ..................... commits c56b2de · 64dff76 · commit de evidencia (este) · sin migración · rutas 211 · regresión 1056 passed · 49 skipped · 0 failed (1173 s; 1031 previas + 25 nuevas; los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado) · vitest 102/102 · tsc 6
SIGUIENTE TRANCHE (identificado, NO iniciado)
  R-152 → R-153 (Progenitoras: estructura del plan de importación; creación automática del lote de abuelas) — spec propia; sin decisión pendiente.
  Alternativa: R-176 + R-178 (la edición y las reglas no keyed por lote; linaje tras anular/mover) o R-175 (higiene de fixtures bajo gobernanza de validez).
```

## 24. Tranche 11 · pre-flight (2026-09-10) — recuento revalidado y puerta de composición

```
recuento ....................... 34 · 17 cerrados · 4 parciales · 13 abiertos — recontado desde la última línea de estado de cada ID en el backlog; consistente con §23
                                 sin altas nuevas de Wave B · R-45 (Wave 2, P2, abierto) queda absorbido por R-176 (mismo defecto) · R-176 normalizado P3 → P2
gate R-176 ..................... ACTIVE · GOBERNADO (AC-W09/RR-18 · GA-REM-023 · GA-REM-035 · R-30 · R6 · spec.md BR-08/BR-11) · sin decisión · ejecutable ·
                                 paridad de validación pura sobre el estado candidato en la guarda central de R-173 (PUT y POST /corrections) · GA-REM-023-B
gate R-178 ..................... ACTIVE · linaje = trazabilidad generacional (egg_batches/chick_batches; no GeneticLine) · GOBERNADO (OD-10 §2.4/2.5/4bis/4bis.5 · BR-10 ·
                                 GA-REM-008 AC04/AC06 · GA-REM-031 AC03) · sin decisión · sin migración · ejecutable · GA-REM-031-A
gate R-177 ..................... pre-flight COMPLETO · registro corregido (evento ovoscopy) · DATA QUALITY + modelo → OWNER_DECISION_REQUIRED (AOD-24) · sin implementación
gate R-175 ..................... NON-BLOCKING (baseline del tranche 10) · control ampliado T11→A/A→T11/T11→B/B→T11 antes de la regresión completa
modo ........................... R176_PLUS_R178 (CASE A) · sin migración prevista
P1 abiertos .................... 0        P2 abiertos 7 (R-142 · R-144 · R-147 · R-148 · R-152 · R-164 · R-176)        P3 abiertos 6 (R-153 · R-156 · R-166 · R-175 · R-177 · R-178)
decisiones del propietario ..... 9 (AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23 · AOD-24)
artefactos ..................... R176_CREATE_EDIT_CORRECTION_VALIDATION_PARITY_MATRIX.md · R178_LINEAGE_CANCEL_MOVE_INTEGRITY_MATRIX.md · R177_EGG_TYPE_OVOSCOPY_DOMAIN_MATRIX.md ·
                                 R175_TEST_ORDER_DEPENDENCY_CONTROL.md §4 · GA-REM-023-B · GA-REM-031-A · AOD-24
```

## 25. Estado tras el tranche 11 (2026-09-10) — recalculado desde el backlog (recuento canónico 34)

```
TOTAL ......................... 34
CERRADOS ...................... 20   R-130 · R-135 · R-143 · R-159 · R-160 · R-161 · R-162 · R-163 · R-165 · R-167 · R-168 · R-169 · R-170 · R-171 · R-172 · R-173 · R-174 · R-175 · R-176 · R-178
PARCIALES ......................  4   R-136 · R-140 · R-154 · GA-REM-021
ABIERTOS ....................... 10   R-142 · R-144 · R-147 · R-148 · R-152 · R-153 · R-156 · R-164 (BLOCKED_RUNTIME) · R-166 · R-177 (AOD-24)
P1 ABIERTOS ...................  0        P2 ABIERTOS  6   (R-142 · R-144 · R-147 · R-148 · R-152 · R-164)        P3 ABIERTOS  4   R-153 · R-156 · R-166 · R-177
BLOQUEADOS .....................  4   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-156 (AOD-20) · R-177 (AOD-24) · [+ R-136 SAP · B03 (AOD-22) · B04 (AOD-14)]
DECISIONES DEL PROPIETARIO .....  9   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23 · AOD-24
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c          BLOCKED_RUNTIME ....... R-164
FUERA DE WAVE B ................ R-45 (Wave 2) cerrado con R-176
ESTADO ......................... IN PROGRESS
TRANCHE 11 ..................... commits 172ec12 · 4c72c40 · 00b3bd6 · commit de evidencia (este) · sin migración · rutas 211 · regresión 1070 passed · 49 skipped · 0 failed (931 s; 1056 previas + 14 nuevas; los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado) · vitest 102/102 · tsc 6
SIGUIENTE TRANCHE (identificado, NO iniciado)
  R-152 → R-153 (Progenitoras: estructura del plan de importación; creación automática del lote de abuelas) — spec propia; sin decisión pendiente.
  Alternativa: R-166 (approve/reject concurrentes sobre el mismo CORRECTED: bloqueo de fila, misma primitiva que R-130).
```

## 26. Tranche 12 · pre-flight (2026-09-10) — recuento revalidado y puerta de composición

```
recuento ....................... 34 · 20 cerrados · 4 parciales · 10 abiertos — recontado desde la última línea de estado de cada ID en el backlog; consistente con §25
                                 + alta de este pre-flight: R-179 (FK de maestros de otra empresa en eventos) → recuento canónico 35 · 20 · 4 · 11
R-152 ......................... «grandparent_import sin estructura para el plan de importación» · P2 · H360A-02 · docs/02 §3.4.1 · spec.md §4.4 · P-01 paso 1 · unidad grandparent
                                 ACTIVE · GOBERNADO · sin decisión · ejecutable · spec propia GA-REM-042 (BR-22 · RC-16/RR-19) · sin migración
R-153 ......................... «lote de abuelas no se crea automáticamente al completar la importación» · P3 · H360A-03 · docs/02 §3.4.2
                                 ACTIVE · NO gobernado en lo implementación-crítico → OWNER_DECISION_REQUIRED (AOD-25) · depende de R-152 (HARD_DATA_MODEL + HARD_FUNCTIONAL)
modo ........................... R152_ONLY
P1 abiertos .................... 0        P2 abiertos 6 (R-142 · R-144 · R-147 · R-148 · R-152 · R-164)        P3 abiertos 5 (R-153 · R-156 · R-166 · R-177 · R-179)
decisiones del propietario ..... 10 (AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23 · AOD-24 · AOD-25)
artefactos ..................... R152_R153_DEPENDENCY_TRACE.md · R152_R153_PROGENITORAS_FUNCTIONAL_PARITY_MATRIX.md · R152_PROGENITORAS_GAP_MATRIX.md ·
                                 R153_PROGENITORAS_GAP_MATRIX.md · GA-REM-042 · AOD-25 · RC-16
```

## 27. Estado tras el tranche 12 (2026-09-10) — recalculado desde el backlog (recuento canónico 35)

```
TOTAL ......................... 35   (34 + R-179, alta formal en §26)
CERRADOS ...................... 21   R-130 · R-135 · R-143 · R-152 · R-159 · R-160 · R-161 · R-162 · R-163 · R-165 · R-167 · R-168 · R-169 · R-170 · R-171 · R-172 · R-173 · R-174 · R-175 · R-176 · R-178
PARCIALES ......................  4   R-136 · R-140 · R-154 · GA-REM-021
ABIERTOS ....................... 10   R-142 · R-144 · R-147 · R-148 · R-153 (AOD-25) · R-156 · R-164 (BLOCKED_RUNTIME) · R-166 · R-177 (AOD-24) · R-179
P1 ABIERTOS ...................  0        P2 ABIERTOS  5   (R-142 · R-144 · R-147 · R-148 · R-164)        P3 ABIERTOS  5   R-153 · R-156 · R-166 · R-177 · R-179
BLOQUEADOS .....................  5   R-142 (AOD-17) · R-144 (R-131 + AOD-08) · R-153 (AOD-25) · R-156 (AOD-20) · R-177 (AOD-24) · [+ R-136 SAP · B03 (AOD-22) · B04 (AOD-14)]
DECISIONES DEL PROPIETARIO ..... 10   AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23 · AOD-24 · AOD-25
SAP_DEFERRED ...................  R-136 post-SAP · OD-17.c          BLOCKED_RUNTIME ....... R-164
ESTADO ......................... IN PROGRESS
TRANCHE 12 ..................... commits d3e0e70 · 2323d0c · commit de evidencia (este) · sin migración · rutas 211 · regresión 1088 passed · 49 skipped · 0 failed (1113 s; 1070 previas + 18 nuevas; los 49 saltados son test_upgrade_path y test_runtime_startup, que exigen su script dedicado) · vitest 108/108 · tsc 6
SIGUIENTE TRANCHE (identificado, NO iniciado)
  R-166 — approve/reject concurrentes sobre el mismo evento CORRECTED (sin bloqueo de fila; el último flush gana): misma primitiva que R-130/R-173. Sin decisión pendiente.
  Alternativa: R-179 (pertenencia de maestros referenciados por los eventos; clase R-42).
```

## 28. Tranche 13 · pre-flight (2026-09-10) — recuento revalidado y puerta de composición

```
recuento ....................... 35 · 21 cerrados · 4 parciales · 10 abiertos — recontado desde la última línea de estado de cada ID en el backlog; consistente con §27
                                 + alta de este pre-flight: R-180 (galpones origen/destino de los submovimientos) → recuento canónico 36 · 21 · 4 · 11
gate R-179 ..................... ACTIVE · reproducido por API (7 familias × 3 superficies; fila persistida entre empresas) · GOBERNADO por GA-REM-002 ADDENDUM Wave 3
                                 («global si es nulo, propio si está fijado»; la ampliación de entonces cubrió solo lo estructural) · sin decisión ·
                                 severidad P3 → **P1** (clase R-42/R-59) · GA-REM-002 enmienda D · sin migración
gate R-166 ..................... ACTIVE · reproducido por API (approve||reject: dos decisiones efectivas, dos auditorías, notificación de rechazo sobre evento
                                 aprobado) · fila autoritativa operational_events · primitiva ya existente (FOR UPDATE del reverso) · contrato de error existente ·
                                 sin decisión · severidad P3 → **P2** · GA-REM-007 enmienda B · sin migración
independencia .................. raíces distintas (referencia de catálogo vs serialización de decisión); ninguna bloquea a la otra
modo ........................... R179_PLUS_R166 (R-179 primero: es P1 y toca la superficie de escritura que R-166 no toca)
P1 abiertos .................... 1 (R-179, este tranche)   P2 abiertos 6 (R-142 · R-144 · R-147 · R-148 · R-164 · R-166 · R-180 → 7 con el alta)   P3 abiertos 4 (R-153 · R-156 · R-177 · R-179 ya no cuenta)
decisiones del propietario ..... 10 (AOD-08 · AOD-14 · AOD-17 · AOD-18 · AOD-19 · AOD-20 · AOD-22 · AOD-23 · AOD-24 · AOD-25) — ninguna nueva
artefactos ..................... R179_MASTER_REFERENCE_AUTHORITY_MATRIX.md · R166_REVIEW_DECISION_CONCURRENCY_MATRIX.md · GA-REM-002-D · GA-REM-007-B
```
