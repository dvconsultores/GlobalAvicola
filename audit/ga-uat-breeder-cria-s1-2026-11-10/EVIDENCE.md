# Evidencia y certificación — GA-UAT-BREEDER-CRIA-S1-2026-11-10

| Campo | Valor |
|---|---|
| **Mandato** | `GA-UAT-BREEDER-CRIA-S1-2026-11-10` |
| **Rama** | `main` (sin ramas de trabajo) |
| **Baseline HEAD** | `7ff5451` |
| **Implementación (IMPL)** | `562c346` |
| **Spec** | `specs/015-breeder-cria-uat-s1/spec.md` |
| **Hallazgos** | `audit/ga-uat-breeder-cria-s1-2026-11-10/00_FINDINGS_TABLE.md` |
| **Migración** | **ninguna** (`MIGRATION=none`) |
| **Head Alembic** | `g2b3c4d5e6f7` |
| **Escrituras SAP reales** | **0** (`REAL_SAP_WRITES=0`) |
| **Secretos en la evidencia** | **0** (`SECRETS_IN_EVIDENCE=0`) |
| **Fecha** | 2026-11-18 |

Los logs, JSON de E2E y capturas citados están en
`audit/ga-uat-breeder-cria-s1-2026-11-10/evidence/`.
## 1. Cadena demostrada (E2E P18A · `evidence/e2e_p18a_correccion_inspeccion.json`)

Lote de reproductoras → **inspección de granja** → **recepción de aves** con cuadre
(`BR-20`: `received_total` = Σ filas + muertas + rechazadas) → submovimientos de
**mortalidad, descarte, salida, pesaje, alimento, agua, vacunación y medicación** →
**envío a revisión** → **inicio de revisión** (`review_started`) → **corrección del peso
promedio** de la fila macho (`bird_movements[91].avg_weight`: **2.0 → 2.5**, motivo
«Báscula mal calibrada en recepción») → **aprobación** → el **detalle final conserva 2.5**
(filas: hembra 880 @ 1.8 · macho 100 @ **2.5**).

**Auditoría** del evento, en orden: `created` → `updated` → `review_started` → `corrected`.

Controles negativos del mismo escenario: la cantidad de la recepción breeder **no** es
corregible (`400`, identidad `BR-20`) y corregir tras la aprobación también devuelve `400`.
Capturas: `evidence/screenshots/p18a_correccion_before.png`, `..._after.png`.
## 2. Aislamiento por unidad de negocio (sin bypass)

Actor con **solo** la unidad *breeder* habilitada frente a un lote *broiler* de la misma
empresa (E2E P18C · `evidence/e2e_p18c_bu_identidad.json`).

| Comprobación | Resultado |
|---|---|
| `GET /lots` (token breeder) | 200 — solo lotes de su unidad |
| `GET /lots?bird_type=…` | el parámetro **no amplía** el alcance (valor inválido ⇒ 400) |
| `GET /lots/{id}` del lote ajeno | **404** |
| `GET /operations/{id}` de evento ajeno | **404** |
| `GET /operations?lot_code=<ajeno>` | 200 **sin filas** |
| `GET /reports/lot/{id}` ajeno | **404** |
| `GET /reports/kpis?lot_id=<ajeno>` | **404** |
| `POST /operations` sobre lote ajeno | **400** «Lote no encontrado» (`BR-07`) |
| UI `/lots` sin unidades concedidas | solo pestañas de unidades efectivas; **aviso** y **0 peticiones** |
| UI URL directa a reporte de lote ajeno | **sin datos** | 

Resultado: **sin bypass**. `S1-BU-02` = VERIFIED; **P0/P1 abiertos en alcance = 0**.
## 3. Matriz de obligatorios por operación (11 operaciones)

Fuente: E2E P18B · `evidence/e2e_p18b_matriz_obligatorios.json` (`fallos: []`).

