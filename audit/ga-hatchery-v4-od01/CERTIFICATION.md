# CERTIFICACIÓN LOCAL — GA-HATCHERY-V4-OD-FERTILE-EGGS-TO-PIT

Amendment de `specs/018-cutover-hatchery-v4-non-incubables/spec.md` §7. Baseline `main == develop == 52abd20`.
Implementación `22d800b` + `bee4832` (solo comentarios de tests). Sin migración (head `h3c4d5e6f7a8`). El código certificado es el árbol de `bee4832`; el commit de certificación solo añade documentación/evidencia.

## 1. Decisión Owner
```text
OD-HATCH-V4-01 = RATIFIED  (Owner, 2026-11-21)
```
`fertile_eggs_to_pit` = huevos **ya cargados** retirados del proceso durante la incubación/ovoscopia, antes de nacedora. **POST-CARGA.** No es clasificación previa, no es no incubable, no se suma a `eggs_discarded` (V3).

## 2. Modelo de dos etapas (implementado)
```
A (recepción/clasificación): received → { set | oversized | dirty | broken | aún por cargar }   set + Σ(no incubables KNOWN) ≤ received (sin igualdad)
B (incubación):              set      → { transferred | fertile_eggs_to_pit | en proceso }     transferred + pit ≤ set
```

| | Antes (D-5) | Después (D-12/D-13) |
|---|---|---|
| `eggs_in_process` V4 | `set − transferred` solo con pit KNOWN = 0; si no, sin calcular | `set − transferred − pit` cuando los tres son KNOWN; UNKNOWN si falta alguno |
| Validación de la fosa | `pit ≤ received` | `pit ≤ set` (set KNOWN) y `transferred + pit ≤ set` (los tres KNOWN); sin set KNOWN solo la cota derivada `pit ≤ received` |
| BR-03 | no resta la fosa | **sin cambio** (no resta la fosa: ocurre después de la carga) |
| V3 | `set − transferred − eggs_discarded` | **sin cambio** |
| `eggs_discarded` V4 | NULL + `NOT_APPLICABLE` | **sin cambio** |

Las reglas de la fosa se evalúan **aunque `eggs_received` falte** (no dependen de lo recibido). Transferencias operativas: no existe validador de `transfer_to_hatcher` en operación normal → nada que modificar (sigue en OPERATIONAL_MODEL_GAP). `chicks_hatched ≤ transferred (o set)` intacta; sin contradicción.

## 3. Pruebas del mandato (H4-FOSA)
| ID | Caso | Resultado |
|---|---|---|
| H4-FOSA-01 | set 9000, transferred 8000, pit 100 → en proceso 900 | PASS (backend + E2E) |
| H4-FOSA-02 | pit 1000 → en proceso 0 | PASS |
| H4-FOSA-03 | pit 1001 → DENY (`CONSISTENCY_MISMATCH` en la fosa; no se puede enviar a aprobación) | PASS |
| H4-FOSA-04 | set 9000, pit 9001 → DENY (y 9000 válido con transferred UNKNOWN) | PASS |
| H4-FOSA-05 | pit UNKNOWN → en proceso UNKNOWN (no 1000) en preview, API y UI | PASS |
| H4-FOSA-06 | pit 0 = cero conocido → `set − transferred`, estado KNOWN | PASS |
| H4-FOSA-07 | received 10000, no incubables 1000, set 9000, pit 100, transferred 8000 → disponible 0, en proceso 900 (no −100 ni 800); BR-03 no resta la fosa | PASS |

## 4. Regresión
| Gate | Resultado | Evidencia |
|---|---|---|
| Backend completo (`22d800b`) | 1956 passed, **1 failed**, 59 skipped | `evidence/40_backend_full.log` |
| El fallo | `test_time_determinism::test_t028_04` (guarda BR-19): fecha literal «2026-11-21» en 5 **comentarios** de tests (defecto mío de forma). Corregido en `bee4832`; guarda + 4 archivos afectados: 87 passed | `evidence/41_backend_fix_dates.log` |
| Backend dirigido tras el fix + post-mutación | 255 passed (hatchery/cutover, guarda de fechas, bootstrap-independiente, pines Alembic, QA dataset) | `evidence/51_backend_postmutation.log` |
| Frontend completo | **743 passed, 1 skipped** (124 archivos) | `evidence/42_frontend_full.log` |
| TSC / Build | PASS / PASS | `43_tsc.log`, `44_build.log` |
| P16 + Spec 018 + H4-FOSA (E2E dirigido) | 14 passed | `evidence/30_e2e_hatchery.log` |
| E2E completa `--workers=1` | **220 passed, 0 failed** (11,7 min; incluye P16, E2E-V4-01..06 y H4-FOSA-01..07) | `evidence/45_e2e_full.log`, `e2e_od01/` |
| Sensibilidad | **8/8 detectados** (pit ≤ received, sin regla transferred+pit, en proceso sin fosa, UNKNOWN→0 en derivados y en servicio, V3 con fosa, BR-03 restando la fosa) | `evidence/50_mutation_campaign.md` |
| Post-mutación | backend 255 passed · frontend 20 passed | `51_`, `52_` |

La regresión completa de backend corrió sobre `22d800b`; entre ese commit y el final solo cambian comentarios de 4 archivos de tests, y los archivos afectados más la guarda se reejecutaron en verde.

## 5. Observaciones
- **O-13** (ambigüedad histórica V3 de `eggs_discarded`): sin tocar. **O-14** (P17e flaky): no se repitió en esta corrida (220/0). **O-11 / O-12**: fuera de alcance.
- **OPERATIONAL_MODEL_GAP**: operación normal sin `oversized` ni evento de fosa ni validador de transferencia; spec separada.
- **O-15 (nueva, menor, preexistente)**: el resumen del preview suma `eggs_in_process` tratando los `None` como 0 (chip agregado). No afecta a la reconciliación por lote (que sí muestra UNKNOWN); candidato a un ajuste posterior.
- Las aperturas ya aplicadas no se tocan: las V4 aplicadas antes del amendment con fosa > 0 conservan su dato; su `eggs_in_process` ahora se calcula con la fórmula nueva al leer.
