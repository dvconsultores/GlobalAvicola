# Implementation Plan: SPEC 007 — QA Integral Synthetic Dataset

**Baseline**: `3e146ac` · **Rama**: `main` · **Alembic head**: `e0f1a2b3c4d5` (sin nuevas migraciones)

## 1 · Principio

Un solo seed canónico que **reutiliza la arquitectura existente** (modelos, servicios, validadores, staging/promotion inbound, CutoverService) en lugar de un segundo sistema de datos. La historia operativa se produce por `OperationsService.create_event` con `idempotency_key` determinista, de modo que cada evento pasa por las mismas reglas de negocio que un registro hecho por la UI (BR-01…BR-22, CUT-GL-02, BR-18). Lo único que no sigue el camino de la UI es la **aprobación masiva del histórico** (`QA_HISTORY_FASTPATH`): un evento histórico aprobado se marca `APPROVED` con su `ApprovalAction` y su transición auditada, porque recorrer 3 pasos de revisión para 330 eventos no aporta cobertura y sí minutos. Los eventos destinados a demostrar el workflow sí recorren los servicios reales (`flujo`).

## 2 · Componentes

| Componente | Archivo | Responsabilidad |
|---|---|---|
| Constructores | `backend/seeds/qa_integral_builders.py` | `QaBuilder`: empresas, roles (lookup, nunca alta), usuarios, concesiones BU, pasos de aprobación, fases, maestros, SAP sintético (staging real + promoción), lotes, aperturas manuales, fases de lote, eventos, fastpath, flujo real, corrección, reverso, notificación, cutover aplicado, cierre de lote, XLSX de cutover |
| CLI | `backend/seeds/qa_integral_dataset.py` | guardas, credenciales, `escenarios()` (el guion del dataset), `fixtures_cutover()`, `inventario()`, `verificar()`, `limpiar()`, `aplicar()`, manifest |
| Tests | `backend/tests/test_qa_integral_dataset.py` | guardas estáticas y de entorno; fail-closed del cleanup; cobertura FK del plan de limpieza |
| Evidencia | `audit/qa-integral-dataset/` | 01…12, manifest MD+JSON, matriz de cobertura, fixtures XLSX, logs saneados |
| Guía QA | `docs/MANUAL_QA_PRUEBA_INTEGRAL_GLOBAL_AVICOLA.md` + `.docx`, `docs/QA_EXECUTION_RESULTS_TEMPLATE.docx` | documento de usuario |

## 3 · Fases de `--apply` (cada una con commit)

1. `empresas` → 2. `roles` (lookup canónico; falla si falta uno) → 3. `usuarios` (hash bcrypt de la credencial inyectada) → 4. `unidades` (CompanyBusinessUnit habilitadas/apagadas + UserBusinessUnit) → 5. `fases` (lookup) → 6. `maestros_principal` → 7. `maestros_aislamiento` → 8. `pasos_de_aprobacion` → 9. `sap_sintetico` → 10. `escenarios` (lotes, aperturas, historia, workflow, correcciones, reversos, notificaciones, consolidación, empresa de aislamiento, cutover aplicado) → fixtures XLSX → contadores → manifest.

## 4 · Idempotencia

Cada constructor busca por clave natural antes de crear: `tax_id`, `username`, `code`/`name`+`company_id`, `lot_code`, `(lot_id, phase_id)`, `idempotency_key`, `source_key` del inbound, `(company, type, payload.qa_key)` de notificación, `legacy_lot_code` del cutover. Los flujos de revisión se saltan si el evento ya no está `REGISTERED`. Resultado esperado de la segunda corrida: `CREATED=0`.

## 5 · Cleanup

`limpiar()` acota todo a las dos empresas QA (por `tax_id`), audita que todo usuario/lote/referencia SAP dentro de ellas lleve marcador (`qa.`, `QA-`, `QAP…`); si no, devuelve `AMBIGUOUS_QA_DATA` sin borrar nada (`--force-unmarked` es la única excepción, explícita). El orden de borrado se deriva de `Base.metadata.sorted_tables` invertido; un test exige que toda tabla con FK hacia el plan esté en el plan. `--dry-run` solo cuenta. **No se ejecuta en el runtime compartido** (OD-QA-04).

## 6 · Seguridad

- `exigir_entorno_seguro`: `ENVIRONMENT` prohibido ⇒ abort; escritura ⇒ `--confirm-target <nombre_bd>` obligatorio (o `GA_QA_SEED_CONFIRM_TARGET`).
- Credenciales: `GA_QA_SEED_PASSWORD` o archivo 0600 (`/tmp/global_avicola_qa_credentials.txt` por defecto). Nada en código, repo, evidencia ni manual.
- SAP: `source_system=QA_SYNTHETIC`; no se toca `SapInboundWatermark` real, no se habilita outbound, no hay payloads `sent_to_sap`.
- Audit: `set_current_audit_user(actor)` antes de cada operación para que los listeners registren al usuario QA correcto.

## 7 · Verificación

Aislado (pgserver del arnés): `baseline_seeds.sembrar_baseline` → `--inventory` → `--apply` → `--verify` → `--apply` (CREATED=0) → `--cleanup --dry-run` → `--cleanup` → `--inventory` (vacío, baseline intacto) → `--apply` → `--verify`. Regresión completa backend (`run_tests.sh`) y frontend (`vitest`, `tsc`, `build`) sin cambios en el código versionado de la aplicación (el seed es aditivo). Runtime: `--inventory` → `--apply --confirm-target avicolav2` → `--verify` → login de cada usuario QA y lectura de dashboard/lotes/revisión/SAP/reportes/cutover por API.

## 8 · Despliegue

AOD-29: commit en `main`, push SSH a `origin/main`, `REMOTE_SHA_MATCH`. El seed se ejecuta contra la base del runtime desde el repositorio en el SHA certificado; los workflows + Watchtower sirven el código (no cambia la app).