| Operación | CONTRATO | FRONTEND | BACKEND | RESULTADO |
|---|---|---|---|---|
| Inspección | granja + galpón | exige ambos | `BR-08` | **PASS** |
| Recepción | `received_total` / muertas / rechazadas cuadradas | exige cuadre breeder | `BR-20` | **PASS** |
| Distribución | solo ubicación | exige galpón | `BR-08` | **PASS** (vacío con ubicación = 201 por contrato) |
| Alimento | ≥ 1 fila con `kg > 0` | exige | `RR-23` | **PASS** |
| Agua | litros > 0 | exige | `B05`/`RR-11` | **PASS** (`UAT_EVIDENCE_INSUFFICIENT` del UAT original) |
| Pesaje | `avg_weight > 0` | exige | `RR-20` | **PASS** |
| Vacunación | `vaccine_id` | exige | `RR-21` | **PASS** |
| Medicación | `medication_id` | exige | `RR-22` | **PASS** |
| Mortalidad | cantidad > 0 y ≤ saldo | exige cantidad | `BR-01` | **PASS** |
| Descarte | cantidad > 0 y ≤ saldo | exige cantidad | `BR-01` | **PASS** |
| Salida | cantidad > 0 ≤ saldo + galpón (transporte y destino **opcionales**, D3) | exige cantidad y galpón | `BR-01`/`BR-08` | **PASS** |

Notas de la matriz: el vacío **con** ubicación en Distribución es **201 por contrato** (su
único obligatorio es la ubicación); el saldo se valida por **TOTAL de aves vivas (D4)**, no
por sexo; los mensajes no exponen códigos internos y la regla viaja en el campo `rule`.
## 4. Verificación (gates ejecutados)

| Gate | Resultado | Log |
|---|---|---|
| Backend completo **pre-commit** | **1878 passed · 0 failed · 49 skipped** | `13_backend_full_pre_commit.log` |
| Backend completo **post-mutación** (árbol = IMPL + `test_t9`) | **1879 passed · 0 failed · 49 skipped** | `40_backend_full_post_mutation.log` |
| Frontend `vitest` | **121 archivos · 703 passed** | `41_frontend_vitest_post_mutation.log` |
| `tsc -b` | **rc 0** | `11_frontend_tsc.log` |
| `vite build` | **rc 0** | `12_frontend_build.log` |
| E2E nuevos P18A / P18B / P18C / P18D | **3/3 · 5/5 · 4/4 · 8/8 = 20** | `20_e2e_p18*.log`, `e2e_p18*.json` |
| E2E suite completa **en serie** (`--workers=1`) | **184 passed · 1 failed** (P-17-G *operator*, ver **O-8**) | `42_e2e_full_post_mutation.log` |
| Sensibilidad backend | **9/9 DETECTADAS** (B9 sobrevivió y se cerró con `test_t9`) | `30_sensibilidad_backend.md` |
| Sensibilidad frontend | **10/10 DETECTADAS** | `31_sensibilidad_frontend.md` |
| Diff de producción vs IMPL | **0** | `git diff --stat 562c346` |

Suites S1 de backend incluidas en la cifra total: `test_uat_s1_corrections` 9 ·
`test_uat_s1_required_data` 12 · `test_uat_s1_identity` 7 · `test_uat_s1_inspection_trace` 5.
## 5. Hallazgos descubiertos por E2E y corregidos

1. **Toast con `z-index` insuficiente** → el contenedor de *toasts* se monta en un
   **portal sobre `document.body`** (subir el `z-index` no bastaba: el overlay del
   `ConfirmDialog` vive en otro contexto de apilamiento) — `AC-S1-U02`.
2. **Diálogo de rechazo sin motivo** → se añade el campo de motivo (≥ 10 caracteres,
   validación inline con mensaje único); antes el rechazo era imposible de completar —
   `AC-S1-U03`.
