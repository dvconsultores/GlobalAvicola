# GA-REM-011 — CERTIFICATION REPORT

| | |
|---|---|
| **GA-REM** | `GA-REM-011` — Alineación de contratos FE ↔ BE · **Wave** 1 · 2026-09-03 |
| **Estado final** | **`PARTIALLY CERTIFIED`** — 10 desajustes inequívocos corregidos, 8 diferidos con justificación |

## Finding
**P0-5** y grupo — 13 desajustes de contrato sobre 176 llamadas del frontend, con **5 pantallas caídas**. Ninguna llamada apunta a una ruta inexistente: todos los fallos son de **forma** del contrato.

## Entregable previo obligatorio
`audit/remediation/FE_BE_CONTRACT_MATRIX.md` — **18 desajustes** (`C-01` … `C-18`) consolidados **antes** de aplicar corrección alguna, cada uno clasificado y con acción decidida.

## Corregidos en Wave 1 (10)

| ID | Clasificación | Corrección |
|---|---|---|
| C-01 | `FE_WRONG` | `company.store.ts` — `limit` 200 → 100. Recupera el selector de compañía |
| C-02 | `FE_WRONG` | `UsersPage.tsx` — 200 → 100. Recupera **toda** la pantalla de usuarios |
| C-03 | `FE_WRONG` | `LotDetailPage.tsx` — sustituye listar 200 lotes por **`GET /lots/{id}`**. Recupera KPIs, fases, eventos, alertas y trazabilidad |
| C-04 | `FE_WRONG` | `ReviewDetail.tsx` — sustituye listar 200 eventos por **`GET /operations/{id}`** |
| C-05 | `FE_WRONG` | `CorrectionForm.tsx` — ídem |
| C-06 | `FE_WRONG` | `ReportsPage.tsx` — 200 → 100. Recupera las gráficas |
| C-07 | `FE_WRONG` | `useMasters.ts` (×4) y `useOperations.ts` — corrección **preventiva** en la capa muerta |
| C-08 | `BE_WRONG` | `GET /operations` acepta **`registered_by_me`**. «Mis Pendientes» muestra solo lo propio |
| C-09 | `BE_WRONG` | `GET /operations` acepta **lista de estados separada por coma** con validación explícita. Elimina el **HTTP 500** de «Mis Pendientes» |
| C-17 | `BE_WRONG` | **8 esquemas `Update`** nuevos y registrados: `Supplier`, `GeneticLine`, `Breed`, `FeedType`, `Vaccine`, `MortalityCause`, `Transport`, `ProcessingPlant`. Elimina el **405** en 8 pantallas de catálogo |

## Diferidos a Wave 2 (8) — con justificación

| ID | Motivo del diferimiento |
|---|---|
| C-10 … C-14 | Filtros de Revisión y Auditoría (`status`, `operator_id`, `search`, `action_contains`, `group_by`). Implementarlos cambia la semántica de consulta y su comportamiento esperado depende de decisiones que Wave 1 no resuelve. Hoy son **inertes pero no rompen nada** |
| C-15 | `sap_document_ref` — enviarlo **activa BR-11 y BR-18**, hoy inertes. Es un cambio de comportamiento de negocio que puede bloquear registros de operadores. Requiere coordinación con `RC-07`. **No es inequívoco** en el sentido del §23 |
| C-16 | `idempotency_key` — §33 indica preferir idempotencia **del lado servidor**. Dónde se genera es una decisión de diseño (`GA-REQ-059`), no un defecto inequívoco |
| C-18 | Envoltorio `{items, total}` uniforme — afecta a 4 módulos y a todos sus consumidores. Cambio de contrato amplio |

**`BLOCKED_BY_REQUIREMENT_CONFLICT`: 0.** Ningún desajuste quedó bloqueado por `RC-01` … `RC-05`. Los 8 diferidos lo están por criterio de alcance.

## AC — verificación

| AC | Criterio | Resultado |
|---|---|---|
| AC01 | Ninguna llamada produce 422 por límite | ✅ `grep -rn "limit=200\|limit: 200" frontend/src` → **0 resultados** |
| AC02 | Las 5 pantallas caídas cargan | ✅ contratos corregidos; ⚠ comprobación E2E en `GA-REM-016` |
| AC03 | Mis Pendientes muestra solo lo propio | ✅ `registered_by_me` implementado; el 500 eliminado |
| AC04 | Los filtros filtran o no existen | ⚠ **`DEFERRED`** (C-10…C-14) |
| AC05 | La referencia SAP se persiste | ⚠ **`DEFERRED`** (C-15) |
| AC06 | Idempotencia efectiva | ⚠ **`DEFERRED`** (C-16) |
| AC07 | Edición de maestros sin 405 | ✅ **12 de 12** entidades que la UI ofrece editar tienen `PUT` |
| AC08 | Paginación con total real | ⚠ **`DEFERRED`** (C-18) |
| AC09 | Contrato versionado | ⚠ **`DEFERRED`** — `openapi.json` versionado en Wave 2 |
| AC10 | Contract testing activo | ⚠ **`DEFERRED`** — Wave 2 |

## Regression
`tsc -b --noEmit` **exit 0** · `vitest` **61/61 PASS** · paridad i18n **865=865** · `compileall` OK · 0 deriva de esquema · **176 operaciones OpenAPI** (168 + 8 PUT nuevos).

Durante la corrección de C-01 se introdujo un error de sintaxis en `company.store.ts` (comentario dentro de un literal de objeto) que `tsc` detectó de inmediato; corregido y reverificado. **Es la primera vez en el proyecto que un typecheck detecta un defecto antes de que llegue a `main`.**

## Final status
**`PARTIALLY CERTIFIED`.** Los 10 desajustes inequívocos están corregidos; los 8 diferidos tienen justificación explícita y destino en Wave 2.
