# R-198 · FINDING — EVIDENCIAS: EL DETALLE LAS DESCARTA AL RECARGAR · ADJUNTAR SIN GATE · SIN AUDITORÍA

| Campo | Valor |
|---|---|
| **ID canónico** | **R-198** (asignado en `GA_CLAUDE_DISCOVERED_GAP_SPEC_REGISTER.md §0`; máximo previo R-189) |
| **Título** | `GET /operations/{id}` descarta `evidences`/`egg_storage_records` del detalle tipado: las evidencias subidas desaparecen de la UI al recargar; además se pueden adjuntar en cualquier estado (aprobado/consolidado/cancelado) sin auditoría, y el borrado físico ocurre antes del commit |
| **Severidad** | **P2** (§49: pérdida percibida de evidencia + trazabilidad; P-09) |
| **Clase** | `STATE_REFRESH` / `RESPONSE_CONTRACT` / `DATA_INTEGRITY` (borrado pre-commit) |
| **Proceso** | P-09 (auditoría/evidencias), transversal (evidencias de cualquier evento) |
| **Fecha · HEAD** | 2026-09-13 · `c0b4afc` |
| **Familia** | C#1/C#36 (informe C); E-15/GAP-12 (informe E/D); `R-52` (almacén) |
| **Paquete** | `audit/ga-claude-final-audit/specs/R-198/` (completo, 6 ficheros) |
| **GA-REM** | a asignar al autorizar; siguiente libre GA-REM-043 |
| **Bloquea SAP** | **SÍ** (integridad de la evidencia y de su rastro; §37) |
| **UAT del propietario** | sí, mínima (subir adjunto → refrescar → sigue visible; adjuntar en estado no editable ⇒ impedido) |

## 1 · Evidencia

### 1.1 Código (verificado en HEAD)

- `backend/app/operations/router.py:277-292` — el detalle (`OperationalEventDetailRead`, `schemas.py:298-305`, que **declara** `evidences`/`egg_storage_records`) hace `pop("evidences")`/`pop("egg_storage_records")` y no los reasigna ⇒ llegan **siempre `[]`**. La ruta `GET /operations/{id}/evidences` (`:334-341`) existe y sí devuelve las filas.
- `frontend/src/pages/operations/OperationDetailPage.tsx:66,76-114` — lista de evidencias en estado local; tras F5 el detalle vuelve vacío ⇒ «Sin archivos» aun habiendo adjuntos.
- Adjuntar/borrar permitido en cualquier estado: `:297,327` en la página; backend solo verifica unidad (`operations/service.py:1369`).
- Sin auditoría de subida/borrado: `operations/service.py:1363-1414` (ni `audit_accion` ni listeners); el **borrado físico del fichero ocurre antes** del `db.delete` + commit (`:1409-1414`) ⇒ si el commit falla, fichero perdido y fila viva.

### 1.2 Evidencia runtime

`OperationDetailPage` tras subir un adjunto y recargar: lista vacía (C#1); ruta de evidencias 200 con la fila (verificado en la misma sesión de auditoría).

## 2 · Causa raíz

El detalle tipado se construyó reasignando solo los bloques «conocidos» (bird/egg/feed/hatchery/inspection) y se descartó el resto; la UI confió en el detalle y no usa la ruta dedicada; nunca se añadió gate por estado ni auditoría a las operaciones de evidencia; el borrado se implementó antes del commit.

## 3 · Impacto

- Evidencias «desaparecen» tras recargar (confusión grave en auditoría; los usuarios re-suben duplicados).
- Adjuntos añadidos a eventos aprobados/consolidados/cancelados (contaminan la evidencia inmutable).
- Subida/borrado sin rastro (P-09 incompleto; borrado sin recuperación).
- Riesgo de estado partido (fichero borrado, fila viva) en fallos de commit.

## 4 · Dedup realizada (§48)

| Registro | Resultado |
|---|---|
| R-001…R-189 | `R-52` (almacén/volumen) y `GA-REM-009` (evidencias huérfanas) tratan almacenamiento, no el contrato del detalle ni el gate/auditoría. |
| Informes C/E/D | C#1/C#36 + E-15/GAP-12: sin registro previo conjunto. |

Conclusión: **nuevo**; ID asignado **R-198**.

## 5 · Propietario sugerido

Backend (`operations`) + frontend (detalle). Coordinación con P1-12-REOPEN (auditoría de evidencias entra allí como productor; aquí el gate y el contrato del detalle).

## 6 · Bloquea SAP y por qué

**SÍ (integridad/trazabilidad)**: las evidencias respaldan registros que irán a SAP; su persistencia visible y su rastro de alta/baja son requisitos de auditoría (§37).

## 7 · Interdependencias

- **P1-12-REOPEN**: productores de auditoría de evidencias (T-06 de ese paquete); este paquete define el contrato del detalle y el gate.
- **R-52/GA-REM-009**: almacén; sin cambios aquí.
- **R-215**: render de errores del detalle si aplica (ya usa `getErrorMessage`).
