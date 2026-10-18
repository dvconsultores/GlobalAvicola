# 01 · Discovery — SPEC 007 QA Integral Synthetic Dataset

Fecha: 2026-10-18 · Baseline: `3e146ac` (main) · Alembic head: `e0f1a2b3c4d5` · Tablas: 65

## Estado del repositorio al inicio

- Rama `main`, HEAD `3e146ac` (SPEC-006 RUNTIME). Árbol con manuales no versionados (`docs/MANUAL_USUARIO.md`, `docs/MANUAL_CARGAS_INICIALES.md`) y un archivo local de credenciales del arnés (`audit/ga-claude-final-audit/evidence/harness/local_creds.env`, **no versionable**).
- `specs/007-*` libre ⇒ se crea `specs/007-qa-integral-demo-dataset/`.

## Qué existe y se reutiliza

| Área | Hallazgo | Decisión |
|---|---|---|
| Modelo | 65 tablas; tenancy por `company_id`; BU como `lots.bird_type`; concesiones `user_business_units` acotadas a `company_business_units` | se puebla el modelo tal cual; sin migraciones |
| Roles | 7 roles canónicos (`company_id NULL`) con matriz RBAC desde migración `l2m3n4o5p6q7` | lookup, nunca alta/modificación |
| Eventos | `OperationsService.create_event` aplica BR-01…BR-22, `idempotency_key` deduplica | toda la historia por el servicio real |
| Workflow | `ReviewService`/`ApprovalService` con `approval_levels` por empresa y BR-14 | MAIN con 2 niveles (corrected intermedio), ISO con 1 |
| Correcciones/Reversos | `CorrectionService.create_correction`, `ReversalService.solicitar` + contrapartida | servicios reales |
| Cutover v2 | `CutoverService` (SPEC 006) por BU | 4 batches aplicados + fixtures XLSX |
| SAP inbound | `staging.stage` + `promotion.upsert_reference` para 14 `HanaObject`; `source_system` libre | `QA_SYNTHETIC`; 0 llamadas HANA |
| SAP outbound | deshabilitado (`SAP_ENABLED=false`, modo manual) | no se toca |
| Seeds | `baseline_seeds` (prerrequisito), `scenario_fixtures` (`FX-` + retiro), `live_data_boost` (`BOOST_TAG`) | patrón marcador+retiro adoptado; nuevo seed canónico independiente |
| Navegación | `frontend/src/data/navigationConfig.ts`: 6 secciones, 26 entradas con permiso/BU/capacidad; móvil = solo `poultry` | base de la matriz de cobertura |
| Guardas | `tests/environment_guard.py` (FORBIDDEN_ENVIRONMENTS, nombres de BD prohibidos), `scripts/test_db.py` (pgserver aislado) | el seed replica la guarda de entorno y añade `--confirm-target` |
| Emails | `test_seed_email_domains.py` prohíbe `.local/.test/...` en seeds | dominio `qa.globalavicola.com` |

## Riesgos identificados

1. Ambigüedad en el cleanup si alguien crea datos no marcados dentro de una empresa QA ⇒ fail-closed `AMBIGUOUS_QA_DATA`.
2. Códigos SAP de centro (`WERKS`, 4 caracteres) no caben en `QA-` ⇒ `QAP…` reconocido por `es_codigo_qa`.
3. Orden de borrado manual frágil ⇒ derivado del metadata + test de cobertura FK.
4. Historia de 300+ eventos por 3 pasos de revisión sería lenta ⇒ fastpath auditado solo para el histórico; el workflow demostrativo usa servicios reales.
5. El runtime compartido es una base remota de desarrollo: toda escritura exige `--confirm-target avicolav2` explícito; cleanup **no** se ejecuta allí.
