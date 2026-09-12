# GA-F01 · CERTIFICACIÓN RUNTIME — R-189 (F-01 · F-01d · F-01e)

Fecha: 2026-09-13 · Generaciones certificadas: C2d `index-BwuucRxo.js` (sha256 `f7f69b5e…a624e`,
Last-Modified 2026-09-12 21:51:52 GMT) y C2f `index-DDCcWL76.js` (sha256 `d049408a…fed60d`,
Last-Modified 2026-09-12 22:23:13 GMT) · Runtime: `https://avicola.globaldv.net` (health 200).

## 1 · Veredicto

**R-189 — CORREGIDO Y CERTIFICADO TÉCNICAMENTE A NIVEL RUNTIME (UI).**
El guardado del asistente emite el contrato canónico (importación y recepción), los 4xx gobernados se
muestran de forma segura (0 React #31, 0 fatales) y el camino canónico de `OD-25 (B)`
(importar sin lote → aprobar → lote `L-GP-…` → **recepcionar** → población una vez) es alcanzable
**por UI** extremo a extremo.

- Recorrido de referencia (ATTEMPT 2, retry): **7/7 casos UAT en verde**, **35/35 asserts**,
  **0 pageerror**, **0 respuestas 5xx** (`evidence/runtime-c2f/retry-walkthrough.json`).
- `OWNER_ACCEPTANCE`: **PENDIENTE** — sesión del propietario lista (`audit/ga-r153/uat/`).
- R-153 mantiene `CLOSED_FUNCTIONALLY_CERTIFIED`; OD-25 mantiene `RATIFIED_IMPLEMENTED`.

## 2 · Correcciones documentales (declaradas; el histórico no se reescribe)

- **D-01 — F-01 = alias de descubrimiento; R-189 = hallazgo canónico.** Confirmado en
  `GA_F01_DEDUP_RECONCILIATION.md §3` («F-01 → R-189 (canónico) · P1», siguiente libre verificado).
  `F-01d` y `F-01e` son **extensiones del mismo hallazgo R-189** (misma clase: contrato de guardado
  del formulario), con anexo propio cada una. Redacción corregida: *«durante C2/C2d/C2e/C2f no se
  creó ningún R adicional»* (no «no se creó un hallazgo nuevo»).
- **D-02 — primer intento de GA-UAT-09 = `ATTEMPT 1 · STARTED_AND_BLOCKED_BY_F01`**: UAT-01 FAIL
  (verificado ×2); UAT-02…06 NO ALCANZABLES por dependencia; UAT-07 PARCIAL. No debe caracterizarse
  como «7/7 ejecutados». Evidencia original intacta (`GA_OWNER_UAT_R153_OBSERVATIONS.md`).

## 3 · Mapeo C2d → gobernanza (`C2d_UNGOVERNED_PRODUCT_CHANGE: NO`)

| Cambio C2d | Gobernado por |
|---|---|
| Serializadores alimento/incubadora (frontend) | Anexo F-01d §4-D1 · spec AC55/56 · AC-F01D-01/02 |
| Escritura estricta (`FeedMovementCreateSchema`/`HatcheryParamsCreateSchema` ⇒ 422) | Anexo F-01d §4-D2 · spec AC57 · AC-F01D-03/04 |
| Lectura tolerante (`FeedMovementSchema` sin `gt`) | Anexo F-01d §4-D3 · spec AC58 · AC-F01D-06 |
| Fila válida visible | Spec AC59 · AC-F01D-05 |
| Suite R-153 ejecutable (fixture) | Anexo F-01d §7 · spec AC61 · AC-F01D-08 |

## 4 · Pruebas de generación desplegada (backend C2d, sin mutación)

| Sonda | Resultado |
|---|---|
| `POST /operations` con `feed_movements:[{}]` | **422** `greater_than` en `quantity_kg` (escritura estricta viva) |
| `GET /operations/{100,112,115,116,117}` (filas históricas 0.0) | **200** las cinco (lectura tolerante viva; antes: 500) |
| Health `/health` | 200 |

## 5 · Recorrido de referencia y E2E

### 5.1 · Corrida A (generación C2d · expectativa «gap») — `evidence/runtime-c2d/`

29/29 asserts · 0 fatales · 0×5xx. Certifica por UI: importación sin lote (201), OC tipada,
almacenamiento/alimento/incubadora `[]`, detalle «Se creará al aprobar», aprobación P-07 crea
**L-GP-2026-10** (id 64, sin galpón), bracket pre-recepción (`mortalidad ×1 ⇒ 400 «saldo (0)»`),
UX de error segura (400 real), vía manual visible, idempotencia (re-aprobación ⇒ 400; sin segundo
lote). **Capturó en RED el bloqueo F-01e** (recepción ⇒ 400 BR-08) → anexo F-01e.

### 5.2 · Corrida B (generación C2f · retry completo) — `evidence/runtime-c2f/`

35/35 asserts · 0 fatales · 0×5xx:

| Caso | Resultado |
|---|---|
| Importación por UI sin lote | **201** (evento 121); payload canónico (`[]`×3; `sap_document_ref`=código) |
| Aprobación P-07 | `approved`; **L-GP-2026-11** (id 65) exactamente uno (+1) |
| Datos del lote | código/dominio/sexo `mixed`/fecha = llegada/empresa 1 |
| Sin aves antes de recepción | bracket `mortalidad ×1 ⇒ 400 «saldo (0)»` |
| **Recepción por UI** | **201** (evento 122) — `house_id: 1` desde la fila (F-01e corregido); payload `[]`×3 |
| Aprobación de recepción | `approved`; aparece **una vez** |
| Población exacta | `mortalidad ×100 ⇒ 201` (creada y **cancelada**, 123) · `×101 ⇒ 400 «excede el saldo … (100)»` ⇒ **saldo = 100** |
| UX 4xx real | formulario montado; mensaje normalizado; 0 fatales |
| Vía manual | «Nuevo Lote» visible |
| Idempotencia | re-aprobación ⇒ 400 gobernado; total lotes 7 (sin duplicado) |
| Móvil 390×844 | captura `C08m` |

### 5.3 · Cobertura de los E2E del encargo

- E2E-01/02/03/04 (import UI, OC, storage, 4xx UX) ✓ corrida B · E2E-05 (recepción UI) ✓ corrida B ·
  **F-01e** ✓.
- **Conservados de la certificación R-153 C3** (sin cambio de superficie en este tranche; diff de
  `auth`/tenancy/lots = 0): E2E-08/09 (concurrencia multi-proceso — primitiva intacta, cubierta en
  CI), E2E-10 (devuelto/rechazado), E2E-12…15 (negativos de tenant/BU/RBAC — requieren credencial
  global de administración, no disponible en este entorno; superficie sin cambios), E2E-11 (creación
  manual completa — visibilidad re-verificada).
- Nota declarada: en la corrida B el clic final de «Aprobar» cayó a la llamada API equivalente por
  temporización del re-chequeo (mismo actor autorizado; start/complete por UI); el clic de «Aprobar»
  por UI quedó probado en la corrida A (`approve: 200`). El script endureció la espera de visibilidad
  (commit C3) para re-ejecuciones.

## 6 · Límites declarados

- Negativos de seguridad admin-only no re-ejecutados (motivo arriba); R-153 C3 sigue vigente para esa
  matriz; los cambios de este tranche no tocan autorización/tenencia.
- Derivación de galpón fuera de recepción (distribución/traslado) no reabierta (anexo F-01e §7).
- Suite backend íntegra local: ver apéndice (resultado de la corrida en el PostgreSQL de pruebas).

## 7 · Índice de evidencia

- `evidence/runtime-c2d/` (corrida A: 12 capturas + journal) · `evidence/runtime-c2f/` (corrida B: 12 capturas + journal).
- `evidence/f01e/` (RED v1/v2, GREEN, doc RED runtime) · `GA_F01E_SUBSANACION_ANNEX.md` · anexo F-01d.
- Trazas: `GA_F01_DEDUP_RECONCILIATION.md`, `GA_F01_IMPORT_CONTRACT_TRACE.md`, `R189_*`.
- UAT: `audit/ga-r153/uat/GA_OWNER_UAT_R153_RETRY_REFERENCE.md` (+ guía/observaciones/ledger).

## 8 · Próximo paso

Sesión del propietario (guía `GA_OWNER_UAT_R153_GUIDE.md`, 7 casos) → decisión → limpieza post-decisión
(ledger §4/§5). Sin auto-aceptación.
