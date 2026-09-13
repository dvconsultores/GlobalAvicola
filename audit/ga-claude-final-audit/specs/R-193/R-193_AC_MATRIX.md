# R-193 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

| AC | Criterio | Unit / integración | RED en HEAD | E2E runtime (API) | UAT | Evidencia |
|---|---|---|---|---|---|---|
| AC01 | Tras reverso efectivo, recepción de 400 ⇒ 201; tercera de 700 ⇒ BR-18 `ya recibidas: 400` | `backend/tests/test_r193_oc_limit_after_reversal.py::test_r193_01_tras_un_reverso_efectivo_la_oc_recupera_su_capacidad` | **rojo** (400, `ya recibidas: 800`) | `R193-RT-01` | n/a | `evidence/r193/{red,green}/backend_*.log`, `runtime-c3.json` |
| AC02 | Reverso pendiente: A cuenta; tras aprobar, libera | `::test_r193_02_el_reverso_pendiente_no_libera_la_oc` | 1.ª mitad verde (control), 2.ª **roja** | `R193-RT-02` | n/a | ídem |
| AC03 | Contrapartida rechazada/cancelada no cuenta; A sí | `::test_r193_03_la_contrapartida_rechazada_no_cuenta` | verde en HEAD si la contrapartida no está `REVERSED`… **rojo** en la variante «cancelada antes de aprobar» sólo si contara; documenta el control | `R193-RT-03` | n/a | ídem |
| AC04 | Dos reversos ⇒ acumulado 0 ⇒ 1000 OK / 1001 BR-18 | `::test_r193_04_dos_reversos_dejan_el_acumulado_en_cero` | **rojo** (acumulado 1600) | `R193-RT-04` | n/a | ídem |
| AC05 | Sin reverso: matriz `t_014_*` intacta | `test_purchase_order_receipt.py::test_t_014_01…07` | verde | — | n/a | log |
| AC05b | Mensaje reporta neto | `::test_r193_05_el_mensaje_reporta_el_neto` | **rojo** | `R193-RT-05` | n/a | log |
| AC06 | Edición no duplica (`exclude_event_id`) | `test_edit_validation_parity.py` (existente) | verde | — | n/a | log |
| AC07 | Aislamiento de empresa | `::test_r193_03` (variante `company B`) | verde (control) | — | n/a | log |
| AC08 | Sin migración/ruta/permiso | guardianes existentes | verde | — | n/a | log |
| AC09 | Regresión | suites listadas en `R-193_SPEC.md §26` | — | — | n/a | logs |
| AC10 | Runtime post-fix | — | — | `R193-RT-01…05` | n/a | `runtime-c3.json` |

Sensibilidad: S1 (sin exclusión de `REVERSED`) ⇒ AC01/AC04/AC05b rojas · S2 (sin exclusión de contrapartidas) ⇒ AC02/AC03 rojas.
