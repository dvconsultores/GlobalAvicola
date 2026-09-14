# GA-CLAUDE · CERTIFICACIÓN RUNTIME — R-211 · CAPACIDAD DEL GALPÓN POR FILA (BR-17)

Fecha: 2026-09-14 · Spec `specs/R-211` · Procesos: **P-01/P-02** (captura multi-galpón) · Tranche T7 · Baseline: T6 CERRADA (`82b250f`).

## 1 · Ciclo ejecutado

| Fase | Commit(s) | Evidencia |
|---|---|---|
| **C1 · RED** | `3dd397b` | BE `2F/2P` (`evidence/red/backend_red.log`): 01 reparto 500+500 a A+B rechazado con «400 — capacidad (500)»; 02 mensaje sin galpón. Controles 03 (mono-galpón) y 04 (residual C-02=A) verdes |
| **C2 · Implementación** | `b00a83b` | `validate_house_capacity_by_rows`: Σ **por `target_house_id`** contra su `capacity`; filas sin destino caen al `house_id` del evento (contrato F-01e); mensaje con **nombre y capacidad** del galpón |
| **C2s · Sensibilidad** | `e30178b` | S1 (vuelta a Σ contra el galpón del evento) ⇒ 2F (01 falso positivo; 02 mensaje) |
| **GREEN** | — | BE dirigido **4/4** · regresión (population-invariant, reception-reconciliation, master-reference-tenancy, R-190 contigua, edit-validation-parity, BU enforcement ops+lots) **140/140** |
| **C3 · Runtime** | ⏸ ventana (G-06) | `R211-RT-01…05` + captura UI del 201 multi-galpón |

## 2 · Criterios de aceptación

| AC | Resultado | Dónde |
|---|---|---|
| AC-R211-01 galpones 500+500 con filas 500/500 ⇒ 201 | ✅ | `test_r211_01` |
| AC-R211-02 fila excedida ⇒ 400 con galpón y capacidad | ✅ | `test_r211_02` |
| AC-R211-03 mono-galpón excedido ⇒ 400 (sin relajación) | ✅ | `test_r211_03` |
| AC-R211-04 residual C-02=A documentado (201+201) | ✅ | `test_r211_04` |
| AC-R211-06 el `house_id` del evento no decide la Σ | ✅ | `test_r211_01` (evento A, filas A+B) |
| AC-R211-07 sin migración/endpoint/permiso | ✅ | guardianes |
| AC-R211-08 regresión | ✅ | 140/140 |
| AC-R211-05 distribución multi-galpón intacta | ✅ | regresión `edit-validation-parity` + suites de recepción |

## 3 · Decisión del propietario — `C-02`

Opciones: **A** (por defecto, implementada) validar solo el evento — corrige el falso positivo; el exceso acumulado entre eventos al mismo galpón queda como **residual documentado** (`test_r211_04`). **B** acumular entre eventos vigentes por galpón (endurecimiento con consulta agregada; documentado en acta). Elevada como **AOD-28**; si el propietario decide B, se especifica como anexo del paquete con su prueba de acumulado.

## 4 · Veredicto

**R-211 `CLOSED_TECHNICALLY`** — la captura multi-galpón por filas es validable de verdad (cada destino contra su capacidad; mensaje accionable), sin migración ni contrato nuevo. C3 runtime + decisión C-02 pendientes de ventana/propietario.
