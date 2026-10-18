# Implementation Plan: SPEC 008 — QA Yolinel Findings Remediation

**Directorio**: `specs/008-qa-yolinel-findings-remediation` · **Rama**: `main` (sin rama nueva)
**Baseline**: `83c9cd8` · **Created**: 2026-10-18 · **Status**: `IMPLEMENTING` · **Prioridad**: P1
**Entrada**: `spec.md` (matriz QA-001…QA-018, FR-01…FR-08) · `tasks.md` (T01…T20) · `audit/qa-yolinel-2026-10-17/01…04`

---

## 1. Principios de ejecución

1. **RED primero**: ningún bloque de código se escribe sin un test que hoy falle y describa el hallazgo.
2. **Sin cambio de contrato no pedido**: solo se añaden campos de lectura y el filtro de cadena de BR-23; no se renombra ni se elimina nada existente.
3. **Una decisión Owner no se implementa**: si un FR depende de OD-QA2-01…05, se detiene y se reporta.
4. **Trazabilidad**: todo cambio referencia su QA-ID y su FR (mensaje de commit y comentario de test).
5. **Prohibido**: SAP real, DROP/TRUNCATE, `main` sobrescrita, tocar `.github/workflows`, reducir tests.

## 2. Orden de ejecución

```text
FASE 0  Discovery / clasificación            → DONE (T01, T02; audit 01..04)
FASE R  RED (tests que fallan)               → T03, T04, T05, T06, T07, T08
FASE 1  BE · BR-23 cadena de la OC           → T09
FASE 2  FE · Maestros (etiquetas, estado, padre) → T10, T11
FASE 3  FE · Revisión (bucle, usuario/fecha)  → T12, T13
FASE 4  FE · Fechas (max=hoy)                → T14
FASE 5  BE+FE · Listados y filtro granja      → T15, T16
FASE 6  Regresión completa                   → T17
FASE 7  Commit                                → T18
FASE 8  Sensibilidad (mutaciones)            → T19
FASE 9  Restore + post-mutación              → T19
FASE 10 Docs DOCX + certificación + push      → T20
```

## 3. FASE R — RED

| Test | Archivo (destino) | Assertion que hoy falla |
|---|---|---|
| BR-23 unidad | `backend/tests/*/test_br23_oc_chain.py` | OC de centro mapeado a unidad ≠ `lots.bird_type` ⇒ 400; cruzada entre centros ⇒ 400; sin mapping ⇒ 2xx |
| BR-23 contrato | mismo archivo / `test_sap_references_chain_filter.py` | `/sap/references` filtra por cadena y devuelve `chain`/`chain_known` |
| Columnas de maestros | `frontend/src/**/masters/__tests__/columnLabels.test.tsx` | Ninguna columna usa clave `common.edit`/`common.save`/acción; campo↔valor correcto |
| Padre en hijos | `frontend/src/**/masters/__tests__/childListsParent.test.tsx` | Galpones muestran Granja; incubadoras/nacedoras muestran Planta; `—` si falta |
| Estado/Desactivar | `frontend/src/**/masters/__tests__/deactivateAction.test.tsx` | Rótulo Desactivar/Reactivar, columna Estado, fila atenuada, toast de error |
| Bucle revisión | `frontend/src/**/review/__tests__/reviewCenter.requests.test.tsx` | Conteo de peticiones constante tras interacciones (`ApprovalPanel` idem) |
| `max=hoy` | `frontend/src/**/operations/__tests__/eventDateMax.test.tsx` | Input de fecha de evento tiene `max` = hoy; planificadas/cutover sin `max` |
| Listados + filtro | `frontend/src/**/__tests__/listColumns.test.tsx` + `backend` test de contrato | `farm_name`/`hatchery_name`, `created_by`, `created_at` presentes; filtro `farm_id` enviado |

Regla RED: ejecutar solo los archivos nuevos (`backend/scripts/run_tests.sh <ruta>`, `npx vitest run <ruta>`) y capturar la salida de fallo como evidencia de partida.

## 4. FASE 1 — BE · BR-23 (QA-007 · FR-01)

1. **Derivación de cadena de la OC** en el módulo de recepción de aves / validadores:
   leer las posiciones de la OC (`sap_references`/datos de OC ya persistidos), resolver `WERKS` → `SapEntityMapping(entity_type=PLANT).business_unit_code` (`inbound/promotion.py:109-116, 246-256` como referencia de forma del dato).
2. **Función pura** `derive_oc_chain(positions) -> (code | None, known: bool, conflict: bool)` — testeable sin BD.
3. **Validación** junto a `validate_oc_limit` (`validators.py:908-948`) sin alterar BR-18:
   - conocida ≠ `lots.bird_type` ⇒ `400` BR-23 (`motivo=CHAIN_MISMATCH`);
   - conflicto entre centros ⇒ `400` BR-23 (`motivo=CHAIN_CONFLICT`);
   - desconocida ⇒ permitida, se propaga `chain_known=false`.
