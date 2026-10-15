# CUTOVER-INITIAL-BALANCES · 13_MUTATION_EVIDENCE

Fecha: 2026-10-15 · SPEC 006 · Sensibilidad S1–S12 (mandato §39) · `IMPLEMENTATION_COMMIT = 507d896ebed2ec163fe6e8b1e1b5bbf65c1a7a68`

Protocolo (`audit/remediation/MUTATION_CHECKPOINT_GOVERNANCE.md`): la sensibilidad corre **después** del commit de implementación, con el árbol productivo limpio y bajo `backend/scripts/mutation_guard.py` (7 señales). Cada mutación se instala en el archivo productivo, se ejecuta la prueba que debe enrojecer con el arnés real (`run_tests.sh`, base aislada) y se restaura con `git restore --source=507d896 -- <archivo>`, comprobando byte a byte contra `git show 507d896:<archivo>` y `git diff --exit-code`. Las mutaciones no se commitean. Driver y logs: `evidence/mutations/driver.py`, `S1..S12.log`, `SENSITIVITY_SUMMARY.log`, `driver_output.log` (saneados).

## 1 · Resultados (corrida final)

| ID | Mutación | Archivo | Prueba objetivo | Observado | DETECTED | Restauración |
|---|---|---|---|---|---|---|
| S1 | celda vacía de métrica → `{0, KNOWN}` (UNKNOWN → 0) | `backend/app/cutover/parser.py` | `test_vacio_es_unknown_cero_es_known_na_es_not_applicable` | `1 failed in 0.37s` | **YES** | `git restore --source=507d896` · byte a byte |
| S2 | `N/A` → UNKNOWN | `parser.py` | ídem | `1 failed in 0.35s` | **YES** | ídem |
| S3 | granja resuelta sin filtro de empresa (maestro ajeno permitido) | `backend/app/cutover/validation.py` | `test_maestro_de_otra_empresa_no_resuelve` | `1 failed, 1 warning in 1.73s` | **YES** | ídem |
| S4 | concesión de BU ignorada en el apply | `backend/app/cutover/service.py` | `test_multiempresa_bu_deshabilitada_y_sin_concesion` | `1 failed, 1 warning in 2.15s` | **YES** | ídem |
| S5 | doble apply permitido (capa completa: estado APPLIED admitido **y** filas aplicadas no bloquean) | `service.py` | `test_idempotencia_doble_apply_y_segregacion` | `1 failed, 2 warnings in 1.94s` | **YES** | ídem |
| S6 | relación galpón→granja ignorada | `validation.py` | `test_relaciones_padre_hijo` | `1 failed, 1 warning in 1.78s` | **YES** | ídem |
| S7 | `eggs_set` deja de ser obligatorio (campo crítico de incubadora ignorado) | `backend/app/cutover/contracts.py` | `test_campo_obligatorio_de_incubadora` | `1 failed, 1 warning in 1.70s` | **YES** | ídem |
| S8 | `hatchery_openings.eggs_received` no se persiste (opening crítico) | `service.py` | `test_hatchery_siguiente_paso_de_incubacion` (BR-03 rechaza la primera carga) | `1 failed, 1 warning in 1.83s` | **YES** | ídem |
| S9 | CUT-GL-02 apagada (evento ≤ corte permitido) | `backend/app/operations/validators.py` | `test_cut_gl_02_rechaza_eventos_hasta_el_corte` | `1 failed, 1 warning in 1.93s` | **YES** | ídem |
| S10 | mismo checksum en otro batch del mismo corte aceptado | `service.py` | `test_idempotencia_doble_apply_y_segregacion` | `1 failed, 1 warning in 1.78s` | **YES** | ídem |
| S11 | plantilla de reproductoras aceptada en batch de incubadora (sin BU/schema_id) | `parser.py` | `test_plantilla_de_otra_bu_rechazada` | `1 failed in 0.36s` | **YES** | ídem |
| S12 | cabecera obligatoria ausente en CSV aceptada | `parser.py` | `test_cabeceras_duplicadas_desconocidas_y_faltantes` | `1 failed in 0.38s` | **YES** | ídem |

## 2 · Notas de construcción

- **S5** requirió una mutación de **capa completa**: con solo admitir `APPLIED` en la máquina de estados, la segunda capa (filas ya `applied` ≠ `valid` ⇒ 409) seguía bloqueando el doble apply y la prueba no enrojecía (`run1/`, `run2/`: `NOT_DETECTED`). Se reconstruyó quitando las dos capas (`driver.py` admite varios fragmentos por mutación) y se repitió S1–S12 íntegra: 12/12. Las dos corridas previas se conservan en `evidence/mutations/run1/` y `run2/` (11/12 en ambas, `FINAL_DIFF = 0`).
- **S1/S2/S11/S12** se observan con pruebas de parser sin base de datos (el arnés igualmente levanta pgserver, de ahí el tiempo).
- **S8** se observa por el motor: sin `eggs_received` la primera carga de incubación post-corte choca con `BR-03`.

## 3 · Restauración explícita

```text
FINAL_RESTORE_SHA = 507d896ebed2ec163fe6e8b1e1b5bbf65c1a7a68
FINAL_DIFF = 0   (git diff --exit-code 507d896 -- backend/app frontend/src backend/alembic)
ÁRBOL PRODUCTIVO TRAS LA SENSIBILIDAD = LIMPIO
MUTATION = PASS (12/12 DETECTED)
```

## 4 · Regresión post-mutación

Ver `14_LOCAL_CERTIFICATION.md §3` y `evidence/post-mutation/`.