3. **Mensajes de agua con código interno** → se reescribieron los 4 mensajes de
   `water_consumption` sin códigos internos, viajando la regla en el campo `rule` —
   `AC-S1-M01`.
4. **Filtro de tipo de lote** → se **restituyó la defensa de cliente** (validación del
   `bird_type` antes de pedir) porque el **E2E AC10 con API simulada** lo exigía; el
   servidor mantiene el alcance de BU sin ampliarlo — `AC-S1-B01`.
## 6. Observaciones no bloqueantes

| ID | Observación | Tratamiento |
|---|---|---|
| **O-1** | El detalle de evento no publica `id` por fila de submovimiento. | Las correcciones usan `row_id` de `correctable-fields`; sin cambio de contrato. |
| **O-2** | Los `422` de validación estructural de pydantic llegan en inglés desde la API. | La UI los traduce a español; límite documentado. |
| **O-3** | La clasificación de pendientes solo está disponible por API (`POST /operations/{id}/classify`). | La UI expone la bandeja en solo lectura; el selector de unidad queda pendiente de decisión del Owner. |
| **O-4** | Las correcciones de campos de catálogo (`cause_id`, `vaccine_id`, …) se hacen por código numérico. | Sin selector en el formulario; funcional pero poco ergonómico. |
| **O-5** | El usuario sembrado `test_approver` no tiene `review:read`. | Dato de pruebas, no de producto; se ajusta en el seed si se automatiza el UAT. |
| **O-6** | `POST /operations` sobre un lote de otra unidad responde **400** «Lote no encontrado». | Anti-enumeración, comportamiento previo; se mantiene. |
| **O-7** | AC-S1-WATER: sin evidencia suficiente en el UAT original (`UAT_EVIDENCE_INSUFFICIENT`). | El servidor ya exigía litros > 0 y ahora la interfaz también. |
| **O-8** | **P-17-G · operator** da una **falsa inconsistencia** (`/cutover`, la UI permite = `false` con API = `200`) cuando corre **tras** `P-16 cutover-breeder` en la misma base: reproducido en el **baseline `7ff5451`** con el mismo par de specs (`24_e2e_baseline_p16_p17d_pair.log`) y en el **árbol actual** (`23_e2e_p16_p17d_pair.log`); **pasa aislado**. Defecto **preexistente de orden entre specs**, no regresión. | preexistente; fuera de alcance |
| **O-9** | La regresión completa de E2E con **2 workers** por defecto muestra *flakiness* por carga/concurrencia en specs ajenos (legado `tests/operations.spec.ts`, timeout de **P-17-A**); **en serie y aislados pasan**. | ejecutar la suite con `--workers=1` |
## 7. Estado final

```text
MIGRATION=none · REAL_SAP_WRITES=0 · SECRETS_IN_EVIDENCE=0

Hallazgos (00_FINDINGS_TABLE.md):
  S1-BU-01  FIXED
  S1-BU-02  VERIFIED (sin bypass)
  S1-ID-01  FIXED
  S1-ID-02  FIXED
  S1-I18N-01 FIXED
  S1-TRACE-01 FIXED (clasificación de pendientes solo por API: O-3)
  S1-CORR-01  FIXED
  S1-REP-01   FIXED
  S1-REP-02   FIXED
  S1-UX-01    FIXED
  S1-FLT-01   FIXED
  S1-VAL-01   FIXED
  S1-WATER    UAT_EVIDENCE_INSUFFICIENT (no se declara PASS/FAIL del UAT)
  S1-MORT     VERIFIED (NO-OP; pin D4)
  Adicionales: FIXED (toast→portal, motivo de rechazo, mensajes de agua, defensa de cliente del filtro)

P0/P1 abiertos en alcance = 0
Observaciones no bloqueantes: O-1 … O-9

FINAL_STATUS=CERTIFIED_WITH_NON_BLOCKING_OBSERVATIONS
```

