# CERTIFICACIÓN LOCAL — GA-UAT-BREEDER-CRIA-S2-2026-11-24

Spec: `specs/020-uat-breeder-cria-s2/spec.md` · Descubrimiento: `00_DISCOVERY.md` · Baseline `develop` = `00fd162` (= runtime UAT), `main` = `1587073`.
Sin migración (cabeza Alembic `h3c4d5e6f7a8`). Commit de implementación (último con código de producción): `8366827`. Los commits posteriores solo tocan tests, manual y evidencia (`git diff 8366827 -- backend/app frontend/src frontend/public` vacío).

## 1. Gate 0 — ambiente
| | |
|---|---|
| `DEPLOYMENT_MISMATCH` | **NO** |
| `SESSION2_FINDINGS_VALID_FOR_CODE` | **YES** |
| SHA probado por Yolinel | `NOT_ACCESSIBLE` (el PDF no trae marca de versión); inferido: build intermedio `8531d95`…`00fd162` (su historial de corrección está sellado antes del build `00fd162`) — todos descienden de la entrega de la Sesión 1 (`562c346`) |
| Evidencia funcional | capturas con campos corregibles por fila, código de lote en listas y mínimos de la Sesión 1 |

## 2. Disposición de hallazgos
| ID | Hallazgo | Clasificación | Disposición | Evidencia |
|---|---|---|---|---|
| S2-A1/A2 | Corrección de maestros por ID y sin selector | UX / NEW_REQUIREMENT (O-4 de la Sesión 1) | **FIXED** — `correctable-fields` con `master` y `current_display`; historial con `original_display`/`corrected_display`; selector controlado | CORR-S2-01/02/03/08, vitest `uatS2.correctionMaster`, E2E-S2-01 |
| S2-A3 | Corrección acepta muestra negativa | BUG P1 | **FIXED** — `RR-24`; la corrección y la edición heredan el contrato del campo | CORR-S2-04, OPS-S2-04 |
| S2-A3b | Peso promedio negativo | EXPECTED | NO-OP (ya daba 400) + mensaje funcional | CORR-S2-05 |
| S2-A4 | Corrección vacía | EXPECTED | `event_date` no vaciable (antes `TypeError`/500, ahora 400); opcionales siguen anulables | CORR-S2-06/07 |
| S2-A5 | Nombres técnicos en errores | UX P2 | **FIXED** — «Peso promedio», «Semana», «Cantidad de alimento (kg)», «Tamaño de muestra», «Fecha del evento» | CORR-S2-05, E2E-S2-02 |
| S2-A6 | Corrección sin tipo | OWNER_DECISION_REQUIRED | `OD-S2-01` | — |
| S2-B1 | Filtro de lote pide ID | UX P2 (cierre incompleto de S1-ID-02) | **FIXED** — `lot_code` en Revisión y Aprobaciones | REV-S2-01/05, REV-S2-UI-01/02/05, E2E-S2-01/03 |
| S2-B2 | Rango de fechas da error | BUG P2 | **FIXED** — `date_from`/`date_to` tipados (antes 500 por comparar texto con `date`); inicio > fin ⇒ 400/aviso único | REV-S2-02/03/04, REV-S2-UI-03/04, E2E-S2-03 |
| S2-C1 | Inspección sin contenido | OWNER_DECISION_REQUIRED | `OD-S2-02`; contrato vigente fijado | OPS-S2-01/02 |
| S2-C2 | Inspección aprobada sin lote | EXPECTED (D1) + BUG de UX | **FIXED** el texto «Se creará al aprobar» (solo `grandparent_import`); «Sin lote (nivel granja)»; manual §9.3 | vitest `uatS2.listLotLabel`, E2E-S2-04 |
| S2-D1 | Recepción con campos vacíos | EXPECTED | NO-OP | OPS-S2-03 |
| S2-D2 | Muestra mayor que lo recibido | BUG P1 | **FIXED** — `RR-25` (población = `received_total` o alojadas + mortalidad al arribo) | OPS-S2-04, OPS-S2-11, CORR-S2-04, E2E-S2-02 |
| S2-E | Distribución con cero aves | OWNER_DECISION_REQUIRED | `OD-S2-03`; comportamiento vigente fijado | OPS-S2-05 |
| S2-F | Alimento sin fase/tipo | EXPECTED | NO-OP | OPS-S2-06 |
| S2-G | Pesaje sin semana | OWNER_DECISION_REQUIRED | `OD-S2-04` | OPS-S2-07 |
| S2-H | Vacunación sin lote de vacuna | OWNER_DECISION_REQUIRED | `OD-S2-05` | OPS-S2-08 |
| S2-I/J | Mortalidad/descarte sin causa ni semana | OWNER_DECISION_REQUIRED | `OD-S2-06`, `OD-S2-04` | OPS-S2-09/10 |
| S2-I/J-b | «Todo vacío» en mortalidad/descarte | NOT_REPRODUCED | NO-OP (capturas con cantidades; vacío ⇒ 400) | OPS-S2-09/10 |
| (nuevo) | `dosage_per_bird`, `treatment_days`, `chicks_*` negativos aceptados al corregir | MISSING_VALIDATION | **FIXED** — `RR-26` | OPS-S2-DOSIS |

