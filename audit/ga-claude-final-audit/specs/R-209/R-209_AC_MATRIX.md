# R-209 · MATRIZ DE CRITERIOS DE ACEPTACIÓN

HEAD `c0b4afc` · Artefactos bajo `specs/R-209/evidence/`.

| AC | Criterio (resumen) | Test | RED en HEAD | Caso E2E | Artefacto |
|---|---|---|---|---|---|
| AC-R209-01 | `bird_exit`: `sap_document_ref` = código | `r209.sapCodeSelectors › exit` | rojo (id) | RT-01 | `runtime-c3.json` |
| AC-R209-02 | `feed_registration`: `sap_order_id` = código | `› feed` | rojo (id) | RT-02 | ídem |
| AC-R209-03 | Fallback sin código ⇒ ausente (nunca id) | `› fallback` | rojo | RT-03 | ídem |
| AC-R209-04 | Comparativo casa por `sap_code` (control) | `test_r209_*` | verde | RT-04 | ídem |
| AC-R209-05 | Selector superior R-189 intacto (control) | `f01.payloadContract` | verde | — | log |
| AC-R209-06 | Sin migración/endpoint/permiso | revisión | — | — | `git diff --stat` |
| AC-R209-07 | ES/EN sin cambio (control) | lectura locales | — | — | — |
| AC-R209-08 | Inventario históricos con id registrado | consulta lectura | — | — | `inventory.txt` |

Cobertura: 8 AC · 3 con RED nueva · 3 controles · 4 casos E2E · UAT no requerida.

## Trazabilidad fuente → AC

| Fuente (B-09/B-10) | AC |
|---|---|
| `setValue('sap_document_ref', String(o.id))` | AC-01/05 |
| `sap_order_id ← String(id)` | AC-02 |
| R-189 §2 (canónico) | AC-03/05 |
| Comparativo por `sap_code` | AC-04 |
