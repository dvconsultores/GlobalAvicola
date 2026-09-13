# P1-12-REOPEN · SPEC — UN PRODUCTOR ÚNICO DE AUDITORÍA, COBERTURA COMPLETA Y PRUEBA BAJO LIFESPAN

Fecha: 2026-09-13 · Riesgo reabierto: **P1-12** (P2 condicional) · HEAD `c0b4afc` · Origen E-11/E-10/E-12/E-13/E-15/E-16 · Registro G-18. Secciones §47.

## 1 · Contexto

La auditoría es el sistema probatorio del producto (P-09): aprobaciones, rechazos, correcciones, reversos, cambios de configuración y accesos. Hoy dos mecanismos escriben simultáneamente (listener `after_flush` + helpers) y varias acciones críticas no escriben nada; los tests no ven la duplicación (transporte sin `lifespan`).

## 2 · Evidencia

`P1-12-REOPEN_FINDING.md §1` (código + local H6/H8b + tabla de faltantes + norma).

## 3 · Causa raíz

Doble mecanismo sin reconciliación; productores fuera del listener nunca añadidos; rama de `complete_review` con acción incorrecta; tests sin `lifespan`.

## 4 · Impacto de negocio

Traza no fiable (recuentos, SLA, auditoría externa); acciones críticas sin evidencia; riesgo directo sobre la defensa de la certificación pre-SAP.

## 5 · Comportamiento actual

| Acción | Filas hoy (runtime) | Esperado |
|---|---|---|
| Alta de evento | `created ×2` | 1 |
| `start_review` | `review_started ×3` | 1 |
| `approve` (nivel 1) | `approved ×2` (+ `corrected` espuria) | 1 `approved` |
| Cerrar lote | 0 | 1 (`UPDATED`/`CLOSED` de lote) |
| Activación manual | 0 | 1 (con saldos) |
| Fase de lote | 0 | 1 |
| Usuario alta/edición/baja | 0 | 1 cada una |
| Evidencia subir/borrar | 0 | 1 cada una |
| Curva crear/activar | 0 | 1 cada una |
| Batch de revisión | 0 transición | 1 fila `pending_review` |

## 6 · Comportamiento esperado

1. **Un productor por acción** (decisión C-01; recomendado «híbrido determinista»):
   - El **listener** queda como único productor para `OperationalEvent`, `CorrectionLog`, `ApprovalAction` (CREATED/transiciones/acciones) **con** deduplicación: se retiran las llamadas `audit_event_created`/`audit_state_transition`/`audit_correction` que solapen, o se marcan con guarda de idempotencia por (entidad, id, acción, estado) — la opción final en C-01.
   - Los **helpers** (`audit_accion`) cubren lo que el listener no ve: lotes (cierre/activación/fases), usuarios, roles, evidencias, curvas, exportaciones, BU (ya cubiertos), SAP.
2. **Cobertura nueva** de la tabla §1.3, con `previous/new values` y motivo donde aplique (cierre: resumen; activación: saldos; fase: código/fecha; usuarios: rol/estado — sin secretos; evidencias: nombre/evento; exportaciones: informe/alcance).
3. **Fix de la fila espuria**: `review/service.py:363` usa `CORRECTED` solo en la rama de corrección; al aprobar escribe `REVIEW_COMPLETED`/`APPROVED` (según `:370-380`).
4. **Tests bajo `lifespan`**: el arnés registra el listener (o lo registra explícitamente) para que la duplicación sea detectable; las aserciones «exactamente 1» se vuelven verdaderas por construcción.
5. **Reconciliación GA-REM-032**: AC01 (login/logout) y AC04 (exportaciones) se anotan con su estado real (logout sigue en GA-REM-003 AC04; exportaciones se cubren aquí vía `audit_accion` desde el cliente o se documentan como `NOT_APPLICABLE_CLIENT` si se decide no auditar exportaciones cliente — C-03).

## 7 · Alcance

- `backend/app/audit/listeners.py`, `audit/helpers.py` (según C-01).
- Productores nuevos: `lots/service.py` (3), `auth/service.py` (usuarios), `operations/service.py` (evidencias), `masters/curves.py` (2).
- `review/service.py:363` (acción).
- Tests: `backend/tests/test_p112_audit_single_producer.py` (nuevo, con listener); ajuste de aserciones existentes si C-01 cambia semántica; `conftest.py` (registro de listener en el arnés de los tests afectados, sin cambiar el global).
- Sin migración; sin endpoint; sin permiso.

## 8 · Fuera de alcance

- Inmutabilidad BD (R-148) y empresa nulable (R-83).
- `AuditPage` (R-219) y filtros (E-17).
- Reverso: filas existentes; solo se añade la transición faltante del batch (E-06) si C-01 lo incluye.
- Auditoría de `close_lot` con snapshot de resumen completo (se registra lo esencial; ampliaciones futuras documentadas).

