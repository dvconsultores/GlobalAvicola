# Research — SPEC 006 Cutover Initial Balances Remediation

**Fecha**: 2026-10-15 · Discovery sobre `57a421a` · pila local + runtime compartido (solo lectura con credenciales UAT disponibles)

## 1 · Contexto

GA-REQ-061 (T14, cerrado 2026-09-15) entregó el ciclo batch → upload → validación → aprobación → apply → reconciliación con una **plantilla v1 única** de 8 columnas y la certificación de continuidad solo en broiler. `CUTOVER_MASTER_SPEC` (go-live) ya declaraba campos distintos por BU, la guarda CUT-GL-02 y la auditoría fina de incubadora (CUT-06) como bloqueantes. El Owner probó Cargas Iniciales en vivo (2026-10-15) y la carga falló.

## 2 · Reproducción (HEAD, UI real; `audit/cutover-initial-balances/evidence/head-repro/`)

| Caso | Resultado en HEAD |
|---|---|
| Plantilla descargada y subida sin datos | «Validado» con 0 filas; el envío fallaría con 409 |
| Datos «como los escribe un usuario» (`01/08/2026`, `1.200`, `N/A` en vivas) | `INVALID_DATE`, `INVALID_NUMBER`, y la fila con `N/A` en `live_males` queda **válida** |
| Reelegir el mismo archivo | no ocurre nada (input sin reset) |
| Cambiar el selector tras crear el batch y descargar | plantilla de otra BU → `422 BUSINESS_UNIT_MISMATCH` |
| CSV | `422 INVALID_FILE: File is not a zip file` |
| Recargar la página | se pierde el batch (sin listado) |
| Runtime compartido | credenciales UAT sin `cutover:*` → 403; runtime = `57a421a` (marcadores SPEC 005 presentes) |

## 3 · Hechos del dominio que fijan el diseño

| Hecho | Fuente |
|---|---|
| Fases productivas globales por código: `CRIA`, `PROD`, `INCUB`, `ENGORDE`; sin `bird_type` | `seeds/baseline_seeds.py:123-128`, `masters/models.py:260` |
| Galpón, incubadora, nacedora y raza no tienen `code` (solo `name`) | `masters/models.py:92-145, 246` |
| Pesos en gramos (`avg_weight: 2400`) | `masters/models.py:226`, E2E P-06 |
| Saldos: `get_current_bird_balance` = opening(male+female) + entradas − salidas; huevos y pollitos sin opening | `operations/validators.py:52-227` |
| Reconciliación cuenta `event_date > corte` (estricto) | `cutover/reporting.py:69`, test C5 |
| BR-06 compara con `Lot.start_date` y se salta solo con `activation_type="manual"` | `validators.py:551-561` |
| `OpeningBalance.lot_id` es único; `phase_at_activation_id` obligatorio | `lots/models.py:37-45` |
| `uq_lots_company_legacy_code` y `lots.lot_code` único global | migración `b7c8d9e0f1a2`, `masters/models.py:294` |
| Frontend: axios, `hasPermission`, `BackNavigation`, i18n `cutover.*`; `xlsx` (SheetJS) disponible en frontend, no en `e2e/` | informe frontend |
| E2E escribe xlsx con openpyxl vía `execFileSync` y sube con `multipart` | `e2e/proceso-p16-…:40-98` |

## 4 · Decisiones de diseño tomadas

Ver `spec.md §CLARIFICATIONS` (Q1–Q12). Resumen: referencias por nombre dentro del padre; fase declarada y validada por BU; población mixta para engorde; `hatchery_openings` como entidad canónica; POST estricto (`> corte`) + guarda CUT-GL-02; v1 retirada con error claro; sin tolerancias.

## 5 · Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Añadir `code` a galpones/incubadoras/razas | migración + UI de maestros fuera de alcance; el nombre dentro del padre es único en la práctica y se valida ambigüedad |
| Guardar métricas nuevas en `opening_state` JSON | el mandato lo prohíbe (campos críticos solo en JSON = GAP) |
| Reutilizar `OpeningBalance` para incubadora sin tabla nueva | no representa huevos cargados, equipo, fechas ni etapa |
| Mantener v1 como `SUPPORTED_LEGACY` | no puede declarar fase ni galpón; su apply fija `CRIA` para todo |

## 6 · Riesgos

Ver `spec.md §RISKS`.

## 7 · Referencias

`audit/ga-claude-final-audit/specs/GA-REQ-061/**` · `audit/go-live/{CUTOVER_MASTER_SPEC,CUTOVER_GAP_MATRIX,REAL_DATA_MIGRATION_PLAN}.md` · `docs/02-functional-spec.md §3.4–3.9` · `docs/03-domain-model.md` · `specs/remediation/OD-16, OD-19, OD-21` · `specs/005-…` (formato)