`SESSION1_REGRESSION = NO`. Cierre incompleto de la Sesión 1 corregido: `S1-ID-02` (filtro por código) ahora cubre Revisión y Aprobaciones.

## 3. Reglas nuevas
`RR-24` muestra declarada ≥ 1 · `RR-25` muestra ≤ aves recibidas (recepción) · `RR-26` dosis, días de tratamiento y pollitos sanos/débiles no negativos. Viven en las rutas de escritura (alta, edición y corrección comparten las mismas funciones), **no** en el esquema base de lectura: existen filas históricas inválidas (p. ej. el evento 1115 de UAT con `sample_size = -1`) que deben seguir leyéndose. Ese dato no se toca.

## 4. Regresión (código = `8366827`; HEAD de pruebas `3073ff6` + test `CORR-S2-11`)
| Gate | Resultado | Evidencia |
|---|---|---|
| Backend completo | **2051 passed, 1 failed, 59 skipped** (36:14). El único fallo, `test_r141_tendencia_mortalidad_ignora_cancelados`, **falla igual en el árbol base `00fd162`** el mismo día: dependencia de calendario preexistente (observación O-20) | `evidence/20_backend_full.log`, `21_r141_baseline.txt` |
| Frontend completo | **768 passed** (128 archivos) | `evidence/30_frontend_full.log` |
| TSC / Build | PASS / PASS | `31_tsc.log`, `32_build.log` |
| E2E completa `--workers=1` | **231 passed, 0 failed** (22,7 min); incluye E2E-S2-01..04 (la primera corrida, con 2 fallos de pruebas, se conserva) | `40_e2e_full.log`, `40_e2e_full_run1_2fail.log` |
| Dirigidas S2 (CORR-S2-01..11, REV-S2-01..05, OPS-S2-01..11) | 62 casos; CORR-S2-11 añadido al cerrar M12 | `50_*`, `60_post_mutation_backend.log` |
| Posterior a mutaciones | backend dirigido **135 passed**; frontend completo **768 passed**; tsc limpio | `60_*`, `61_*` |

Pruebas previas adaptadas por contradecir el contrato nuevo (no se relajó ninguna regla): `test_corrections.py` (el error nombra «Días de tratamiento», no `treatment_days`), `f4.lotFilterDebounce` (filtro por código; se conservan debounce de 400 ms y unicidad por ráfaga y se añade la de Aprobaciones), E2E P18D-P5b y P5c (filtro por código en vez de ID numérico).

## 5. Sensibilidad (después del commit de implementación, restauración explícita `git restore --source=8366827 -- <archivo>`)
**Backend 12/12 detectados, frontend 7/7 detectados** (19/19). M12 (aislamiento por empresa de `_nombre_de_maestro`) **sobrevivió** y se cerró con `CORR-S2-11` (un maestro de otra empresa no se nombra), tras lo cual fue detectado. Tras cada mutante, `git diff --stat` vacío; tras la campaña, producción idéntica a `8366827`. Detalle: `evidence/50_mutation_backend_t1.md`, `50_mutation_backend_t2.md`, `51_mutation_frontend.md`.

## 6. Decisiones Owner pendientes (no implementadas)
`OD-S2-01` tipo de corrección obligatorio (recomendado: sí, solo en nuevas) · `OD-S2-02` contenido mínimo de la inspección · `OD-S2-03` distribución con suma > 0 (recomendado: sí) · `OD-S2-04` semana derivada vs obligatoria (recomendado: derivada y editable) · `OD-S2-05` lote de vacuna obligatorio (recomendado: no por ahora) · `OD-S2-06` causa de mortalidad/descarte obligatoria (recomendado: sí, con «desconocida/otra»).

## 7. Observaciones no bloqueantes
| ID | Observación |
|---|---|
| **O-20** | `test_r141_tendencia_mortalidad_ignora_cancelados` falla hoy en `00fd162` y en este ciclo (Δ = 0): depende del calendario (semana ISO). Ajeno a SPEC 020; requiere ciclo propio. |
| **O-21** | El evento 1115 de la empresa QA conserva `sample_size = -1` (dato de prueba creado en la Sesión 2); la corrección lo permite arreglar con un valor válido. |
| **O-22** | El selector de maestros de la corrección carga 100 registros (patrón de O-11). |
| **O-23** | Un campo de maestro vacío no se ofrece en el selector de corrección (no se puede asignar un proveedor a un evento que no lo tenía); mejora futura. |
| **O-24** | Los textos de la Sesión 1 en el manual sobre clasificación desde pantalla estaban desfasados (O-3 se cerró en SPEC 016); corregido en este ciclo. |
| **O-25** | Entorno local: `nvm` sin versión por defecto (los E2E usan Node 24 por ruta explícita). |

## 8. Decisión final
```
SESSION2 = PARTIAL
SESSION1_REGRESSION = NO
DEVELOP_READY_FOR_PR = YES
OWNER_UAT_READY = YES
OWNER_ACCEPTED = NO
```
`PARTIAL` porque seis puntos del UAT dependen de decisión de negocio (§6); todo lo que tenía contrato o invariante físico claro está corregido y verificado. `PR_CREATED = NO` · `MAIN_CHANGED = NO` · `PRODUCTION_DEPLOYED = NO`.
