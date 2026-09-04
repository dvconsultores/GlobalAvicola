# BACKEND TEST — WAVE 2 FINAL

**Fecha** 2026-09-04 · **Comando** `bash backend/scripts/run_tests.sh`
**Línea base histórica** → `BACKEND_TEST_BASELINE_RUN_01.md` (congelado, **no se sobrescribe**)

---

## 1. Comparativa

| Metric | Baseline Run 01 | RUN 05 (Wave 1.5) | **Wave 2 Final** | Delta vs Run 01 |
|---|---:|---:|---:|---:|
| Collected | 101 | 101 | **211** | **+110** |
| PASS | 29 | 74 | **211** | **+182** |
| FAIL | 6 | 26 | **0** | **−6** |
| ERROR | 66 | 0 | **0** | **−66** |
| SKIP | 0 | 1 | **0** | — |
| Duración | — | 22,8 s | 62,8 s | — |

```
Run 01 (Wave 1.5) ....  29 passed ·  6 failed · 66 errors
Run 05 (Wave 1.5) ....  74 passed · 26 failed ·  1 skipped
Wave 2 Final ......... 211 passed ·  0 failed ·  0 skipped
```

**La suite backend está entera en verde por primera vez en la historia del proyecto.**

---

## 2. Cómo se llegó aquí

El salto de 74 a 211 tiene dos componentes que conviene no confundir:

| Origen | Tests |
|---|---:|
| Tests preexistentes que pasaron a verde | 26 |
| Tests **nuevos** escritos en la Wave 2 | +110 |

De los 26 fallos de RUN 05:

| Causa | Nº | Resolución |
|---|---:|---|
| `TEST_DEFECT` — *payload* incompleto, ruta equivocada, credencial eliminada | 14 | corregido el test, con evidencia de por qué el test estaba mal |
| `IMPLEMENTATION_BUG` | 4 | corregido el código (`P0-14`, `R-26`) |
| `OBSOLETE_TEST` — contrato que cambió legítimamente | 4 | actualizado a la realidad (25 tipos de evento, `GA-REM-010`) |
| `FIXTURE_DEFECT` | 2 | catálogos maestros sembrados |
| `SPEC_MISMATCH` | 1 | resuelto al completar el *payload* |
| `UNKNOWN` | 0 | — |

**Ningún test se relajó para pasar.** Donde el test tenía razón y el código no —`vaccine_id`,
`medication_id`, `BR-08` como 400, `BR-14`— se corrigió el código.

---

## 3. Determinismo

La suite se ejecutó con el calendario adelantado para comprobar que `R-28` sigue resuelto:

| Calendario | Resultado |
|---|---|
| hoy real (2026-09-04) | `211 passed` |
| 2026-09-28 *(pasada la caducidad original)* | `211 passed` |
| 2028-03-15 | `211 passed` |

Idéntico en los tres. La suite ya no caduca.

---

## 4. Cobertura por área

| Fichero | Tests | Objeto |
|---|---:|---|
| `test_full_workflow_audit.py` | 23 | flujos F1–F10 |
| `test_p014_persistence.py` | 24 | persistencia del contrato de operaciones |
| `test_rbac.py` | 21 | autorización, aislamiento multiempresa, renovación de sesión |
| `test_corrections.py` | 18 | correcciones e integridad del dato |
| `test_environment_guard.py` | 25 | guarda del entorno de pruebas |
| `test_mortality.py` | 13 | mortalidad, saldo, alertas, deriva de enums |
| `test_operations.py` | 13 | operaciones |
| `test_p013_password.py` | 11 | cambio de contraseña |
| `test_time_determinism.py` | 10 | `BR-19`, determinismo temporal |
| `test_r26_error_contract.py` | 9 | contrato de error de las reglas |
| `test_sap.py` | 9 | integración SAP (adaptador manual) |
| `test_masters.py` · `test_review.py` · `test_audit_reports.py` | 20 | maestros, revisión, informes |
| `test_traceability.py` | 4 | trazabilidad generacional |
| `test_multi_company.py` | 5 | aislamiento multiempresa |
| `test_auth.py` | 6 | autenticación |

---

## 5. Fallos restantes

**Ninguno.** No quedan tests `OBSOLETE`, `WRONG` ni `BLOCKED` sin resolver.

Lo que sí queda son **hallazgos trazados sin corregir**, con destino asignado y por decisión
de alcance explícita —no por descuido—: `R-24`, `R-25`, `R-33`, `R-35`, `R-42`, `R-45`,
`R-46`, `R-47` y el `AC08` de `GA-REM-005`. Todos figuran en
`WAVE_2_EXECUTION_REPORT.md §12`.

---

## 6. Declaración de integridad

- Ningún test se modificó para ocultar un defecto del código.
- Ningún código se modificó para complacer un test incorrecto.
- Ningún `skip` ni `xfail` se añadió: los dos tests que se dejaron deliberadamente en rojo
  durante la Wave (`T-028-03b` en el Stage 0 y `cause_id` en mortalidad en el Stage 1) se
  escribieron con la aserción correcta y los pusieron en verde los Stages 2 y 4.
- El resultado se reprodujo con tres calendarios distintos.
- Producción no se tocó en ningún momento.
