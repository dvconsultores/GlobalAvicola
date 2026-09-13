# R-198 · SPEC — EVIDENCIAS PERSISTENTES EN EL DETALLE, GATE POR ESTADO Y AUDITORÍA DE ALTA/BAJA

Fecha: 2026-09-13 · Hallazgo canónico: **R-198** (P2 · bloquea P-09) · HEAD `c0b4afc` · Origen C#1/E-15 · Registro G-09. Secciones §47.

## 1 · Contexto

Las evidencias de un evento se suben desde el detalle (`multipart`), se listan localmente, y se consultan mediante `GET /operations/{id}/evidences`. El detalle tipado descarta el bloque; la UI no usa la ruta dedicada. Sin gate por estado, sin auditoría, con borrado físico pre-commit.

## 2 · Evidencia

`R-198_FINDING.md §1`: `router.py:277-292,334-341`; `OperationDetailPage.tsx:66,76-114,297,327`; `service.py:1363-1414`.

## 3 · Causa raíz

Construcción parcial del detalle + UI acoplada a él; operaciones de evidencia sin política de estado ni auditoría; orden de borrado incorrecto.

## 4 · Impacto de negocio

Evidencia no visible tras recargar (riesgo de pérdida percibida y duplicados); evidencia añadida a estados inmutables; sin rastro de quién subió/borró; borrados no atómicos.

## 5 · Comportamiento actual → esperado

| Aspecto | Hoy | Esperado |
|---|---|---|
| Detalle `GET /operations/{id}` | `evidences: []` siempre | devuelve las evidencias reales (o la UI re-lee la ruta dedicada — C-01) |
| F5 tras subir | «Sin archivos» | la evidencia sigue visible |
| Gate de estado | ninguno | solo estados editables (`draft/registered/pending_review/in_review/returned/rejected/corrected`) **o** política decidida (C-02) |
| Auditoría | ninguna | fila `UPDATED`/evidencia al subir y al borrar (con nombre y evento) |
| Borrado | `os.remove` antes del commit | commit primero (o borrado lógico) y borrado físico después / con recuperación |

## 6 · Comportamiento esperado (detalle)

1. **Contrato**: `GET /operations/{id}` incluye `evidences` (y `egg_storage_records` si se decide) **o** la pantalla consume `GET /operations/{id}/evidences` en la carga (opción C-01; se implementa una y se documenta).
2. **Persistencia tras F5/relogin**: la lista se reconstruye del servidor; subir ⇒ respuesta con la fila ⇒ recarga local; borrar ⇒ recarga.
3. **Gate**: subir/borrar solo en estados editables; en estados no editables, la UI oculta/deshabilita y el backend **deniega** (400/403 con mensaje) — seguridad en servidor, UI como espejo.
4. **Auditoría**: alta y baja escriben fila de auditoría (productor definido en P1-12-REOPEN T-06; aquí se fija el requisito y el contenido: `event_id`, `evidence_id`, nombre de archivo, tipo; sin contenido binario).
5. **Atomicidad**: subida: fichero a disco temporal/definitivo **tras** validar y persistir fila (o limpieza en fallo documentada); borrado: fila y fichero tras commit (o borrado lógico con limpieza posterior). Sin dejar fichero huérfano ni fila sin fichero (mitigación R-52/GA-REM-009 citada).
6. Sin migración; sin endpoint nuevo (la ruta de listado ya existe).

## 7 · Alcance

- `backend/app/operations/router.py` (detalle y/o uso de la ruta de evidencias), `service.py` (gate + auditoría + orden de borrado).
- `frontend/src/pages/operations/OperationDetailPage.tsx` (carga de evidencias del servidor; gate de botones).
- Tests: `backend/tests/test_r198_evidences_contract.py` (nuevo) + regresión evidencias; UI: unit de carga/gate si el arnés lo permite.
- Sin migración; sin permiso nuevo.

## 8 · Fuera de alcance

- Almacén/volumen (R-52/GA-REM-009/RES-05).
- Antivirus/inspección de contenido (G.2 del informe D, P3).
- Borrado lógico vs físico: se decide C-03 (por defecto: físico tras commit, manteniendo fila de auditoría).

