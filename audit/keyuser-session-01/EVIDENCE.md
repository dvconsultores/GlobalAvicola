# KeyUser Session 01 — Evidencia de implementación y certificación (SPEC 009)

**Fecha:** 2026-10-22 · **Rama:** `main` · **Spec:** `specs/009-keyuser-cutover-template-adjustments/spec.md` · **Baseline:** SPEC 006 (cutover v2).

Mandato Owner 2026-10-22 («SESION 1 - REVISION PLANTILLAS - CON KEYUSER», PDF `PENDIENTE_DE_CONTRASTE`). Roles: Claude orquesta + decide técnico + audita/verifica/certifica; DeepSeek escribe código y pruebas. `REAL_SAP_CALLS=0`, `REAL_SAP_WRITES=0`. Sin rama nueva, sin force push.

## 1. Decisiones técnicas (Claude, con evidencia)

- **A** · `genetic_line_code` / `breed_name` = `GLOBAL_AVICOLA_INTERNAL_MASTER`. Errores funcionales nuevos `GENETIC_LINE_NOT_FOUND`, `BREED_NOT_FOUND`, `BREED_NOT_IN_GENETIC_LINE` (solo para esos dos campos; el resto conserva sus códigos). Sin autocrear maestros, sin degradar a texto, sin eliminar FK.
- **B** · Mortalidad histórica obligatoria **solo** en `breeder` (`required=True`, `0` = KNOWN válido). En `grandparent` sigue opcional. `_METRICAS_REPRODUCTORAS` refactorizado a `_metricas_reproductoras(bu)`.
- **C** · Hoja `Catalogos` + columna `source` ∈ {`SAP`, `GLOBAL_AVICOLA`}. `farm` y `house` = `SAP` por el mapping canónico `sap_entity_mappings` (ENTITY_PLANT→`farm_id`, ENTITY_STORAGE_LOCATION→`house_id`); el resto = `GLOBAL_AVICOLA`. Declara gobernanza, no llamada SAP viva; nunca se fabrican filas.
- **D** · Nuevo `egg_origin` {`internal`, `purchased`} persistido en `hatchery_openings.egg_origin` (migración `f1a2b3c4d5e6` sobre `e0f1a2b3c4d5`). `generation` intacto {grandparent, breeder}. `purchased` no exige lote interno; `internal` mantiene la validación.
- **Versionado** · Incubadora → **v3** (`CUTOVER_HATCHERY_V3`); breeder/grandparent/broiler siguen v2. Un archivo de versión anterior de la misma BU ⇒ `TEMPLATE_VERSION_UNSUPPORTED` accionable.

## 2. Archivos cambiados

- **Código:** `backend/app/cutover/{contracts,parser,validation,service,templates,models}.py`; migración `backend/alembic/versions/f1a2b3c4d5e6_add_egg_origin_to_hatchery_openings.py` (cabeza única sobre `e0f1a2b3c4d5`).
- **Pruebas (nuevas, SPEC 009):** `backend/tests/test_cutover_v2_keyuser_s01_red_parse.py` (15), `test_cutover_v2_keyuser_s01_red_db.py` (11). Actualizadas por cambio de contrato: `cutover_v2_fixtures.py`, `test_cutover_v2_contracts.py`, `test_cutover_v2_validation.py`, `test_cutover_v2_red.py`. Ninguna prueba eliminada ni `skip`.
- **Seed/QA (§26):** `backend/seeds/qa_integral_dataset.py` — hatchery cutover con `egg_origin` (aplicado `internal`; fixtures `internal` + nueva fila `purchased`, `QA_SYNTHETIC`).
- **Docs:** `docs/MANUAL_CARGAS_INICIALES.md` (§9 nuevo); regenerados desde código por `backend/scripts/cutover_v2_docs.py`: `audit/cutover-initial-balances/03..10` (05 hatchery v3 + egg_origin; 04 breeder mortalidad obligatoria; 07 lineage FILAS=94; 09 con los 3 códigos nuevos). Generador: +3 entradas en `CATALOGO_ERRORES`.
- **Frontend:** sin cambios de código necesarios; la presentación ES de `egg_origin` (internal/purchased) vive en la hoja `Instrucciones` de la plantilla. `cutoverV2.test.tsx` y demás suites verdes sin tocar.

## 3. Pruebas — fase RED (spec ejecutable)

| Archivo | Resultado RED (código previo) | Log |
|---|---|---|
| `..._red_parse.py` (15) | 10 failed · 5 passed | `evidence/01_red_parse.log` |
| `..._red_db.py` (11) | 7 failed · 4 passed | `evidence/02_red_db.log` |

Los fallos RED expresan el comportamiento objetivo (mortalidad breeder, hatchery v3 + egg_origin, códigos genetic/breed, Catalogos `source`, purchased/internal, persistencia apply); los passes son invariantes a conservar.

## 4. Pruebas — targeted GREEN (tras implementación)

- Área cutover completa (SPEC 006 + SPEC 009): **102 passed / 0 failed** — `evidence/06_green_cutover_full.log`.
- Desglose incremental: RED parse 15/15 tras contracts+parser (`evidence/03_green_parse_tras_contracts.log`); RED db 11/11 tras models+migración+validation+service+templates (`evidence/04_green_db.log`).