## 9 · Impacto frontend

Ninguno (una acción exportación cliente, si C-03=B, requeriría endpoint de auditoría — fuera por defecto).

## 10 · Impacto backend

Auditoría (listener/helpers), 6 módulos con productores nuevos, 1 fix de acción. Sin modelos.

## 11 · Contrato frontend↔backend

`GET /audit`/`timeline`: mismos esquemas; **menos** filas duplicadas y **más** filas reales. La UI de timeline (sin consumidor) sin cambio.

## 12 · Impacto en datos

Sin migración. Históricos con duplicados permanecen (no se borran; regla de inmutabilidad). Inventario de lectura opcional para dimensionar.

## 13 · Seguridad

Sin cambio de superficie; la traza gana completitud (incluye cambios de rol de usuarios, que hoy no dejan rastro).

## 14 · Inquilino

`audit_accion` sin empresa no escribe (R-83 vigente); los productores nuevos siguen el patrón (`company_id` del contexto).

## 15 · Unidad de negocio · 16 · RBAC

Sin cambio.

## 17 · Transacciones

Los productores nuevos escriben en la misma transacción del cambio (patrón `audit_accion`); sin bloqueos nuevos.

## 18 · Auditoría

Es el objeto del paquete: productor único, cobertura completa, prueba bajo `lifespan`.

## 19 · i18n · 20 · Escritorio · 21 · Móvil · 22 · Manejo de errores

Sin cambio (los mensajes no cambian; las acciones auditadas nuevas no alteran UX).

## 23 · Impacto de migración

Ninguna.

## 24 · Impacto SAP

La traza de aprobaciones/cambios es la evidencia de la que P-08 tomará eventos consolidados; su fiabilidad es requisito de la fase.

## 25 · Compatibilidad hacia atrás

- APIs: sin cambio.
- Tests existentes: pueden requerir actualización de conteos exactos (si hoy afirman 1 y el runtime estaba en 2, el fix los mantiene verdes; si alguno afirma 2 en runtime, se corrige con nota).
- Datos históricos: intactos.

## 26 · Criterios de aceptación

| AC | Criterio |
|---|---|
| AC-P112-01 | Alta de evento ⇒ exactamente 1 fila `created` (runtime con lifespan, API y UI) |
| AC-P112-02 | `start_review`/`approve`/`return`/`reject` ⇒ 1 fila cada uno (sin duplicados) |
| AC-P112-03 | `complete_review` al aprobar ⇒ sin fila `corrected` espuria |
| AC-P112-04 | Cierre de lote, activación manual y fase ⇒ 1 fila cada uno con valores |
| AC-P112-05 | Usuarios (alta/edición/baja/cambio rol) ⇒ 1 fila cada uno (sin secretos) |
| AC-P112-06 | Evidencias (subir/borrar) ⇒ 1 fila cada uno |
| AC-P112-07 | Curvas (crear/activar) ⇒ 1 fila cada uno |
| AC-P112-08 | Batch de revisión y contrapartida ⇒ fila de transición `pending_review` |
| AC-P112-09 | Suite completa verde **con** listener registrado (aserción «exactamente 1» verdadera) |
| AC-P112-10 | `GA-REM-032` reconciliado (AC01/AC04 anotados con estado real; C-03) |
| AC-P112-11 | Sin migración/endpoint/permiso; `git diff` limitado a audit + módulos + tests |

## 27 · Pruebas RED→GREEN

`§1`: `test_p112_01_alta_una_fila` (rojo en runtime-arnés: 2), `test_p112_02_aprobacion_una_fila` (rojo: 2+espuria), `test_p112_03_cierre_auditado` (rojo: 0), `test_p112_04_usuarios_auditados` (rojo: 0), `test_p112_05_evidencias_curvas` (rojo: 0), `test_p112_06_batch_transicion` (rojo: 0).

## 28 · E2E

`§2`: `R-P112-RT-01…08` (API/UI local: alta, aprobación, cierre, activación, usuario, evidencia, curva, batch) con recuento exacto por acción; artefacto `evidence/p112/runtime-{red,c3}.json`.

## 29 · UAT

No requerida. Verificación informativa: mostrar la línea de tiempo de un evento con 1 fila por acción tras el fix.

## 30 · Criterios de cierre

C-01/C-03 decididas · AC-01…11 verdes · sensibilidad (S1: reactivar el helper duplicado ⇒ AC-01/02 rojas; S2: retirar un productor nuevo ⇒ AC-04/05/06/07 rojas) · suite con `lifespan` verde · GA-REM-032 anotado · P1-12 → `CLOSED` con GA-REM asignado.