## 9 · Impacto frontend

`OperationDetailPage` (carga/gate). Sin rediseño.

## 10 · Impacto backend

`router.py`/`service.py` de operaciones (3 puntos). Sin modelos.

## 11 · Contrato frontend↔backend

`GET /operations/{id}` gana `evidences` poblado (o la UI usa la ruta existente). `POST/DELETE` con gate y auditoría. Errores nuevos: 400/403 de estado no editable (mensaje claro).

## 12 · Impacto en datos

Sin migración. Filas existentes permanecen; la corrección es de contrato/gate.

## 13 · Seguridad

Gate en servidor (no solo UI); tenencia ya verificada; auditoría de operaciones añade trazabilidad. Sin cambio de permisos.

## 14 · Inquilino · 15 · Unidad · 16 · RBAC

Sin cambio (`operations:*`; unidad verificada en el servicio).

## 17 · Transacciones

Corrección del orden de borrado; subida con limpieza en fallo documentada. Sin bloqueos nuevos.

## 18 · Auditoría

Es requisito central (alta/baja); coordinado con P1-12-REOPEN.

## 19 · i18n

Mensaje de estado no editable (reutilizar existente si lo hay). Sin claves nuevas si el 400 usa texto del backend.

## 20 · Escritorio · 21 · Móvil

Botones de evidencia visibles en táctil (el proyecto tiene R3: acciones con `opacity-0 group-hover` — corregir a visibles táctil si se toca el bloque; anotado como parte del AC si aplica).

## 22 · Manejo de errores

| Caso | Comportamiento |
|---|---|
| 400/403 de estado | mensaje claro; sin crash |
| 413/límite | mensaje existente (10 MB/MIME) |
| 404 | evento inexistente (patrón) |

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

Indirecto (evidencia de registros consolidados).

## 25 · Compatibilidad hacia atrás

- Detalle: gana un campo (no rompe consumidores).
- Gate: adjuntar en estados no editables pasa de permitido a denegado (corrección).

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-R198-01 | Subir evidencia ⇒ aparece; **F5** ⇒ sigue apareciendo (contrato/releé) |
| AC-R198-02 | Relogin ⇒ sigue apareciendo |
| AC-R198-03 | Evento en estado no editable ⇒ subir/borrar **denegado en servidor** (400/403) y UI oculta/deshabilita |
| AC-R198-04 | Alta y baja escriben fila de auditoría (evento, evidencia, nombre, tipo) |
| AC-R198-05 | Borrado: no se pierde el fichero si el commit falla (orden/fix) |
| AC-R198-06 | `GET /operations/{id}/evidences` sigue operativa (control) |
| AC-R198-07 | Móvil: botones visibles/usables en táctil |
| AC-R198-08 | Sin migración/endpoint/permiso; diff limitado a operations + detalle |
| AC-R198-09 | Regresión: suite de evidencias (`test_od14_productive_surfaces` s03/s04, `test_lots_bu_enforcement` e05…) verde |

## 27 · Pruebas RED→GREEN

`§1`: `test_r198_01_detalle_devuelve_evidencias` (rojo), `test_r198_02_estado_no_editable_deniega` (rojo), `test_r198_03_alta_auditada`/`04_baja_auditada` (rojo), `test_r198_05_borrado_no_pierde_fichero` (rojo condicional al orden).

## 28 · E2E

`§2`: `R198-RT-01…05` (UI local: subir→F5→visible; gate; borrar→auditoría; móvil). Artefacto `evidence/r198/runtime-{red,c3}.json`.

## 29 · UAT

Mínima: subir un adjunto, refrescar y verlo; intentar adjuntar en un evento aprobado (impedido). 5 min, agrupable.

## 30 · Criterios de cierre

C-01/C-02/C-03 decididas · AC-01…09 verdes · sensibilidad (S1: retirar relectura ⇒ AC-01 rojo; S2: retirar gate servidor ⇒ AC-03 rojo) · sin migración/endpoint/permiso · R-198 → `CLOSED` con GA-REM asignado (coordinado con P1-12 T-06).
