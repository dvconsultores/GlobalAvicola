# GA-FE-07 · ESPECIFICACIÓN — ELEGIBILIDAD DE ÁREA ACTIVA EN REFERENCIAS NUEVAS DE LOTE

## 1 · Contexto

`GA-FE-06` cerró el contrato del alta de lote (`planned_close_date` + `area_id`) y `GA-FE-06-A` cerró la **pertenencia** de área (empresa). `GA-UAT-04` levantó una observación: el selector mostró un área propia **en baja lógica**. `GA-GOV-01` la clasificó `OWNER_DECISION_REQUIRED` (silencio canónico). El propietario eligió **Opción C — regla de dominio completa**, registrada como **OD-21**.

## 2 · Decisión del propietario (OD-21)

**Un recurso maestro dado de baja lógica NO puede usarse para NUEVAS referencias.** Desactivación ≠ borrado: la historia se conserva. (Principio general; implementación limitada a Área→Lote.)

## 3 · Origen GA-GOV-01

`audit/ga-gov-01/GA_GOV_01_CLASSIFICATION_DECISIONS.md §OBS-UAT-04` (pregunta A/B/C) → elección C del propietario → este desarrollo. Finding: **R-185** (P2, integridad de dominio).

## 4 · Problema

Hoy: `POST/PUT /lots` acepta áreas inactivas (RED runtime capturado: 201/200) y el selector las muestra. OD-21 define lo contrario.

## 5 · Alcance

- Elegibilidad de **Área** en **referencias nuevas desde Lote** (alta + cambio de referencia en edición).
- Filtro del selector del formulario de lote (transaccional).
- Backend autoritativo con detección correcta de cambio.

## 6 · Fuera de alcance

R-184 · OBS-UAT-01 (navegación) · mostrar área en detalle · otros maestros (principio general documentado, sin implementación) · jerarquías de área · reescritura de históricos · migraciones · permisos/roles/endpoints nuevos · BU-D10 · Wave B/C · SAP.

## 7 · Ciclo de vida del Área

`is_active` + baja oficial `DELETE /masters/areas/{id}` (baja lógica, fila permanece). Listado devuelve inactivas y `is_active` viaja en la respuesta. Traza completa: `GA_FE_07_AREA_LIFECYCLE_TRACE.md`.

## 8 · «Referencia nueva» (definición)

- Alta de lote con `area_id` no nulo.
- Edición que **cambia efectivamente** `area_id`: valor distinto (incluye a valor nulo→ID, ID→otro ID, e ID nulo histórico→ID). `area_id` igual al actual = **no** es referencia nueva. Omisión del campo = no es referencia nueva. `null` explícito = withdraw de referencia (no nueva asignación).

## 9 · «Referencia histórica» (definición)

`area_id` persistido que existía antes de un cambio de estado del área. Se conserva, se lee y no se reescribe.

## 10 · Semántica de ALTA

| Caso | Resultado |
|---|---|
| área activa propia | **ALLOW** (201) |
| área inactiva propia | **DENY (400)** — «Área inactiva», regla BR-07 |
| área ajena (activa/inactiva) | **DENY (400)** — «Área no encontrado» (anti-enumeración, R-182-A) |
| área inexistente | **DENY (400)** — «Área no encontrado» |
| `NULL` | **ALLOW** (contrato R-182 sin cambio) |

## 11 · Semántica de EDICIÓN (matriz histórica obligatoria)

| Caso | Payload | Resultado |
|---|---|---|
| H1 | omite `area_id` (área actual inactiva) | **ALLOW**; área intacta |
| H2 | `area_id` = mismo ID actual (aunque inactivo) | **ALLOW**; sin invalidación (no hay referencia nueva) |
| H3 | cambio a **inactiva** (X→Y inactivo) | **DENY (400)** |
| H4 | cambio a **activa** válida | **ALLOW**; fresh GET = nueva |
| H5 | cambio desde activa a inactiva | **DENY (400)** |
| — | cambio a ajena / inexistente | **DENY (400)** «no encontrado» |
| — | `area_id: null` (withdraw) | **ALLOW** (no nueva asignación) |

## 12 · Selector (frontend)

