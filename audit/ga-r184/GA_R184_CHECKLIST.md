# GA-R184 · CHECKLIST (mapeo AC → tarea → prueba → evidencia runtime)

Sin AC huérfano. Tarea = `GA_R184_TASKS.md`. Suite = `backend/tests/test_r184_ipe_date_semantics.py`. Runtime = `GA_R184_AUTHENTICATED_RUNTIME_EVIDENCE.md`.

| AC | Tarea | Prueba | Evidencia runtime | Estado |
|---|---|---|---|---|
| R184-AC01 500 exacto reproducido | T1 | RED runtime (ya capturado) | `evidence/red/runtime-red.json` | ✔ |
| R184-AC02 Excepción exacta documentada | T1 | repro local determinista | `evidence/red/typeerror-local.txt` | ✔ |
| R184-AC03 Mismatch de tipos documentado | T1 | traza temporal §2 | íd. | ✔ |
| R184-AC04 Semántica temporal de negocio documentada | T2 | traza fechas §4-5 | — | ✔ |
| R184-AC05 Fórmula preservada | T3 | diff de C2 (1 expresión) | E2E-02 | ○ |
| R184-AC06 Lote válido ⇒ éxito no-500 | T4 | `test_..._ipe_valido_200_y_valor_determinista` | E2E-01/02 | ○ |
| R184-AC07 Esquema de respuesta | T4 | asserts de claves | E2E-02 | ○ |
| R184-AC08 Valor determinista independiente | T4 | `ipe == 33333.3` (cálculo independiente) | E2E-02 | ○ |
| R184-AC09 Redondeo preservado | T4 | asserts de redondeos | E2E-02 | ○ |
| R184-AC10 Estabilidad | T4 | `test_..._estable` | E2E-02 (doble llamada) | ○ |
| R184-AC11 DATE normalizado | T4 | `age_days == 19` | E2E-03 | ○ |
| R184-AC12 DATETIME solo donde corresponde | T4 | sin conversiones nuevas | — | ○ |
| R184-AC13 Sin TypeError residual | T5 | suite completa | E2E-01/03 | ○ |
| R184-AC14 Sin off-by-one de zona | T4 | `age_days` exacto | E2E-03 | ○ |
| R184-AC15 Conteo de días canónico | T4 | 19 / 30 / clamp 1 | E2E-03/04 | ○ |
| R184-AC16 Fronteras | T5 | `test_..._hoy_y_sin_inicio` | E2E-04 | ○ |
| R184-AC17 Ausencia ⇒ no 500 | T5 | íd. | E2E-06 | ○ |
| R184-AC18 Cero/inválido ⇒ no 500 | T5 | íd. (guarda fcr) | E2E-07 | ○ |
| R184-AC19 Estado no soportado ⇒ no 500 | T5 | matriz estados (todos calculan) | E2E-05 | ○ |
| R184-AC20 Lote inválido ⇒ no 500 | T5 | `..._inexistente_404` | E2E-08 | ○ |
| R184-AC21 KPI no disponible ⇒ respuesta controlada | T5 | íd. (0.0 documentado) | E2E-06/07 | ○ |
| R184-AC22 Lote ajeno denegado | T6 | `..._ajeno_404` | E2E-09 | ○ |
| R184-AC23 BU de empresa OFF denegada | T6 | `..._bu_off_404` | E2E-10 | ○ |
| R184-AC24 Sin BU de usuario denegada | T6 | `..._sin_concesion_404` | E2E-11 | ○ |
| R184-AC25 RBAC ausente denegado | T6 | `..._sin_permiso_403` | E2E-12 | ○ |
| R184-AC26 Global no bypassa BU OFF | T6 | `..._global_no_bypass` | E2E-10 (admin) | ○ |
| R184-AC27 Sin fuga por errores KPI | T6 | detalles idénticos «Lote no encontrado» | E2E-08/09 | ○ |
| R184-AC28..33 Regresión GA-FE-02..07 | T7 | suite frontend + runtime puntual | §regresión | ○ |
| R184-AC34 R-181 sigue CLOSED | T8 | verificación documental | — | ○ |
| R184-AC35 R-182 sigue CLOSED_OWNER_ACCEPTED | T8 | íd. | — | ○ |
| R184-AC36 R-185 sigue CLOSED_OWNER_ACCEPTED | T8 | íd. | — | ○ |
| R184-AC37 OBS-UAT-01 sin cambio | T8 | íd. | — | ○ |