4. **Contrato de lectura** de la referencia/OC: exponer `business_unit_code` derivado y `chain_known`.
5. **`/sap/references`** (`sap/service.py:153-163`): parámetro opcional de cadena aplicado **después** del filtro por empresa (que no se toca); devolver `chain`/`chain_known`.
6. **No tocar**: BR-18, R3/R4, `lots.bird_type` como fuente de verdad de la cadena.
7. Documentar la regla en `docs/02` cuando se cierre la ronda (nota breve + referencia a BR-23).

> Si las posiciones de OC no están persistidas con `WERKS`, la derivación se hace en el momento de la importación y se guarda el resultado; **no** se inventa el dato ni se consulta SAP.

## 5. FASE 2 — FE · Maestros

### 5.1 Etiquetas reales (QA-013 · FR-02)
- Reemplazar en las definiciones de columna de los 20 maestros las claves de acción por claves propias (`masters.*`): `tax_id`, `country`, `code`, `location`, `capacity`, `plate`, `laboratory`, `category`, `order`, `description`, `sap_code` y el resto hasta 20.
- Añadir las entradas a los catálogos ES/EN existentes (mismo esquema que el resto).
- Test guardián: ninguna columna de datos puede tener clave cuyo namespace sea de acción.

### 5.2 Estado y «Desactivar» (QA-002 · FR-04)
- `MasterListPage.tsx` + `DataTable.tsx`: acción de fila → «Desactivar»/«Reactivar»; eliminar el texto «no se puede deshacer».
- Columna **Estado** (`Activo`/`Inactivo`) y clase de fila atenuada para `is_active=false`.
- Manejo de error del endpoint de baja lógica → `toast` de error con mensaje del backend (dejar de ser silencioso).
- **Backend intacto** (`masters/router.py:69-81`, `masters/service.py:267-272`): solo se documenta que es baja lógica.
- Badge/nota para maestros con origen SAP (`source_system`/`sap_code`) con el texto de OD-24 (espejo de solo lectura cuando exista P-08); sin cambio de comportamiento.

### 5.3 Padre en listados hijos (QA-012 · FR-03)
- Galpones → columna **Granja** (nombre); Incubadoras (equipo) y Nacedoras → columna **Planta** (nombre).
- Resolver nombre por catálogo ya cargado o por campo `farm_name`/`hatchery_name` del contrato; sin N+1.
- Marcador `—` si falta el padre.

## 6. FASE 3 — FE · Revisión

### 6.1 Bucle de peticiones (QA-017 · FR-05)
- `useCan`: devolver una referencia estable (`useCallback`) o exponer los primitivos de permiso; `ReviewCenter.tsx` depende de esos primitivos, no de la función.
- `fetchEvents` envuelto en `useCallback` con dependencias primitivas; el `useEffect` depende de `fetchEvents` y de filtros primitivos; `toast` consumido por referencia estable (o vía `useRef` del handler).
- Guardia anti-duplicado (abort/`AbortController` o `requestId`) para no aplicar respuestas obsoletas.
- Test: contar llamadas al cliente HTTP en montaje + 3 interacciones; el total no crece tras la primera carga por filtro. Mismo test para `ApprovalPanel`.

### 6.2 Usuario y fecha de registro (QA-018 · FR-07)
- Columnas **Registrado por** y **Fecha de registro** (`created_at`), con etiqueta explícita que la distingue de la **fecha del evento**.

## 7. FASE 4 — FE · Fechas (QA-016 · FR-06)

- `max={todayISO}` en los `input type="date"` de **fecha de evento** operativa (Recepción de Aves, eventos de granja/planta, etc. según inventario).
- **No** aplicar a `start_date`, `activation_date`, `cutover_datetime` (OD-QA2-05).
- Entregar `FIELD / ROUTE / ALLOW_FUTURE` en la documentación de la ronda.
- Test: `max` presente y igual a hoy; backend BR-19/R-30 sin cambios y su test en verde.

## 8. FASE 5 — BE+FE · Listados y filtro granja (QA-014, QA-015)