- Selector transaccional del formulario de lote: **solo áreas activas** (misma empresa — ya venía filtrado por el backend).
- Filtro cliente sobre el listado (el endpoint no ofrece filtro de estado; no se crea uno nuevo).
- **Masters admin NO se toca**: la lista administrativa sigue mostrando activas e inactivas.

## 13 · Autoridad del backend

El filtro UI es UX; el rechazo de backend es la guarda de dominio (defensa en profundidad). Petición directa con inactiva ⇒ DENY.

## 14 · Tenencia

Sin cambios: validador canónico `verificar_catalogo_de_empresa` **extendido** con `exigir_activo` (default `False`, callers existentes intactos). Ajena sigue «no encontrado».

## 15 · BU / RBAC

Sin cambios (se reverifican como regresión).

## 16 · Semántica de error

- Inactiva propia: `400 {"detail": "Área inactiva", "rule": "BR-07"}` — distinguible dentro del mismo inquilino (el propietario/admin la ve en maestros) con mensaje claro.
- Ajena/inexistente: `400 {"detail": "Área no encontrado", "rule": "BR-07"}` (anti-enumeración intacta; **sin** metadatos de empresa).

## 17 · Auditoría

Denegaciones: **0** filas de éxito (validación antes de persistir/auditar). Éxitos válidos e históricos: auditoría normal sin cambios.

## 18 · Desktop / Móvil / i18n

Desktop 1440×900 y móvil 390×844: mismo contrato de selector y formulario. Sin textos nuevos de UI (el mensaje del backend se muestra por el canal de errores existente; sin claves i18n nuevas → N/A documentado).

## 19 · Criterios de aceptación

**Gobernanza:** GA07-AC01 OD-21 registrada · AC02 principio general documentado sin implementación masiva · AC03 alcance Área→Lote explícito · AC04 referencias históricas válidas · AC05 ningún FK histórico reescrito.

**Alta:** AC06 activa propia ALLOW · AC07 inactiva propia DENY · AC08 ajena activa DENY · AC09 ajena inactiva DENY · AC10 inexistente DENY · AC11 NULL sin cambio.

**Edición:** AC12 update no relacionado con histórica inactiva ALLOW · AC13 histórica preservada · AC14 cambio a activa ALLOW · AC15 cambio a inactiva DENY · AC16 cambio a ajena DENY · AC17 mismo ID inactivo explícito sin falsa invalidación.

**Frontend:** AC18 inactiva ausente del selector nuevo · AC19 activa presente · AC20 sin IDs crudos · AC21 display histórico no se rompe · AC22 visibilidad admin no se degrada · AC23 móvil = desktop · AC24 ES completa · AC25 EN completa.

**Autoridad:** AC26 backend aplica la regla · AC27 filtro UI no es la única defensa · AC28 tenencia R-182-A intacta · AC29 BU OFF DENY · AC30 usuario sin BU DENY · AC31 RBAC DENY · AC32 global no evade ventana.

**Calidad:** AC33 sin falso éxito · AC34 denegación no persiste · AC35 sin auditoría de éxito en denegaciones · AC36 consola sin errores fatales · AC37 sin tormenta de fetch · AC38–AC42 regresiones GA-FE-02..06 · AC43 R-182 sigue CLOSED · AC44 R-184 intacto.

## 20 · Pruebas

- Backend PG (CI): `tests/test_lot_area_eligibility.py` (matriz 10/11 completa, persistencia + auditoría).
- Frontend vitest: `gaFe07.inactiveAreaEligibility.test.tsx` (selector filtrado + controles).
- Runtime autenticado E2E-01…12 (§ del encargo) sobre generación congelada.

## 21 · Despliegue

Push a main → backend/frontend rebuild → Watchtower. Sin cambios de pipeline.

## 22 · Evidencia

`GA_FE_07_*` (RED, backend, frontend, runtime, red, capturas, ledger, reconciliación de cierre, certificación, UAT) + actualizaciones de backlog/roadmap/catálogo/GA-GOV-01.

## 23 · Cierre del finding

R-185 → CLOSED solo con: denegaciones runtime + selector filtrado + preservación histórica + positivos + tenencia intacta + regresiones verdes.

## 24 · Readiness UAT del propietario

`GA_FE_07_OWNER_UAT.md`: 5 comprobaciones visibles (inactiva ausente, activa presente, histórico conservado tras baja, update no relacionado no destruye referencia, móvil).