## 5. Frontend

- `npx vitest run` → **96 archivos · 576 passed** (`evidence/08_frontend_vitest.log`).
- `npx tsc -b` → `tsc_rc=0` (`evidence/08_frontend_tsc.log`). `npx vite build` → `build_rc=0` (`evidence/08_frontend_build.log`).

## 6. Regresión backend completa

- **Pre-mutación (línea base):** `1765 passed · 0 failed · 49 skipped` (cabeza Alembic `f1a2b3c4d5e6`) — `evidence/07_backend_full.log`. Sin reducción de pruebas: +26 casos nuevos de SPEC 009.
- La primera corrida (con el seed previo) dio 19 fallos, todos triados y corregidos: 14 de la suite legada GA-REQ-061 (su BU pasa a grandparent —contrato de reproductoras idéntico— por la mortalidad obligatoria de breeder), 2 guardas de cabeza Alembic avanzadas a `f1a2b3c4d5e6` (CLAUDE.md §10) y 1 del bucle de plantillas por BU (hatchery v3). `evidence/05_spec006_breakage.log`, `09_green_afectadas.log`.
- **Post-mutación:** `1765 passed · 0 failed · 49 skipped` (cabeza `f1a2b3c4d5e6`) — **idéntica a la pre-mutación**; la restauración explícita no dejó residuo — `evidence/12_backend_full_post_mutation.log`.

## 7. E2E cutover por BU (§25)

`breeder` y `hatchery` por la interfaz (Playwright, `scripts_e2e.sh`): **2 passed** — `evidence/10_e2e_cutover.log`. breeder ejerce la mortalidad obligatoria; hatchery ejerce la plantilla **v3 con `egg_origin`** (internal) de extremo a extremo (descarga → relleno → subida validada → preview → aprobación → apply → reconciliación → primer evento post-corte). Ejecutado con `--workers=1`: con workers en paralelo, `asegurarFases` del soporte E2E tiene una carrera de siembra que duplica la fase `PROD` (`MASTER_AMBIGUOUS`) — traba de aislamiento del arnés E2E **preexistente**, ajena a SPEC 009 (hatchery, que usa `INCUB` implícita, pasa con o sin carrera). El caso `purchased` queda cubierto por la suite de backend (R16/R17/R19) y el fixture QA.

## 8. Mutación / sensibilidad (tras el commit de implementación `7261f70`)

**6/6 DETECTED.** Cada mutación se aplicó al código real, se verificó que una prueba la detecta y se restauró con `git restore --source=7261f70 -- <archivo>` (`FINAL_DIFF=0`).

| ID | Mutación | Prueba que la detecta | Resultado |
|---|---|---|---|
| S1 | mortalidad breeder deja de ser obligatoria (`_req=False`) | `…_red_parse::r1/r2` | DETECTED (2 failed) |
| S2 | genetic_line vuelve a `MASTER_NOT_FOUND` | `…_red_db::genetic_line_inexistente` | DETECTED (1 failed) |
| S3 | `purchased` deja de eximir el lote interno (`comprado=False`) | `…_red_db::r17_purchased` | DETECTED (1 failed) |
| S4 | `CATALOG_SOURCE={}` (farm/house dejan de ser SAP) | `…_red_db::r9_catalogos_source` | DETECTED (1 failed) |
| S5 | se anula el chequeo de versión por contrato | `…_red_parse::hatchery_v2_rechazada` | DETECTED (1 failed) |
| S6 | el apply no persiste `egg_origin` | `…_red_db::r19_apply_persiste` | DETECTED (1 failed) |

Logs: `evidence/11_mut_S1.log` … `11_mut_S6.log`.

## 9. Estado SAP / cierre

```
REAL_SAP_CALLS=0
REAL_SAP_WRITES=0
UNMAPPED_TEMPLATE_FIELDS=0
REQUIRED_DOMAIN_FIELDS_MISSING_FROM_TEMPLATE=0
```

```
IMPLEMENTATION_SHA=7261f70507439dd9ba160dcbd78c47b4d9abe270
BACKEND_FULL_PRE_MUTATION=1765 passed · 0 failed · 49 skipped
BACKEND_FULL_POST_MUTATION=1765 passed · 0 failed · 49 skipped (idéntica)
FRONTEND=576/576 · TSC=PASS · BUILD=PASS
E2E=breeder+hatchery 2/2 passed
MUTATION=6/6 DETECTED (S1–S6)
ALEMBIC_HEAD=f1a2b3c4d5e6 (única)
REAL_SAP_CALLS=0 · REAL_SAP_WRITES=0
```

`FINAL_STATUS = CERTIFIED_KEYUSER_SESSION_01_IMPLEMENTED` (local). Pendiente de push `origin/main` + `REMOTE_SHA_MATCH` y, como pendientes externos ajenos a esta implementación: contraste con el PDF original de la sesión KeyUser y la prueba real de SAP (`SAP_REAL_TEST`).
