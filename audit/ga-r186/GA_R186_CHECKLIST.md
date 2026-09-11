# GA-R186 · CHECKLIST (AC → tarea → prueba → runtime)

Tarea = `GA_R186_TASKS.md` · Suite = `backend/tests/test_r186_g05_date_semantics.py` · Runtime = `GA_R186_AUTHENTICATED_RUNTIME_EVIDENCE.md`. Estado inicial = fase RED.

| AC | Tarea | Prueba | Evidencia runtime | Estado |
|---|---|---|---|---|
| AC01 500 original reproducido/probado | T1 | RED heredado `prodindex35` + repro local | `evidence/red/runtime-red.json` (R-184) | ✔ |
| AC02 TypeError exacto documentado | T1 | repro local | `evidence/red/typeerror-local.txt` | ◐ |
| AC03 Mismatch documentado | T1 | traza temporal §2 | íd. | ✔ |
| AC04 Dominio temporal canónico | T2 | traza §3 | — | ✔ |
| AC05 Fórmula G-05 preservada | T3 | diff C2 (1 expresión) | E2E-02 | ○ |
| AC06 Pedido válido ⇒ éxito documentado | T4 | `..._determinista` | E2E-01/02 | ○ |
| AC07 Esquema sin cambios | T4 | asserts de claves+unit | E2E-02 | ○ |
| AC08 Valor determinista independiente | T4 | `production_index == 400.0` | E2E-02 | ○ |
| AC09 Redondeo preservado | T4 | asserts redondeos | E2E-02 | ○ |
| AC10 Estabilidad | T4 | doble llamada | E2E-02 | ○ |
| AC11 Normalización DATE | T4 | `age_days == 19` | E2E-03 | ○ |
| AC12 Sin TypeError | T5 | suite | E2E-01/03 | ○ |
| AC13 Sin ±1 día | T4 | edad exacta | E2E-03 | ○ |
| AC14 Mismo día canónico | T5 | age 0 ⇒ PI 0 | E2E-04 | ○ |
| AC15 Multi-día canónico | T4 | 19/110 | E2E-02/03 | ○ |
| AC16 Sin inicio ⇒ canónico sin 500 | T5 | age 30 ⇒ PI 0 | E2E-05 (N/A runtime probado) | ○ |
| AC17-22 Colección | T5 | **N/A — endpoint un solo lote (Query requerido)** | E2E-06/07 N/A probado | ○ |
| AC23 Ausencia sin 500 | T5 | lotes sin datos | E2E-08 | ○ |
| AC24 Cero/inválido sin 500 | T5 | guardas | E2E-08 | ○ |
| AC25/26 Sin NaN/∞ | T4/T5 | asserts numéricos | E2E-02/08 | ○ |
| AC27 Sin valores fabricados | T5 | contrato preservado | E2E-08 | ○ |
| AC28-33 Seguridad | T6 | 404/403/BU-OFF/global | E2E-09…13 | ○ |
| AC34-35 R-184 intacto | T7 | `ipe/11` = 556.6 | E2E-R184 | ○ |
| AC36-41 GA-FE/R-181/182/185 | T7 | regresión documental+spots | §regresión | ○ |
| AC42 Observación IPE intacta | T8 | verificación documental | — | ○ |
| AC43 OBS-UAT-01 intacto | T8 | íd. | — | ○ |