1. **BE**: añadir al contrato de lectura el nombre del padre — `lots/schemas.py:77-86`, `operations/schemas.py:269-279` — `farm_name` y `hatchery_name`/`plant_name` cuando aplique, resueltos con join (una consulta por listado, sin N+1); `created_by` (username) y `created_at` ya/already expuestos de forma explícita.
2. **BE**: verificar que `/operations` (`operations/router.py:42-71`) y `/lots` (`lots/router.py:23`) mantienen `farm_id`/`status`/`date_from`/`date_to`; añadir test de contrato.
3. **FE**: columnas condicionales Granja / Planta + Registrado por + Fecha de registro en Lotes, Historial, Mis pendientes, Centro de Revisión y Aprobaciones.
4. **FE**: filtro **Granja** en Operaciones y selector de estado/fecha ya soportados; no crear `hatchery_id`.
5. Documentar Planta como pendiente (QA-015 hatchery).

## 9. FASE 6 — Regresión

```bash
backend/scripts/run_tests.sh                      # suite backend completa
npx tsc -b                                        # typecheck frontend
npx vitest run                                    # suite frontend completa
```

Criterio: 0 fallos nuevos respecto del baseline `83c9cd8`; los tests de segregación (`test_segregation_r143`), BR-18, BR-19/R-30 y el E2E `proceso-03` siguen en verde.

## 10. FASE 7 — Commit

- Un commit (o serie corta) en `main`, mensaje `SPEC-008: remediación QA Yolinel (QA-007/013/017 + HTML QA-002/003/012/014/015/016/018 + docs QA-001/005/006/008/009/010/011)`.
- Sin push en esta fase; sin ramas.

## 11. FASE 8 — Sensibilidad (mutaciones obligatorias)

| ID | Mutación | Test que debe fallar |
|---|---|---|
| **S1** | Permitir OC cross-BU (desactivar la comparación de cadena en BR-23) | BR-23 `test_br23_oc_chain` (AC-01.2/AC-01.4) |
| **S5** | Desactivar BR-14 accidentalmente (`require_segregation` ignorado / exclusiones no aplicadas) | Ya cubierta por `test_segregation_r143` g01-g06 (debe fallar) |
| **S6** | Ocultar el filtro de empresa en los listados | Test de listados/filtros (empresa presente y aplicada) |
| **S7** | Reintroducir el bucle de revisión (quitar estabilidad de dependencias) | `reviewCenter.requests.test.tsx` (conteo de peticiones) |
| **S8** | Reintroducir una etiqueta de maestro con clave de botón (`common.edit` para `tax_id`) | Guardián de columnas (`columnLabels.test.tsx`) |

Cada mutación: aplicar → ejecutar el test → registrar salida de fallo → revertir.

## 12. FASE 9 — Restore + post-mutación

- `git diff` limpio de mutaciones (`git status --porcelain` sin cambios ajenos).
- Re-ejecutar la suite completa (backend + frontend) y `npx tsc -b` → verde.
- Registrar evidencia en el certificado.

## 13. FASE 10 — Docs DOCX, certificación y push

1. Generar/actualizar los documentos DOCX de la ronda a partir de `02`/`03`/`04` y de `OPERATION_STATE_MACHINE.md` (misma herramienta que rondas anteriores).
2. Certificado de la ronda: `docs/` siguiendo el estándar del proyecto (`LOCALLY_CERTIFIED`), citando QA-ID → FR → test → evidencia.
3. `push` a `main` **solo** autorizado por el Orquestador (esta delegación no hace push).

## 14. Puertas de calidad (Definition of Done)

| Puerta | Criterio |
|---|---|
| G1 Clasificación | 18 hallazgos clasificados y con conteos que cuadran (5/2/3/7/6/0/5) |
| G2 RED→GREEN | Cada FR tiene test que falló antes y pasa después |
| G3 Regresión | Backend + frontend + `tsc -b` en verde |
| G4 Sensibilidad | S1, S5, S6, S7, S8 matan su test y el repo queda restaurado |
| G5 Documentación | AC-08.1…AC-08.8 verificables y trazables |
| G6 Owner | Las 5 decisiones pendientes quedan explícitamente abiertas; nada de ellas implementado |
| G7 Alcance | 0 llamadas SAP reales, 0 DROP/TRUNCATE, sin ramas, sin cambios en `.github/workflows` |

## 15. Riesgos y planes B

| Riesgo | Plan B |
|---|---|
| Posiciones de OC sin `WERKS` persistido | Derivar y persistir en importación; si no hay dato, cadena desconocida ⇒ permitir (nunca inventar) |
| `useCan` no puede estabilizarse sin tocar muchos usos | Exponer primitivos (`can: {approve: bool, ...}`) y consumir desde `ReviewCenter` |
| Nombres de padre requieren más joins de los previstos | Carga por lote de ids únicos (mapa id→nombre) |
| Test de conteo de peticiones frágil | Contar con `vi.fn()` sobre el cliente HTTP y comparar por delta entre interacciones, no por tiempo |
| PDF de QA aparece durante la ejecución | Recontrastar `01` y ajustar clasificación antes de certificar |
